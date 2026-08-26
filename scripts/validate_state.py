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

        lu = as_date(d.get("last_updated"))
        if lu is None:
            warns.append(f"{rel}: last_updated 未填或格式非 YYYY-MM-DD")

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
