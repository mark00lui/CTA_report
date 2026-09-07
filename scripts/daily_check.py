#!/usr/bin/env python3
"""每日機械檢查 — 對現有檔案做純計算，不改任何模型、不寫 state 或 reports。

用法:
    python scripts/daily_check.py              # 人可讀報告
    python scripts/daily_check.py --json       # 機器可讀
    python scripts/daily_check.py --strict     # 有任一 ALERT 時 exit 1（供 CI 熔斷用）

設計原則
--------
1. **只讀不寫。** 本腳本永遠不修改 state/、drivers/、reports/。
   它的產出是一份清單，交給人或 /auto-cycle 決定要不要動模型。

2. **只做算得出來的事。** 每一項檢查都是對既有欄位的算術或日期比較。
   凡是需要判斷的（這個錨合不合理、這則消息是 L1 還是 L2）都不在這裡。

3. ⚠ **有一項檢查是啟發式的，已明確標記。**
   「錨缺 as-of」用正則掃 multiple_basis 找日期樣式 —— 而正則掃的是措辭不是內容。
   2026-09-01 本倉庫就因此誤判 MU「未宣告任何錨」（它用的措辭是「循環股框架」）。
   故該項一律輸出為 HINT 而非 ALERT，且提示文字明寫需人工確認。
"""
import sys
import os
import re
import glob
import json
from datetime import date, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML： pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CIRCULARITY_PCT = 5.0       # 目標價落在現價 ±X% 內即觸發循環性檢查
NEAR_PCT = 8.0              # 逼近（僅提示）
RESIDUAL_FLOOR = 0.50       # 基準年殘餘度低於此值，當年度結論須降權
FRAME_REVIEW_DAYS = 120     # 估值方法組合的複核週期
QUEUE_BACKLOG_DAYS = 14     # 扇出待辦積壓門檻

# 各標的的財報揭露節奏 → 用來算「當年度剩餘未公告月份」。
# 台股逐月揭露，美股逐季。會計年度非曆年者另記起始月。
FISCAL_START_MONTH = {      # 未列者視為曆年制（1 月起）
    "MSFT": 7, "INTU": 8, "MU": 9, "SNDK": 9, "NVDA": 2, "COHR": 7,
}

alerts, hints, info = [], [], []


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_states():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "state", "*.yaml"))):
        b = os.path.basename(f)
        if b.startswith("_") or b == "coverage.yaml":
            continue
        try:
            d = yaml.safe_load(open(f, encoding="utf-8"))
        except yaml.YAMLError as e:
            alerts.append({"檢查": "YAML 解析", "標的": b, "訊息": f"解析失敗: {e}"})
            continue
        if isinstance(d, dict):
            d["_file"] = os.path.relpath(f, ROOT)
            out.append(d)
    return out


def base_year_residual(d, today):
    """基準年殘餘度 = 當年度剩餘未公告月份 / 12。

    以該標的實際的揭露節奏認定「已公告」：
      台股 — 逐月揭露，每月 10 日前公告上月營收
      美股 — 逐季揭露，季末後約 4–6 週
    回傳 (殘餘度, 說明)；無法判定時回傳 (None, 原因)。
    """
    t = str(d.get("ticker") or "")
    by_raw = str(d.get("valuation_base_year") or "")
    m = re.search(r"(\d{4})", by_raw)
    if not m:
        return None, "valuation_base_year 無法解析"
    year = int(m.group(1))
    start_month = FISCAL_START_MONTH.get(t, 1)

    # 基準年的起訖（以起始月推算）
    fy_start = date(year - 1, start_month, 1) if start_month > 1 else date(year, 1, 1)
    months_elapsed = (today.year - fy_start.year) * 12 + (today.month - fy_start.month)
    if months_elapsed < 0:
        return 1.0, f"基準年 {by_raw} 尚未開始"
    if months_elapsed >= 12:
        return 0.0, f"基準年 {by_raw} 已結束"

    if d.get("market") == "TW":
        # 上月營收於本月 10 日前公告
        announced = months_elapsed if today.day >= 10 else months_elapsed - 1
    else:
        # 季報：完整季度結束後才算已公告，保守取整季
        announced = (months_elapsed // 3) * 3
    announced = max(0, min(12, announced))
    return (12 - announced) / 12.0, f"已公告 {announced} 個月"


def check_all(today):
    states = load_states()

    # ── 1. 循環性門檻 ──────────────────────────────────────────
    for d in states:
        sc = d.get("scenarios") or {}
        px = _f((d.get("cta") or {}).get("price"))
        base_tp = _f((sc.get("base") or {}).get("tp"))
        w_tp = _f(sc.get("weighted_tp"))
        if not px:
            hints.append({"檢查": "循環性", "標的": d.get("ticker"), "訊息": "cta.price 未填，無法計算"})
            continue
        for label, tp in (("base", base_tp), ("加權", w_tp)):
            if tp is None:
                continue
            gap = (tp / px - 1) * 100
            if abs(gap) < CIRCULARITY_PCT:
                alerts.append({
                    "檢查": "循環性觸發", "標的": d.get("ticker"),
                    "訊息": f"{label} {tp:.0f} 對現價 {px:.2f} 為 {gap:+.1f}%（門檻 ±{CIRCULARITY_PCT}%）",
                    "動作": "先跑基準年位移測試；移出即判為基準年假象，不移出才進入輸入獨立性辯護",
                })
            elif abs(gap) < NEAR_PCT:
                hints.append({
                    "檢查": "循環性逼近", "標的": d.get("ticker"),
                    "訊息": f"{label} {tp:.0f} 對現價 {px:.2f} 為 {gap:+.1f}%",
                })

    # ── 2. 基準年殘餘度 ────────────────────────────────────────
    for d in states:
        r, why = base_year_residual(d, today)
        if r is None:
            hints.append({"檢查": "基準年殘餘度", "標的": d.get("ticker"), "訊息": why})
            continue
        rec = {"檢查": "基準年殘餘度", "標的": d.get("ticker"),
               "訊息": f"殘餘度 {r:.2f}（基準年 {d.get('valuation_base_year')}，{why}）"}
        if r < RESIDUAL_FLOOR:
            rec["動作"] = "當年度結論須降權，且不得單獨作為方向判定依據"
            alerts.append(rec)
        else:
            info.append(rec)

    # ── 3. 估值方法組合的宣告與複核 ────────────────────────────
    for d in states:
        vf = d.get("valuation_frame")
        if not isinstance(vf, dict) or not vf:
            alerts.append({"檢查": "valuation_frame", "標的": d.get("ticker"),
                           "訊息": "未宣告（象限／族群／方法組合）",
                           "動作": "下次 /revalue 的步驟 1b 必須補"})
            continue
        rv = vf.get("reviewed")
        try:
            rvd = datetime.strptime(str(rv), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            alerts.append({"檢查": "valuation_frame", "標的": d.get("ticker"),
                           "訊息": "reviewed 未填或格式非 YYYY-MM-DD"})
            continue
        age = (today - rvd).days
        if age > FRAME_REVIEW_DAYS:
            alerts.append({"檢查": "方法組合逾期", "標的": d.get("ticker"),
                           "訊息": f"已 {age} 天未複核（門檻 {FRAME_REVIEW_DAYS} 天）",
                           "動作": "象限會漂移，方法要跟著換"})
        if not (vf.get("methods") or {}).get("secondary"):
            alerts.append({"檢查": "單一方法", "標的": d.get("ticker"),
                           "訊息": "methods.secondary 未填 — 單一方法無法交錯驗證"})
        if not vf.get("axes_crossed"):
            alerts.append({"檢查": "未跨軸", "標的": d.get("ticker"),
                           "訊息": "axes_crossed 未填 — 兩個方法若因同一理由失效，交錯驗證是假的"})

    # ── 4. ⚠ 錨的 as-of（啟發式，一律為 HINT）──────────────────
    DATE_PAT = re.compile(r"20\d{2}-\d{2}-\d{2}|as-of|as_of|20\d{2}\s*年\s*\d{1,2}\s*月")
    for d in states:
        mb = str(((d.get("scenarios") or {}).get("base") or {}).get("multiple_basis") or "")
        if not mb:
            alerts.append({"檢查": "base 無錨", "標的": d.get("ticker"),
                           "訊息": "base.multiple_basis 空白"})
        elif not DATE_PAT.search(mb):
            hints.append({
                "檢查": "錨可能缺 as-of（啟發式）", "標的": d.get("ticker"),
                "訊息": "base.multiple_basis 找不到日期樣式",
                "動作": "⚠ 正則掃的是措辭不是內容，必須人工確認後才算數"
                        "（2026-09-01 曾因此誤判 MU「未宣告任何錨」）",
            })

    # ── 5. 扇出待辦積壓 ────────────────────────────────────────
    qp = os.path.join(ROOT, "drivers", "_queue.yaml")
    if os.path.exists(qp):
        q = yaml.safe_load(open(qp, encoding="utf-8")) or {}
        for item in (q.get("pending") or []):
            if not isinstance(item, dict):
                continue
            try:
                since = datetime.strptime(str(item.get("since")), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            age = (today - since).days
            if age > QUEUE_BACKLOG_DAYS:
                alerts.append({"檢查": "佇列積壓", "標的": item.get("ticker"),
                               "訊息": f"{item.get('driver')} 的待辦已積壓 {age} 天（門檻 {QUEUE_BACKLOG_DAYS} 天）",
                               "動作": "要嘛做掉，要嘛明確標為不做並寫原因"})

    # ── 6. falsifier 的判定對象是否為缺口 ──────────────────────
    for d in states:
        empty = {v.get("name") for v in (d.get("key_variables") or [])
                 if isinstance(v, dict) and str(v.get("value")) == "__"}
        if not empty:
            continue
        for f in (d.get("falsifiers") or []):
            if not isinstance(f, dict):
                continue
            cond = str(f.get("condition") or "")
            for name in empty:
                if name and name in cond:
                    hints.append({"檢查": "看不見對象的 falsifier", "標的": d.get("ticker"),
                                  "訊息": f"「{cond[:40]}」的判定對象「{name}」目前為 __"})


def main():
    today = date.today()
    check_all(today)
    as_json = "--json" in sys.argv
    strict = "--strict" in sys.argv

    if as_json:
        print(json.dumps({"date": today.isoformat(), "alerts": alerts,
                          "hints": hints, "info": info},
                         ensure_ascii=False, indent=2))
    else:
        print(f"# 每日機械檢查 — {today.isoformat()}\n")
        print("本報告只讀不寫，不改任何模型。每一項都是對既有欄位的算術或日期比較。\n")
        for title, items, mark in (("ALERT — 需處理", alerts, "⚠"),
                                   ("HINT — 提示，須人工確認", hints, "·"),
                                   ("INFO", info, " ")):
            print(f"\n## {title}（{len(items)}）\n")
            if not items:
                print("無")
                continue
            for it in items:
                line = f"{mark} **{it.get('標的')}**｜{it.get('檢查')}｜{it.get('訊息')}"
                if it.get("動作"):
                    line += f"\n    → {it['動作']}"
                print(line)
        print(f"\n---\n合計：{len(alerts)} alert／{len(hints)} hint／{len(info)} info")

    return 1 if (strict and alerts) else 0


if __name__ == "__main__":
    sys.exit(main())
