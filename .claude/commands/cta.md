---
description: 處理一則個股新資訊 — 影響掃描、定級、修正模型、寫報告、更新 state、commit
argument-hint: <ticker> <連結或原文>
---

處理以下新資訊：$ARGUMENTS

依 `.claude/skills/cta-research/SKILL.md` 的流程執行：

0. **先看 `drivers/_queue.yaml`** 有沒有這檔的 `pending` 待辦（`/brief` 收錄共用資料時留下的）。
   有的話一併處理——它們是「已知該看但還沒看」的東西，本次事件正好是處理它的時機。
   處理完把該筆從 `pending` 移進 `done`，填上實際 `level` 與報告路徑（L0 則 `report: null`）。

1. 讀取受影響標的的 `state/<ticker>.yaml`（可能不只一支）。若事件涉及總經或 AI capex，一併讀 `state/coverage.yaml`。
   依 `driver_refs` 讀對應的 `drivers/<slug>.yaml`，**共用數值取 driver 的現值**，不要用 state 裡的複本。
   若該檔還沒有指向相關 driver 的 `driver_refs`，這次補上——並確認 driver 的 `transmission` 有回指這一檔，方向一致。單向引用是這個架構最容易腐爛的地方。
2. **檢查 driver 層**：讀該檔的 `driver_refs`，若事件會改變任何共用驅動因子的數值
   （例如某家 CSP 上修 capex guidance），**不要只更新這一檔** — 同時走 `/driver <slug>`
   更新共用值並扇出到其他引用該 driver 的標的。共用數字只有一個家。

3. 影響掃描：比對事件與 `key_variables`、`falsifiers`，列出觸及的變數與新舊值。
4. 定級 L0–L3（用 SKILL.md 的客觀門檻，寫出滿足哪一條）。
5. 依級做對應深度的修正。需要現價、月營收、財報數字就去查，標來源與日期。
6. 寫報告到 `reports/YYYY/MM/YYYY-MM-DD-<ticker>-L<n>-<slug>.md`，套用 `templates/report.md` 的 front-matter 與變更單模板。
7. 更新 `state/<ticker>.yaml`（論點、情境、變數、否證點、CTA 位階、訊號），追加 `event_log` 一筆並更新 `last_updated`。
8. 跑 `python scripts/check_public.py && python scripts/check_append_only.py && python scripts/validate_state.py && python scripts/build_index.py`。
9. Commit：`cta(<ticker>): L<n> <一句話> → <關鍵影響>`。commit message 同樣不得含倉位資訊。

寫報告時逐句自問：這行能不能被拿來推論持倉？訊號寫「偏多」不寫「加碼」；
技術面寫「失效價位」不寫「停損」。`check_public.py` 是正則比對不是理解，擋不住所有間接洩漏。

一則事件影響多支個股時，分別出報告、分別 commit，最後在結尾補一段覆蓋層影響（共同前提是否鬆動）。

不要 push — 由我自己決定何時推送。
