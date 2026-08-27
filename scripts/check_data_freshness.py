#!/usr/bin/env python3
"""資料層護欄 — 驗「數值是否過期」與「tier 是否配得上來源順位」。

用法:
    python scripts/check_data_freshness.py
    python scripts/check_data_freshness.py --list-due   # 只列到期表，不判定

ERROR 讓 exit code = 1，用來擋 commit。WARN 只提示。

為什麼需要這支：
    validate_state.py 驗的是**結構**（機率合計 1.00、key_variables <= 6、否證點 >= 2）。
    結構全對而數字過期，它一個字都不會說 —— 只有 90 天的 NOTE，而台股一季是 90 天，
    等於「落後整整一季」剛好落在 NOTE 都不觸發的邊界內。

    這是最安靜的失效模式：thesis 沒動、否證點沒觸發、驗證全綠，
    但 key_variable 標著 tier「事實」而它的基期已經被一份更新的官方財報取代。
    模型不會報錯，它只會用舊數字繼續算出看起來很精確的目標價。

    台股的公布期限是**日曆決定的**，不是主觀的：月營收每月 10 日前、季報 5/15
    與 8/14 與 11/14、年報 3/31。既然到期日可以算，「該更新而沒更新」就該被機械抓出來。

第二項檢查（tier vs 來源順位）：
    SKILL.md 已經寫死「順位 3 以下不得標事實、不得單獨支撐 L2 以上」，
    但目前沒有任何東西強制它 —— 規則寫在 skill 文件裡，靠人記得。
    要能機械檢查，key_variables 需要多一欄 source_rank（1-6）。
    本腳本對「沒有這欄」的既有檔只出 NOTE，不擋 commit —— 遷移期不該一次全紅。
"""
import os
import re
import sys
import glob
from datetime import date, datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML： pip install pyyaml")

PLACEHOLDER = "__"
# 資料商鏡像會比官方公告晚一兩天落地。寬限期不是放水，是避免在期限當天製造假紅燈。
GRACE_DAYS = 3
REVENUE_DUE_DAY = 10          # 台股月營收：每月 10 日前公布上月
QUARTER_DUE = {1: (5, 15), 2: (8, 14), 3: (11, 14), 4: (3, 31)}   # 4 為次年
MAX_TRUSTED_RANK = 2          # 順位 1-2 才可標「事實」

errors, warns, notes = [], [], []
QPAT = re.compile(r"(20\d{2})\s*Q([1-4])")


def is_placeholder(v):
    return v is None or v == PLACEHOLDER or (isinstance(v, str) and v.strip("_ ") == "")


def latest_due_month(today):
    """今天為止，最新一個「公布期限已過」的營收月份，回傳 (year, month)。"""
    y, m = today.year, today.month
    if today.day < REVENUE_DUE_DAY + GRACE_DAYS:
        m -= 1                      # 本月 10 日還沒到，只能要求上上月
    m -= 1                          # 10 日公布的是「上個月」的營收
    while m <= 0:
        m += 12
        y -= 1
    return y, m


def latest_due_quarter(today):
    """今天為止，最新一個「申報期限已過」的季別，回傳 (year, quarter)。"""
    cands = []
    for yr in (today.year - 1, today.year):
        for q, (mm, dd) in QUARTER_DUE.items():
            due_year = yr + 1 if q == 4 else yr
            try:
                due = date(due_year, mm, dd) + timedelta(days=GRACE_DAYS)
            except ValueError:
                continue
            if due <= today:
                cands.append(((yr, q), due))
    if not cands:
        return None
    return max(cands, key=lambda x: x[1])[0]


def check_monthly_revenue(rel, d, today):
    """月營收序列是否落後於公布期限；順帶檢查序列有沒有斷月。"""
    series = d.get("monthly_revenue")
    if not series:
        return
    months = []
    for row in series:
        if not isinstance(row, dict):
            continue
        mv = str(row.get("month", ""))
        try:
            months.append(datetime.strptime(mv, "%Y-%m").date().replace(day=1))
        except ValueError:
            warns.append(f"{rel}: monthly_revenue.month 格式非 YYYY-MM — {mv!r}")
    if not months:
        return

    newest = max(months)
    dy, dm = latest_due_month(today)
    due = date(dy, dm, 1)
    if newest < due:
        lag = (due.year - newest.year) * 12 + (due.month - newest.month)
        errors.append(
            f"{rel}: monthly_revenue 最新為 {newest:%Y-%m}，"
            f"但 {dy}-{dm:02d} 的營收公布期限已過 — 落後 {lag} 個月"
        )

    # 斷月：state 只留最近幾筆是允許的，但中間跳月會讓 YoY/MoM 無法自我檢核
    if len(months) >= 2:
        ms = sorted(months)
        for a, b in zip(ms, ms[1:]):
            if (b.year - a.year) * 12 + (b.month - a.month) > 1:
                warns.append(
                    f"{rel}: monthly_revenue 序列在 {a:%Y-%m} 與 {b:%Y-%m} 之間斷月"
                )


def check_quarterly_staleness(rel, d, today):
    """key_variables 的 source 若寫明季別，檢查是否已被更新的季報取代。

    刻意從 source 字串解析季別，而不要求新欄位 —— 這樣現有 state 檔今天就能被
    檢查到，不需要先做一輪 schema 遷移。

    落後不代表作者偷懶：公司可能根本不逐季揭露該項（例如某產品線的營收占比只在
    年報或法說出現）。檢查本身分不出這兩件事，所以：
      - 落後 1 季 → 幾乎一定是「該更新而沒更新」，tier 事實時為 ERROR
      - 落後 2 季以上 → 更可能是揭露頻率問題，只出 WARN，並要求標記
        `disclosure_frequency`，讓「這項拿不到」在檔案裡看得見而不是被當成疏漏
    一個逼作者去改一個改不了的東西的檢查，最後一定會被整支關掉。
    """
    due = latest_due_quarter(today)
    if due is None:
        return
    dy, dq = due
    for kv in d.get("key_variables") or []:
        if not isinstance(kv, dict) or is_placeholder(kv.get("value")):
            continue
        freq = str(kv.get("disclosure_frequency") or "").strip()
        if freq in ("annual", "irregular", "none"):
            continue                # 作者已明示非逐季揭露，跳過
        m = QPAT.search(str(kv.get("source") or ""))
        if not m:
            continue
        vy, vq = int(m.group(1)), int(m.group(2))
        if (vy, vq) >= (dy, dq):
            continue
        lag = (dy - vy) * 4 + (dq - vq)
        name, tier = kv.get("name", "?"), kv.get("tier")
        msg = (
            f"{rel}: 變數「{name}」基期為 {vy}Q{vq}，但 {dy}Q{dq} 的申報期限已過"
            f" — 落後 {lag} 季（tier={tier}）"
        )
        if lag >= 2:
            warns.append(
                msg + "。若公司不逐季揭露此項，請在該變數加"
                " disclosure_frequency: annual|irregular"
            )
        elif tier == "事實":
            # tier 事實 + 已被更新期別取代 = 檔案在宣稱一件不再為真的事。
            errors.append(msg)
        else:
            warns.append(msg)


def check_source_rank(rel, d):
    """tier「事實」必須來自順位 1-2。缺 source_rank 欄位的檔案只提示，不擋。"""
    kvs = [kv for kv in (d.get("key_variables") or []) if isinstance(kv, dict)]
    filled = [kv for kv in kvs if not is_placeholder(kv.get("value"))]
    if not filled:
        return
    if not any("source_rank" in kv for kv in filled):
        notes.append(
            f"{rel}: key_variables 無 source_rank 欄位 — tier 與來源順位的一致性"
            "目前無法機械檢查（SKILL.md：順位 3 以下不得標事實）"
        )
        return
    for kv in filled:
        rank, tier, name = kv.get("source_rank"), kv.get("tier"), kv.get("name", "?")
        if rank is None:
            warns.append(f"{rel}: 變數「{name}」有值但未填 source_rank")
            continue
        try:
            rank = int(rank)
        except (TypeError, ValueError):
            errors.append(f"{rel}: 變數「{name}」的 source_rank={rank!r} 不是 1-6 的整數")
            continue
        if not 1 <= rank <= 6:
            errors.append(f"{rel}: 變數「{name}」的 source_rank={rank} 超出 1-6")
        elif tier == "事實" and rank > MAX_TRUSTED_RANK:
            errors.append(
                f"{rel}: 變數「{name}」tier=事實 但 source_rank={rank}"
                f" — 只有順位 {MAX_TRUSTED_RANK} 以內可標事實"
            )


def check_price_kind(rel, d):
    """cta.price 是盤中或盤前價時，不該當成當日定價基準留在檔案裡。"""
    cta = d.get("cta") or {}
    if is_placeholder(cta.get("price")):
        return
    kind = cta.get("price_kind")
    blob = " ".join(str(cta.get(k, "")) for k in ("note", "位階", "updated"))
    if kind in ("盤中", "盤前", "盤後"):
        warns.append(f"{rel}: cta.price_kind={kind} — 非收盤價，位階判讀會隨當日行情變動")
    elif kind is None and re.search(r"盤中|盤前|未收盤|盤後", blob):
        warns.append(
            f"{rel}: cta 的註記顯示 price 可能非收盤價，但無 price_kind 欄位可判定"
        )


def main():
    today = date.today()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if "--list-due" in sys.argv:
        dy, dm = latest_due_month(today)
        dq = latest_due_quarter(today)
        print(f"今日 {today}（寬限 {GRACE_DAYS} 天）")
        print(f"  月營收：{dy}-{dm:02d} 之前（含）都應已公布")
        print(f"  季報　：{dq[0]}Q{dq[1]} 之前（含）都應已公布" if dq else "  季報　：無")
        return 0

    scanned = 0
    for path in sorted(glob.glob(os.path.join(root, "state", "*.yaml"))):
        base = os.path.basename(path)
        if base.startswith("_") or base == "coverage.yaml":
            continue
        rel = os.path.relpath(path, root)
        try:
            d = yaml.safe_load(open(path, encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{rel}: YAML 解析失敗 — {e}")
            continue
        if not isinstance(d, dict):
            continue
        scanned += 1
        if str(d.get("market", "")).upper() == "TW":
            check_monthly_revenue(rel, d, today)
            check_quarterly_staleness(rel, d, today)
        check_source_rank(rel, d)
        check_price_kind(rel, d)

    for label, items in (("ERROR", errors), ("WARN", warns), ("NOTE", notes)):
        for m in items:
            print(f"[{label}] {m}")

    print(
        f"\n檢查 {scanned} 個 state 檔："
        f" {len(errors)} error, {len(warns)} warn, {len(notes)} note"
    )
    if errors:
        print("\n有 ERROR：數值已被更新的官方期別取代，請更新 state 並補對應報告。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
