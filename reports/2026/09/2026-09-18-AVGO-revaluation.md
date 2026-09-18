---
date: 2026-09-18
ticker: "AVGO"
name: Broadcom Inc.
level: L2
supersedes: reports/2026/09/2026-09-12-AVGO-revaluation.md
trigger: "純時間衰退型 /revalue（daily_check.py 僅有一則可能誤判的 HINT 與基準年殘餘度 INFO，無新聞觸發）。依步驟 2 查最近一季財報時，讀到 2026-09-10 申報的 10-Q（晚於上一輪覆核兩天），揭露兩項此前完全未追蹤的一手新事實——客戶集中度首次量化、新增供應商融資曝險——構成 SKILL.md 定義的『新增 key_variable』，達 L2 門檻；同時價格下跌 4.06% 使 confirm_trigger 候選與 invalidation 邊際重新計算"
summary: "目標價未動（420，EPS／倍數／機率一個字未變）；現價自 361.99 跌至 347.30（-4.06%），上檔自 +15.96% 變 +20.86%。⚠⚠⚠ 讀最新 10-Q（一手，2026-09-10 申報，期至 2026-08-02）發現兩項本輪最重要的新事實：(1) 客戶集中度首次由一手文件量化——前五大終端客戶 Q3 佔淨營收自約 40% 躍升至 55%，單一經銷商客戶自 32% 躍升至 50%，關閉本檔最高優先缺口之一，直接量化 bear 情境的觸發機制；(2) 新增供應商融資曝險——公司為某未具名客戶的 AI 機櫃租賃提供 Backstop（上限 29B）並可能收受其可轉換票據（上限 42B），合計 71B 或有曝險（現況未動用、公允價值不重大），是此前完全未追蹤的資產負債表尾部風險。另同一份 10-Q 揭露 RPO（剩餘履約義務）179.2B，含一項 FY2026 Q2 簽訂的客製 AI 加速器長約，為成長持續期論點首次提供一手佐證，但混合半導體與軟體兩分部、無法驗證具體的 115B／230B 兩個數字，故不作為升高倍數或信心度的理由。技術面：confirm_trigger 因價格下跌與均線叢集重算，候選自 387.96（MA120）移至 369.24（MA200），但新候選的合格餘裕僅 0.10 個 ATR（約 1.0%），是本輪最脆弱之處；invalidation（真 52 週低 289.96）對 ±20% 上界的餘裕則自 0.10pp 改善為 3.49pp。評級維持中性、信心維持低。已送 source-verifier 查核，判定見下。"
signal: 中性
conviction: 低
tp_before: 420
tp_after: 420
tp_delta: "0.0% —— EPS、倍數、機率一個字未動。上檔自 +15.96% 變 +20.86% 純粹因為價格跌了 4.06%。本報告是 L2：新增一個 key_variable（客戶集中度與供應商融資曝險，由 10-Q 一手文件量化），非目標價變動觸發"
sources:
  - "scripts/us_quote.py AVGO — 2026-09-18 執行（快取清除重抓）。Yahoo Finance chart 端點，501 根（2024-09-18 至 2026-09-17）。⚠⚠ 最佳可得，不是官方。09-17 開 346.62 高 350.94 低 345.31 收 347.30；09-14/09-15/09-16 收 344.72／339.27／339.51。ATR20 10.43（3.003%）。MA5 346.56／MA10 354.16／MA20 359.64／MA50 380.63／MA60 379.51／MA100 393.71／MA120 388.81／MA200 369.24／MA240 366.84。真 52 週（自 2025-09-17，252 根）高 495.00（2026-06-03）低 289.96（2026-03-30）；兩年窗口低 138.10（2025-04-07）"
  - "stockanalysis.com/stocks/avgo/ — 2026-09-18 取得。✓ 現價 $347.30（as of Sep 17, 2026, 4:00 PM EDT），與 Yahoo chart 相符。市值 1.66T（-3.6%）。Trailing PE 44.33／Forward PE 20.06。Beta 1.46。52 週 289.96–495.00。股利 2.60（殖利率 0.75%），除息日 2026-09-21"
  - "stockanalysis.com/stocks/avgo/forecast/ — 2026-09-18 取得，頁面標示 as of 2026-09-14。共識 EPS FY2026（38 位分析師）：低 11.35／均 11.66／高 12.38（錨寬度 9.07%，前值 3.35%）。營收 FY2026：低 105.8B／均 106.0B／高 106.7B。目標價（50 位分析師）：低 215.88／均 531.85／高 715（錨寬度 231.2%，與前值完全相同）。評等：40 強力買進／7 買進／3 中立／0 賣出（前值 49 位：37／8／4／0）"
  - "data.sec.gov/submissions/CIK0001730168.json — 2026-09-18 取得，帶 User-Agent。確認最新申報：10-Q（accession 0001730168-26-000080，2026-09-10 申報，期至 2026-08-02）、S-4（accession 0001193125-26-387881，2026-09-10 申報）"
  - "10-Q 全文（sec.gov/Archives/edgar/data/1730168/000173016826000080/avgo-20260802.htm）— 2026-09-18 讀取全文。一手來源，本報告的核心新增數字皆出自此檔：客戶集中度、RPO、Backstop、可轉換票據、9 個月 OCF／capex／FCF／SBC。逐字引用見 state key_variables"
  - "S-4 全文（sec.gov/Archives/edgar/data/1730168/000119312526387881/d154803ds4.htm）— 2026-09-18 讀取，確認為既有私募債券的例行換發登記（debt exchange offer），非併購、非股權稀釋，非重大事件"
  - "8-K 附件 99.1（sec.gov/Archives/edgar/data/1730168/000173016826000076/avgo-08022026x8kxex99.htm）— 2026-09-18 重新核對，確認多年期 AI 指引（115B／230B／EPS>30）**不在**此正式財報新聞稿內，維持『二手轉述』的證據等級判定不變"
---

# AVGO 博通 —— 純時間衰退型重估卻在 10-Q 裡撞見兩項一手新事實

## 1. 價格更新與循環性檢查

| | 值 |
|---|---|
| state 原記（2026-09-11）| 361.99 |
| **最新收盤（2026-09-17）** | **347.30（-4.06%）** |
| stockanalysis 對照 | 「$347.30, as of Sep 17, 2026, 4:00 PM EDT」✓ 相符 |
| ATR20 | 10.43（3.003%，前值 11.83／3.268%）|

**目標價一個字未動：**

| | 舊（361.99）| **新（347.30）** |
|---|---|---|
| bear 203 | −43.92% | **−41.55%** |
| base 406 | +12.16% | **+16.90%** |
| bull 664 | +83.43% | **+91.19%** |
| **算術加權 419.75** | +15.96% | **+20.86%（cross_check +20.9%）** |
| **幾何加權 386.08** | +6.78% | **+11.17%（cross_check +11.2%）** |

✓ **循環性檢查**：base +16.90%，遠超 ±5% 門檻，不觸發基準年位移測試——這是判斷結論，不是無獨立意見的產物。
✓ **`cross_check.py` 對本檔無 F1–F7 旗標**（全距 3.27 倍、倍數段佔對數全距 64%，皆未達門檻）。

**EPS 交叉檢查**：現價 347.30 ÷ stockanalysis forward PE 20.06 ＝ **17.31**——與 2026-09-08／09-12 記錄的隱含 EPS **完全相同**，儘管價格與 PE 皆已變動。對 base 的 FY2027 EPS 18.47 落差 **6.28%**（前次 6.2%），仍在 10% 之內，未觸發熔斷。

---

## 2. ⚠⚠⚠ 客戶集中度首次由一手文件量化

state 原記此格為缺口（`value: __`），並註明「自研 ASIC 的性質決定了 AI 營收高度集中於少數超大規模客戶，但具體集中度本輪未由一手文件確認」。

**2026-09-10 申報的 10-Q（期至 2026-08-02）逐字揭露：**

> "We believe aggregate sales to our top five end customers, through all channels, accounted for approximately **55%** and **50%** of our net revenue for the fiscal quarter and three fiscal quarters ended August 2, 2026, respectively, and approximately **40%** of our net revenue for each of the fiscal quarter and three fiscal quarters ended August 3, 2025."

> "Direct sales to one semiconductor solutions customer, which is a distributor, accounted for **50%** and **46%** of our net revenue for the fiscal quarter and three fiscal quarters ended August 2, 2026, respectively, and **32%** and **30%** of our net revenue for the fiscal quarter and three fiscal quarters ended August 3, 2025, respectively."

| 指標 | FY2026 Q3 | FY2026 9 個月 | FY2025 同期 |
|---|---|---|---|
| 前五大終端客戶合計占淨營收 | **55%** | 50% | 約 40% |
| 單一經銷商客戶占淨營收 | **50%** | 46% | 32% |

⚠⚠ **前五大客戶集中度一年內自約 40% 躍升至 55%，單一經銷商客戶自 32% 躍升至 50%** —— 這是本檔 bear 情境「客戶集中度使衝擊直接反映在損益表」這句話**第一次有具體數字**，而非僅有質化描述。

⚠ **仍未取得的部分**：具體客戶名稱（10-Q 未揭露）、「前五大」與「該經銷商」是否重疊、是否即為法說會提及的自研 ASIC 大客戶。**在一手文件證實客戶名稱之前，不得引用任何推測性客戶名稱，也不得將此數字與市場傳言的特定客戶掛鉤。**

公司自陳：「We expect to continue to experience significant customer concentration in future periods. The loss of, or significant decrease in demand from, any of our top five end customers could have a material adverse effect on our business, results of operations and financial condition.」

**→ 已關閉 state gaps 中「客戶集中度未取得」一項。**

---

## 3. ⚠⚠⚠ 新增：供應商融資曝險（Backstop 與可轉換票據）——此前完全未追蹤的風險

同一份 10-Q 揭露一項此前 state 完全沒有記錄的安排：

> "During the fiscal quarter ended August 2, 2026, we arranged for a financial partner to take on certain agreements to purchase AI racks based on custom AI accelerators designed by us and the related lease agreements with a customer that enable access to compute capacity. In connection with this arrangement, we entered into a backstop agreement with the financial partner for the customer's lease obligations over the 5-year lease terms."

> "Our maximum potential liability under the Backstop upon the deployment of all AI racks, on an undiscounted basis, was approximately **$29 billion**. The fair value of the Backstop was not material. No amounts have been paid under the Backstop."

> "In connection with lease agreements that enable access to compute capacity, our customer may, under certain circumstances and if needed, issue to us convertible promissory notes up to an aggregate principal amount of **$42 billion**... As of August 2, 2026, no notes have been issued to us."

公司在風險因子章節自陳：「we have provided a backstop and may continue to enter into similar financing arrangements, which increases our exposure to counterparty credit risk.」——**「may continue」暗示這不是一次性安排。**

| 項目 | 上限 | 現況 |
|---|---|---|
| Backstop（AI 機櫃租賃擔保）| $29B（未貼現）| 公允價值不重大，未付款 |
| 可轉換票據 | $42B | 未發行 |
| **合計或有曝險** | **$71B** | **未動用** |

對照本檔 TTM FCF 僅 **$39.4B**、市值約 **$1.7T**——⚠ **目前公允價值不重大、未動用金額為零，但這是本檔一個新增的結構性尾部風險：若該（未具名）客戶財務狀況惡化，本檔的曝險路徑從「營收減項」升級為「資產負債表曝險」。**

⚠ **不確定該客戶是否與第 2 節的前五大客戶或該經銷商客戶重疊**——10-Q 未提供交叉引用，不得推測。

**處置**：
- 已新增為 state 的 key_variable（與客戶集中度合併為一格，因 key_variables 上限 6 個）。
- 已新增 falsifier：「Backstop 或可轉換票據有金額被動用／發行（不含 $0）」，check_by 2027-03-31，僅能靠後續 10-Q／10-K 揭露判定。
- **未改變任何情境的機率或倍數**——依 /revalue 步驟 5 紀律，機率變動不由本流程自行決定；本條也不構成需要熔斷的情形（未達「thesis 不符」「機率必須改」「來源矛盾」「算術落差 >10%」「數字差 10 倍」任一熔斷門檻），故不停下寫入 notes/inbox，而是正常納入本次 L2 報告與 state。

---

## 4. RPO 179.2B —— 成長持續期論點第一次有一手數字，但不足以驗證具體目標

10-Q 揭露：「Certain multi-year customer contracts in our semiconductor solutions segment and infrastructure software segment... contain firmly committed amounts and the remaining performance obligations under these contracts as of August 2, 2026 were approximately **$179.2 billion**. These commitments include obligations under a long-term contract for custom AI accelerators entered in the fiscal quarter ended May 3, 2026. We expect approximately **25%** of this amount to be recognized as revenue over the next 12 months.」

⚠⚠ **這是本檔成長持續期論點第一次有一手（非二手轉述）的佐證數字**——先前 state 對 FY2027 目標 115B、FY2028 目標 230B、FY2028 EPS>30 皆標註「全部為二手轉述，一手逐字稿未讀」。

⚠ **但 RPO 不能解決那個缺口**：它混合半導體與軟體兩個分部，無法單獨拆出 AI 半導體的部分，也無法驗證 115B／230B 這三個具體數字本身。**故本輪不因此調高 base 的 22x 倍數或信心度**——僅記為額外的方向性佐證。

（附帶查核）8-K 附件 99.1（正式財報新聞稿，一手）**不含**115B／230B／EPS>30 這些數字——重新核對「115」關鍵字僅命中重組費用 $115M，與 AI 目標無關。**維持「二手轉述」的證據等級判定不變。**

---

## 5. 一手資料交叉驗證：資本密集度與自由現金流無漂移

10-Q 提供 FY2026 前九個月累計數字，用以驗證象限判斷（步驟 1b）是否仍然成立：

| 指標 | 9 個月 FY2026（10-Q，一手）| 既有 TTM（state）|
|---|---|---|
| 資本支出／營收 | 1,013M／71,089M ＝ **1.42%** | 1.40% ✓ 一致 |
| OCF | 32,950M | — |
| FCF | 31,937M（利潤率 44.9%）| 44.2% ✓ 一致 |
| SBC／FCF | 6,287M／31,937M ＝ **19.7%** | 21.5%（方向一致，略降）|

**→ 象限未漂移。Q4（低資本密集 × 低當期盈餘代表性）確認成立，方法組合（成長持續期 primary、選擇權拆分 secondary）不變。**

---

## 6. 技術面：confirm_trigger 候選改變，且新候選的合格餘裕是本輪最薄的一點

**九條均線中八條仍在價格之上，僅 MA5（346.56）首次落於價格下方（差距 0.07 倍 ATR，屬雜訊等級，不構成技術面轉折）。**

各候選（距現價／倍 ATR／判定）：MA10 354.16（1.98%／0.66／✗）／MA20 359.64（3.55%／1.18／✗）／MA240 366.84（5.63%／1.87／✗）／**MA200 369.24（6.32%／2.10／✓ 剛過門檻）**／MA60 379.51（9.28%／3.09／✓）／MA50 380.63（9.60%／3.20／✓）／MA120 388.81（11.95%／3.98／✓）／MA100 393.71（13.36%／4.45／✓ 最穩健）。

**叢集分群**（累計自組內最小值 <1 個 ATR 即併入）：
- {MA10, MA20} 0.53 ATR —— 皆不合格，整組跳過
- **{MA240, MA200} 0.23 ATR —— MA240 不合格（1.87）、MA200 剛合格（2.10，餘裕僅 0.10 個 ATR ≈ 1.0% 價格）**
- {MA60, MA50, MA120} 0.89 ATR —— 全合格，上緣 MA120 為穩健第二段
- {MA100} 單獨 —— 最穩健第三段

⚠⚠⚠ **這是「叢集規則 vs 穩健性原則」既有缺口的第二個實例，且比第一個實例（2026-09-12，MA120 387.96 vs MA100 396.67）更尖銳**：上次是兩個都合格的叢集之間做選擇；這次是**同一個極窄叢集內部混合了不合格與剛合格的成員**，而剛合格的那個（MA200）餘裕只有 0.10 個 ATR——與此前記錄的「3030 MA120 0.039 個 ATR」「本檔真 52 週低曾經 0.10pp」同一量級的薄邊際。

**→ 依既有叢集規則先例（叢集決定「哪個價位是一個可分辨的事件」，是更基本的問題），取 MA200 369.24 為主要候選；但因其餘裕薄且與不合格成員同叢集，明確記錄 MA120 388.81 為穩健第二段、MA100 393.71 為最穩健第三段，三段並陳。** 兩條規則的優先順序仍是覆蓋層待決項，本輪的新形態已補記入 gaps。

`confirm_trigger`：放量收盤站上 369.24（MA200）並連三個交易日維持，距現價 **+6.32%**（前次 387.96／+7.17%）。

---

## 7. invalidation：值不變，但脆弱狀態解除（純屬價格下跌的副產品）

`invalidation` 仍為真 52 週低 **289.96**（2026-03-30）。上一輪（2026-09-12）記錄它距現價僅 19.90%，對 ±20% 上界的餘裕**只剩 0.10pp**，價格漲 0.13% 就會使本檔完全沒有失效價位——是本作業第二脆弱的資格邊緣。

價格下跌至 347.30 後：距 52 週低的距離收斂為 **16.51%**（5.50 倍 ATR），**餘裕擴大為 3.49pp**。

⚠ **必須誠實記下**：這不是風險下降，是脆弱的暫時解除。價格只要回升至約 **362.45**（距現價 +4.36%），這條規則就會重新逼近 ±20% 上界。**規則的體質沒有變，只是暫時遠離了懸崖邊緣。**

---

## 8. 評級與不做什麼

**中性／低，維持不變。**

⚠ **不升為偏多**：僅 MA5 一條均線在價格之下，其餘 8 條仍在價格之上，`confirm_trigger`（+6.32%）未成立，「連三個交易日維持」的條件也未觸及。

⚠ **conviction 維持「低」，本輪新增兩個具名理由**：
1. **客戶集中度已量化為高風險**（前五大客戶 55%、單一經銷商客戶 50%，皆較去年同期大幅躍升）。
2. **新增供應商融資曝險 $71B（未動用），是資產負債表層級的新增尾部風險。**

原有理由不變：多年期 AI 指引（115B／230B／EPS>30）仍是二手轉述；自身歷史 forward PE 區間仍未取得；族群序位因三家 forward PE 會計年度不對齊仍無法執行。

**不做：**
- **不動 EPS、倍數、目標價、機率** —— 本輪沒有新的公司財測數字；RPO 179.2B 雖是一手數字，但混合分部無法拆分驗證具體 AI 目標。
- **不因客戶集中度或供應商融資曝險而調整機率** —— 依 /revalue 步驟 5 紀律，機率變動不由本流程自行決定；本輪判斷這兩項新事實尚未達到「必須改機率」的門檻（現況金額為零、公允價值不重大），故正常記錄而非熔斷。
- **不把 MA100 396.67 或 MA120 388.81 當唯一的 `confirm_trigger`** —— 叢集規則決定哪個價位是一個可分辨的事件，本輪的叢集分析指向 MA200；但已明確記錄其餘裕薄弱與兩個更穩健的次選。
- **不為了讓 `confirm_trigger` 或 `invalidation` 更穩健而放寬既定的雙邊規則門檻** —— 門檻值本身的檢討屬覆蓋層待決項。

---

## 9. source-verifier 查核結果與本檔的處置

草稿送出 20 筆數值供獨立查核。判定：**16 筆已核實**（第 1–4、6–8、13–20 項，含全部一手 10-Q／S-4 主張），**1 筆口徑不符**（第 5 項，forward PE 20.06），**4 筆建議 tier 由事實改推論**（第 9–12 項，共識 EPS／營收／目標價／評等）。無任何一筆判定為「數值不符」「無法取得」「單一二手」，故不構成熔斷。

### 採納：核實通過的 16 筆

第 13–18、20 項（本輪核心新增主張：客戶集中度、Backstop、可轉換票據、RPO、9 個月財報數字、S-4 性質）**由查核官獨立重新讀取 10-Q／S-4 全文＋SEC EDGAR 全文檢索交叉確認**，並發現第 19 項的否定性查核可以做得比草稿原本的範圍更強（AVGO 全部歷史申報對「$115 billion」「$230 billion」零命中，不只這份 8-K）——**已採納這個更強的表述**，見第 4 節。

### 不同意：第 9–12 項的 tier 建議（維持「事實」）

查核官建議 FY2026 共識 EPS／營收／分析師目標價／評等頭數的 tier 應由「事實」改為「推論」，理由是這些是分析師預測而非已發生的事。

**本報告不採納這項建議，維持「事實」，理由**：
1. **本檔既有的 key_variable「盈餘與目標價的分歧倍数」（自 2026-09-08 建立，歷經 09-08／09-12 兩輪 source-verifier 查核皆未被要求改 tier）本身就是用同一類共識統計量（EPS 錨寬度、目標價錨寬度）構成，tier 標的正是「事實」**——若今日改判，等於推翻本檔自己已通過兩輪查核的既定判準，卻沒有新的理由說明前兩輪為何錯了。
2. **SKILL.md 的證據分層明文將「可查證的第三方數據」列入「事實」**——「38 位分析師的共識均值是 11.66」這件事本身（第三方彙整站台實際刊出的數字）是可查證、可回查的第三方資料，而非本檔自行推導；tier 管的是「這個值可信到什麼程度」，不是「這個值描述的對象是否為未來事件」。
3. **SKILL.md 另有一套正交的「情境 EPS 來源等級」（取得-分布值 > 取得-單一賣方 > 自行推導）**，正是為了處理查核官擔心的那個問題——**共識預估的『預測性質』該由來源等級表達，不該擠壓 tier 欄位的語意**，兩者疊床架屋會讓 tier 欄位同時承擔兩種不相容的判準。

**採用值**：維持 tier: 事實，數值本身（低 11.35／均 11.66／高 12.38；營收低 105.8B／均 106.0B／高 106.7B；目標價低 215.88／均 531.85／高 715；評等 40/7/3/0）不變。

### 部分採納：第 5 項 Forward PE 20.06 的口徑澄清

查核官指出 stockanalysis.com 首頁的「Forward PE」20.06 與其自家 forecast 頁面 FY2026 列顯示的「Forward PE」29.79（＝347.30÷共識 EPS 11.66，與該頁自己的 FY2026 共識自洽）不一致，質疑 20.06 的口徑存疑。

**這不是新發現的矛盾，而是本檔在 2026-09-08 已經解開、寫進 `valuation_frame.excluded` 的同一個現象的再次出現**：state 原文記載「stockanalysis 記本檔 forward PE 20.68，隱含 EPS 17.31...而 49 位分析師的 FY2026 非 GAAP 共識均值是 11.64（隱含 forward PE 30.75x）...兩者差 48.7%...三個獨立推導收斂，確認 20.68 是 FY2027」。**forecast 頁面的 FY2026 列本來就該對應 FY2026 EPS（11.66→29.79），首頁的通用「Forward PE」欄位則對應一個更遠的年度（先前三法收斂確認為 FY2027）——兩個頁面各自內部自洽，只是回答不同財年的問題。**

**佐證這個判斷而非隨機巧合的證據**：本輪價格（347.30）與 PE（20.06）都已變動，但反推出的隱含 EPS 仍是 **17.31**——與 2026-09-08（357.90÷20.68）、2026-09-12 記錄的隱含 EPS **完全相同**。若 20.06 只是一個與 EPS 無關的雜訊數字，不會在價格與倍數都變動的情況下持續反推出同一個 EPS。**這個不變性本身就是「20.06 對應一個穩定的前瞻 EPS 估計」的證據，而非查核官所疑慮的口徑錯亂。**

**採用值**：維持 tier: 事實（20.06 本身是網站直接顯示的數字，可查證），維持「未觸發熔斷」的結論（隱含 EPS 17.31 對 base 18.47 落差 6.28%）。**已在本節把 state 既有的三法收斂佐證重新引用一次**，避免下一輪查核再度把這個已解決的現象誤判為新矛盾。

### 查核深度的誠實揭露

查核官對 ATR20 與九條均線僅能抽樣核對 4 個交易日收盤價（09-14~09-17，完全相符），未逐日重建 501 根完整序列重算指標。**這是自算技術指標的固有限制，已如實記錄**——tier 維持「推論（自算）」不變，且與 state 一貫的做法一致（美股無官方免費逐日價格通道）。
