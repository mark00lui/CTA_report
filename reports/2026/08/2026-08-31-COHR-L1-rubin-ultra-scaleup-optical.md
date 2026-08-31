---
date: 2026-08-31
ticker: "COHR"
name: Coherent
level: L1
driver: accelerator-roadmap
trigger: "CPO進度與時程 值不變但信心提高 — 管理層的 scale-up 時程首次取得客戶端 roadmap 的外部驗證"
summary: "NVIDIA Rubin Ultra NVL576 排定 2027 下半，其 576 顆 NVLink domain 明載為銅纜加直接光連接 — 與本檔管理層說法時點吻合"
signal: 中性
conviction: 低
tp_before: 328
tp_after: 328
tp_delta: "0%"
supersedes: ""
sources:
  - "DataCenterDynamics／TweakTown／wccftech 2026-08 — NVIDIA Rubin Ultra NVL576 排定 2027 下半、600kW/櫃、Kyber 機櫃架構；scale-up domain 自 144 顆擴大至 576 顆，由 8 個 MGX NVL 機櫃各 72 顆組成單一 NVLink domain，採 copper and direct optical connections"
  - "NVIDIA Technical Blog / Radiant — Vera Rubin Ultra 導入兩層 all-to-all NVLink 拓撲；15 EF FP4 推論、4.6 PB/s HBM 頻寬"
  - "drivers/accelerator-roadmap.yaml（2026-08-31 更新，含 cpo_layer_note 的 scale_up 狀態更正）"
---

# 變更單｜COHR Coherent｜2026-08-31

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L1**｜觸發：`CPO進度與時程` 的**值不變，信心提高**
**事件**：NVIDIA 下一代平台規格揭露，時點與本檔管理層說法吻合｜證據 tier：推論（第三方規格報導）
**driver 來源**：`accelerator-roadmap`

## 兩個獨立來源的時點對上了

| 來源 | 說法 |
|---|---|
| **本檔管理層**（2026-08 法說） | scale-up 型 CPO 自**曆年 2027 下半**開始貢獻營收 |
| **NVIDIA 產品 roadmap**（第三方規格報導） | Rubin Ultra NVL576 排定 **2027 下半**出貨，其 576 顆單一 NVLink domain 為 **copper and direct optical connections** |

一個是供應商自述，一個是客戶端的產品時程。**兩者互相驗證。**

建檔時我把本檔的研究價值寫成「覆蓋清單中唯一能提供第一手 CPO 時程的標的，可用以交叉驗證 6442 與 3008」。本次是**反過來**——本檔自己的說法拿到了外部座標。

## 順帶更正了 driver 的一個記載

`drivers/accelerator-roadmap` 的 `cpo_layer_note` 原本寫著：

> `scale_up`：**仍為銅** — Rubin 採 NVLink 6 銅纜；**CPO 尚未進入 scale-up 域**

那在 **Rubin 世代成立**，在 **Rubin Ultra 世代不成立**。已更正為「銅光並用，光學開始進入」，並註明時點必須分開講。

**這件事對 cpo 因子三檔（6442／3008／COHR）都重要**：scale-up 是比 scale-out 大得多的市場，光學若進入該層，可及市場的量級不同。

## 模型未變動

| | |
|---|---|
| 三情境 EPS 與倍數 | **不變**（7.80/9.41/10.69 × 22x/33x/43x） |
| 加權目標價 | **328，不變**，相對現價 279.20 為 +17.5% |
| 訊號 | 中性／信心低，**不變** |

**沒有據此上修的理由**：576 顆 domain 中「銅纜 + 直接光連接」的**光學占比未揭露**。時點對上了，**金額還沒**——而 BOM 價值量才是能進模型的東西。

信心維持低：建檔時列的四個理由（錨 A 失效、錨 C 不可用、bull EPS 口徑存疑、客戶集中度未取得）一個都沒被本則解決。

## ⚠ 缺口

- **576 顆 domain 的光學占比**（決定 CPO 在 scale-up 的實際 BOM 價值量）。取得途徑：NVIDIA 技術文件、ODM 拆解報告、或本檔法說 Q&A。
- 本檔既有缺口未關閉：客戶集中度（資料中心段已占營收 79%）、capex 峰值時點、FY2027 EPS 共識區間口徑不一致。
- ⚠ 第三條 falsifier（CPO 初期營收未於 2026 年 12 月當季認列）**不受本則影響**——那是 scale-out 的初期營收，本則講的是 scale-up，兩者是不同的產品層。
