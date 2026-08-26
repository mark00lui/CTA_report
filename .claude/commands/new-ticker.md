---
description: 新增追蹤標的並建立 state 檔
argument-hint: <ticker> <名稱>
---

為 $ARGUMENTS 建立研究覆蓋。

1. 複製 `state/_TEMPLATE.yaml` 為 `state/<ticker>.yaml`。
2. 讀 `.claude/skills/cta-research/references/state-schema.md` 確認欄位語意。
3. 查最新財報、月營收（台股）、股價與技術位階，填入能確定的值並標 tier 與來源日期。
4. **查不到的填 `__` 並寫進 `gaps`，附上取得途徑。** 不要用推估值充數。
5. thesis 必須是一句話且可否證。寫不出來就先留 `__` 並告訴我為什麼 — 論點還沒成形時建檔是合理的，假裝有論點不是。
6. 至少 2 條有數字門檻的 falsifiers，其中至少 1 條在未來 6 個月可驗證。
7. 更新 `state/coverage.yaml` 的 coverage 清單與等權因子分布，
   並指出新增這檔是否加深既有的因子集中。
8. 跑 `check_public.py` 與 `validate_state.py`，再 commit：`state(<ticker>): 新增追蹤標的`。
