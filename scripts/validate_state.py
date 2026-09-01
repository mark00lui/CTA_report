#!/usr/bin/env python3
"""驗證 state/*.yaml 的結構不變量。

用法:
    python scripts/validate_state.py            # 全部檢查
    python scripts/validate_state.py --stale    # 只列陳舊變數
    python scripts/validate_state.py --gaps     # 只列未填欄位統計

錯誤 (ERROR) 會讓 exit code = 1，用來擋 commit。
警告 (WARN) 只提示，不擋。
"""
import sys
import glob
import os
from datetime import date, datetime

# 與 check_public.py 同樣的理由：本腳本會把使用者寫的變數名與否證點條件原樣印出，
# 那些字串可能含 cp950 編不出來的字元，在 Windows 主控台會讓 print 拋例外。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML： pip install pyyaml")

PLACEHOLDER = "__"
STALE_DAYS = 90
MAX_KEY_VARS = 6
MIN_FALSIFIERS = 2
VALID_TIERS = {"事實", "推論", "假設", "缺口"}
VALID_SIGNAL = {"偏多", "中性", "偏空"}
VALID_CONVICTION = {"高", "中", "低"}
VALID_QUADRANT = {"Q1", "Q2", "Q3", "Q4"}
# 象限判準見 .claude/skills/cta-research/references/valuation-map.md 第二部分。
# Q1 盈餘倍數／Q2 現金流與企業價值／Q3 資產與循環／Q4 營收與選擇權。
FRAME_REVIEW_DAYS = 120   # 象限與方法組合超過這個天數沒複核就提示

errors, warns, notes = [], [], []


def is_placeholder(v):
    return v is None or v == PLACEHOLDER or (isinstance(v, str) and v.strip("_ ") == "")


def as_date(v):
    if is_placeholder(v):
        return None
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except ValueError:
        return None


def check_scenarios(path, d):
    """三情境機率合計必須為 1.00 — 這是最容易在手改時弄錯的地方。"""
    sc = d.get("scenarios") or {}
    ps = []
    for k in ("bear", "base", "bull"):
        node = sc.get(k)
        if node is None:
            errors.append(f"{path}: scenarios 缺少 {k}")
            continue
        p = node.get("p")
        if is_placeholder(p):
            continue
        try:
            ps.append(float(p))
        except (TypeError, ValueError):
            errors.append(f"{path}: scenarios.{k}.p 不是數字 ({p!r})")
    if len(ps) == 3:
        total = round(sum(ps), 4)
        if abs(total - 1.0) > 1e-6:
            errors.append(f"{path}: 三情境機率合計 = {total}，必須為 1.00")
    elif ps:
        warns.append(f"{path}: 情境機率只填了 {len(ps)}/3，無法檢核合計")


def check_key_vars(path, d):
    kvs = d.get("key_variables") or []
    if len(kvs) > MAX_KEY_VARS:
        errors.append(
            f"{path}: key_variables 有 {len(kvs)} 個，上限 {MAX_KEY_VARS} — "
            "超過代表沒分清主次"
        )
    today = date.today()
    for kv in kvs:
        if not isinstance(kv, dict):
            errors.append(f"{path}: key_variables 項目格式錯誤: {kv!r}")
            continue
        name = kv.get("name", "?")
        tier = kv.get("tier")
        if not is_placeholder(tier) and tier not in VALID_TIERS:
            errors.append(f"{path}: 變數「{name}」的 tier={tier!r} 不在 {VALID_TIERS}")
        val_filled = not is_placeholder(kv.get("value"))
        if val_filled and tier == "缺口":
            warns.append(f"{path}: 變數「{name}」已有值但 tier 仍是「缺口」")
        if val_filled and is_placeholder(kv.get("source")):
            warns.append(f"{path}: 變數「{name}」有值但沒有 source")
        u = as_date(kv.get("updated"))
        if u and (today - u).days > STALE_DAYS:
            notes.append(f"{path}: 變數「{name}」已 {(today - u).days} 天未更新")


def check_falsifiers(path, d):
    fs = d.get("falsifiers") or []
    real = [f for f in fs if isinstance(f, dict) and not is_placeholder(f.get("condition"))]
    if len(real) < MIN_FALSIFIERS:
        errors.append(
            f"{path}: 只有 {len(real)} 條有效否證點，至少需要 {MIN_FALSIFIERS} 條"
        )
    for f in real:
        cond = str(f.get("condition", ""))
        if PLACEHOLDER in cond:
            warns.append(f"{path}: 否證點門檻未填數字 — 「{cond}」不可驗證")


def check_thesis(path, d):
    t = d.get("thesis")
    if is_placeholder(t):
        notes.append(f"{path}: thesis 尚未寫定")
    elif len(str(t)) > 120:
        warns.append(f"{path}: thesis 超過 120 字 — 寫不成一句話代表論點還沒想清楚")


def check_valuation_frame(path, d):
    """估值方法組合（象限＋族群＋方法）是否宣告且近期複核過。

    刻意只發 NOTE 不發 ERROR：這一欄是 2026-09-01 才引入的，
    既有檔案本來就沒有，用 ERROR 會一次擋下全部 commit。
    但它必須每次執行都出現在輸出裡 —— 看不見的無知會被當成判斷使用。
    """
    vf = d.get("valuation_frame")
    if not isinstance(vf, dict) or not vf:
        notes.append(
            f"{path}: 未宣告 valuation_frame（象限／族群／方法組合）"
            " — 見 references/valuation-map.md"
        )
        return

    q = vf.get("quadrant")
    if is_placeholder(q):
        notes.append(f"{path}: valuation_frame.quadrant 未填")
    elif str(q) not in VALID_QUADRANT:
        warns.append(
            f"{path}: valuation_frame.quadrant「{q}」不在 {sorted(VALID_QUADRANT)}"
        )

    methods = vf.get("methods") or {}
    if not methods.get("primary") or is_placeholder(methods.get("primary")):
        notes.append(f"{path}: valuation_frame.methods.primary 未填")
    if not methods.get("secondary") or is_placeholder(methods.get("secondary")):
        notes.append(
            f"{path}: valuation_frame.methods.secondary 未填"
            " — 單一方法無法交錯驗證"
        )

    # 至少要跨一個軸，否則兩個方法會因為同一個理由一起失效
    axes = vf.get("axes_crossed") or []
    if not axes:
        notes.append(
            f"{path}: valuation_frame.axes_crossed 未填"
            " — 兩個方法若因同一理由失效，交錯驗證是假的"
        )

    r = as_date(vf.get("reviewed"))
    if r is None:
        notes.append(f"{path}: valuation_frame.reviewed 未填或格式非 YYYY-MM-DD")
    elif (date.today() - r).days > FRAME_REVIEW_DAYS:
        warns.append(
            f"{path}: 估值方法組合已 {(date.today() - r).days} 天未複核"
            f"（門檻 {FRAME_REVIEW_DAYS} 天）— 象限會漂移，方法要跟著換"
        )


def count_gaps(d, prefix=""):
    n = 0
    if isinstance(d, dict):
        for k, v in d.items():
            n += count_gaps(v)
    elif isinstance(d, list):
        for v in d:
            n += count_gaps(v)
    elif is_placeholder(d):
        n = 1
    return n


def check_driver_integrity(root):
    """driver_refs 與 drivers/*.yaml 的 transmission 必須雙向一致。

    單向引用是這個架構最可能腐爛的地方：新增個股時填了 driver_refs
    卻忘了在 driver 的 transmission 補上，扇出就會漏掉那一檔 —
    而漏掉不會報錯，只會安靜地讓某檔的模型停止更新。
    """
    driver_dir = os.path.join(root, "drivers")
    if not os.path.isdir(driver_dir):
        return

    drivers = {}
    for path in sorted(glob.glob(os.path.join(driver_dir, "*.yaml"))):
        if os.path.basename(path).startswith("_"):
            continue
        rel = os.path.relpath(path, root)
        try:
            d = yaml.safe_load(open(path, encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{rel}: YAML 解析失敗 — {e}")
            continue
        if not isinstance(d, dict):
            continue
        did = d.get("id") or os.path.basename(path)[:-5]
        targets = {}
        for t in d.get("transmission") or []:
            if isinstance(t, dict) and t.get("ticker"):
                targets[str(t["ticker"])] = t
        drivers[did] = {"rel": rel, "targets": targets, "data": d}

        lu = as_date(d.get("last_updated"))
        if lu and (date.today() - lu).days > 100:
            notes.append(f"{rel}: driver 已 {(date.today() - lu).days} 天未更新")

    state_tickers, back_refs = set(), {}
    for path in sorted(glob.glob(os.path.join(root, "state", "*.yaml"))):
        base = os.path.basename(path)
        if base.startswith("_") or base == "coverage.yaml":
            continue
        rel = os.path.relpath(path, root)
        try:
            d = yaml.safe_load(open(path, encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(d, dict):
            continue
        tick = str(d.get("ticker", ""))
        state_tickers.add(tick)
        back_refs.setdefault(tick, set())
        for ref in d.get("driver_refs") or []:
            if not isinstance(ref, dict):
                continue
            slug = ref.get("driver")
            if slug not in drivers:
                errors.append(f"{rel}: driver_refs 指向不存在的 driver `{slug}`")
                continue
            back_refs[tick].add(slug)
            if tick not in drivers[slug]["targets"]:
                errors.append(
                    f"{rel}: 引用了 `{slug}`，但該 driver 的 transmission "
                    f"沒有 {tick} — 扇出會漏掉這一檔"
                )
                continue
            t = drivers[slug]["targets"][tick]
            if ref.get("direction") and t.get("direction") \
                    and ref["direction"] != t["direction"]:
                errors.append(
                    f"{rel}: `{slug}` 的傳導方向不一致 "
                    f"(state: {ref['direction']} vs driver: {t['direction']})"
                )

    for did, info in drivers.items():
        missing_file, no_back_ref = [], []
        for tick in info["targets"]:
            sp = os.path.join(root, "state", f"{tick}.yaml")
            if not os.path.exists(sp):
                missing_file.append(tick)
            elif did not in back_refs.get(tick, set()):
                no_back_ref.append(tick)
        if missing_file:
            warns.append(
                f"{info['rel']}: transmission 指向 {'、'.join(missing_file)}，"
                "但沒有對應的 state 檔"
            )
        if no_back_ref:
            # 單向引用：driver 認得這檔，這檔不認得 driver。扇出會做，
            # 但個股層讀不到共用數值，於是遲早有人把數字複製進 state。
            warns.append(
                f"{info['rel']}: transmission 指向 {'、'.join(no_back_ref)}，"
                f"但這些 state 檔沒有回引 `{did}` 的 driver_refs — 單向引用"
            )


def main():
    only_stale = "--stale" in sys.argv
    only_gaps = "--gaps" in sys.argv

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, "state", "*.yaml")))
    gap_counts = {}

    for path in files:
        rel = os.path.relpath(path, root)
        base = os.path.basename(path)
        if base.startswith("_"):
            continue
        with open(path, encoding="utf-8") as fh:
            try:
                d = yaml.safe_load(fh)
            except yaml.YAMLError as e:
                errors.append(f"{rel}: YAML 解析失敗 — {e}")
                continue
        if not isinstance(d, dict):
            errors.append(f"{rel}: 頂層不是 mapping")
            continue

        gap_counts[rel] = count_gaps(d)

        if base == "coverage.yaml":
            continue

        for field in ("ticker", "thesis", "scenarios", "key_variables", "falsifiers",
                      "signal"):
            if field not in d:
                errors.append(f"{rel}: 缺少必要欄位 {field}")

        sig = d.get("signal") or {}
        rating = sig.get("rating")
        if not is_placeholder(rating) and rating not in VALID_SIGNAL:
            errors.append(f"{rel}: signal.rating={rating!r} 不在 {VALID_SIGNAL}")
        conv = sig.get("conviction")
        if not is_placeholder(conv) and conv not in VALID_CONVICTION:
            errors.append(f"{rel}: signal.conviction={conv!r} 不在 {VALID_CONVICTION}")
        if not is_placeholder(rating) and is_placeholder(sig.get("changes_if")):
            errors.append(
                f"{rel}: signal 有評級但 changes_if 未填 — "
                "沒有翻轉條件的評級無法被檢驗"
            )

        check_thesis(rel, d)
        check_scenarios(rel, d)
        check_key_vars(rel, d)
        check_falsifiers(rel, d)
        check_valuation_frame(rel, d)

        lu = as_date(d.get("last_updated"))
        if lu is None:
            warns.append(f"{rel}: last_updated 未填或格式非 YYYY-MM-DD")

    check_driver_integrity(root)

    if only_stale:
        print("=== 陳舊變數 (>%d 天) ===" % STALE_DAYS)
        print("\n".join(notes) if notes else "無")
        return 0

    if only_gaps:
        print("=== 未填欄位統計 ===")
        for k, v in sorted(gap_counts.items(), key=lambda x: -x[1]):
            print(f"{v:4d}  {k}")
        print(f"{sum(gap_counts.values()):4d}  合計")
        return 0

    for label, items in (("ERROR", errors), ("WARN", warns), ("NOTE", notes)):
        for m in items:
            print(f"[{label}] {m}")

    total_gaps = sum(gap_counts.values())
    print(
        f"\n檢查 {len(gap_counts)} 個檔案："
        f" {len(errors)} error, {len(warns)} warn, {len(notes)} note,"
        f" {total_gaps} 個未填欄位"
    )
    if errors:
        print("\n有 ERROR，請修正後再 commit。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
