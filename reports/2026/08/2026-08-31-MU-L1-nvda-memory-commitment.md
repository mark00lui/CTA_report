---
date: 2026-08-31
ticker: "MU"
name: Micron
level: L1
driver: ai-accelerator-demand
trigger: "key_variable 值不變但信心提高 — 漲價循環首次取得來自下游客戶財務長的一手量化證據"
summary: "NVIDIA 採購承諾 119 → 279 bn、明言主要為記憶體，並使其自身毛利率觸底 71–72%"
signal: 中性
conviction: 低
tp_before: 1060
tp_after: 1060
tp_delta: "0%"
supersedes: ""
sources:
  - "NVIDIA Q2 FY2027 財報與法說 2026-08-26 — 對供應商採購承諾自三個月前的 119 bn 增至 279 bn，CFO Colette Kress 稱增幅 primarily related to the procurement of memory；總未來承諾約 366 bn（供應承諾 279 + 雲端協議 29 + 長期租賃與股權投資）"
  - "同上 — 毛利率路徑 Q3 74.0% ±50bp → Q4 觸底 71–72% → FY2028 72–73%；Kress：memory costs exceeded our prior expectations and are headed even higher into next year"
  - "drivers/ai-accelerator-demand.yaml（2026-08-31 更新）"
---

# 變更單｜MU Micron｜2026-08-31

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L1**｜觸發：`HBM進度` 的**值不變，信心提高**
**事件**：NVIDIA Q2 FY2027 法說揭露採購承諾倍增且主要用於記憶體｜證據 tier：**事實**（客戶財務長於法說會揭露）
**driver 來源**：`ai-accelerator-demand`

## 為什麼這是 L1 而不是 L0

`HBM進度` 這一格的**內容一個字都沒改**，仍是「HBM4 已為領先客戶進入高量產、HBM4E 目標 2027 曆年量產」。

改變的是**證據等級**。本檔漲價循環先前的佐證：

| 順序 | 佐證 | 來源性質 |
|---|---|---|
| 1 | Meta 上修 capex 時提及零組件價格，記憶體為主因之一 | 支出方自述 |
| 2 | Amazon 將 +20B capex 上修直接歸因於記憶體成本 | 支出方自述 |
| 3 | TrendForce 估記憶體占 CSP capex 68% | ⚠ **二手引用，未讀到原始報告** |

`notes/2026-08.md` 於 2026-08-27 據此拒絕把本主題晉升為 driver：

> ⚠ **但先不晉升**：這第三次是 TrendForce 經二手來源引用，我沒讀到原始報告。前兩次是公司自己說的，這次不是。在一個 68% 這種量級的數字上，二手引用不足以支撐建 driver。

**本次補上的正是那個缺口。**

## 新證據

| | |
|---|---|
| NVIDIA 對供應商採購承諾 | **119 bn → 279 bn**（三個月內增逾一倍） |
| 增幅用途 | CFO Colette Kress：**primarily related to the procurement of memory** |
| 對 NVIDIA 自身毛利率的影響 | Q3 74.0% → **Q4 觸底 71–72%** → FY2028 回到 72–73% |
| Kress 對成本的說法 | memory costs **exceeded our prior expectations and are headed even higher into next year** |
| 總未來承諾 | 約 366 bn（供應承諾 279 + 雲端協議 29 + 長期租賃與股權投資） |

這不是產業機構的推估，是**下游最大客戶為了鎖料而實際簽下的金額**，加上它對該客戶自身損益約 3pp 的可量測壓縮。

## ⚠ 方向相反：同一則消息，兩個結論

| | 方向 | 為什麼 |
|---|---|---|
| **MU（本檔）** | **利多** | 客戶願意用更高的價格、簽更長的約來鎖定供給 |
| **NVDA** | **利空** | 同一筆成本壓縮它的毛利率至 71–72% |

這正是 CLAUDE.md 所說的「同一則消息對不同標的方向可能相反」。若對這兩檔寫出同方向的結論，那就是套用而非分析。

## 傳導的是價格，不是數量

本次順帶補上一個結構修正：**MU 與 SNDK 此前在覆蓋清單內，卻不在任何 driver 的 `transmission`**。這是結構缺口——兩檔的營收明顯受加速器需求驅動，卻沒有可引用的傳導路徑。

沒有早點補的原因是誠實的：在此之前只有「看起來應該相關」，**沒有一手證據證明這條路徑存在**。279 bn 的採購承諾提供了那個證據。

已補入 `ai-accelerator-demand` 的 transmission 並在 state 補上 `driver_refs`，完成雙向引用。傳導性質已寫明：

> ⚠ 與其他硬體端的傳導性質不同：3324／6442／COHR 是「加速器賣得多，我的零件就賣得多」，本檔是「加速器廠為了鎖料，願意用更高的價格簽更長的約」——**傳導的是價格不是數量**。因此該 driver 上修時，本檔的反應應先出現在合約價與毛利率，而非出貨量。

SNDK 同時補入但標明**強度較低**：NVIDIA 的承諾主要指向 HBM／DRAM，NAND 屬資料中心儲存層、不在加速器 BOM 的關鍵路徑上。這與 `coverage.yaml` 對 memory 因子「同向但不等深」的既有註記一致，定級 **L0**。

## 模型未變動

| | |
|---|---|
| 三情境 EPS 與倍數 | **不變** |
| 加權目標價 | **1,060，不變** |
| 訊號 | 中性／信心低，**不變** |

**沒有據此上修的理由**：279 bn 中記憶體占多少**未揭露**（只說 primarily），無法換算成本檔的營收金額。用一個算不出來的數字去調整模型，就是編造。

本檔仍是循環股框架，`multiple_basis` 記錄的正常化對照未變——現價隱含市場假設的中週期正常化 EPS 約 58 美元，為 FY2027 峰值共識 155.03 的 37%。

## ⚠ 缺口

- **279 bn 中記憶體的占比未揭露**。取得它才能與 TrendForce 的「記憶體占 CSP capex 68%」相互驗算，目前兩個數字各自懸空。取得途徑：NVIDIA 10-Q 的承諾附註是否拆分品項。
- 本檔既有缺口未關閉：中週期正常化 EPS 的自下而上估算；街上 47 位分析師目標價 361–2,200 的六倍價差。
