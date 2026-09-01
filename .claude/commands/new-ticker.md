---
description: 新增追蹤標的並建立 state 檔
argument-hint: <ticker> <名稱>
---

為 $ARGUMENTS 建立研究覆蓋。

1. 複製 `state/_TEMPLATE.yaml` 為 `state/<ticker>.yaml`。
2. 讀 `.claude/skills/cta-research/references/state-schema.md` 確認欄位語意。
3. 查最新財報、月營收（台股）、股價與技術位階，填入能確定的值並標 tier 與來源日期。
4. **查不到的填 `__` 並寫進 `gaps`，附上取得途徑。** 不要用推估值充數。
5. **⚠ 決定估值方法組合，並寫進 `valuation_frame`。** 讀
   `.claude/skills/cta-research/references/valuation-map.md`，依序回答：

   **(i) 象限**（軸：當期盈餘的代表性 × 資本密集度）—— 判準要指名數值：
   capex／營收（**15%** 是門檻）、折舊占營收比重、淨負債、循環位置、分母是否趨零。
   Q1 盈餘倍數／Q2 現金流與企業價值／Q3 資產與循環／Q4 營收與選擇權。

   **(ii) 族群與同業** —— ⚠ **多數族群在覆蓋清單內只有 1–2 檔，同業必須從清單外取。**
   同時寫定 2–3 個排序指標（該族群真正付錢買的東西），供日後 `/revalue` 定序位用。
   **事先寫定**這件事本身就是紀律 —— 事後挑指標來支持已想好的答案是這一層的自欺。

   **(iii) 2–3 種方法，且要跨軸** —— 四軸：分母／層級／時間／**參照**。
   至少跨一個，最好兩個，填進 `axes_crossed`。
   ⚠ 「PE ＋ PEG」「trailing PE ＋ forward PE」「自身歷史 PE ＋ 自身歷史 PB」都是**假的**交錯驗證。

   ⚠ **建檔時就要做這一步，不要留到第一次 `/revalue`。** 建檔階段查資料的動作最密集，
   此時決定「該用哪幾把尺」才知道要去查什麼 —— 反過來會變成「查到什麼就用什麼」，
   而那正是錨 A 被當成唯一錨的成因。查不到的方法所需資料，**列進 `gaps` 並附取得途徑**。

6. thesis 必須是一句話且可否證。寫不出來就先留 `__` 並告訴我為什麼 — 論點還沒成形時建檔是合理的，假裝有論點不是。
7. 至少 2 條有數字門檻的 falsifiers，其中至少 1 條在未來 6 個月可驗證。
8. 更新 `state/coverage.yaml` 的 coverage 清單與等權因子分布，
   並指出新增這檔是否加深既有的因子集中。
9. 跑 `check_public.py` 與 `validate_state.py`，再 commit：`state(<ticker>): 新增追蹤標的`。
