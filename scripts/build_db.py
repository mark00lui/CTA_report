#!/usr/bin/env python3
"""把 state/、drivers/、reports/ 攤平成一個可查詢的衍生索引。

用法:
    python scripts/build_db.py              # 重建 .cache/research.sqlite
    python scripts/build_db.py --stats      # 重建並印出摘要
    python scripts/build_db.py --sql "..."  # 重建並跑一句 SQL

⚠⚠⚠ **這是衍生層，不是真相。**
來源真相是 `state/*.yaml`（可變、當下最佳判斷）與 `reports/**/*.md`（不可改、append-only）。
本檔的輸出**每次執行都整個砍掉重建**，不進版控（見 .gitignore 的 .cache/），
**任何在資料庫裡做的修改都會在下次執行時消失** —— 與 `build_index.py`／`build_site.py` 同規格。

## 它解決的問題

推論散文（`multiple_basis`、`signal.basis`、報告本文）在來源層是**不可查詢**的：
要回答「TSM 的 base 倍數理由這一年怎麼演化」只能 grep。
而 grep 回答不了「跨標的比較」「依日期排序」「和數值條件做交集」這類問題。

⚠ **但這不構成「改用 markdown database」的理由。**
那種做法要把來源真相換成 front-matter ＋ 查詢語法，
**會失去 `check_append_only.py` 的機械不可變性與 `git blame` 的逐行可追溯性 —— 淨損。**
正確的做法是來源真相不動，在旁邊長一層**可以隨時砍掉重建**的索引。

## 表

    tickers        一檔一列：論點、訊號、象限、加權目標價、現價、ATR
    scenarios      一檔三列：bear/base/bull 的機率、EPS、倍數、目標價、**倍數的錨**
    key_variables  型別化後的變數（kind／value／qualifier／unit／period／tier／as-of）
    kv_series      時間序列型變數的每一個 (period, value)
    kv_components  多值型變數的每一個 (name, value)
    events         event_log 的 date/level/summary（delta 已於 2026-09-13 搬進沿革檔）
    gaps           已知的未知
    driver_refs    個股 → driver 的引用與方向
    reports        每份報告的 front-matter（含 tp_before/tp_after，可看目標價的時間序列）
"""
import argparse
import glob
import io
import json
import os
import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML： pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, ".cache")
OUT_DB = os.path.join(OUT_DIR, "research.sqlite")

SCHEMA = """
CREATE TABLE tickers (
  ticker TEXT PRIMARY KEY, name TEXT, market TEXT,
  thesis TEXT, thesis_since TEXT,
  signal_rating TEXT, signal_conviction TEXT,
  quadrant TEXT, peer_group TEXT, frame_reviewed TEXT,
  valuation_base_year INTEGER,
  weighted_tp REAL, price REAL, price_date TEXT, atr20 REAL,
  invalidation TEXT, last_updated TEXT,
  n_gaps INTEGER, n_events INTEGER
);
CREATE TABLE scenarios (
  ticker TEXT, cell TEXT, p REAL, eps REAL, exit_multiple REAL, tp REAL,
  multiple_basis TEXT, p_basis TEXT, narrative TEXT,
  PRIMARY KEY (ticker, cell)
);
CREATE TABLE key_variables (
  ticker TEXT, name TEXT, kind TEXT, value TEXT, value_num REAL,
  value_qualifier TEXT, value_low REAL, value_high REAL,
  unit TEXT, unit_note TEXT, period TEXT, tier TEXT, updated TEXT, source TEXT
);
CREATE TABLE kv_series     (ticker TEXT, name TEXT, seq INTEGER, period TEXT, value REAL);
CREATE TABLE kv_components (ticker TEXT, name TEXT, seq INTEGER, part TEXT, value REAL);
CREATE TABLE events (ticker TEXT, date TEXT, level TEXT, summary TEXT);
CREATE TABLE gaps (ticker TEXT, question TEXT, how_to_close TEXT);
CREATE TABLE driver_refs (ticker TEXT, driver TEXT, direction TEXT, note TEXT);
CREATE TABLE reports (
  path TEXT PRIMARY KEY, date TEXT, ticker TEXT, name TEXT, level TEXT,
  signal TEXT, conviction TEXT,
  tp_before TEXT, tp_after TEXT, tp_delta TEXT,
  supersedes TEXT, driver TEXT, trigger TEXT, summary TEXT, n_sources INTEGER
);
CREATE INDEX ix_kv_ticker   ON key_variables(ticker);
CREATE INDEX ix_ev_ticker   ON events(ticker);
CREATE INDEX ix_rp_ticker   ON reports(ticker, date);
"""


def as_num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def s(v):
    return None if v is None else str(v)


def load_yaml(path):
    with io.open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh.read())


def state_files():
    for p in sorted(glob.glob(os.path.join(ROOT, "state", "*.yaml"))):
        b = os.path.basename(p)
        if b.startswith("_") or b == "coverage.yaml":
            continue
        yield p


def build(con):
    cur = con.cursor()
    cur.executescript(SCHEMA)
    n_bad = 0

    for path in state_files():
        d = load_yaml(path)
        tk = str(d.get("ticker"))
        sc = d.get("scenarios") or {}
        cta = d.get("cta") or {}
        sig = d.get("signal") or {}
        vf = d.get("valuation_frame") or {}
        gaps = d.get("gaps") or []
        events = d.get("event_log") or []

        cur.execute(
            "INSERT INTO tickers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tk, s(d.get("name")), s(d.get("market")),
             s(d.get("thesis")), s(d.get("thesis_since")),
             s(sig.get("rating")), s(sig.get("conviction")),
             s(vf.get("quadrant")), s(vf.get("peer_group")), s(vf.get("reviewed")),
             as_num(d.get("valuation_base_year")),
             as_num(sc.get("weighted_tp")), as_num(cta.get("price")),
             s(cta.get("updated")), as_num(cta.get("atr20")),
             s(cta.get("invalidation")), s(d.get("last_updated")),
             len(gaps), len(events)))

        for cell in ("bear", "base", "bull"):
            c = sc.get(cell) or {}
            if not c:
                continue
            cur.execute("INSERT INTO scenarios VALUES (?,?,?,?,?,?,?,?,?)",
                        (tk, cell, as_num(c.get("p")), as_num(c.get("eps")),
                         as_num(c.get("exit_multiple")), as_num(c.get("tp")),
                         s(c.get("multiple_basis")), s(c.get("p_basis")),
                         s(c.get("narrative"))))

        for kv in d.get("key_variables") or []:
            cur.execute("INSERT INTO key_variables VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (tk, s(kv.get("name")), s(kv.get("kind")),
                         s(kv.get("value")), as_num(kv.get("value")),
                         s(kv.get("value_qualifier")),
                         as_num(kv.get("value_low")), as_num(kv.get("value_high")),
                         s(kv.get("unit")), s(kv.get("unit_note")), s(kv.get("period")), s(kv.get("tier")),
                         s(kv.get("updated")), s(kv.get("source"))))

            for i, x in enumerate(kv.get("series") or []):
                if isinstance(x, dict):
                    cur.execute("INSERT INTO kv_series VALUES (?,?,?,?,?)",
                                (tk, s(kv.get("name")), i, s(x.get("period")), as_num(x.get("value"))))
            for i, x in enumerate(kv.get("components") or []):
                if isinstance(x, dict):
                    cur.execute("INSERT INTO kv_components VALUES (?,?,?,?,?)",
                                (tk, s(kv.get("name")), i, s(x.get("name")), as_num(x.get("value"))))

        for e in events:
            cur.execute("INSERT INTO events VALUES (?,?,?,?)",
                        (tk, s(e.get("date")), s(e.get("level")), s(e.get("summary"))))

        for g in gaps:
            if isinstance(g, dict):
                cur.execute("INSERT INTO gaps VALUES (?,?,?)",
                            (tk, s(g.get("question")), s(g.get("how_to_close"))))

        for r in d.get("driver_refs") or []:
            if isinstance(r, dict):
                cur.execute("INSERT INTO driver_refs VALUES (?,?,?,?)",
                            (tk, s(r.get("driver")), s(r.get("direction")), s(r.get("note"))))

    for f in sorted(glob.glob(os.path.join(ROOT, "reports", "**", "*.md"), recursive=True)):
        if os.path.basename(f) == "INDEX.md":
            continue
        text = io.open(f, encoding="utf-8").read()
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except Exception:
            # ⚠ 與 build_index.py 一樣只能略過，而那條「解析失敗只 warn」本身是未處理的缺口。
            n_bad += 1
            continue
        if not isinstance(fm, dict):
            n_bad += 1
            continue
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        srcs = fm.get("sources") or []
        cur.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (rel, s(fm.get("date")), s(fm.get("ticker")), s(fm.get("name")),
                     s(fm.get("level")), s(fm.get("signal")), s(fm.get("conviction")),
                     s(fm.get("tp_before")), s(fm.get("tp_after")), s(fm.get("tp_delta")),
                     s(fm.get("supersedes")), s(fm.get("driver")),
                     s(fm.get("trigger")), s(fm.get("summary")),
                     len(srcs) if isinstance(srcs, list) else 0))
    con.commit()
    return n_bad


CANNED = [
    ("覆蓋標的", "SELECT COUNT(*) FROM tickers"),
    ("三情境列數", "SELECT COUNT(*) FROM scenarios"),
    ("key_variables", "SELECT COUNT(*) FROM key_variables"),
    ("　├ 量化", "SELECT COUNT(*) FROM key_variables WHERE kind='量化'"),
    ("　└ 質性", "SELECT COUNT(*) FROM key_variables WHERE kind='質性'"),
    ("　　序列點", "SELECT COUNT(*) FROM kv_series"),
    ("　　分量", "SELECT COUNT(*) FROM kv_components"),
    ("事件", "SELECT COUNT(*) FROM events"),
    ("缺口", "SELECT COUNT(*) FROM gaps"),
    ("driver 引用", "SELECT COUNT(*) FROM driver_refs"),
    ("報告", "SELECT COUNT(*) FROM reports"),
]


def stats(con):
    cur = con.cursor()
    print("=== 衍生索引摘要 ===")
    for label, q in CANNED:
        print("  %-16s %d" % (label, cur.execute(q).fetchone()[0]))

    print()
    print("=== 只有衍生層才問得出來的幾個例子 ===")

    print("\n-- base 倍數的錨提到「同業」的標的（錨 B 是否真的用過）")
    rows = cur.execute(
        "SELECT ticker FROM scenarios WHERE cell='base' AND multiple_basis LIKE '%同業%' "
        "ORDER BY ticker").fetchall()
    print("   %d 檔：%s" % (len(rows), "／".join(r[0] for r in rows) or "無"))

    print("\n-- 訊號為偏多、但 invalidation 無合格位階的標的")
    rows = cur.execute(
        "SELECT ticker, signal_conviction FROM tickers "
        "WHERE signal_rating='偏多' AND invalidation='none_qualifies'").fetchall()
    print("   %d 檔：%s" % (len(rows), "／".join("%s(信心%s)" % r for r in rows) or "無"))

    print("\n-- 目標價曾被改過最多次的五檔（報告的 tp_after 變動次數）")
    rows = cur.execute(
        "SELECT ticker, COUNT(DISTINCT tp_after) n FROM reports "
        "WHERE ticker IS NOT NULL AND ticker<>'coverage' AND tp_after NOT IN ('n/a','__') "
        "GROUP BY ticker ORDER BY n DESC, ticker LIMIT 5").fetchall()
    for t, n in rows:
        print("   %-6s %d 個相異目標價" % (t, n))

    print("\n-- 每檔的缺口數（前五）")
    rows = cur.execute("SELECT ticker, n_gaps FROM tickers ORDER BY n_gaps DESC LIMIT 5").fetchall()
    for t, n in rows:
        print("   %-6s %d" % (t, n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="重建後印出摘要與示範查詢")
    ap.add_argument("--sql", help="重建後執行一句 SQL 並印出結果")
    a = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(OUT_DB):
        os.remove(OUT_DB)          # 單向產生：每次砍掉重建，手改必失
    con = sqlite3.connect(OUT_DB)
    n_bad = build(con)

    cur = con.cursor()
    n_t = cur.execute("SELECT COUNT(*) FROM tickers").fetchone()[0]
    n_r = cur.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    print("已產生 %s — 標的 %d、報告 %d%s"
          % (os.path.relpath(OUT_DB, ROOT).replace("\\", "/"), n_t, n_r,
             ("；⚠ front-matter 解析失敗 %d 份（未入表）" % n_bad) if n_bad else ""))

    if a.stats:
        print()
        stats(con)
    if a.sql:
        print()
        for row in cur.execute(a.sql).fetchall():
            print("  " + " | ".join("" if v is None else str(v)[:80] for v in row))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
