---
date: 2026-09-17
ticker: coverage
level: L1
driver: discount-rate
trigger: "2026-09-16 FOMC：升息一碼至 3.75–4.00（2023-07 以來首次）、SEP 中位數 2026／2027 年底利率上修至 4.1／4.1、10Y 收 5.01；Fed 主席 Warsh 於記者會把殖利率上行歸因於三件事，第二件點名 AI hyperscalers 募資 —— notes 於 2026-08-31 與 09-08 兩度事先寫定的「第 3 次」門檻達到"
summary: "**折現率通道自 notes 晉升為 driver（`drivers/discount-rate.yaml`），11 檔扇出全 L0，0 份個股變更單。** 建檔理由不是本則的數值（current 只動 +5bp，4.96 → 5.01），是它達到了事先寫定的門檻：「官員談話明確把 AI 資本支出或 AI 發債列為考量」—— 發言者是 Fed 主席、場合是 FOMC 記者會。⚠ 保留兩點：問答段的一手逐字稿尚未發布（目前二手引述一手，列 checkpoint）；Warsh 講的是殖利率為何上行的歸因，不是升息的理由 —— hyperscaler 募資是殖利率的解釋變數，不是 FOMC 的反應函數。｜**扇出的產出不是等級，是 11 條被量化或被否證的傳導假設**：INTU 錨 C 重跑 −15%／100bp、偏離 ≥34bp 才 L2（sensitivity 中 → 高）；CEG 09-11→09-16 溢價壓縮九成在 09-14、是 AI-power 族群因子不是利率（sensitivity 高 → 中，原判是斷言）；MSFT 曝險在錨 A 的零利率期窗口；台股五檔台債 0bp、鏈第一節未動，補一條台債門檻的 escalation。｜coverage.yaml 的 `shared_macro_inputs` 遷入 driver，只留指標；11 檔 state 補 driver_refs（雙向引用完成），五檔台股過時的「rf 未取得」缺口改為指向 driver、不複製數值。**本報告不動任何標的的情境、機率、倍數或目標價。**"
signal: n/a
conviction: n/a
tp_before: n/a
tp_after: n/a
tp_delta: "n/a —— 11 檔全 L0，無任何目標價變動"
supersedes: null
sources:
  - "FOMC 聲明 2026-09-16 — federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm — 2026-09-17 取得（一手）：升息 1/4 點至 3-3/4 到 4，12–0；「Productivity growth is strong, and capital investment is robust」「Inflation remains elevated」"
  - "FOMC 經濟預測摘要 2026-09-16 — federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm — 2026-09-17 取得（一手）：中位數聯邦資金利率 2026 4.1／2027 4.1／2028 3.9／長期 3.2；PCE 3.7／2.3；核心 3.4／2.5；GDP 2.3／2.4；失業率 4.1。6 月為 3.8／3.6／3.4"
  - "記者會開場聲明 PRELIMINARY 逐字稿 — federalreserve.gov/mediacenter/files/FOMCpresconf20260916.pdf — 2026-09-17 取得（一手，4 頁，僅開場）：「hard-pressed to describe broad financial conditions as restrictive」「removed a dose of accommodation」「a monetary policy discipline, not to a decision」「total PCE prices likely was around 3.6 percent in August」"
  - "Yahoo Finance FOMC 實錄 2026-09-16 — finance.yahoo.com/economy/policy/live/federal-reserve-meeting-live-updates-chairman-kevin-warsh-143452661.html — 2026-09-17 取得（⚠ 二手引述一手）：殖利率三因 —— 經濟強、「Competition for capital」點名 AI hyperscalers「out in the market raising funding」、地緣政治；市場反應 18:19 UTC 10Y −4bp／S&P +0.3%，20:24 UTC 道瓊 −1.2%／10Y 站回 5%"
  - "美國財政部每日殖利率曲線 CSV — home.treasury.gov（daily_treasury_yield_curve，2026）— 2026-09-17 取得（一手）：09-16 2Y 4.74／10Y 5.01／30Y 5.35；09-15 5.00；09-14 4.97；09-11 4.96；09-10 4.95；09-08 4.80；09-01 4.79"
  - "Fed 公開市場操作頁 — federalreserve.gov/monetarypolicy/openmarket.htm — 2026-09-17 取得（一手）：2024-09-19 −50 至 4.75–5.00 … 2025-12-11 −25 至 3.50–3.75；2026-09-17（生效日）+25 至 3.75–4.00"
  - "FOMC 行事曆 — federalreserve.gov/monetarypolicy/fomccalendars.htm — 2026-09-17 取得：10-27／28（無 SEP）、12-08／09（含 SEP）；紀要於決議後三週（約 10-07）"
  - "tradingeconomics.com/taiwan/government-bond-yield — 2026-09-17 取得（第三方，單一通道）：「held steady at 1.94% on September 16, 2026」；09-11 的 1.94 有三條通道一致（見 2026-09-12 coverage 報告）"
  - "使用者提供的中文摘要（2026-09-17）：與開場聲明逐字稿及 Yahoo 實錄一致；「他並未將週三的升息定性為風險管理舉措」一句在一手材料中未直接出現，依實錄為記者會問答內容，tier 二手"
  - "本倉庫 notes/2026-08.md（2026-08-31 兩則）、notes/2026-09.md（2026-09-08）：折現率通道第 1、2 次與「看似第 3 次但不合格」的記錄，以及事先寫定的第 3 次門檻"
  - "本倉庫 11 個扇出判官輸出（2026-09-17，driver-fanout agent，每檔隔離）：CEG／INTU／MSFT／GOOG／META／COHR／2308／3037／6239／8046／8299；CEG 判官另取 stockanalysis 09-14～09-16 收盤（CEG／VST／TLN／XLU／SPY，非官方通道）"
---

# coverage —— 折現率通道晉升為 driver，11 檔扇出全 L0

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L1**｜觸發：新增一個共用驅動因子並遷移兩個共用數值的家；11 檔 state 補回引與文字校準。
**本報告不動任何標的的情境、機率、倍數、目標價或訊號。**

---

## 1. 事件：一手能確認什麼、不能確認什麼

| 項目 | 值 | tier | 來源 |
|---|---|---|---|
| 聯邦資金目標區間 | 3.50–3.75 → **3.75–4.00**（+25bp，12–0） | 事實 | FOMC 聲明 |
| 上一次升息 | 2023-07；其間 2024-09 至 2025-12 降息六次共 175bp | 事實 | Fed 公開市場操作頁 |
| SEP 中位數利率 2026／2027／2028 年底 | 3.8／3.6／3.4 → **4.1／4.1／3.9** | 事實 | SEP |
| SEP PCE 2026 | 3.6 → **3.7** | 事實 | SEP |
| 主席對 8 月 PCE 的估計 | 總 **約 3.6**／核心約 3.2 | 推論（由 CPI／PPI 推估） | 開場聲明 |
| 美債 10Y | 09-11 4.96 → 09-15 **5.00**（首次）→ 09-16 **5.01** | 事實 | 財政部 CSV |
| 美債 2Y／30Y | 2Y 4.63 → **4.74**；30Y 5.35 → **5.35**（持平） | 事實 | 財政部 CSV |
| 台債 10Y | **1.94**，對 09-11 持平 | 推論（單一第三方通道） | tradingeconomics |

**開場聲明（一手）裡與使用者摘要對得上的三句**：

- 「I would be hard-pressed to describe broad financial conditions as restrictive … So we removed a dose of accommodation.」
- 「I expressed my commitment to a monetary policy discipline, not to a decision.」
- 「The plain fact is that inflation is too high and has been for too long.」

**問答段（二手引述一手）**：Warsh 把殖利率上行歸因於三件事 —— 經濟強、**「Competition for capital」並點名 AI hyperscalers「out in the market raising funding」**、地緣政治推升商品價格。

⚠ **Fed 目前只發布了開場聲明的 PRELIMINARY 逐字稿（4 頁）。** 問答段的一手確認列為 driver checkpoints 第一項（約 09-23）。
若完整逐字稿沒有那句話，排擠通道的第 2 次降級為二手。

---

## 2. 為什麼建 driver：門檻是事前寫的，不是事後找的

`notes/README.md`：同一主題出現 3 次以上 → 建 driver。折現率通道的計數：

| 次 | 日期 | 證據 | tier | 通道 |
|---|---|---|---|---|
| 1 | 2026-08-31 | 影片經 Gemini 摘要：AI capex 等同財政刺激 → 通膨 → Fed 降息空間有限 | 三手 | 通膨 |
| 2 | 2026-08-31 | Warsh Jackson Hole 演說 ＋ 7 月 PCE 3.7 ＋ 10Y 4.728 | 一手 | 通膨 |
| （不合格） | 2026-09-08 | CMoney 轉述：AI 企業發債與公債競爭資金 | 二手 | 排擠 |
| **3** | **2026-09-16** | **Fed 主席於 FOMC 記者會把 hyperscaler 募資列為殖利率上行原因** | 二手引述一手 | 排擠 |

第 2 次記錄裡**事先寫定**第 3 次該長什麼樣：「FOMC 會議紀要或官員談話明確把 AI 資本支出列為通膨考量」；
09-08 那則維持門檻不放寬並補上「或 AI 發債列為政策考量」。**本則逐條符合：發言者是 Fed 主席、場合是 FOMC 記者會、內容是 AI hyperscaler 募資。**

### 09-08 留下的計數疑慮在此定案

那則問：通膨通道與排擠通道是一件事還是兩件事？**答：一個 driver、兩條 channel、分開計數。**
兩條通道終點相同（折現率），但可觀測訊號不同（PCE／SEP 對 投資級發行量／期限溢酬）、falsifier 不同。
driver 檔的 `channels` 區塊把兩條各自的 occurrences 列出來，之後各自計數。

### ⚠ 一句不可混讀的話

**Warsh 講的是「殖利率為何上行」的歸因，不是「政策為何升息」的理由。** 升息的理由他講得很清楚：通膨太高太久。
hyperscaler 募資是殖利率的解釋變數，不是 FOMC 的反應函數。把它讀成「Fed 因為 AI capex 而升息」是過度推論。

---

## 3. 建了什麼、搬了什麼

**新建 `drivers/discount-rate.yaml`**：current（10Y 5.01）、components（政策區間／SEP 路徑／SEP 通膨成長／主席 PCE 估計／2Y／30Y／台債 10Y）、
history（08-28 起 9 點）、policy_rate_history（2024-09 起 7 次）、channels（通膨／排擠）、market_reaction_regime、
transmission 11 檔、falsifiers 3 條、escalation 4 條、checkpoints 5 個、gaps 7 項。

**以 10Y 為 current 的理由**：它是清單裡實際被代進估值模型的那一項（INTU／COHR 的 CAPM、MSFT 的 reverse-DCF 對照、CEG 的債券替代品倍數），政策利率只透過它傳導。

**遷移**：`state/coverage.yaml` 的 `shared_macro_inputs` 自 2026-09-12 起暫置美債 10Y 與台債 10Y 並標記「待遷移」（理由：建 driver 需使用者同意）。
本次遷入 driver，coverage.yaml 只留指標與遷移當時的值（供對帳），**不再保留任何數值**。
`state/3665.yaml` 一處指向該區塊的文字改為指向 driver。

**⚠ 一個順手抓到的漂移**：INTU 與 COHR 的 state 都寫「rf 4.97%（10 年期美債 2026-09-10）」，而財政部 CSV 同日為 4.95 —— 資料商當日值，來源不同。
**自本檔起 rf 一律以財政部 CSV 為準**；兩檔下次重估時把 4.97 改為引用 driver。對結論零影響，但兩處各自漂移正是 driver 要防的事。

---

## 4. 扇出：11 檔全 L0，但產出不是等級

11 檔各起一個隔離的判官（看不到彼此的結論）。**同方向檢查**：11 檔全為 −，已確認這是折現率通道而非需求通道，同方向是真的；需求側的方向分歧住在 hyperscaler-capex。

| 檔 | 等級 | 判官抓到的東西 | driver 層據此改了什麼 |
|---|---|---|---|
| **INTU** | L0 | 以 09-11 報告參數把錨 C 重建到一分不差後重跑：**加權目標價每 100bp rf 約 −15%**；本則 −0.6%；**偏離 ≥ +34bp（≈5.31%）才跨 −5%** | sensitivity 中 → **高**；新增 INTU 專屬 escalation；「為 0.6% 重錨是假精確」記進 path |
| **CEG** | L0 | 09-11→09-16 溢價約 60% → 57.1%，但逐日拆解：**九成跌幅在 09-14**（CEG −7.09%／VST −5.16%／TLN −8.38%，10Y +1bp）—— AI-power 族群因子；FOMC 當日 −0.14%、XLU 0.00% | sensitivity 高 → **中**（原判是斷言）；path 去掉寫死的 67.0%；history 補 09-14；regime 補「bond-proxy 反應在 09-15 不在 FOMC 日」 |
| **MSFT** | L0 | 反推 g 對 rf 斜率 ≈ 0.98：本則 +0.05pp、累計 +0.3pp，仍在 100bp 網格同一格；**真正的曝險在錨 A 的 5 年窗口含零利率期** | path 的「淨現金」有誤（EV 3.74T > 市值 3.69T）已改；escalation 動作加「重審錨 A 窗口」 |
| **GOOG** | L0 | 模型無 r；提出不複製數值的檢查器：盈餘殖利率對 10Y 利差（base 20x → 約 0；現價隱含 24.85x → 低於 10Y 約 1pp） | 記進 path 待 /cta 決定；補「本檔也是排擠來源」；sensitivity 改為「模型 0／經濟 中」分列 |
| **META** | L0 | 利息費用在營業線以下，不在「總成本費用」口徑；SOTP 的 r=9% 彈性約 0.1%／pp；曝險在 bull 22x | path 改為「沒有進 key_variables 的 r」並記 SOTP 那個；錨 B 對本 driver 天生中性 |
| **COHR** | L0 | r 14.4 → 14.46%，對回收期結論無影響；**漏了浮動利率負債那條真實現金腿**（量級未取得；+25bp 要動營運現金流佔營收 1pp 需約 285 億美元浮動負債） | path 補該腿；gaps 加浮動負債餘額與避險比例 |
| **2308** | L0 | 台債 0bp；「Fed 升、台央行不跟」對本檔不乾淨 —— 匯率（+）與淨現金利息（+）部分對沖折現率（−） | path 記對沖；lag 語意改為「以台債 10Y 為觀測點」（五檔皆同） |
| **3037** | L0 | 台債 0bp；beta 2.34 為 ABF 三家最高 —— 方法層若改 CAPM 類，本檔 r 上移最多 | — |
| **6239** | L0 | 台債 0bp；**台股五檔裡唯一有融資成本腿**：淨負債 299 億元、三年 1,200 億元 capex 靠籌資 | path 補該腿；lag 加「融資成本再落後 1–2 季進損益」 |
| **8046** | L0 | 台債 0bp；「sensitivity 低」是無可更新參數，不是估值對 r 不敏感 —— r +1pp → base 目標價約 −10% 至 −14% | path 明寫此區分 |
| **8299** | L0 | 台債 0bp；即使 r 錨定，正常化 ROE 那個串聯缺口仍擋著檢查器；各檔 beta 是對大盤的，不是對利率的 | gaps 第 5 項加註 |

**五檔台股的共同結構問題**：driver 的三條 falsifier 與第一條 escalation 全以美債或 SEP 為門檻，而台股五檔的 r 只吃台債。
**Fed +25bp 對台債 0bp 這個實測本身就說明兩者不能互為代理。** 已新增一條以台債 10Y ≥ 2.20 或台灣央行升息為門檻的 escalation —— 否則五檔在本 driver 裡永遠只能被動判 L0。

**不在 transmission 的 28 檔**：折現率不在任何模型參數裡，L0，未逐檔起判官。**不是免疫，是沒有可更新的東西**；第一條 escalation（10Y ≥ 5.25 連續 10 日）觸發時全清單重估。

---

## 5. state 改了什麼（全部是結構與文字，無數值）

| 檔 | 改動 |
|---|---|
| CEG／INTU／MSFT／GOOG／META／COHR／2308／3037／6239／8046／8299 | 補 `driver_refs: discount-rate, direction '-'`（INTU 原本連 `driver_refs` 鍵都沒有；CEG 的刻意留空註解改寫為「需求軸仍空、折現率軸已補」）；`last_updated` → 2026-09-17 |
| 2308（2 項）／3037／6239／8046／8299 | gaps 裡「台幣無風險利率未取得／cnyes 2024-09-10 不可用」改為「rf 已住在 driver（以引用取用，不複製）；剩下的是 beta 不可用的方法層決定」 |
| coverage.yaml | `shared_macro_inputs` 改為指標；`as_of` → 2026-09-17；一處指向該區塊的文字改指 driver |
| 3665 | 一處指向 `shared_macro_inputs` 的文字改指 driver |
| notes/2026-09.md | 追加第 3 次記錄與計數定案 |

---

## 6. 另案，不在此處理

- **CEG 的 CTA 位階**：`invalidation` 為「週收盤跌破 268.47」，09-16 收 259.53 已在其下；判定點是 **09-18 週收盤**。訊號已是偏空，觸發的效果落在 `changes_if` 的「週收盤 < 50DMA → 偏空確認」與信心，不是評級跨級。**走 /cta CEG 的 L2 路。** 同檔 key_variable 的 67.0% 與 multiple_basis 已重測的 60.0% 不一致，屆時同步。
- **CEG 09-14 的 −7.09% 沒有任何 driver 路由過來**：本檔沒有需求側 driver_refs，所以不在 hyperscaler-capex 09-14 那輪 31 檔扇出裡。state gaps 裡「該建 `datacenter-power-demand` driver」的缺口這次真的咬人了。
- **方法層決定（driver gaps 第 2 項）**：rf 兩國都有了，但 beta 在本清單被判不可用，錨 C 仍算不出來。要決定的是「全族群單一折現率」或「分市場單一 ERP」。⚠ 對 INTU 這種 r 直接進目標價的標的，那個決定是 L2 級（beta 0.98 → 1.20 即 −13.5%）—— 決定前先用判官已算好的敏感度表。
- **GOOG 盈餘殖利率利差檢查器**：不需 beta，可在方法層決定之前先做；由 /cta GOOG 決定是否採用。

---

## 7. 本報告不做什麼

- 不動任何標的的情境、機率、倍數、目標價或訊號 —— 11 檔全 L0，E4 對照不受影響。
- 不把 5.01 或 1.94 複製進任何一份個股 state。
- 不因為 10Y 站上 5% 調整任何機率 —— 那是價格層的事，除非構成 CTA 位階變化（CEG 的那個走另案）。
- 不把「Fed 主席點名 hyperscaler 募資」讀成 Fed 的反應函數。
