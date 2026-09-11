#!/usr/bin/env python3
"""從 state/ 與 drivers/ 產生 docs/index.html — GitHub Pages 的公開門面。

用法:
    python scripts/build_site.py

設計原則:

**單向產生，絕不手改。** 與 reports/INDEX.md 同一性質：docs/index.html 是輸出不是輸入。
手改它會在下次執行時被覆蓋，且 CI 會擋下不一致的提交。

**自我包含，不依賴 CDN。** 不引用外部字型、CSS、JS。GitHub Pages 雖然不像 Artifact
有 CSP 限制，但外部依賴會讓頁面在別人 fork 之後悄悄壞掉，也讓「這頁到底載入了什麼」
變成一個需要查證的問題。字型一律用系統堆疊。

**輸出必須是決定性的。** 不嵌入建置時間戳、不讀 git log（CI 的 shallow clone 只有一個
commit，git log 會產生不同結果而讓 freshness 檢查誤判）。時間軸改由 reports 的
front-matter 與 driver 的 event_log 組成 —— 那本來就是研究記錄，比 commit log 更貼題。

**不輸出任何倉位資訊。** 沒有配置圓餅圖、沒有權重長條、沒有損益曲線。頁面只呈現
state 與 drivers 裡已經存在的欄位。產生後仍會被 check_public.py 掃描（.html 已納入）。
"""
import datetime
import glob
import html
import json
import os
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
OUT = os.path.join(ROOT, "docs", "index.html")
PLACEHOLDER = "__"

SIGNAL_CLASS = {"偏多": "sig-long", "中性": "sig-flat", "偏空": "sig-short"}


def is_blank(v):
    return v is None or v == PLACEHOLDER or (isinstance(v, str) and v.strip("_ ") == "")


def clean(v):
    """把 __ 佔位符換成 None（前端統一顯示為「未填」），並把日期轉成字串。

    PyYAML 會把未加引號的 2026-08-27 解析成 datetime.date，那不能 JSON 序列化；
    而 state 裡的日期有些加引號（'2026-11'）有些沒有，兩種都會出現。
    """
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return None if is_blank(v) else v


def days_between(a, b):
    """b − a 的天數；任一端不是可解析的 ISO 日期就回 None（不假裝是 0）。"""
    try:
        da = datetime.date.fromisoformat(str(a)[:10])
        db = datetime.date.fromisoformat(str(b)[:10])
    except (TypeError, ValueError):
        return None
    return (db - da).days


def load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def front_matter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def collect():
    tickers, drivers, reports = [], [], []

    for path in sorted(glob.glob(os.path.join(ROOT, "state", "*.yaml"))):
        base = os.path.basename(path)
        if base.startswith("_") or base == "coverage.yaml":
            continue
        d = load_yaml(path)
        if isinstance(d, dict):
            d = clean(d)
            # 台股代號未加引號時 YAML 會解析成整數（3324 而非 "3324"），
            # 但報告 front-matter 用的是字串。型別不一致不會讓頁面壞掉，
            # 卻會讓任何想把 tickers 與 reports 對起來的程式安靜失敗。
            d["ticker"] = str(d.get("ticker", ""))
            # event_log 在此保留供 timeline 使用，投影會在稍後才做。
            tickers.append(d)

    cov = clean(load_yaml(os.path.join(ROOT, "state", "coverage.yaml")))

    for path in sorted(glob.glob(os.path.join(ROOT, "drivers", "*.yaml"))):
        if os.path.basename(path).startswith("_"):
            continue
        d = load_yaml(path)
        if isinstance(d, dict):
            drivers.append(clean(d))

    for path in sorted(glob.glob(os.path.join(ROOT, "reports", "**", "*.md"), recursive=True)):
        if os.path.basename(path) == "INDEX.md":
            continue
        fm = front_matter(path)
        if not fm:
            continue
        reports.append({
            "date": str(fm.get("date", "")),
            "ticker": str(fm.get("ticker", "")),
            "name": str(fm.get("name", "")),
            "level": str(fm.get("level", "")),
            "summary": str(fm.get("summary", "")),
            "signal": str(fm.get("signal", "")),
            "tp_after": fm.get("tp_after"),
            "path": os.path.relpath(path, ROOT).replace(os.sep, "/"),
        })
    reports.sort(key=lambda r: r["date"], reverse=True)

    # 時間軸 = 報告 + driver event_log + state event_log。三者都是研究記錄，不用 git log。
    #
    # state 的 event_log 必須納入，否則會漏掉一整類更新：
    #   建檔（state(<ticker>): 新增追蹤標的）只寫 state，不產生報告
    #   L1 重估依 /revalue 的規定「不寫報告，只更新 state」
    # 少了它們，一個叫「更新時間軸」的東西會安靜地漏掉這些事件 ——
    # 那比沒有時間軸更糟，因為它看起來是完整的。
    timeline = [{
        "date": r["date"], "kind": "report", "ticker": r["ticker"],
        "level": r["level"], "text": r["summary"], "path": r["path"],
    } for r in reports]

    for dv in drivers:
        for ev in (dv.get("event_log") or []):
            if not isinstance(ev, dict):
                continue
            timeline.append({
                "date": str(ev.get("date", "")), "kind": "driver",
                "ticker": dv.get("id", ""), "level": "driver",
                "text": str(ev.get("summary", "")), "path": None,
            })

    # 同一天同一檔的同一個等級若已有報告，就不再放 state 事件 —— 報告是較豐富的那一份。
    #
    # 去重鍵必須含 level。只用 (date, ticker) 會出事：建檔與當日稍後的重估是同一天同一檔，
    # 但等級不同（建檔是「—」、重估是 L2）。少了 level，建檔會被重估的報告連帶洗掉 ——
    # 而建檔正是這段程式要救回來的那一類事件。
    covered = {(r["date"], r["ticker"], r["level"]) for r in reports}
    for t in tickers:
        tk = str(t.get("ticker", ""))
        for ev in (t.get("event_log") or []):
            if not isinstance(ev, dict):
                continue
            date = str(ev.get("date", ""))
            lvl = str(ev.get("level") or "state")
            if (date, tk, lvl) in covered:
                continue
            timeline.append({
                "date": date, "kind": "state", "ticker": tk,
                "level": lvl, "text": str(ev.get("summary", "")), "path": None,
            })

    timeline.sort(key=lambda x: (x["date"], x["kind"]), reverse=True)

    # ⚠ 投影：只把畫面真的會渲染的欄位送進 payload。
    #
    # 為什麼這件事重要，而且不只是效能問題 ——
    # CLAUDE.md：「docs/index.html 是洩漏面積最大的檔案。它把 state 與 drivers
    # 整頁攤開給不讀 YAML 的人看，且掛在一個比 repo 本身更容易被看到的網址上。」
    # 實測（2026-09-10）：投影前 tickers 佔 486,905 字元，其中 **52.3% 的欄位
    # 從未被前端渲染**（event_log 135K、valuation_frame 43K、notes 21K…）——
    # 那些內容仍然完整地躺在公開頁面的原始碼裡，只是沒有畫出來。
    # **沒被畫出來不等於沒被送出去。**
    #
    # ⚠ 投影名單要對照前端維護。新增欄位到卡片時，必須同步加進 TICKER_FIELDS，
    # 否則畫面會安靜地顯示「未填」—— 那是最難查的一種壞法。
    TICKER_FIELDS = (
        "ticker", "name", "market", "thesis", "valuation_base_year",
        "last_updated", "factor_tags", "driver_refs",
        "key_variables", "falsifiers", "scenarios", "cta", "signal",
        # ⚠ 以下兩項此前被送出但未渲染。本次選擇「渲染它們」而非「砍掉」——
        # 理由是本倉庫的核心紀律：看不見的無知會被當成判斷使用。
        # 缺口與檢驗點正是不確定性的所在，把它們藏起來的介面比醜的介面糟。
        "gaps", "checkpoints",
    )
    slim = []
    for t in tickers:
        o = {k: t[k] for k in TICKER_FIELDS if k in t}
        # valuation_frame 整塊很大且多半是推導過程（屬 repo 的內容），
        # 但象限與複核日期是讀者該看到的兩個字，單獨留下。
        vf = t.get("valuation_frame") or {}
        if isinstance(vf, dict):
            o["quadrant"] = vf.get("quadrant")
            o["frame_reviewed"] = vf.get("reviewed")
        slim.append(o)

    # ⚠ 兩個衍生欄位。兩者都不是 state 裡的欄位，是算出來的 ——
    # 因此畫面上必須寫出算式與口徑，否則讀者會把它們當成一手數字。
    #
    # upside（上檔空間）＝ weighted_tp ÷ cta.price − 1。
    # ⚠⚠ cta.price 是**該檔最後覆核時的錨定價**，不是即時報價，而各檔的 cta.updated
    # 不同（本輪實測跨兩週）。所以這一欄是一組**時點不齊**的數字，會隨時間失真。
    # price_age_days 就是為了讓那件事看得見：藏起來的話，讀者會把它讀成現價，
    # 而一個把缺口藏起來的漂亮介面比醜的介面糟得多。
    #
    # 基準日刻意取「資料裡最新的日期」而不是今天：輸出必須是決定性的
    # （見本檔開頭的設計原則），用執行當下的日期會讓同一份 state 產生不同的 HTML。
    all_dates = [cov.get("as_of") if isinstance(cov, dict) else None]
    for t in slim:
        all_dates.append(t.get("last_updated"))
        all_dates.append((t.get("cta") or {}).get("updated"))
    iso = sorted(d for d in (str(x)[:10] for x in all_dates if x)
                 if len(d) == 10 and d[4] == "-" and d[7] == "-")
    ref_date = iso[-1] if iso else ""

    for t in slim:
        tp = (t.get("scenarios") or {}).get("weighted_tp")
        px = (t.get("cta") or {}).get("price")
        ok = (isinstance(tp, (int, float)) and not isinstance(tp, bool)
              and isinstance(px, (int, float)) and not isinstance(px, bool) and px > 0)
        t["upside"] = round(tp / px - 1, 6) if ok else None
        t["price_age_days"] = days_between((t.get("cta") or {}).get("updated"), ref_date)

    return {"tickers": slim, "coverage": cov, "drivers": drivers,
            "reports": reports, "timeline": timeline, "ref_date": ref_date}


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#0a0908; --panel:#141210; --panel2:#1c1917; --line:#2b2724;
  --ink:#e8e3dc; --muted:#9a9188; --dim:#6b635c;
  --gold:#c9a449; --long:#e05252; --short:#3fa87a; --flat:#8a827a;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Songti TC","Noto Serif CJK TC",serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif;
  line-height:1.65;font-size:15px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 80px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:.01em;line-height:1.25}
h1{font-size:clamp(28px,5vw,42px);margin:0 0 8px}
h2{font-size:clamp(20px,3vw,26px);margin:56px 0 6px;color:var(--gold)}
h3{font-size:17px;margin:0}
a{color:var(--gold)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.sub{color:var(--muted);font-size:14px;margin:0}
.dim{color:var(--dim)}
header{border-bottom:1px solid var(--line);padding:48px 0 30px;margin-bottom:8px}
.meta{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 20px;margin:6px 0 0}
.meta span{display:inline-flex;align-items:baseline;gap:5px}
.meta b{font-family:var(--mono);font-variant-numeric:tabular-nums;
  font-size:15px;font-weight:600;color:var(--ink)}
.meta i{font-style:normal;font-size:12.5px;color:var(--dim)}
.lede{color:var(--ink);font-size:clamp(15px,1.7vw,17px);max-width:60ch;margin:18px 0 0}
.prov{color:var(--muted);font-size:14px;max-width:66ch;margin:7px 0 0}
.prov b{color:var(--gold);font-weight:600}
.disc{margin:26px 0 0;padding:16px 18px;border-left:3px solid var(--gold);
  background:var(--panel);color:var(--muted);font-size:13.5px;border-radius:0 8px 8px 0}
.disc h2{font-family:var(--serif);font-size:16px;color:var(--gold);
  margin:0 0 9px;font-weight:600;line-height:1.4}
.disc ul{margin:0;padding:0;list-style:none}
.disc li{position:relative;padding-left:15px;margin:0 0 5px}
.disc li::before{content:"—";position:absolute;left:0;color:var(--dim)}
.disc strong{color:var(--ink);font-weight:600}
.disc .fine{margin:10px 0 0;padding-top:9px;border-top:1px solid var(--line);
  color:var(--dim);font-size:12.5px}
.secnote{color:var(--muted);font-size:14px;margin:0 0 20px;max-width:74ch}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.card-hd{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:4px}
.tk{font-family:var(--mono);font-size:19px;color:var(--gold);font-weight:600}
.nm{color:var(--muted);font-size:13px}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;
  font-weight:600;border:1px solid currentColor;white-space:nowrap}
.sig-long{color:var(--long)}.sig-short{color:var(--short)}.sig-flat{color:var(--flat)}
.tags{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 12px}
.tag{font-family:var(--mono);font-size:11px;color:var(--dim);
  border:1px solid var(--line);border-radius:4px;padding:1px 6px}
.thesis{font-size:14px;color:var(--ink);margin:0 0 14px;padding-left:11px;border-left:2px solid var(--line)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 14px;font-size:13px;margin:0 0 12px}
.kv dt{color:var(--muted)}
.kv dd{margin:0;font-family:var(--mono);text-align:right}
.pbar{display:flex;height:7px;border-radius:4px;overflow:hidden;margin:12px 0 6px;background:var(--panel2)}
.pbar i{display:block}
.pbar .b{background:var(--short)}.pbar .m{background:var(--flat)}.pbar .u{background:var(--long)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:right;padding:5px 6px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:500;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
td.n{font-family:var(--mono);font-variant-numeric:tabular-nums}
details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
summary{cursor:pointer;color:var(--muted);font-size:12.5px;list-style:none;user-select:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ ";color:var(--gold)}
details[open]>summary::before{content:"▾ "}
details>div{padding-top:10px}
.ok{color:var(--short)}.warn{color:var(--gold)}.bad{color:var(--long)}
.fx{font-size:12.5px;margin:0 0 9px;padding-left:11px;border-left:2px solid var(--line)}
.fx b{font-weight:600}
.scroll{overflow-x:auto}
.tl{list-style:none;padding:0;margin:0;border-left:1px solid var(--line)}
.tl li{position:relative;padding:0 0 20px 22px}
.tl li::before{content:"";position:absolute;left:-4.5px;top:8px;width:8px;height:8px;
  border-radius:50%;background:var(--gold)}
.tl li.driver::before{background:var(--flat)}
.tl li.state::before{background:var(--dim)}
.tl .d{font-family:var(--mono);font-size:12px;color:var(--dim)}
.tl .t{font-size:14px;margin:2px 0 0}
.tl .m{font-size:12px;color:var(--muted);margin-top:2px}
.lvl{font-family:var(--mono);font-size:11px;border:1px solid var(--line);
  border-radius:4px;padding:0 5px;color:var(--muted);margin-left:6px}
.sum{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 18px}
.sum .s{background:var(--panel);border:1px solid var(--line);border-radius:8px;
  padding:9px 13px;display:flex;align-items:baseline;gap:8px}
.sum .s b{font-family:var(--mono);font-size:19px;font-variant-numeric:tabular-nums;color:var(--ink)}
.sum .s span{font-size:12px;color:var(--muted)}
.sum .s.hl{border-left:3px solid var(--gold)}
.sum .s.hl b{color:var(--gold)}
.gapn{font-family:var(--mono);font-size:11px;color:var(--gold);
  border:1px solid var(--line);border-radius:3px;padding:1px 5px;margin-left:6px}
.q{margin:0 0 10px;font-size:13.5px;line-height:1.6}
.q .how{display:block;color:var(--dim);font-size:12.5px;margin-top:2px}
.sig-mark{font-family:var(--mono);margin-right:4px}
.prem{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:0 8px 8px 0;padding:16px 18px;margin:0 0 16px}
footer{margin-top:72px;padding-top:22px;border-top:1px solid var(--line);
  color:var(--dim);font-size:12.5px}
@media (max-width:560px){.kv dd{text-align:left}.grid{grid-template-columns:1fr}}
"""


def esc(v):
    return html.escape("" if v is None else str(v))


# ── 掃描視圖（39 檔）專用樣式 ───────────────────────────────────────────────
#
# 刻意與上面的 CSS 分成兩段而不是混寫：上面那段是原本的卡片式版面（驅動因子、
# 覆蓋層、時間軸仍在用），這段是 2026-09-11 為「39 檔要能互相比較」新增的表格視圖。
# 分開讓 git diff 看得出哪些規則是新的，也讓日後要拆掉其中一套時不必逐行辨認。
#
# ⚠ 顏色語意沿用上面的 --long／--short：紅＝偏多、綠＝偏空（台股慣例）。
# 上檔空間為正用紅、為負用綠，與訊號評級同一套語彙。而顏色一律附帶正負號與文字 ——
# 紅綠色盲讀者靠 ＋／− 與百分比本身就能讀完整張表。
CSS_SCAN = """
.tool{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:0 0 10px}
.tool label{font-size:12px;color:var(--muted);display:inline-flex;align-items:center;gap:6px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden;background:var(--panel)}
.seg button{appearance:none;background:none;border:0;color:var(--muted);font:inherit;
  font-size:12.5px;padding:4px 9px;cursor:pointer}
.seg button+button{border-left:1px solid var(--line)}
.seg button[aria-pressed="true"]{background:var(--panel2);color:var(--gold)}
.btn{appearance:none;background:var(--panel);border:1px solid var(--line);border-radius:6px;
  color:var(--muted);font:inherit;font-size:12.5px;padding:4px 10px;cursor:pointer}
.btn[aria-pressed="true"]{color:var(--gold);border-color:var(--gold)}
.btn:hover,.seg button:hover{color:var(--ink)}
.srch{background:var(--panel);border:1px solid var(--line);border-radius:6px;color:var(--ink);
  font:inherit;font-size:13px;padding:5px 9px;min-width:170px}
.tagbox{margin:0 0 10px;border-top:0;padding-top:0}
.tagpick{display:flex;flex-wrap:wrap;gap:5px;padding-top:8px}
.tagpick button{appearance:none;font-family:var(--mono);font-size:11px;color:var(--dim);
  background:none;border:1px solid var(--line);border-radius:4px;padding:1px 6px;cursor:pointer}
.tagpick button[aria-pressed="true"]{color:var(--gold);border-color:var(--gold)}
.status{font-size:12.5px;color:var(--muted);margin:0 0 10px;line-height:1.7}
.status b{color:var(--gold);font-weight:600}
table.scan th{position:sticky;top:0;background:var(--bg);z-index:2;white-space:nowrap}
table.scan th button{appearance:none;background:none;border:0;color:var(--muted);font:inherit;
  font-size:11.5px;letter-spacing:.04em;cursor:pointer;padding:0}
table.scan th[aria-sort] button{color:var(--gold)}
table.scan td{padding:7px 6px;vertical-align:top}
table.scan tr.r:hover>td{background:var(--panel)}
table.scan tr.grp th{position:static;text-transform:none;font-size:12px;color:var(--gold);
  background:var(--panel2);padding:6px 8px;text-align:left;letter-spacing:0}
table.scan tr.grp th .c{color:var(--dim);font-family:var(--mono);margin-left:8px}
.tg{appearance:none;background:none;border:0;color:inherit;font:inherit;text-align:left;
  cursor:pointer;padding:0;display:flex;gap:2px 6px;align-items:baseline;flex-wrap:wrap}
.tg:hover .nm{color:var(--ink)}
.tg .tw{color:var(--gold);font-size:10px;font-family:var(--mono)}
.tg .tk{font-family:var(--mono);font-size:15px;color:var(--gold);font-weight:600}
.tg .nm{color:var(--muted);font-size:12.5px}
.mk{font-family:var(--mono);font-size:10.5px;color:var(--dim);border:1px solid var(--line);
  border-radius:3px;padding:0 4px}
.ubar{position:relative;display:block;height:5px;margin-top:5px;min-width:76px;
  background:var(--panel2);border-radius:3px}
.ubar i{position:absolute;top:0;height:5px}
.ubar .zero{left:calc(50% - 0.5px);width:1px;background:var(--dim)}
.ubar .pos{left:50%;background:var(--long);border-radius:0 3px 3px 0}
.ubar .neg{right:50%;background:var(--short);border-radius:3px 0 0 3px}
.age{display:block;font-family:var(--mono);font-size:10.5px;color:var(--dim);white-space:nowrap}
.age.old{color:var(--gold)}
.mini{font-size:11.5px;color:var(--muted);display:block}
tr.det>td{background:var(--panel);border-bottom:1px solid var(--gold);padding:0 6px 16px}
.dpane{display:grid;gap:14px;padding-top:12px}
.blk{border-top:1px solid var(--line);padding-top:10px}
.blk>h4{font-family:var(--serif);font-size:14px;color:var(--gold);margin:0 0 7px;font-weight:600}
.blk>h4 .sub2{font-family:system-ui,sans-serif;font-size:11.5px;color:var(--dim);
  font-weight:400;margin-left:6px}
.lb{display:inline;color:var(--dim);font-size:12px;margin-right:4px}
.wm{font-style:normal;color:var(--gold)}
code{font-family:var(--mono);font-size:.92em;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{font-size:11.5px;color:var(--muted);border:1px solid var(--line);border-radius:4px;
  padding:1px 7px;text-decoration:none;display:inline-block}
a.chip:hover{border-color:var(--gold)}
.chip .d{font-family:var(--mono)}
.honest{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:0 8px 8px 0;padding:14px 16px;margin:0 0 18px;font-size:13.5px;color:var(--muted)}
.honest h3{font-size:15px;color:var(--gold);margin:0 0 7px}
.honest p{margin:0 0 7px}
.honest p:last-child{margin-bottom:0}
.honest .f{font-family:var(--mono);color:var(--ink);font-variant-numeric:tabular-nums;
  background:var(--panel2);border-radius:5px;padding:5px 9px;display:inline-block}
.honest strong{color:var(--ink);font-weight:600}
.legend{font-size:12px;color:var(--dim);margin:12px 0 0;max-width:78ch;line-height:1.7}
@media (max-width:900px){.c-quad,.c-stance{display:none}}
@media (max-width:720px){.c-upd{display:none}}
@media (max-width:560px){.c-tp{display:none}.dpane{gap:12px}}
"""


# ── 覆蓋層專用樣式 ─────────────────────────────────────────────────────────
#
# 第三段 CSS，理由同 CSS_SCAN：讓 git diff 看得出哪些規則是新的。這一段只服務
# 「等權基準下的因子分布」與「連動關係」兩張表 —— 它們的資料形狀與別處不同
# （見 JS 裡 segs() 上方的註解），需要自己的密度規則。
#
# ⚠ .cbar 是**逐列獨立**的水平長條，量的是檔數（欄名即口徑），不會被加總成一個整體。
# 那是它與甜甜圈／堆疊長條的分界：後者把各格拼成一個「全部」，那個形狀就是資產配置
# 的視覺語彙。刻意用中性灰（--flat）而非金色 —— 檔數不是訊號，不該搶強調色。
CSS_COV = """
table.mix{min-width:700px}
table.mix td{padding:7px 7px;vertical-align:top}
table.mix tr:hover>td{background:var(--panel2)}
table.mix td.k{font-family:var(--mono);white-space:nowrap}
table.mix td.au{white-space:nowrap;font-size:11.5px}
table.mix td.nt{min-width:290px}
.nt,.hist,.cwl>details>div{overflow-wrap:anywhere}
.cbar{display:block;height:5px;margin-top:5px;min-width:64px;background:var(--panel2);border-radius:3px}
.cbar i{display:block;height:5px;background:var(--flat);border-radius:3px}
.nt details{margin:0;border-top:0;padding:0}
.nt>details>summary{display:flex;gap:5px;align-items:flex-start;color:var(--muted)}
.nt>details>summary::before{flex:none}
.nt .pv{flex:1 1 auto;min-width:0}
.nt .full{display:block;font-size:12.5px;line-height:1.55}
.clamp{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;
  overflow:hidden;font-size:12.5px;line-height:1.55}
/* ⚠ 不支援 -webkit-line-clamp 的瀏覽器會直接顯示全文 —— 那是刻意的降級方向：
   寧可一次顯示太多，也不要讓任何一段註記在某些瀏覽器上安靜地消失。 */
details[open] .clamp{display:block;-webkit-line-clamp:unset;overflow:visible}
.nth{flex:none;font-family:var(--mono);font-size:10.5px;color:var(--gold);
  border:1px solid var(--line);border-radius:3px;padding:0 4px;white-space:nowrap}
.hist{margin:8px 0 0;padding:0 0 0 2px;list-style:none}
.hist li{margin:0 0 10px;font-size:12.5px;color:var(--muted)}
.hist .hd{display:block;font-family:var(--mono);font-size:10.5px;color:var(--dim);
  letter-spacing:.03em;margin-bottom:1px}
.drift{font-size:12.5px;color:var(--muted);margin:12px 0 0;padding-top:10px;
  border-top:1px solid var(--line);line-height:1.75}
.drift b{color:var(--ink);font-weight:600}
.cwl{margin-top:4px}
.cwl>details{margin:0;border-top:1px solid var(--line);padding:7px 0}
.cwl>details>summary{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap;
  font-size:13px;color:var(--ink);line-height:1.5}
.cwl>details>summary::before{flex:none}
.cwl>details>div{padding:8px 0 10px 16px;font-size:13px;color:var(--muted)}
.cwl .who{font-weight:600;flex:0 1 auto;min-width:0}
.cwl .hl2{color:var(--muted);flex:1 1 14ch;min-width:0}
.cwl .cwd{font-family:var(--mono);font-size:10.5px;color:var(--dim);flex:none}
.cwl>details:target{background:var(--panel2)}
@media (max-width:560px){.cwl>details>div{padding-left:4px}}
"""


# ── 前端 ───────────────────────────────────────────────────────────────────
#
# ⚠ 這段是純字串（不是 f-string），所以 JS 的 `{}` 與 `${}` 都照寫、不必加倍。
# build_html() 只把它與 payload 一起插進 HTML 骨架。
JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const COV = D.coverage || {};
const TS = (D.tickers || []).slice();
const BY = {}; TS.forEach(t => { BY[t.ticker] = t; });
// 基準日 = 全站資料裡最新的一個日期（coverage.as_of 與各檔覆核日取最大），由產生器算好。
// 不用 new Date() —— 頁面是靜態輸出，拿瀏覽器當下時間會讓同一份 HTML 每天說不同的話。
const REF = D.ref_date || COV.as_of || '';
const SC = {'偏多':'sig-long','中性':'sig-flat','偏空':'sig-short'};
// ⚠ 訊號不可只用顏色區分 —— 紅綠色盲讀者看不出偏多偏空。
//    顏色沿用台股慣例（紅漲綠跌），符號與文字是它的無障礙備援，三者並存。
const SM = {'偏多':'▲','中性':'●','偏空':'▼'};
const UPFULL = 40;          // 上檔空間長條的滿格刻度：±40%
const STALE = 7;            // 錨定價距基準日幾天起標記為「已舊」
const TL_HEAD = 30;         // 時間軸預設顯示筆數

const E = s => String(s ?? '').replace(/[&<>"']/g, c => (
  {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// state 的長欄位（signal.basis、multiple_basis、gaps[].question…）是 markdown，
// 含大量 **粗體** 與 ⚠。原樣輸出會像壞掉的純文字，故在此處理最小子集：
// 粗體、行內 code、換行，並把 ⚠／✓ 串染成金色 —— 那是作者標注重要性的方式。
function md(s) {
  if (s === null || s === undefined || s === '') return '<span class="dim">未填</span>';
  return E(s)
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/(⚠+|✓+)/g, '<em class="wm">$1</em>')
    .replace(/\r?\n/g, '<br>');
}
const plain = s => String(s ?? '').replace(/\*\*/g, '').replace(/`/g, '').replace(/\s+/g, ' ').trim();

// ── 報告路徑 → 可點的連結 ────────────────────────────────────────────────
//
// ⚠ 連結**不能**寫成相對路徑。GitHub Pages 把 docs/ 當站台根目錄，
//    `../reports/...` 會跑到 mark00lui.github.io/reports/...（站外），而且 reports/
//    根本沒有被發佈 —— 那是一個保證 404 的連結。對照倉庫要走 blob 網址，
//    與時間軸用的是同一個 base。
const GH = 'https://github.com/mark00lui/CTA_report/blob/main/';
// ⚠ 只把**確實存在於 D.reports 裡**的路徑變成連結，不用正則猜。
//    代價是：文字提到一份還沒建檔的報告時它維持純文字 —— 那正是想要的降級方向，
//    因為一個壞掉的連結會讓讀者以為內容不存在。長的先換，避免互相吃到。
const RPATH = (D.reports || []).map(r => r.path).filter(Boolean)
  .sort((a, b) => b.length - a.length);
function mdRef(s) {
  let out = md(s);
  for (let i = 0; i < RPATH.length; i++) {
    const p = RPATH[i];
    if (out.indexOf(p) >= 0) out = out.split(p).join('<a href="' + GH + p + '">' + p + '</a>');
  }
  return out;
}
function clip(s, k) {
  const p = plain(s);
  return p.length > k ? E(p.slice(0, k)) + '…' : E(p);
}
const n = v => (v === null || v === undefined || v === '') ? '<span class="dim">未填</span>' : E(v);
function num(v) {
  if (typeof v !== 'number' || !isFinite(v)) return n(v);
  const s = Number.isInteger(v) ? String(v) : v.toFixed(2);
  const p = s.split('.');
  return p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (p[1] ? '.' + p[1] : '');
}
const pct = p => (p === null || p === undefined) ? 0 : Math.round(p * 100);
const upTxt = u => (u >= 0 ? '+' : '−') + (Math.abs(u) * 100).toFixed(1) + '%';
const upCls = u => u > 0 ? 'sig-long' : (u < 0 ? 'sig-short' : 'sig-flat');
// null 一律排在最後，不假裝它是 0 —— 缺值排到中間會被讀成「沒什麼上檔空間」。
const cmpN = (a, b) => {
  const x = (typeof a === 'number'), y = (typeof b === 'number');
  if (!x && !y) return 0;
  if (!x) return 1;
  if (!y) return -1;
  return b - a;
};

function upBar(u) {
  if (typeof u !== 'number') return '';
  const w = (Math.min(Math.abs(u) * 100, UPFULL) / UPFULL * 50).toFixed(1);
  const side = u >= 0 ? '<i class="pos" style="width:' + w + '%"></i>'
                      : '<i class="neg" style="width:' + w + '%"></i>';
  return '<span class="ubar" aria-hidden="true"><i class="zero"></i>' + side + '</span>';
}

// 錨定價的新舊 —— 這一格存在的理由見頁面上「上檔空間什麼時候會說謊」那段。
function ageTag(d) {
  if (typeof d !== 'number' || d <= 2) return '';
  return '<span class="age' + (d >= STALE ? ' old' : '') + '" title="錨定價時點距基準日 '
    + E(REF) + ' 已 ' + d + ' 天；這段期間的價格變動不在這一頁上">' + d + ' 天前</span>';
}

function fxState(s) {
  if (s === '未觸發') return '<span class="ok">○ 未觸發</span>';
  if (s === '已觸發') return '<span class="bad">● 已觸發</span>';
  return '<span class="warn">△ ' + E(s || '未驗證') + '</span>';
}

function sigBadge(sig) {
  const r = sig.rating || '未評級';
  return '<span class="badge ' + (SC[r] || 'sig-flat') + '" aria-label="訊號評級 ' + E(r) + '">'
    + '<span class="sig-mark" aria-hidden="true">' + (SM[r] || '○') + '</span>' + E(r) + '</span>';
}

// driver 方向：同一個 driver 對硬體端與平台端常常相反，不可抹平成一個值。
function dirTxt(d) {
  if (d === '+') return '<span class="sig-long">＋ 同向</span>';
  if (d === '-') return '<span class="sig-short">− 反向</span>';
  return '<span class="dim">' + n(d) + '</span>';
}

// ── 索引：族群（factor_tags）與倉庫自記的連動關係 ──────────────────────
const TAGI = {};
TS.forEach(t => (t.factor_tags || []).forEach(g => { (TAGI[g] = TAGI[g] || []).push(t.ticker); }));
const TAGS = Object.keys(TAGI).sort((a, b) => (TAGI[b].length - TAGI[a].length) || (a < b ? -1 : 1));
const MIX = COV.equal_weight_factor_mix || {};
const CW = COV.correlation_watch || [];

// ── coverage.yaml 的 note 是一條 append-log，不是一段文字 ────────────────
//
// 這一區的資料形狀與倉庫其他地方不同，而那個差別決定了它該怎麼畫：
// 每次新增標的，新判讀被 prepend 到字串**最前面**，舊的全部用「原註：」串在後面保留。
// 所以 ai_capex_hw 那一格不是一段註記，是「最新判讀 ＋ 21 段歷史判讀」黏成的
// 一個 7,001 字單一字串（實測 2026-09-11：37 格共 38,666 字、108 段）。
// ⚠ 這個寫法只出現在 coverage.yaml（equal_weight_factor_mix 與 common_premise）——
//    drivers／state／timeline 都是 0 次。所以這是這一區獨有的形狀，不是通例，
//    也因此處理它的程式刻意只用在這一區。
//
// ⚠⚠ 切段是**顯示層**的事，一個字都不丟。兩個方向都錯：
//    整串攤開 → 37 格 38,666 字貼成一面牆，沒有人讀得完，等於沒有呈現；
//    截斷丟棄 → 砍掉的是「我當時憑什麼那樣想」的研究記錄，那是本倉庫的校準價值本身。
//    所以：第一段（最新判讀）顯示但預設截兩行，其餘折進「歷史沿革」的逆時序清單。
const SEGMARK = '原註：';
const segs = s => String(s ?? '').split(SEGMARK).map(x => x.trim()).filter(x => x.length);
// 段首多半自帶日期（實測 108 段中 96 段有）—— 抽出來當清單標籤，讓沿革可掃。
// ⚠ 只抽不刪：日期仍留在內文裡。移除它就不是折疊而是改寫。
function segDate(s) {
  const m = String(s).match(/\d{4}-\d{2}-\d{2}/);
  return m ? m[0] : '';
}
// 歷史沿革：一段一個 <li>，維持原字串順序（新 → 舊），不黏成一個段落。
function histBlock(list) {
  const old = list.slice(1);
  if (!old.length) return '';
  const chars = old.reduce((n, s) => n + s.length, 0);
  return '<details><summary>歷史沿革 ' + old.length + ' 段 · ' + chars
    + ' 字（新 → 舊，原文未刪節）</summary><ol class="hist">'
    + old.map(s => '<li><span class="hd">' + (segDate(s) ? E(segDate(s)) : '未標日期')
        + '</span>' + mdRef(s) + '</li>').join('') + '</ol></details>';
}
// ⚠ 2026-09-11：歷史段落整批移出 state，改存成一份 append-only 的沿革報告，
//    note 尾端只留一行純文字指標（「（歷史沿革 22 段已移入 reports/…md）」）。
//    上面的切段邏輯刻意**保留**：切不出第二段時 histBlock() 回空字串，什麼都不渲染，
//    而日後若又出現 原註： 鏈它會自動再生效 —— 顯示層不該假設資料只有一種形狀。
//    但那個搬遷帶走了一件要緊的事：「那裡有多少東西」不再顯示於標題行。
//    所以從指標文字把段數抓回來。抓不到就退回「全文」，不報錯、不假裝知道段數。
const MOVEDSEG = /歷史沿革\s*(\d+)\s*段[^）]*?(reports\/\S+?\.md)/;
function movedHist(s) {
  const m = String(s ?? '').match(MOVEDSEG);
  return m ? { n: m[1], path: m[2] } : null;
}
const CLAMP = 90;          // 第一段超過這個字數才需要「可展開」的殼
// 表格內用：截兩行 + 可點開。段數寫在標題行上（沿革 N 段），讀者不必先展開才知道有多少。
function noteCell(s) {
  const l = segs(s);
  if (!l.length) return '<span class="dim">未填</span>';
  const h = histBlock(l);
  if (!h && plain(l[0]).length <= CLAMP) return '<span class="full">' + mdRef(l[0]) + '</span>';
  const mv = h ? null : movedHist(l[0]);
  const chip = h ? ['沿革 ' + (l.length - 1) + ' 段', '另有 ' + (l.length - 1) + ' 段歷史判讀，展開後可見']
    : (mv ? ['沿革 ' + mv.n + ' 段 ↗', mv.n + ' 段歷史判讀已移出 state，存放於 ' + mv.path + '；展開後該路徑可點']
          : ['全文', '點開看未截斷的全文']);
  return '<details><summary><span class="pv"><span class="clamp">' + mdRef(l[0]) + '</span></span>'
    + '<span class="nth" title="' + E(chip[1]) + '">' + E(chip[0]) + '</span></summary>'
    + (h ? '<div>' + h + '</div>' : '') + '</details>';
}
// 共同前提用：第一段**不截**。它是 19 檔共用的那一個假設，截掉它等於把唯一的
// 單一失效點折起來 —— 只折歷史沿革。
function noteFull(s) {
  const l = segs(s);
  return (l.length ? mdRef(l[0]) : mdRef(s)) + histBlock(l);
}

function kin(t) {                    // 同族群標的：共用幾個 factor_tag 就是幾
  const mine = new Set(t.factor_tags || []);
  return TS.filter(o => o.ticker !== t.ticker)
    .map(o => ({ t: o, s: (o.factor_tags || []).filter(g => mine.has(g)) }))
    .filter(x => x.s.length)
    .sort((a, b) => (b.s.length - a.s.length) || (a.t.ticker < b.t.ticker ? -1 : 1));
}
function cwFor(tk) {
  const re = new RegExp('(^|[^0-9A-Za-z])' + tk + '([^0-9A-Za-z]|$)');
  return CW.map((c, i) => ({ c: c, i: i })).filter(x => re.test(String(x.c.pair || '')));
}
function refsOf(id) {                // 哪些標的回引了這個 driver
  return TS.map(t => ({ t: t, r: (t.driver_refs || []).find(r => r.driver === id) }))
           .filter(x => x.r);
}

// ── 視圖狀態 ────────────────────────────────────────────────────────────
const SORTS = {
  up_desc: { lb: '上檔空間（高 → 低）', f: (a, b) => cmpN(a.upside, b.upside) },
  up_asc:  { lb: '上檔空間（低 → 高）', f: (a, b) => cmpN(b.upside, a.upside) },
  stale:   { lb: '錨定價時點（舊 → 新）', f: (a, b) => cmpN(a.price_age_days, b.price_age_days) },
  upd:     { lb: '最後更新（新 → 舊）', f: (a, b) => String(b.last_updated || '').localeCompare(String(a.last_updated || '')) },
  gaps:    { lb: '缺口數（多 → 少）', f: (a, b) => cmpN((a.gaps || []).length, (b.gaps || []).length) },
  tk:      { lb: '代號', f: (a, b) => String(a.ticker).localeCompare(String(b.ticker)) },
};
const GROUPS = { none: '不分組', tag: '族群', quad: '象限', mkt: '市場', rating: '評級', conv: '信心' };
const KEY = 'cta_site_view_v2';
const ST = { sort: 'up_desc', group: 'none', mkt: '', rating: '', conv: '', quad: '',
             stale: false, tags: [], q: '', open: {}, tlAll: false };

function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify({
      sort: ST.sort, group: ST.group, mkt: ST.mkt, rating: ST.rating, conv: ST.conv,
      quad: ST.quad, stale: ST.stale, tags: ST.tags, open: Object.keys(ST.open),
    }));
  } catch (e) { /* 無痕模式或配額滿 —— 記不住狀態不該讓頁面壞掉 */ }
}
function load() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || '{}');
    if (!s || typeof s !== 'object') return;
    if (SORTS[s.sort]) ST.sort = s.sort;
    if (GROUPS[s.group]) ST.group = s.group;
    ['mkt', 'rating', 'conv', 'quad'].forEach(k => { if (typeof s[k] === 'string') ST[k] = s[k]; });
    ST.stale = !!s.stale;
    if (Array.isArray(s.tags)) ST.tags = s.tags.filter(g => TAGI[g]);
    if (Array.isArray(s.open)) s.open.forEach(tk => { if (BY[tk]) ST.open[tk] = true; });
  } catch (e) { /* 讀不到就用預設值 —— 不可因此不渲染 */ }
}

function clearFilters() {
  ST.mkt = ST.rating = ST.conv = ST.quad = ''; ST.stale = false; ST.tags = []; ST.q = '';
}

function visible() {
  const q = ST.q.trim().toLowerCase();
  return TS.filter(t => {
    const sig = t.signal || {};
    if (ST.mkt && t.market !== ST.mkt) return false;
    if (ST.rating && sig.rating !== ST.rating) return false;
    if (ST.conv && sig.conviction !== ST.conv) return false;
    if (ST.quad && t.quadrant !== ST.quad) return false;
    if (ST.stale && !(typeof t.price_age_days === 'number' && t.price_age_days >= STALE)) return false;
    if (ST.tags.length && !(t.factor_tags || []).some(g => ST.tags.indexOf(g) >= 0)) return false;
    if (q) {
      const hay = [t.ticker, t.name, t.thesis, (t.factor_tags || []).join(' ')].join(' ').toLowerCase();
      if (hay.indexOf(q) < 0) return false;
    }
    return true;
  });
}

function grouped(list) {
  const s = SORTS[ST.sort] || SORTS.up_desc;
  const srt = a => a.slice().sort((x, y) => s.f(x, y) || String(x.ticker).localeCompare(String(y.ticker)));
  if (ST.group === 'tag') {
    // factor_tags 是多標的，所以一檔會出現在它的每一個族群裡 —— 那是資料的實況，
    // 不該為了版面把它壓成一個。族群由稀少排到普遍：thermal（3 檔）這種有辨識度的
    // 排前面，ai_capex_hw（29 檔）那種背景標籤排最後。
    // ⚠ 重複出現會產生重複的 id，而錨點連結必須唯一 —— 處理方式見 render() 的 canon。
    return TAGS.slice()
      .sort((a, b) => (TAGI[a].length - TAGI[b].length) || (a < b ? -1 : 1))
      .map(g => [g, srt(list.filter(t => (t.factor_tags || []).indexOf(g) >= 0)), g])
      .filter(x => x[1].length);
  }
  if (ST.group === 'none') return [['', srt(list), '']];
  const get = { quad: t => t.quadrant || '未標象限', mkt: t => t.market || '—',
                rating: t => (t.signal || {}).rating || '未評級',
                conv: t => (t.signal || {}).conviction || '未填信心' }[ST.group];
  const mp = {};
  list.forEach(t => { const k = get(t); (mp[k] = mp[k] || []).push(t); });
  return Object.keys(mp).sort().map(k => [k, srt(mp[k]), '']);
}

// ── 掃描列 ──────────────────────────────────────────────────────────────
// 預設只顯示這九欄。細節一律收在展開面板裡 —— 39 檔全部攤開就是一面牆，
// 而一面牆與沒有資訊是同一件事。
const COLS = [
  { lb: '代號 / 名稱', cls: 'c-id', sort: 'tk' },
  { lb: '上檔空間', cls: 'c-up n', sort: 'up_desc' },
  { lb: '加權目標價', cls: 'c-tp n' },
  { lb: '錨定價 / 時點', cls: 'c-px n', sort: 'stale' },
  { lb: '訊號 · 信心', cls: 'c-sig' },
  { lb: '象限', cls: 'c-quad' },
  { lb: 'CTA 位階', cls: 'c-stance' },
  { lb: '缺口', cls: 'c-gap n', sort: 'gaps' },
  { lb: '最後更新', cls: 'c-upd n', sort: 'upd' },
];

function head() {
  return '<thead><tr>' + COLS.map(c => {
    const on = c.sort && (ST.sort === c.sort || (c.sort === 'up_desc' && ST.sort === 'up_asc'));
    const inner = c.sort
      ? '<button data-act="sort" data-v="' + c.sort + '">' + E(c.lb)
        + (on ? ' <span aria-hidden="true">' + (ST.sort === 'up_asc' ? '▴' : '▾') + '</span>' : '') + '</button>'
      : E(c.lb);
    return '<th class="' + c.cls + '"'
      + (on ? ' aria-sort="' + (ST.sort === 'up_asc' ? 'ascending' : 'descending') + '"' : '')
      + '>' + inner + '</th>';
  }).join('') + '</tr></thead>';
}

// canon=false 只會在「依族群分組」時出現：同一檔在第二個以上的族群裡再次露臉。
// 那一列不帶 id（錨點必須唯一），也不展開 —— 改成指回主列的連結，
// 讓「詳情只有一份」這件事在介面上是明確的，而不是兩份可能不同步的內容。
function row(t, canon) {
  const sig = t.signal || {}, cta = t.cta || {}, sc = t.scenarios || {};
  const op = canon && !!ST.open[t.ticker];
  const g = (t.gaps || []).length;
  const up = typeof t.upside === 'number'
    ? '<span class="' + upCls(t.upside) + '">' + upTxt(t.upside) + '</span>' + upBar(t.upside)
    : '<span class="dim">未能計算</span>';
  const id = canon
    ? '<button class="tg" data-act="open" data-v="' + E(t.ticker) + '"'
      + ' aria-expanded="' + op + '" aria-controls="d-' + E(t.ticker) + '">'
      + '<span class="tw" aria-hidden="true">' + (op ? '▾' : '▸') + '</span>'
    : '<a class="tg" href="#t-' + E(t.ticker) + '" aria-label="跳到 ' + E(t.ticker) + ' 的主列">'
      + '<span class="tw" aria-hidden="true">↑</span>';
  return '<tr class="r"' + (canon ? ' id="t-' + E(t.ticker) + '"' : '') + '>'
    + '<td class="c-id">' + id
      + '<span class="tk">' + E(t.ticker) + '</span>'
      + '<span class="nm">' + E(t.name) + '</span>'
      + '<span class="mk">' + E(t.market) + '</span>' + (canon ? '</button>' : '</a>') + '</td>'
    + '<td class="c-up n">' + up + '</td>'
    + '<td class="c-tp n">' + num(sc.weighted_tp) + '</td>'
    + '<td class="c-px n">' + num(cta.price)
      + '<span class="age">' + E(cta.updated || '時點未填') + '</span>' + ageTag(t.price_age_days) + '</td>'
    + '<td class="c-sig">' + sigBadge(sig) + '<span class="mini">信心 ' + n(sig.conviction) + '</span></td>'
    + '<td class="c-quad"><span class="num">' + n(t.quadrant) + '</span></td>'
    + '<td class="c-stance"><span title="' + E(plain(cta['位階'])) + '">'
      + (cta['位階'] ? clip(cta['位階'], 16) : '<span class="dim">未填</span>') + '</span></td>'
    + '<td class="c-gap n">' + (g ? '<span class="warn">' + g + '</span>' : '<span class="dim">0</span>') + '</td>'
    + '<td class="c-upd n">' + n(t.last_updated) + '</td></tr>'
    + (op ? detail(t) : '');
}

function scenBlock(sc) {
  const rows = ['bear', 'base', 'bull'].map(k => {
    const s = sc[k] || {}, lb = { bear: 'Bear', base: 'Base', bull: 'Bull' }[k];
    return '<tr><td>' + lb + '</td><td class="n">'
      + (s.p !== null && s.p !== undefined ? pct(s.p) + '%' : '—') + '</td><td class="n">' + num(s.eps)
      + '</td><td class="n">' + (s.exit_multiple ? num(s.exit_multiple) + 'x' : '—')
      + '</td><td class="n">' + num(s.tp) + '</td></tr>';
  }).join('');
  const b = pct((sc.bear || {}).p), m = pct((sc.base || {}).p), u = pct((sc.bull || {}).p);
  const bar = (b + m + u) > 0
    ? '<div class="pbar" role="img" aria-label="情境機率 Bear ' + b + '% Base ' + m + '% Bull ' + u + '%">'
      + '<i class="b" style="width:' + b + '%"></i><i class="m" style="width:' + m + '%"></i>'
      + '<i class="u" style="width:' + u + '%"></i></div>' : '';
  const det = ['bear', 'base', 'bull'].map(k => {
    const s = sc[k] || {}, lb = { bear: 'Bear', base: 'Base', bull: 'Bull' }[k];
    if (!Object.keys(s).length) return '';
    return '<p class="q"><b>' + lb + '</b> ' + (s.p !== null && s.p !== undefined ? pct(s.p) + '%' : '—')
      + '｜' + md(s.narrative)
      + '<br><span class="lb">關鍵假設</span>' + md(s.key_assumption)
      + '<br><span class="lb">倍數依據</span>' + md(s.multiple_basis)
      + '<br><span class="lb">機率依據</span>' + md(s.p_basis) + '</p>';
  }).join('');
  return bar
    + '<div class="scroll"><table><thead><tr><th>情境</th><th>機率</th><th>EPS</th><th>倍數</th>'
    + '<th>目標價</th></tr></thead><tbody>' + rows + '</tbody></table></div>'
    + (sc.cyclicality_check ? '<p class="fx"><span class="lb">循環性檢查</span>' + md(sc.cyclicality_check) + '</p>' : '')
    + '<details><summary>情境的敘事、關鍵假設與倍數依據</summary><div>' + det + '</div></details>';
}

const CTA_SHOWN = ['位階', 'price', 'updated', 'key_ma', 'support', 'resistance',
                   'invalidation', 'confirm_trigger'];

function detail(t) {
  const sig = t.signal || {}, cta = t.cta || {}, sc = t.scenarios || {};
  const kvs = (t.key_variables || []).map(k =>
    '<tr><td>' + clip(k.name, 48) + '</td><td class="n">' + num(k.value)
    + (k.unit && k.value !== null ? ' <span class="dim">' + clip(k.unit, 26) + '</span>' : '')
    + '</td><td class="dim">' + n(k.tier) + '</td><td class="n dim">' + n(k.updated) + '</td></tr>').join('');
  const kvSrcN = (t.key_variables || []).filter(k => k.source).length;
  const kvSrc = (t.key_variables || []).filter(k => k.source).map(k =>
    '<p class="q"><b>' + clip(k.name, 60) + '</b><br>' + md(k.source) + '</p>').join('');
  const fxs = (t.falsifiers || []).map(f =>
    '<p class="fx"><b>' + fxState(f.status) + '</b> ' + md(f.condition)
    + '<br><span class="dim num">check_by ' + E(f.check_by || '未定') + '</span>'
    + (f.note ? '<br><span class="dim">' + md(f.note) + '</span>' : '') + '</p>').join('');
  const cps = (t.checkpoints || []).map(c =>
    '<tr><td class="num">' + n(c.date) + '</td><td>' + md(c.event)
    + '</td><td style="text-align:left">' + md(c.what_to_watch) + '</td></tr>').join('');
  const gps = (t.gaps || []).length
    ? (t.gaps || []).map(g => '<p class="q">' + md(g.question)
        + (g.how_to_close ? '<span class="how">取得途徑：' + md(g.how_to_close) + '</span>' : '') + '</p>').join('')
    : '<p class="dim">未列缺口 —— 這不代表沒有未知，只代表沒有被寫下來。</p>';
  const refs = (t.driver_refs || []).map(r =>
    '<p class="q"><a class="chip" href="#d-' + E(r.driver) + '"><span class="d">' + E(r.driver)
    + '</span></a> ' + dirTxt(r.direction) + (r.note ? '<br>' + md(r.note) : '') + '</p>').join('')
    || '<p class="dim">未引用任何共用驅動因子。</p>';
  const kk = kin(t);
  const near = kk.filter(x => x.s.length >= 2), far = kk.filter(x => x.s.length < 2);
  const kinHTML = (near.length
      ? '<div class="chips">' + near.map(x => '<a class="chip" href="#t-' + E(x.t.ticker) + '">'
          + '<span class="d">' + E(x.t.ticker) + '</span> ' + E(x.t.name)
          + ' <span class="dim">共用 ' + x.s.length + '：' + E(x.s.join(' · ')) + '</span></a>').join('') + '</div>'
      : '<p class="dim">沒有共用兩個以上族群的標的。</p>')
    + (far.length ? '<details><summary>僅共用 1 個族群（' + far.length + '）</summary><div class="chips">'
        + far.map(x => '<a class="chip" href="#t-' + E(x.t.ticker) + '"><span class="d">' + E(x.t.ticker)
          + '</span> <span class="dim">' + E(x.s.join('')) + '</span></a>').join('') + '</div></details>' : '');
  const cws = cwFor(t.ticker);
  const cwHTML = cws.length
    ? '<div class="chips">' + cws.map(x =>
        '<a class="chip" href="#cw-' + x.i + '">' + clip(x.c.pair, 34) + '</a>').join('') + '</div>'
    : '<p class="dim">覆蓋層未記錄與本檔有關的連動關係。</p>';
  const extra = Object.keys(cta).filter(k => CTA_SHOWN.indexOf(k) < 0).map(k =>
    '<p class="fx"><span class="lb">' + E(k) + '</span>' + md(cta[k]) + '</p>').join('');
  const upLine = typeof t.upside === 'number'
    ? '<span class="' + upCls(t.upside) + '">' + upTxt(t.upside) + '</span>'
      + ' <span class="dim">＝ ' + num(sc.weighted_tp) + ' ÷ ' + num(cta.price) + ' − 1</span>'
    : '<span class="dim">加權目標價或錨定價未填，無法計算</span>';

  return '<tr class="det" id="d-' + E(t.ticker) + '"><td colspan="' + COLS.length + '"><div class="dpane">'
    + '<div class="blk"><h4>論點<span class="sub2">thesis —— 可否證的那一句</span></h4>'
      + '<p class="thesis">' + md(t.thesis) + '</p>'
      + '<dl class="kv"><dt>上檔空間</dt><dd style="text-align:left">' + upLine + '</dd>'
      + '<dt>錨定價時點</dt><dd style="text-align:left">' + n(cta.updated)
        + (typeof t.price_age_days === 'number'
            ? ' <span class="dim">（距基準日 ' + E(REF) + ' ' + t.price_age_days + ' 天，非即時報價）</span>' : '') + '</dd>'
      + '<dt>估值基準年</dt><dd>' + n(t.valuation_base_year) + '</dd>'
      + '<dt>估值象限</dt><dd style="text-align:left">' + n(t.quadrant)
        + ' <span class="dim">複核 ' + E(t.frame_reviewed || '未填') + '</span></dd>'
      + '<dt>族群</dt><dd style="text-align:left">' + ((t.factor_tags || []).map(g =>
          '<a class="tag" href="#f-' + E(g) + '">' + E(g) + '</a>').join(' ') || '<span class="dim">未標</span>')
      + '</dd></dl></div>'
    + '<div class="blk"><h4>三情境<span class="sub2">機率合計恆為 1.00</span></h4>' + scenBlock(sc) + '</div>'
    + '<div class="blk"><h4>訊號評級<span class="sub2">研究結論，不是交易建議</span></h4>'
      + '<p>' + sigBadge(sig) + ' <span class="dim">信心 ' + n(sig.conviction) + '</span></p>'
      + '<p class="fx">' + md(sig.basis) + '</p>'
      + '<p class="fx"><span class="lb">改變評級的條件</span>' + md(sig.changes_if) + '</p></div>'
    + '<div class="blk"><h4>CTA 位階<span class="sub2">invalidation 是技術面失效價位，屬規則參數</span></h4>'
      + '<p class="fx">' + md(cta['位階']) + '</p>'
      + '<dl class="kv"><dt>關鍵均線</dt><dd style="text-align:left">' + md(cta.key_ma) + '</dd>'
      + '<dt>支撐</dt><dd style="text-align:left">' + md(cta.support) + '</dd>'
      + '<dt>壓力</dt><dd style="text-align:left">' + md(cta.resistance) + '</dd>'
      + '<dt>失效價位</dt><dd style="text-align:left">' + md(cta.invalidation) + '</dd>'
      + '<dt>確認條件</dt><dd style="text-align:left">' + md(cta.confirm_trigger) + '</dd></dl>' + extra + '</div>'
    + '<div class="blk"><h4>關鍵變數<span class="sub2">tier 事實／推論／假設 —— 看得見才不會被當成事實使用</span></h4>'
      + '<div class="scroll"><table><thead><tr><th>變數</th><th>值</th><th>tier</th><th>更新</th></tr></thead>'
      + '<tbody>' + (kvs || '<tr><td colspan="4" class="dim">未列</td></tr>') + '</tbody></table></div>'
      + (kvSrc ? '<details><summary>變數來源與註記（' + kvSrcN + '）</summary><div>' + kvSrc + '</div></details>' : '')
      + '</div>'
    + '<div class="blk"><h4>否證點<span class="sub2">' + (t.falsifiers || []).length + ' 條</span></h4>'
      + (fxs || '<p class="dim">未列</p>') + '</div>'
    + '<div class="blk"><h4>缺口 —— 已知的未知<span class="sub2">' + (t.gaps || []).length + ' 項</span></h4>'
      + gps + '</div>'
    + '<div class="blk"><h4>未來檢驗點<span class="sub2">' + (t.checkpoints || []).length + ' 項</span></h4>'
      + '<div class="scroll"><table><thead><tr><th>日期</th><th>事件</th><th>看什麼</th></tr></thead><tbody>'
      + (cps || '<tr><td colspan="3" class="dim">未列</td></tr>') + '</tbody></table></div></div>'
    + '<div class="blk"><h4>共用驅動因子<span class="sub2">＋ 同向／− 反向，逐檔不同，不可套用同一個結論</span></h4>'
      + refs + '</div>'
    + '<div class="blk"><h4>同族群標的<span class="sub2">依共用 factor_tags 數排序</span></h4>' + kinHTML + '</div>'
    + '<div class="blk"><h4>覆蓋層記錄的連動關係<span class="sub2">correlation_watch</span></h4>' + cwHTML + '</div>'
    + '</div></td></tr>';
}

// ── 控制列 ──────────────────────────────────────────────────────────────
function seg(act, cur, opts) {
  return '<span class="seg">' + opts.map(o =>
    '<button data-act="' + act + '" data-v="' + E(o[0]) + '" aria-pressed="' + (cur === o[0]) + '">'
    + E(o[1]) + '</button>').join('') + '</span>';
}

function controls() {
  const rat = ['偏多', '中性', '偏空'].map(r =>
    [r, SM[r] + ' ' + r + ' ' + TS.filter(t => (t.signal || {}).rating === r).length]);
  return '<div class="tool">'
    + '<label>搜尋 <input class="srch" id="q" type="search" placeholder="代號／名稱／論點／族群"'
      + ' aria-label="搜尋代號、名稱、論點或族群" value="' + E(ST.q) + '"></label>'
    + '<label>分組 ' + seg('group', ST.group, Object.keys(GROUPS).map(k => [k, GROUPS[k]])) + '</label>'
    + '</div><div class="tool">'
    + '<label>市場 ' + seg('mkt', ST.mkt, [['', '全部'], ['TW', 'TW'], ['US', 'US']]) + '</label>'
    + '<label>評級 ' + seg('rating', ST.rating, [['', '全部']].concat(rat)) + '</label>'
    + '<label>信心 ' + seg('conv', ST.conv, [['', '全部'], ['高', '高'], ['中', '中'], ['低', '低']]) + '</label>'
    + '<label>象限 ' + seg('quad', ST.quad, [['', '全部'], ['Q1', 'Q1'], ['Q2', 'Q2'], ['Q3', 'Q3'], ['Q4', 'Q4']]) + '</label>'
    + '</div><div class="tool">'
    + '<button class="btn" data-act="stale" aria-pressed="' + ST.stale + '">只看錨定價 ≥ ' + STALE + ' 天未更新</button>'
    + '<button class="btn" data-act="expand">全部展開</button>'
    + '<button class="btn" data-act="collapse">全部收合</button>'
    + '<button class="btn" data-act="reset">清除篩選</button>'
    + '</div>'
    + '<details class="tagbox"' + (ST.tags.length ? ' open' : '')
      + '><summary>族群篩選（可多選，符合任一即顯示）'
      + (ST.tags.length ? ' · 已選 ' + ST.tags.length : '') + '</summary><div class="tagpick">'
      + TAGS.map(g => '<button data-act="tag" data-v="' + E(g) + '" aria-pressed="'
          + (ST.tags.indexOf(g) >= 0) + '">' + E(g) + ' ' + TAGI[g].length + '</button>').join('')
      + '</div></details>';
}

// keepControls=true：只重畫表格與狀態列，不動控制列。
// ⚠ 搜尋框每打一個字就重建一次的話，中文輸入法的組字會被打斷（element 被換掉），
// 而這一頁的讀者就是中文使用者。所以輸入時刻意不重畫控制列。
function render(keepControls) {
  const list = visible();
  const seen = {};
  const body = grouped(list).map(g => '<tbody>'
    + (g[0] ? '<tr class="grp"><th colspan="' + COLS.length + '">'
        + (g[2] ? '<a href="#f-' + E(g[2]) + '">' + E(g[0]) + '</a>' : E(g[0]))
        + '<span class="c">' + g[1].length + ' 檔'
        + (g[2] && TAGI[g[2]].length !== g[1].length
            ? '（族群全體 ' + TAGI[g[2]].length + ' 檔，其餘被目前的篩選排除）' : '')
        + '</span></th></tr>' : '')
    + g[1].map(t => {
        const canon = !seen[t.ticker];
        seen[t.ticker] = true;
        return row(t, canon);
      }).join('') + '</tbody>').join('');
  if (!keepControls) document.getElementById('controls').innerHTML = controls();
  document.getElementById('scan').innerHTML = head()
    + (body || '<tbody><tr><td class="dim">沒有符合條件的標的。</td></tr></tbody>');
  document.getElementById('status').innerHTML =
    '依 <b>' + E(SORTS[ST.sort].lb) + '</b> 排序 —— 排序依據就是這個欄位，不是偏好順序。'
    + ' 分組：<b>' + E(GROUPS[ST.group]) + '</b>'
    + '｜顯示 <b>' + list.length + '</b> / ' + TS.length + ' 檔'
    + (ST.group === 'tag'
        ? '｜<span class="dim">factor_tags 是多標的，一檔會出現在它的每一個族群裡，'
          + '故列數多於檔數；第二次之後的那幾列標 ↑，點它回到該檔可展開的主列</span>' : '')
    + (ST.tags.length ? '｜族群：' + E(ST.tags.join('、')) : '');
}

document.getElementById('cover').addEventListener('click', ev => {
  const b = ev.target.closest('button[data-act]');
  if (!b) return;
  const a = b.dataset.act, v = b.dataset.v;
  if (a === 'sort') ST.sort = (ST.sort === 'up_desc' && v === 'up_desc') ? 'up_asc' : v;
  else if (a === 'group') ST.group = v;
  else if (a === 'mkt' || a === 'rating' || a === 'conv' || a === 'quad') ST[a] = (ST[a] === v ? '' : v);
  else if (a === 'stale') ST.stale = !ST.stale;
  else if (a === 'tag') { const i = ST.tags.indexOf(v); if (i < 0) ST.tags.push(v); else ST.tags.splice(i, 1); }
  else if (a === 'open') { if (ST.open[v]) delete ST.open[v]; else ST.open[v] = true; }
  else if (a === 'expand') visible().forEach(t => { ST.open[t.ticker] = true; });
  else if (a === 'collapse') ST.open = {};
  else if (a === 'reset') clearFilters();
  else return;
  render(); save();
});
document.getElementById('cover').addEventListener('input', ev => {
  if (ev.target.id !== 'q') return;
  ST.q = ev.target.value;
  render(true);
});

// ── 摘要數字 ────────────────────────────────────────────────────────────
(function summary() {
  const ups = TS.map(t => t.upside).filter(u => typeof u === 'number').sort((a, b) => a - b);
  const med = ups.length ? (ups.length % 2 ? ups[(ups.length - 1) / 2]
    : (ups[ups.length / 2 - 1] + ups[ups.length / 2]) / 2) : null;
  const near = ups.filter(u => Math.abs(u) <= 0.05).length;
  const cnt = r => TS.filter(t => (t.signal || {}).rating === r).length;
  const gaps = TS.reduce((s, t) => s + (t.gaps || []).length, 0);
  const old = TS.filter(t => typeof t.price_age_days === 'number' && t.price_age_days >= STALE).length;
  const box = (v, l, hl) => '<div class="s' + (hl ? ' hl' : '') + '"><b>' + v + '</b><span>' + l + '</span></div>';
  document.getElementById('summary').innerHTML =
    box(TS.length, '覆蓋標的')
    + box(med === null ? '—' : upTxt(med), '上檔空間中位數', true)
    + box(ups.length ? upTxt(ups[ups.length - 1]) + ' … ' + upTxt(ups[0]) : '—', '上檔空間全距')
    + box(SM['偏多'] + cnt('偏多') + '  ' + SM['中性'] + cnt('中性') + '  ' + SM['偏空'] + cnt('偏空'),
          '偏多 / 中性 / 偏空')
    // ⚠ 「目標價落在錨定價 ±5% 內」要顯示出來：references/valuation.md 明訂多檔落在
    //    該區間時，不得在覆蓋層聚合成「清單沒有明顯定價錯誤」。
    //    顯示它，讀者才知道要對「大致合理定價」這個印象打折。
    + box(near + '/' + ups.length, '目標價落在錨定價 ±5% 內', true)
    + box(old, '錨定價 ≥ ' + STALE + ' 天未更新', true)
    + box(gaps, '已列缺口', true);
})();

// ── 族群索引 ────────────────────────────────────────────────────────────
document.getElementById('factors').innerHTML =
  '<div class="scroll"><table><thead><tr><th>族群 factor_tag</th><th>檔數</th>'
  + '<th>coverage 因子格</th><th>成員（可點入）</th></tr></thead><tbody>'
  + TAGS.map(g => {
    const m = MIX[g];
    const cell = !m ? '<span class="warn"><em class="wm">⚠</em> <a href="#coverage">未列入因子格</a></span>'
      : (String(m.count) === String(TAGI[g].length)
          ? '<span class="dim">已列 ' + E(m.count) + '</span>'
          : '<span class="warn">已列 ' + E(m.count) + '，與 state 的 ' + TAGI[g].length + ' 不符</span>');
    return '<tr id="f-' + E(g) + '"><td class="num"><button class="btn" data-act="tag" data-v="' + E(g)
      + '" aria-pressed="' + (ST.tags.indexOf(g) >= 0) + '">' + E(g) + '</button></td>'
      + '<td class="n">' + TAGI[g].length + '</td><td>' + cell + '</td>'
      + '<td style="text-align:left"><span class="chips">' + TAGI[g].map(tk =>
        '<a class="chip" href="#t-' + E(tk) + '"><span class="d">' + E(tk) + '</span></a>').join('')
      + '</span></td></tr>';
  }).join('') + '</tbody></table></div>';
// 族群索引裡的族群鈕也要能當篩選器用 —— 它與上面的控制列共用同一個 data-act。
document.getElementById('factors').addEventListener('click', ev => {
  const b = ev.target.closest('button[data-act="tag"]');
  if (!b) return;
  const v = b.dataset.v, i = ST.tags.indexOf(v);
  if (i < 0) ST.tags.push(v); else ST.tags.splice(i, 1);
  b.setAttribute('aria-pressed', String(i < 0));
  render(); save();
  const sec = document.getElementById('cover-h');
  if (sec) sec.scrollIntoView({ block: 'start' });
});

// ── 共用驅動因子 ────────────────────────────────────────────────────────
document.getElementById('drivers').innerHTML = D.drivers.map(d => {
  const c = d.current || {};
  const comps = (d.components || []).map(x =>
    '<tr><td>' + E(x.name) + '</td><td class="n">' + num(x.value) + '</td><td class="dim">'
    + E(x.guidance || '') + '</td></tr>').join('');
  const tr = (d.transmission || []).map(x =>
    '<tr><td class="num">' + (BY[String(x.ticker)]
        ? '<a href="#t-' + E(x.ticker) + '">' + E(x.ticker) + '</a>' : E(x.ticker))
    + '</td><td>' + dirTxt(x.direction) + '</td><td class="dim" style="text-align:left">'
    + E(x.lag) + '</td></tr>').join('');
  const fxs = (d.falsifiers || []).map(f =>
    '<p class="fx"><b>' + fxState(f.status) + '</b> ' + md(f.condition)
    + '<br><span class="dim num">check_by ' + E(f.check_by || '未定') + '</span></p>').join('');
  const back = refsOf(d.id);
  return '<article class="card" id="d-' + E(d.id) + '">'
    + '<div class="card-hd"><div><span class="tk">' + E(d.id) + '</span></div>'
    + '<span class="badge sig-flat">driver</span></div>'
    + '<p class="thesis">' + md(d.what_it_is) + '</p>'
    + '<dl class="kv"><dt>現值</dt><dd>' + num(c.value) + '</dd>'
    + '<dt>單位</dt><dd style="text-align:left">' + n(c.unit) + '</dd>'
    + '<dt>tier</dt><dd>' + n(c.tier) + '</dd><dt>as_of</dt><dd>' + n(c.as_of) + '</dd>'
    + '<dt>更新頻率</dt><dd style="text-align:left">' + n(d.update_cadence) + '</dd></dl>'
    + '<p class="mini" style="margin:12px 0 6px">回引本 driver 的標的（' + back.length
      + '）—— <span class="sig-long">＋ 同向</span>／<span class="sig-short">− 反向</span></p>'
    + '<div class="chips">' + back.map(x => '<a class="chip" href="#t-' + E(x.t.ticker) + '">'
      + '<span class="d">' + E(x.t.ticker) + '</span> '
      + (x.r.direction === '-' ? '<span class="sig-short">−</span>' : '<span class="sig-long">＋</span>')
      + '</a>').join('') + '</div>'
    + '<details><summary>成分（' + (d.components || []).length + '）</summary><div class="scroll">'
      + '<table><thead><tr><th>成分</th><th>值</th><th>guidance</th></tr></thead><tbody>'
      + comps + '</tbody></table></div></details>'
    + '<details><summary>傳導對象（' + (d.transmission || []).length + '）</summary><div class="scroll">'
      + '<table><thead><tr><th>標的</th><th>方向</th><th>時滯</th></tr></thead><tbody>'
      + tr + '</tbody></table></div></details>'
    + '<details><summary>否證點（' + (d.falsifiers || []).length + '）</summary><div>' + fxs + '</div></details>'
    + '</article>';
}).join('');

// ── 覆蓋層 ──────────────────────────────────────────────────────────────
(function coverage() {
  const sf = COV.shared_falsifier || {}, rc = COV.review_cadence || {};
  const rev = Object.keys(COV).filter(k => /^full_revaluation/.test(k));
  // ── 因子分布：主視圖是集中度，不是文字 ────────────────────────────────
  //
  // 這一區要回答的只有一個問題：覆蓋清單集中在哪些因子。那是 count 與 pct 兩個數字。
  // 依檔數排序 + 逐列長條之後，形狀本身就是結論 —— 頭兩格吃掉大半，
  // 接著迅速掉到一長串只有 1 檔的尾巴。那個長尾不是雜訊，是「覆蓋很廣但多半只碰一次」
  // 這件事的證據，所以 37 格全列、不收合尾巴。
  //
  // ⚠ 仍然不做甜甜圈、不做堆疊長條：那類語彙把各格拼成一個「全部」，
  //    而「全部」的形狀就是資產配置的讀法。逐列獨立的長條 + 欄名「檔數」沒有這個問題。
  const mixKeys = Object.keys(MIX).sort((a, b) =>
    ((MIX[b].count || 0) - (MIX[a].count || 0)) || (a < b ? -1 : 1));
  const mixMax = mixKeys.reduce((m, k) => Math.max(m, MIX[k].count || 0), 1);
  // ④-a 對照欄：這一區與「族群索引」數的是同一批標的，兩邊對不上就是漂移。
  //     沒有任何腳本檢查，所以只能顯示出來 —— 看不見的漂移會被當成一致使用。
  function mixAudit(k) {
    const c = MIX[k].count;
    if (TAGI[k]) {
      return String(TAGI[k].length) === String(c)
        ? '<span class="dim">factor_tags ' + TAGI[k].length + ' 檔，一致</span>'
        : '<span class="warn"><em class="wm">⚠</em> factor_tags ' + TAGI[k].length + ' 檔，不符</span>';
    }
    if (!c) return '<span class="bad"><em class="wm">⚠</em> 0 檔 · 無成員</span>';
    return '<span class="warn"><em class="wm">⚠</em> 非 factor_tag · 口徑見註記</span>';
  }
  const mixRows = mixKeys.map(k => {
    const m = MIX[k], c = m.count || 0;
    return '<tr><td class="k">'
      + (TAGI[k] ? '<a href="#f-' + E(k) + '">' + E(k) + '</a>' : E(k)) + '</td>'
      + '<td class="n">' + E(m.count)
      + '<span class="cbar" aria-hidden="true"><i style="width:'
      + (c / mixMax * 100).toFixed(1) + '%"></i></span></td>'
      + '<td class="n">'
      + (typeof m.pct === 'number' ? m.pct.toFixed(1) : E(m.pct)) + '%</td>'
      + '<td class="au">' + mixAudit(k) + '</td>'
      + '<td class="nt">' + noteCell(m.note) + '</td></tr>';
  }).join('');
  // ④-b 兩個資料品質訊號，放在摘要列而不是腳註 —— 它們是這一區自己的漂移。
  const only1 = mixKeys.filter(k => (MIX[k].count || 0) === 1);
  const zero = mixKeys.filter(k => !(MIX[k].count || 0));
  const unlisted = TAGS.filter(g => !MIX[g]);      // TAGS 已依檔數多 → 少排序
  const top = mixKeys[0];
  const sbox = (v, l, hl) => '<div class="s' + (hl ? ' hl' : '') + '"><b>' + v
    + '</b><span>' + l + '</span></div>';
  const mixSum = '<div class="sum" aria-label="因子集中度摘要">'
    + sbox(mixKeys.length, '因子格')
    + sbox(E(MIX[top].count) + ' 檔', '最集中的一格 ' + E(top) + '（' + E(MIX[top].pct) + '%）', true)
    + sbox(only1.length + ' / ' + mixKeys.length, '只有 1 檔的因子格')
    + sbox(zero.length, '0 檔卻留著註記的因子格', true)
    + sbox(unlisted.length, 'state 有標籤、這裡沒有因子格', true)
    + '</div>';
  // ⚠ 2026-09-11：coverage.yaml 的「原註：」歷史段落已整批移出 state，
  //    移進 append-only 的沿革報告（理由：歷史判讀放在一個可變的 state 檔裡，
  //    本來就有被事後修飾的空間；reports/ 由 check_append_only.py 機械強制不可改）。
  //    所以下面那句說明必須依**資料**決定，不可寫死成「收在沿革裡」——
  //    否則頁面會宣稱一件它自己沒有的東西。
  // ⚠ 路徑不寫死在產生器裡：從 note 的指標文字讀出來，讓它只有一個家（coverage.yaml）。
  //    若哪天 prepend 鏈再出現，inPage 會變真，說明自動切回原本的說法。
  const inPage = mixKeys.some(k => segs(MIX[k].note).length > 1)
    || segs(COV.common_premise).length > 1;
  const moved = (() => {
    let n = 0, p = '';
    const grab = s => {
      const m = String(s ?? '').match(/（歷史沿革 (\d+) 段已移入 ([^）]+)）/);
      if (m) { n += Number(m[1]); p = p || m[2]; }
    };
    mixKeys.forEach(k => grab(MIX[k].note));
    grab(COV.common_premise);
    return n ? { n, p } : null;
  })();
  const histNote = inPage
    ? '較舊的判讀一段一條收在「沿革」裡，一個字都沒有刪。'
    : (moved
        // ⚠ 連結必須用 GH（blob 網址），不可用相對路徑 ../reports/…：
        //    docs/ 就是 GitHub Pages 的站台根目錄，../ 會跑到站外，
        //    而 reports/ 根本沒有被發佈 —— 相對路徑在本機看得到、上線就 404。
        ? '較舊的判讀共 <b>' + moved.n + ' 段</b>已移出 state，逐字收在 <a href="' + GH
          + E(moved.p) + '">' + E(moved.p) + '</a> —— 那裡是 append-only 的，'
          + '不可修改也不可刪除，所以它們在那裡比留在這個可變的檔案裡更不會被事後修飾。'
        : '');
  const drift = (zero.length || unlisted.length)
    ? '<p class="drift">'
      + (zero.length ? '<em class="wm">⚠</em> <b>沒有任何成員的因子格</b>：'
          + zero.map(k => E(k) + '（0 檔，註記 ' + String(MIX[k].note || '').length
              + ' 字仍在）').join('、')
          + ' —— 留著不是錯誤：那段註記寫的是「為什麼它一直是 0」，'
          + '包含一次承認模型看不見的事（標籤是標的層級的二元值，表達不了營收組成）。'
          + '把它當空格略過，就會連那個已知的盲點一起略過。' : '')
      + (zero.length && unlisted.length ? '<br>' : '')
      + (unlisted.length ? '<em class="wm">⚠</em> <b>state 有標籤，但這裡沒有對應的因子格</b>：'
          + unlisted.map(g => '<a href="#f-' + E(g) + '">' + E(g) + '</a> '
              + TAGI[g].length + ' 檔').join('、')
          + ' —— 與上面「族群索引」第三欄是同一個漂移的兩面。'
          + '兩份清單都是手寫的，沒有腳本檢查它們一致；漂移不會報錯，'
          + '只會讓這張表安靜地少算一格。' : '')
      + '</p>'
    : '';

  // ── 連動關係：40 條不全攤，一條一個 details，預設只剩標題行 ──────────────
  //
  // ⚠ 每一條自己就是錨點（id="cw-N"）。此前 40 條共用一個外層 details，
  //    個股展開區那些 #cw-N 連結會落進一個關著的容器裡 —— 看起來像壞掉的連結。
  //    jump() 另外補了「目標是 details 就打開它」。
  // pair 本身已是「哪幾檔 — 一句話」的格式（28 條帶 U+2014 破折號），直接當標題行用；
  // 沒有破折號的 12 條是早期的簡短條目，補一段註記開頭讓標題行不至於只有兩個代號。
  const CWX = ['implication', 'check', 'revised'];
  const cws = CW.map((c, i) => {
    const p = String(c.pair || ''), cut = p.indexOf('—');
    const who = (cut > 0 ? p.slice(0, cut) : p).trim();
    const head = cut > 0 ? md(p.slice(cut + 1).trim()) : clip(c.note, 44);
    const l = segs(c.note);
    const extra = CWX.filter(k => c[k]).map(k =>
      '<p class="fx"><span class="lb">' + E(k) + '</span>' + md(c[k]) + '</p>').join('');
    return '<details id="cw-' + i + '"><summary><span class="who">' + md(who) + '</span>'
      + '<span class="hl2">' + head + '</span>'
      + (c.added ? '<span class="cwd">' + E(c.added) + '</span>' : '')
      + '</summary><div>' + (l.length ? mdRef(l[0]) : mdRef(c.note)) + extra + histBlock(l)
      + '</div></details>';
  }).join('');
  const revs = rev.map(k => {
    const o = COV[k] || {};
    return '<details><summary>' + E(k) + '</summary><div>' + Object.keys(o).map(kk =>
      '<p class="q"><b>' + md(kk) + '</b><br>' + md(o[kk]) + '</p>').join('') + '</div></details>';
  }).join('');
  document.getElementById('coverage-body').innerHTML =
    '<div class="prem"><h3>共同前提</h3><div class="sub" style="margin-top:6px">'
      + noteFull(COV.common_premise) + '</div></div>'
    + '<div class="prem"><h3>共用否證點</h3><p class="sub" style="margin-top:6px">'
      + fxState(sf.status) + ' ' + md(sf.condition) + '</p>'
      + '<p class="sub dim" style="margin-top:4px">觸發後：' + md(sf.action) + '</p>'
      + (sf.evidence ? '<p class="sub dim" style="margin-top:4px">' + md(sf.evidence) + '</p>' : '')
      + '<p class="sub dim num" style="margin-top:4px">checked ' + E(sf.checked || '未填') + '</p></div>'
    + '<div class="card"><h3 style="margin-bottom:10px">等權基準下的因子分布 —— 依檔數排序</h3>'
      + '<p class="sub dim" style="margin:0 0 12px">這是覆蓋清單的結構描述，與任何實際配置無關。'
      + '刻意維持表格形式 —— 甜甜圈圖或堆疊長條那類語彙會讓它被讀成資產配置；'
      + '長條是逐列獨立的<b>檔數</b>長度（欄名即口徑），不會被加總成一個整體。'
      + '註記欄預設只顯示最新一段的前兩行，點它展開全文；'
      + histNote + '</p>'
      + mixSum
      + '<div class="scroll"><table class="mix"><thead><tr><th>因子格</th><th>檔數</th>'
      + '<th>等權占比</th><th>與 state 對照</th><th>當前判讀 · 可展開</th></tr></thead>'
      + '<tbody>' + mixRows + '</tbody></table></div>' + drift + '</div>'
    + '<div class="card" style="margin-top:16px"><h3 style="margin-bottom:6px">連動關係 correlation_watch（'
      + CW.length + '）</h3>'
      + '<p class="sub dim" style="margin:0 0 10px">倉庫自己記下的配對關係：同業、上下游、零和競爭、'
      + '循環引用（某檔是另一檔的估值錨）。依覆蓋層的記錄順序（新 → 舊），'
      + '預設只顯示標題行 —— 40 條共 3 萬字，全攤開就沒人讀得下去。'
      + '點任一條看全文；每一條都有自己的錨點（如 <span class="num">#cw-0</span>），'
      + '個股展開後只列與該檔有關的條目並連到這裡。</p>'
      + '<div class="cwl">' + cws + '</div></div>'
    + (revs ? '<div class="card" style="margin-top:16px"><h3 style="margin-bottom:6px">全量重估的自我檢查</h3>'
      + '<p class="sub dim" style="margin:0 0 10px">⚠ 這幾段直接影響上面那張表怎麼讀 —— 裡面有'
      + '「錨被價格追上」與「基準年假象」兩個會讓上檔空間失去意義的具名成因。</p>' + revs + '</div>' : '')
    + '<div class="card" style="margin-top:16px"><h3 style="margin-bottom:10px">複核節奏</h3>'
      + '<dl class="kv">' + Object.keys(rc).map(k =>
        '<dt>' + E(k) + '</dt><dd style="text-align:left">' + md(rc[k]) + '</dd>').join('') + '</dl></div>';
})();

// ── 時間軸 ──────────────────────────────────────────────────────────────
function timeline() {
  const all = D.timeline || [];
  const show = ST.tlAll ? all : all.slice(0, TL_HEAD);
  document.getElementById('timeline').innerHTML = show.map(e =>
    '<li class="' + E(e.kind) + '"><div class="d">' + E(e.date) + '</div>'
    + '<p class="t">' + (e.path
        ? '<a href="' + GH + E(e.path) + '">' + E(e.ticker) + '</a>'
        : (BY[String(e.ticker)] ? '<a href="#t-' + E(e.ticker) + '">' + E(e.ticker) + '</a>' : E(e.ticker)))
    + '<span class="lvl">' + E(e.level) + '</span></p>'
    + '<p class="m">' + md(e.text) + '</p></li>').join('');
  document.getElementById('tl-more').innerHTML = all.length > TL_HEAD
    ? '<button class="btn" data-act="tl">'
      + (ST.tlAll ? '只顯示最近 ' + TL_HEAD + ' 筆' : '顯示全部 ' + all.length + ' 筆') + '</button>'
    : '';
}
document.getElementById('tl-more').addEventListener('click', ev => {
  if (!ev.target.closest('button[data-act="tl"]')) return;
  ST.tlAll = !ST.tlAll;
  timeline();
});

// ── 深層連結 ────────────────────────────────────────────────────────────
// #t-3324（個股）、#f-optical（族群）、#d-hyperscaler-capex（driver）、#cw-0（連動）
// 都可直接分享。指到個股時先清掉篩選，否則連結會落在一個因為篩選而不存在的列上 ——
// 那看起來像壞掉的連結，而壞掉的是狀態不是資料。
function fromHash() {
  const h = decodeURIComponent((location.hash || '').slice(1));
  if (/^t-/.test(h) && BY[h.slice(2)]) { clearFilters(); ST.open[h.slice(2)] = true; return h; }
  if (/^f-/.test(h) && TAGI[h.slice(2)]) return h;
  if (/^(cw-\d+|d-.+|coverage)$/.test(h)) return h;
  return null;
}
function jump() {
  const id = fromHash();
  render();
  if (!id) return;
  const el = document.getElementById(id);
  if (!el) return;
  // #cw-N 指到的是一個預設收合的 <details>。不打開它的話，連結會「跳到」一個
  // 看不見的東西上 —— 讀者會以為連結壞了，而壞掉的是狀態不是資料。
  if (el.tagName === 'DETAILS') el.open = true;
  el.scrollIntoView({ block: 'center' });
}
window.addEventListener('hashchange', jump);

load();
render();
timeline();
jump();
"""


def build_html(data):
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=None,
                         separators=(",", ":"))
    cov = data.get("coverage") or {}
    as_of = esc(cov.get("as_of", ""))
    ref_date = esc(data.get("ref_date", ""))
    n_tick = len(data["tickers"])
    n_rep = len(data["reports"])
    n_drv = len(data["drivers"])
    n_tag = len({g for t in data["tickers"] for g in (t.get("factor_tags") or [])})
    # 錨定價最舊的那一個時點 —— 寫死日期會在下一輪覆核後變成假話，所以從資料算。
    px_dates = sorted(str((t.get("cta") or {}).get("updated") or "") for t in data["tickers"])
    px_dates = [d for d in px_dates if d]
    oldest_px = esc(px_dates[0] if px_dates else "未填")

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CTA 推論專案｜個股研究覆蓋</title>
<meta name="description" content="增量式個股研究倉庫的公開檢視介面。不含任何倉位資訊。">
<meta name="robots" content="index,follow">
<style>{CSS}{CSS_SCAN}{CSS_COV}</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>CTA 推論專案</h1>
  <p class="meta">
    <span><b>{as_of}</b><i>coverage as_of</i></span>
    <span><b>{n_tick}</b><i>覆蓋標的</i></span>
    <span><b>{n_tag}</b><i>族群標籤</i></span>
    <span><b>{n_drv}</b><i>驅動因子</i></span>
    <span><b>{n_rep}</b><i>推論文件</i></span>
  </p>
  <p class="lede">增量式個股研究倉庫。每則新資訊只產生一份差分推論，不重建整份報告。</p>
  <p class="prov"><b>這一頁是輸出，不是輸入。</b>
    內容由 <span class="num">scripts/build_site.py</span> 自 <span class="num">state/</span> 與
    <span class="num">drivers/</span> 直接產生 —— 永遠與倉庫一致，沒有另一份手寫版本。</p>
  <aside class="disc" aria-labelledby="nopos">
    <h2 id="nopos">本倉庫不含任何倉位資訊 —— 這是設計主張，不是免責樣板</h2>
    <ul role="list">
      <li>沒有成本、張數、配置比重、Kelly、損益，也<strong>不揭露作者是否持有任何標的</strong>。</li>
      <li>追蹤清單是<strong>研究覆蓋範圍</strong>，不是持有清單；因子分布以等權為基準，
        那是清單的結構描述，與任何實際配置無關。</li>
      <li>訊號評級（偏多／中性／偏空）是<strong>研究結論，不是交易建議</strong>；
        本頁任何排序都是<strong>依指定欄位排序</strong>，不是推薦順序。</li>
    </ul>
    <p class="fine">本頁所有內容僅供研究記錄與自我校準，非投資建議。</p>
  </aside>
</header>

<section id="cover" aria-labelledby="cover-h">
<h2 id="cover-h">覆蓋清單 —— 依上檔空間排序</h2>
<div class="sum" id="summary" aria-label="覆蓋清單摘要"></div>

<div class="honest">
  <h3>上檔空間怎麼算的，以及它什麼時候會說謊</h3>
  <p class="f">上檔空間 ＝ 加權目標價 ÷ 錨定價 − 1</p>
  <p><strong>「錨定價」是該檔最後一次覆核時記下的價格快照（<span class="num">cta.price</span>），
    不是即時報價。</strong>本頁是靜態輸出，不連任何報價來源。各檔的覆核時點不同
    （<span class="num">cta.updated</span>，目前自 <span class="num">{oldest_px}</span>
    到基準日 <span class="num">{ref_date}</span> 都有），
    <strong>所以這一欄是一組時點不齊的數字</strong>。</p>
  <p>錨定價時點距基準日超過 2 天的，表格裡會標出天數；<strong>達 7 天的標成金色</strong>，
    也可以用下方的「只看錨定價 ≥ 7 天未更新」篩出來。距今越久，這個百分比失真得越多 ——
    它量的是「目標價相對覆核當時的價格」，不是相對現在。</p>
  <p>另有兩個與時間無關、卻同樣會讓這個數字失去意義的具名成因，已寫在覆蓋層：
    <strong>錨被價格追上</strong>（倍數推導當時獨立，之後被市價走到旁邊，模型對市場其實沒有意見）與
    <strong>基準年假象</strong>（滾動基準年之後就移出 ±5% 區間）。見
    <a href="#coverage">覆蓋層 → 全量重估的自我檢查</a>。</p>
</div>

<noscript><p class="honest">這一頁的清單由內嵌的 JSON 在瀏覽器端渲染。
  JavaScript 被停用時下面會是空白 —— 那不是沒有資料，資料在本頁原始碼的
  <span class="num">&lt;script id="data"&gt;</span> 裡，也一字不差地在倉庫的
  <span class="num">state/*.yaml</span> 與 <span class="num">drivers/*.yaml</span> 裡。</p></noscript>
<div id="controls"></div>
<p class="status" id="status"></p>
<div class="scroll"><table class="scan" id="scan"></table></div>
<p class="legend">
  顏色沿用台股慣例，且一律附帶符號與文字：<span class="sig-long">▲ 紅＝偏多／上檔空間為正</span>、
  <span class="sig-flat">● 灰＝中性</span>、<span class="sig-short">▼ 綠＝偏空／上檔空間為負</span>。
  上檔空間長條以 ±40% 為滿格。<strong>缺口欄是該檔「已知的未知」條數 —— 數字大不是缺點，
  是那一檔的無知被寫下來了。</strong>
  點代號可展開該檔的三情境、訊號依據、CTA 位階、關鍵變數（含 tier）、否證點、缺口、
  檢驗點與關聯索引；展開與篩選狀態記在瀏覽器本機。
  每一列都有網址錨點（如 <span class="num">#t-3324</span>），族群是
  <span class="num">#f-optical</span>，可直接分享。
</p>
</section>

<h2>族群索引</h2>
<p class="secnote">
  由各檔 <span class="num">state</span> 的 <span class="num">factor_tags</span> 直接彙總。
  點族群名即以該族群篩選上面的清單，點代號跳到該檔。
  第三欄對照 <span class="num">coverage.yaml</span> 有沒有對應的因子格 ——
  <strong>標籤與因子格是兩份清單，而沒有任何腳本檢查它們一致</strong>；
  漂移不會報錯，只會讓因子分析安靜地少算一格，所以把它顯示出來。
</p>
<div id="factors"></div>

<h2>共用驅動因子</h2>
<p class="secnote">
  跨標的變數的唯一真實來源。一個共用事實只能有一個家 —— 個股用
  <span class="num">driver_refs</span> 引用，絕不複製數值。
  <strong>同一則消息對硬體端與平台端的方向常常相反</strong>（＋ 同向／− 反向），
  逐檔記在 <span class="num">transmission</span>，這一頁不把它抹平成一個值。
</p>
<div class="grid" id="drivers"></div>

<h2 id="coverage">覆蓋層</h2>
<p class="secnote">
  清單層級的共同前提、共用否證點、等權因子結構、連動關係與全量重估的自我檢查。
  <strong>個股層分析再深也看不見這一層的單一失效點。</strong>
</p>
<div id="coverage-body"></div>

<h2>更新時間軸</h2>
<p class="secnote">
  由推論文件的 front-matter、驅動因子與 state 的 event_log 組成 —— 那是研究記錄本身。
  報告是 append-only：判斷錯了寫新報告修正，舊的留在原地。
</p>
<ul class="tl" id="timeline"></ul>
<p id="tl-more"></p>

<footer>
  <p>
    原始碼與完整推論記錄：<a href="https://github.com/mark00lui/CTA_report">github.com/mark00lui/CTA_report</a>
    ｜本頁自動產生，請勿手改。
  </p>
  <p>
    免責：本專案為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
    讀者不應假設作者持有或不持有任何標的。
  </p>
</footer>

</div>
<script id="data" type="application/json">{payload}</script>
<script>{JS}</script>
</body>
</html>
"""


def main():
    data = collect()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_html(data))
    print(f"已產生 docs/index.html — 覆蓋 {len(data['tickers'])} 檔、"
          f"driver {len(data['drivers'])} 個、報告 {len(data['reports'])} 份、"
          f"時間軸 {len(data['timeline'])} 筆、基準日 {data.get('ref_date')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
