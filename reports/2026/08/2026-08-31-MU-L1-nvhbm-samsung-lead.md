---
date: 2026-08-31
ticker: "MU"
name: Micron
level: L1
driver: accelerator-roadmap
trigger: "HBM進度 值不變但信心變化 — 兩個方向相反的訊號同時出現"
summary: "記憶體短缺獲最強確認（NVIDIA 為此重新設計產品），但三星取得 NVHBM 早期領先"
signal: 中性
conviction: 低
tp_before: 1060
tp_after: 1060
tp_delta: "0%"
supersedes: ""
sources:
  - "Tom's Hardware 2026-08 — Nvidia reportedly testing lower memory configs of Rubin Ultra as memory shortage bites back；測試組態低至 192GB，並回退至 HBM4"
  - "Seoul Economic Daily／Sammy Fans／BigGo 2026-08-28 — 三星取得 NVIDIA 自訂記憶體 NVHBM 早期領先，開發 8 層 HBM4E；NVIDIA 訂速度規格 17–18 Gbps（較三星初期 HBM4E 樣品 14.4 Gbps 高約 20%）"
  - "guru3d／Sammy Fans 2026-08-26 — NVHBM 將記憶體控制器移入 HBM base die，相對標準 HBM4E 達 +30% 頻寬、−15% 功耗；首次實作為 Rubin Ultra（2027 下半）；HBM 配置自單一 12-high HBM4E 擴大為 8-high HBM4E／12-high HBM4／8-high HBM4"
  - "drivers/accelerator-roadmap.yaml（2026-08-31 更新）"
---

# 變更單｜MU Micron｜2026-08-31

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L1**｜觸發：`HBM進度` 的**值不變，但同時出現兩個方向相反的訊號**
**事件**：NVIDIA Rubin Ultra 記憶體規格揭露｜證據 tier：推論（第三方報導）
**driver 來源**：`accelerator-roadmap`

## 兩個方向相反的訊號，同一天

### （+）記憶體短缺獲得最強形式的確認

NVIDIA 把 Rubin Ultra 的 HBM 配置**自原本單一的 12-high HBM4E，擴大為多個備案**：8-high HBM4E、12-high HBM4、8-high HBM4，測試中的組態**低至 192GB**。

一手報導（Tom's Hardware）的標題直指原因：***as memory shortage bites back***。

**客戶願意犧牲規格來遷就供給，比任何價格數據都直接。** 這是 2026-08-31 稍早記入 `ai-accelerator-demand` 的 279bn 採購承諾之外，第二個獨立角度的確認。

⚠ **必須記下一個框架陷阱**：引發本次更新的中文二手報導把同一件事寫成**設計哲學選擇**——「NVIDIA 優先提升傳輸速度而非堆疊層數，接受單 GPU 容量下降，靠多 GPU 互連補回算力」。

**兩種框架對本檔的含意完全相反：**

| 框架 | 推論 | 對本檔 |
|---|---|---|
| 設計選擇 | NVIDIA **主動**選擇少用記憶體 → 單 GPU 含量結構性下降 | **偏空** |
| 供給受限 | NVIDIA **買不到**足夠記憶體 | **偏多** |

採後者，理由是它與 NVIDIA 法說的三項揭露互相印證：279bn 採購承諾 primarily memory、毛利率因記憶體成本觸底 71–72%、黃仁勳明言 FY2028 +70% 是**供給受限**。

### （−）三星取得 NVHBM 早期領先

NVIDIA 自訂記憶體 **NVHBM** 將記憶體控制器移入 HBM base die，騰出 XPU 面積，相對標準 HBM4E 達 **+30% 頻寬、−15% 功耗**。首次實作即在 Rubin Ultra（2027 下半）。

**三星電子取得早期領先**，正開發 8 層 HBM4E，NVIDIA 訂的速度規格為 **17–18 Gbps**（較三星初期樣品 14.4 Gbps 高約 20%）。

⚠ 本檔 `HBM進度` 記著「管理層目標為 **HBM 市占率接近其 DRAM 市占率**」。**下一代自訂記憶體的首發夥伴不是本檔。**

⚠ 但「早期領先」**不等於獨家**，SK 海力士與本檔的 NVHBM 進度均未取得。

## 模型未變動

| | |
|---|---|
| 三情境、倍數 | **不變** |
| 加權目標價 | **1,060，不變**，相對現價 932.86 為 +13.6% |
| 訊號 | 中性／信心低，**不變** |

**兩個訊號方向相反且都無法量化**——短缺的程度沒有數字，三星的領先幅度也沒有。用算不出來的東西調模型就是編造。

## ⚠ 缺口

- **本檔與 SK 海力士的 NVHBM 進度**（三星「早期領先」不等於獨家，但缺乏對照就無法評估競爭態勢）。取得途徑：本檔 FQ4 法說（**2026-09-30**，已在 checkpoints）。
- 8 層與 12 層的最終選擇未定，NVIDIA 仍在測試多個備案——這直接決定單 GPU 的 HBM 含量。
- 既有缺口未關閉：279bn 中記憶體占比；中週期正常化 EPS 的自下而上估算。
