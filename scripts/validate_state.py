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
# ⚠⚠ `__` 曾同時代表「不知道，去查」與「已量化，結論是沒有東西合格」——
# 兩個相反的知識狀態共用一個 token，於是 count_gaps 把結論算成缺口。
# MEASURED_NONE 只用於後者：它是一個**被量化的結論**，必須有 basis 佐證。
MEASURED_NONE = "none_qualifies"
STALE_DAYS = 90
MAX_KEY_VARS = 6
MIN_FALSIFIERS = 2
VALID_TIERS = {"事實", "推論", "假設", "缺口"}
# ⚠ `value` 曾有 52/232（22%）裝散文，而「這一格該不該是數字」沒有任何地方寫著 ——
#   於是那既不算違規也不會被發現。`kind` 就是把那件事寫下來。
VALID_KINDS = {"量化", "質性"}
# value_qualifier 的詞彙。設計原則是：**它必須能完整表達原字串的語意**，
# 否則轉型就是有損的，而有損的轉型會把「約 90」變成「90」這種假精確。
VALID_QUALIFIERS = {
    "點值",       # 沒有修飾語
    "區間",       # 需同時有 value_low / value_high；value 為中點（衍生值）
    "下界",       # 「逾／超過／以上」
    "上界",       # 「近／不到／以下」
    "約值",       # 「約」
    "未型別化",   # ⚠ 已知債務：unit 是量化的但 value 仍是散文，需 series／components 才轉得動
}
UNTYPED = "未型別化"
VALID_SIGNAL = {"偏多", "中性", "偏空"}
VALID_CONVICTION = {"高", "中", "低"}
VALID_QUADRANT = {"Q1", "Q2", "Q3", "Q4"}
# 象限判準見 .claude/skills/cta-research/references/valuation-map.md 第二部分。
# Q1 盈餘倍數／Q2 現金流與企業價值／Q3 資產與循環／Q4 營收與選擇權。
FRAME_REVIEW_DAYS = 120   # 象限與方法組合超過這個天數沒複核就提示

errors, warns, notes = [], [], []
stale_notes = []   # 只放「陳舊變數」，供 --stale 使用；與一般 notes 分開
coarse_notes = []  # updated 只有月／年精度者 —— 合法但應收斂
kv_total, kv_dated, kv_undated = [], [], []   # --stale 的涵蓋率分母，見 main()
kv_untyped = []    # kind 量化但 value 仍是散文者 —— 已知債務，可數


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


# ⚠⚠⚠ as_date() 對解析不出來的值回 None，而呼叫端一律寫成 `if u and ...`，
# 於是「填了一個不合法的日期」與「根本沒填」都變成「跳過」，在輸出上完全看不見。
# 2026-09-13 實測：key_variables.updated 有 43/232（18.5%）落在這個分支，
# 寬鬆補算後其中 11 筆已逾 90 天，最舊者 3583 的 `updated: 2024` 已 986 天 ——
# 而 --stale 在 2026-09-12 回報的是「無陳舊變數」。
# → parse_updated() 把三種結果分開，讓呼叫端無法再把它們混為一談。
UPDATED_FORMATS = (
    ("%Y-%m-%d", "day"),
    ("%Y-%m", "month"),
    ("%Y", "year"),
)


def parse_updated(v):
    """解析 as-of 欄位。回傳 (date_or_None, precision, ok)。

    precision: 'day' / 'month' / 'year' / 'none'
    ok=False   填了東西但不是任何一種合法形式 —— 呼叫端應報 error

    ⚠ 精度不足時一律取該期間的**第一天**（2026-08 → 2026-08-01、2026 → 2026-01-01）。
      這是刻意的下界：它讓陳舊判定偏保守（寧可多報，不可漏報），
      而不是把一個不知道的日子補成看起來比較新的樣子。
    """
    if is_placeholder(v):
        return None, "none", True
    if isinstance(v, date):
        return v, "day", True
    s = str(v).strip()
    for fmt, prec in UPDATED_FORMATS:
        try:
            return datetime.strptime(s, fmt).date(), prec, True
        except ValueError:
            continue
    return None, "none", False


def check_dup_keys(path, text):
    """掃出同一層級重複的 YAML 鍵。

    ⚠ PyYAML 預設保留**最後**一個同名鍵且不發任何警告，所以較早的那個
    對每一個讀者都不存在 —— 這是一種靜默的資料遺失，而整條驗證鏈
    在 2026-09-12 之前完全看不到它。實測六處，其中 2308 的 `changes_if`
    （否證條件）與 hyperscaler-capex 的 `affects`（扇出要更新哪些變數）
    都是功能性損失，不只是註解。
    """
    class Dup(yaml.SafeLoader):
        pass

    found = []

    def ctor(loader, node, deep=False):
        seen = {}
        for k, _v in node.value:
            key = loader.construct_object(k, deep=deep)
            line = k.start_mark.line + 1
            if key in seen:
                found.append((key, line, seen[key]))
            seen[key] = line
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    Dup.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, ctor)
    try:
        yaml.load(text, Loader=Dup)
    except yaml.YAMLError:
        return
    for key, line, prev in found:
        warns.append(
            f"{path}: 第 {line} 行的鍵「{key}」與第 {prev} 行重複 — "
            "PyYAML 只保留最後一個，前者被靜默丟棄"
        )


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

        # ---- 型別契約（2026-09-13 S3a）----
        kind = kv.get("kind")
        qual = kv.get("value_qualifier")
        raw_v = kv.get("value")
        v_num = isinstance(raw_v, (int, float)) and not isinstance(raw_v, bool)
        v_blank = is_placeholder(raw_v)
        if kind not in VALID_KINDS:
            errors.append(
                f"{path}: 變數「{name}」的 kind={kind!r} 不在 {VALID_KINDS} — "
                "「這一格該不該是數字」必須寫下來，不能靠讀的人自己判斷"
            )
        elif kind == "量化":
            if qual == UNTYPED:
                kv_untyped.append(f"{path}: 變數「{name}」")
            elif not (v_num or v_blank):
                errors.append(
                    f"{path}: 變數「{name}」kind=量化 但 value 不是數值也不是 `__` — "
                    f"得到 {str(raw_v)[:40]!r}"
                )
        else:   # 質性
            if "質性" not in str(kv.get("unit") or ""):
                errors.append(
                    f"{path}: 變數「{name}」kind=質性 但 unit={kv.get('unit')!r} — "
                    "質性變數的 unit 應標「質性」，否則單位在騙人"
                )
            if qual is not None:
                errors.append(f"{path}: 變數「{name}」kind=質性 不應有 value_qualifier")

        if qual is not None and qual not in VALID_QUALIFIERS:
            errors.append(f"{path}: 變數「{name}」的 value_qualifier={qual!r} 不在 {VALID_QUALIFIERS}")
        if qual == "區間":
            lo, hi = kv.get("value_low"), kv.get("value_high")
            ok = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (lo, hi))
            if not ok:
                errors.append(f"{path}: 變數「{name}」標為區間但 value_low／value_high 未填數值")
            elif not (lo <= hi):
                errors.append(f"{path}: 變數「{name}」的 value_low {lo} > value_high {hi}")
            elif v_num and not (lo <= raw_v <= hi):
                errors.append(f"{path}: 變數「{name}」的 value {raw_v} 不在 [{lo}, {hi}] 之內")
        elif qual in ("value_low", "value_high"):
            pass
        elif kv.get("value_low") is not None or kv.get("value_high") is not None:
            errors.append(f"{path}: 變數「{name}」有 value_low／value_high 但 value_qualifier 不是區間")
        val_filled = not is_placeholder(kv.get("value"))
        if val_filled and tier == "缺口":
            warns.append(f"{path}: 變數「{name}」已有值但 tier 仍是「缺口」")
        if val_filled and is_placeholder(kv.get("source")):
            warns.append(f"{path}: 變數「{name}」有值但沒有 source")
        raw = kv.get("updated")
        u, prec, ok = parse_updated(raw)
        kv_total.append(1)
        if not ok:
            errors.append(
                f"{path}: 變數「{name}」的 updated={raw!r} 不是日期 — "
                "只接受 YYYY-MM-DD / YYYY-MM / YYYY"
            )
        elif prec == "none":
            # 值是空的就不必有 as-of；有值卻沒有 as-of 則這一格無法被引用，也無法陳舊。
            if val_filled:
                errors.append(
                    f"{path}: 變數「{name}」有值但沒有 as-of 日期（updated 未填）— "
                    "沒有 as-of 的數字無法判斷是否過期"
                )
            else:
                kv_undated.append(f"{path}: 變數「{name}」")
        else:
            kv_dated.append(1)
            if prec != "day":
                label = {"month": "月", "year": "年"}[prec]
                coarse_notes.append(
                    f"{path}: 變數「{name}」的 updated 只有{label}精度（{raw}）— "
                    f"陳舊判定以 {u} 計（該期間第一天，偏保守）"
                )
            if (today - u).days > STALE_DAYS:
                msg = (f"{path}: 變數「{name}」已 {(today - u).days} 天未更新"
                       + ("" if prec == "day" else f"（{label}精度，下界）"))
                notes.append(msg)
                stale_notes.append(msg)


def check_event_log(path, d):
    """state 的 event_log 不得帶 delta —— 那是歷史，歷史住在 reports/。

    ⚠ 依據是 schema 自己寫的「delta（一行）」，而實際做出來的是平均 1,636 字元、
      最長 4,057（MU 2026-09-12），超出規定約 27 倍。
      CLAUDE.md 已為 coverage.yaml 的同一個形狀裁決過：
      「當 state 裡的某個欄位開始承擔『記錄歷史』的職責時，它就站錯地方了」。
      2026-09-13 全部 39 檔搬進 reports/2026/09/2026-09-13-<tk>-event-log-archive.md，
      本檢查防的是它長回來。
    """
    el = d.get("event_log") or []
    if not isinstance(el, list):
        return
    bad = [str(e.get("date")) for e in el
           if isinstance(e, dict) and not is_placeholder(e.get("delta"))]
    if bad:
        errors.append(
            f"{path}: event_log 有 {len(bad)} 筆帶 delta（{', '.join(bad[:3])}…）— "
            "事件的細節寫在該事件的報告裡，不要寫回 state。"
            "state 是當下最佳判斷，不是日誌"
        )


def check_cta(path, d):
    """`cta.invalidation` 的兩種空值必須分得開。

    `__`             —— 還沒量化過，是真缺口
    `none_qualifies` —— 已用雙邊規則量化過，沒有位階同時滿足 ≥2 倍 ATR 與 ≤20%

    後者是結論不是缺口，所以**必須**有 invalidation_basis 寫出量到了什麼。
    """
    cta = d.get("cta") or {}
    if not isinstance(cta, dict):
        return
    iv = cta.get("invalidation")
    basis = cta.get("invalidation_basis")
    if iv == MEASURED_NONE:
        if is_placeholder(basis):
            errors.append(
                f"{path}: cta.invalidation 標為 {MEASURED_NONE} 但 invalidation_basis 未填 — "
                "「已量化且無位階合格」是一個結論，沒有依據就只是缺口換個寫法"
            )
    elif is_placeholder(iv):
        warns.append(
            f"{path}: cta.invalidation 為 `__` — 若已用雙邊規則量化過且無位階合格，"
            f"應改用 {MEASURED_NONE}；否則這是尚未量化的真缺口"
        )


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
        check_dup_keys(rel, open(path, encoding="utf-8").read())
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

        check_dup_keys(rel, open(path, encoding="utf-8").read())
        check_thesis(rel, d)
        check_scenarios(rel, d)
        check_key_vars(rel, d)
        check_cta(rel, d)
        check_event_log(rel, d)
        check_falsifiers(rel, d)
        check_valuation_frame(rel, d)

        lu = as_date(d.get("last_updated"))
        if lu is None:
            warns.append(f"{rel}: last_updated 未填或格式非 YYYY-MM-DD")

    check_driver_integrity(root)

    if only_stale:
        # ⚠ 涵蓋率一定要印。2026-09-12 的「無陳舊變數」是在 189/232 上下的結論，
        #   而那件事在舊版輸出裡完全看不見 —— 空白讀起來像「都很新」。
        n_tot, n_dated, n_undated = len(kv_total), len(kv_dated), len(kv_undated)
        print("=== 陳舊變數 (>%d 天) ===" % STALE_DAYS)
        print("涵蓋率：key_variables 共 %d 筆，其中 %d 筆有 as-of 可判定、"
              "%d 筆無值且無 as-of（不需判定）" % (n_tot, n_dated, n_undated))
        if n_dated + n_undated != n_tot:
            print("⚠ 分母對不上 —— 有 %d 筆既不可判定也不屬於免判定，"
                  "去看 ERROR" % (n_tot - n_dated - n_undated))
        print("-" * 60)
        print("\n".join(stale_notes) if stale_notes else "無")
        if coarse_notes:
            print()
            print("=== as-of 精度不足（合法，但陳舊判定取下界）%d 筆 ===" % len(coarse_notes))
            print("\n".join(coarse_notes))
        return 0

    if only_gaps:
        print("=== 未填欄位統計 ===")
        for k, v in sorted(gap_counts.items(), key=lambda x: -x[1]):
            print(f"{v:4d}  {k}")
        print(f"{sum(gap_counts.values()):4d}  合計")
        return 0

    # ⚠ COARSE 不逐筆印在預設輸出裡 —— 21 行會把真正要看的 ERROR/WARN 洗掉，
    #   與 hook 對 cross_check 用 --gate 的理由完全相同。完整清單跑 --stale。
    if kv_untyped:
        print("[UNTYPED] key_variables 型別化未完成 %d 筆（kind=量化 但 value 仍是散文）："
              % len(kv_untyped))
        for m in kv_untyped:
            print("          " + m)

    if coarse_notes:
        print("[COARSE] as-of 精度不足 %d 筆（合法；陳舊判定取期間第一天）— "
              "完整清單：python scripts/validate_state.py --stale" % len(coarse_notes))

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
