---
description: 更新共用驅動因子，並自動扇出到所有引用它的個股
argument-hint: <driver-slug> <連結或原文>
---

更新驅動因子並扇出：$ARGUMENTS

共用資訊（如四大 CSP capex、液冷滲透率、匯率）不屬於任何單一標的。它們住在 `drivers/`，個股用 `driver_refs` 引用。**同一個數字只有一個家** — 絕不複製進個股 state，否則會各自漂移且沒人發現。

## 步驟

1. 讀 `drivers/<slug>.yaml`。若不存在，先問我要不要建（用 `drivers/_TEMPLATE.yaml`）。

2. 更新 `current`、`components`，並在 `history` 追加一筆。**保留舊值** — 對這類變數，修正的方向與速度比絕對值更有訊息量。

3. 檢查該 driver 的 `falsifiers` 是否觸發。

4. **扇出**：讀 `transmission` 清單，對每個 ticker 分別處理：
   - 依 `direction` 判斷方向。**同一則消息對不同標的方向可能相反** —
     capex 上修對硬體端是需求利多，對平台端是折舊與 ROI 利空。
     絕不套用同一個結論。
   - 依 `lag` 判斷這則消息何時才會反映在該檔的財報上。傳導有時滯的，
     不要把「2 季後才發生的事」當成當季的模型變動。
   - 依 `affects` 找出該檔要更新的 key_variables。
   - 對每檔**各自定級 L0–L3**（門檻同 `/cta`）。多數情況下驅動因子的
     小幅變動對個股是 L0 或 L1。

5. 對定級 L1 以上的標的，各寫一份變更單到 `reports/YYYY/MM/`，
   front-matter 加 `driver: <slug>` 標明來源。**各自 commit**，
   不要合併成一次提交。

6. 更新 driver 檔的 `event_log` 與 `last_updated`，以及各受影響 state 的
   `key_variables` 與 `updated`。

7. 跑 `check_public.py` → `check_append_only.py` → `validate_state.py` → `build_index.py`，commit：
   `driver(<slug>): <一句話> → 扇出 N 檔`

## 注意

**不要因為 driver 動了就強迫每檔都出報告。** 大部分 driver 變動對多數標的是 L0。
扇出的價值在於「確認每檔都被檢查過」，不在於「每檔都產生輸出」。
L0 的標的在 driver 的 event_log 記一行即可。

**方向相反是常態，不是例外。** 若你發現自己對硬體端和平台端寫出同方向的結論，
先停下來確認那是真的，而不是偷懶套用。

**與 `/brief` 的分工。** `/brief` 只做共用資料收錄：更新 driver 的數值並產生扇出待辦，不立即扇出。
本指令做的是**收錄加立即扇出**——用在那種你當下就知道要重算個股的變動（例如某家 CSP 正式上修
全年 guidance）。日常的數字更新走 `/brief` 就好，把定級留給之後的 `/cta` 挑著做。
兩者都會更新 driver，差別只在要不要立刻往下走。

**個股自己的事件不走這裡。** 只有當某檔的消息會改變共用變數時（例如 MSFT 財報
上修 capex guidance），才同時走 `/cta MSFT`（更新 MSFT 自己）與 `/driver
hyperscaler-capex`（更新共用值並扇出）。
