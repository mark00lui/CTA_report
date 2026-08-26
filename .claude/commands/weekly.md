---
description: 產生週報 — 事件流回顧、因子曝險檢核、未來兩週檢驗點
---

產生本週覆蓋清單週報。

1. 讀 `state/coverage.yaml` 與全部 `state/*.yaml`。
2. 用 `git log --since="7 days ago" --oneline` 取本週事件流。
3. 對照 `state/coverage.yaml` 的等權因子結構，指出本週事件是否加深既有的因子集中。
   這是覆蓋清單的結構描述，不涉及任何實際配置。
4. 檢查 `common_premise` 與 `shared_falsifier` 是否有新證據鬆動。
5. 列出未來兩週的 `checkpoints`，以及「若不如預期會怎樣」。
6. **回顧 `notes/` 收件匣**（本月與上月），依 `notes/README.md` 的晉升規則處理：
   同一主題出現 3 次以上 → 建 driver 或成為 key_variable；可驗證且有數字門檻 → 晉升為 falsifier；
   出現一次且兩個月內無下文 → 標 `[已淘汰]`，留在原檔不刪。
7. **檢查 driver 層**：讀 `drivers/*.yaml`，列出 `update_cadence` 已到期但 `last_updated` 未更新的，
   以及任何已觸發的 driver falsifier。
8. 列出超過 90 天未更新的變數（`python scripts/validate_state.py --stale`）。
9. 寫到 `reports/YYYY/MM/YYYY-MM-DD-coverage-weekly.md`，套用 SKILL.md 的週報模板。
10. 跑 `check_public.py` → `validate_state.py` → `build_index.py`，再 commit：`coverage: 週報 YYYY-Www`。

結尾寫「本週最重要的一個判斷」。若沒有值得寫的就寫「無」— 硬湊觀點是雜訊來源。
