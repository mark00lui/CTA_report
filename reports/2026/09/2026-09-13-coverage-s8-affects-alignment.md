---
date: 2026-09-13
ticker: coverage
level: L2
supersedes: reports/2026/09/2026-09-13-coverage-s7-silent-drops.md
trigger: "結構調整 S8（由 S7 的 3017 案例引出）：driver 的 affects 是「扇出時要更新哪些變數」，但它的名稱從未被對照過 state 的 key_variables。實測 89 項裡 15 項指向不存在的名稱 —— 扇出指令指著空氣"
summary: "✓✓✓ **S8 完成：driver 的 `affects` 對齊率自 83%（89 項中 74 項）拉到 100%（85 項全中），並升為 error。** **`affects` 的用途是「扇出時要更新哪些變數」，而它的名稱從未被對照過** —— 15 項指向該檔根本沒有的變數名稱，**而扇出腳本不會抱怨：它會照著一組不存在的名字去更新，然後什麼也沒更新。** ｜**15 項分兩類，第二類才是真發現**：**(a) 12 項是名稱漂移** —— 變數被改名而 driver 沒跟著改（3017 的「毛利率」→「Q2 2026 毛利率（對 FY2025 全年 25.79% 的基期）」、「水冷板月產能」→「水冷板月產能目標」、「資本支出強度」→「年度資本支出」；8299 的「毛利率」→「Q2 2026 毛利率」；6239 的兩項其實指向同一個變數，已去重）。**(b) 3 項在該檔根本沒有對應變數，那是 driver 認為該追、而那一檔從來沒在追的東西** —— **3017 的「液冷營收占比」（該檔 thesis 圍繞水冷板，而 driver 問的是液冷整體，兩者不是同一件事）／GOOG 的「資本支出」／META 的「資本支出guidance」。** ⚠⚠ **後兩者特別值得記：GOOG 與 META 的象限判定（Q2，現金流與企業價值）正是建立在資本支出爆炸上，而兩檔的 `key_variables` 都沒有 capex —— 扇出因此無處可落。** 三項自 `affects` 移除並各在該檔的 `gaps` 記一筆（含取得途徑），**不是刪掉了事。** ｜**閘門**：`affects` 的每一項必須是該檔 `key_variables` 的名稱，否則 **error**。反向測試：把 8299 的 `'Q2 2026 毛利率'` 改回 `'毛利率'`，立刻擋下並指名檔案、ticker 與變數名。 ｜⚠ **這一步是 S7 的副產品** —— 修 `hyperscaler-capex` 的 3017 重複鍵時順手比對了一次名稱，才發現這件事。**S7 的報告把它列為「下一個候選檢查」，S8 就是它。** ｜✓ 六支驗證鏈 0 block／0 error；`validate_state.py` 的 WARN 維持 1（僅 AMZN 缺 state 檔）。"
signal: n/a
conviction: n/a
tp_before: n/a
tp_after: n/a
tp_delta: "n/a —— 本報告不動任何標的的情境、倍數、機率或目標價。它讓扇出指令指向實際存在的變數"
sources:
  - "全清單 affects 對齊自算（2026-09-13，修正前）— 89 項中相符 74（83%）、不符 15，分布於 accelerator-roadmap（6239 ×2、3017 ×3）、ai-accelerator-demand（8299 ×1、3017 ×3、GOOG ×1、META ×1）、hyperscaler-capex（8299 ×1、3017 ×3）"
  - "全清單 affects 對齊自算（2026-09-13，修正後）— 85 項全部相符（100%）"
  - "state/3017.yaml 的 key_variables 名稱（2026-09-13）— Q2 2026 毛利率（對 FY2025 全年 25.79% 的基期）／2026 年 8 月營收／ASIC 營收佔比（管理層前瞻）／年度資本支出／水冷板月產能目標／2026 年法人共識稅後純益"
  - "state/8299.yaml 的 key_variables 名稱（2026-09-13）— Q2 2026 毛利率／近四季 EPS／2026 年 8 月營收／當期股東權益報酬率／市營比／存貨周轉天數"
  - "state/GOOG.yaml 與 state/META.yaml 的 key_variables 名稱（2026-09-13）— GOOG：Search營收成長／Cloud成長率／股權證券損益對EPS影響／TPU外部採用進展／反壟斷救濟狀態；META：廣告營收成長／ARPU／總成本費用成長／總費用guidance／Reality Labs虧損。⚠ 兩檔皆無 capex 變數"
  - "scripts/validate_state.py（2026-09-13 改動）— check_driver_integrity 新增 affects 名稱對照，不符即 error"
  - "反向測試（2026-09-13）— 把 hyperscaler-capex 的 transmission[8299].affects 改回 '毛利率'：觸發「不在 state/8299.yaml 的 key_variables 裡 — 扇出指令指著一個不存在的變數」"
---

# coverage —— S8：扇出指令指著空氣

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L2**｜觸發：結構調整 S8
**本報告不動任何標的的情境、倍數、機率或目標價。**

---

## 1. `affects` 從未被對照過

`drivers/*.yaml` 的 `transmission[].affects` 是**「扇出時要更新哪些變數」**。
它是一組指向 `state/<ticker>.yaml` 的 `key_variables[].name` 的**跨檔參照**。

**而那個參照從來沒有被檢查過。**

| | 修正前 | 修正後 |
|---|---:|---:|
| `affects` 項目數 | 89 | 85（去重後） |
| 名稱對得上 | **74（83%）** | **85（100%）** |
| 指向不存在的變數 | **15** | **0** |

⚠ **扇出腳本不會抱怨**：它會照著一組不存在的名字去更新，然後什麼也沒更新。

---

## 2. 15 項分兩類，第二類才是真發現

### (a) 12 項是名稱漂移 —— 變數被改名而 driver 沒跟著改

| driver | ticker | 舊名 | 現行名稱 |
|---|---|---|---|
| ×3 | 3017 | `毛利率` | `Q2 2026 毛利率（對 FY2025 全年 25.79% 的基期）` |
| ×3 | 3017 | `水冷板月產能` | `水冷板月產能目標` |
| ×2 | 3017 | `資本支出強度` | `年度資本支出` |
| ×2 | 8299 | `毛利率` | `Q2 2026 毛利率` |
| ×1 | 6239 | `FOPLP與DDR5_TSV進度` | `FOPLP與DDR5_TSV進度與競爭格局` |
| ×1 | 6239 | `FOPLP競爭格局與規格` | **與上一項指向同一個變數 → 去重** |

**這一類是純粹的維護債**：state 改名是正常的研究活動，
而沒有任何東西提醒 driver 要跟著改。

### (b) ⚠⚠ 3 項在該檔根本沒有對應變數

| driver | ticker | affects 想更新的 | 該檔有嗎 |
|---|---|---|---|
| `accelerator-roadmap` | 3017 | `液冷營收占比` | **沒有** |
| `ai-accelerator-demand` | GOOG | `資本支出` | **沒有** |
| `ai-accelerator-demand` | META | `資本支出guidance` | **沒有**（只有「總費用guidance」） |

**這是 driver 認為該追、而那一檔從來沒在追的東西。**

- **3017**：該檔 thesis 圍繞**水冷板**，而 driver 問的是**液冷整體**的營收占比 ——
  **兩者不是同一件事**，而這個落差此前沒有任何地方記著。
- ⚠⚠ **GOOG 與 META 更值得記**：兩檔的**象限判定（Q2，現金流與企業價值）
  正是建立在資本支出爆炸上**，而兩檔的 `key_variables` 都**沒有 capex**。
  **扇出因此無處可落 —— 一個被宣告為決定性的量，不在關鍵變數裡。**
  （META 的「總費用guidance」不可代用：費用在損益表、capex 在現金流量表。）

三項自 `affects` 移除，並**各在該檔的 `gaps` 記一筆（含取得途徑）—— 不是刪掉了事**。
META 的 `key_variables` 目前 5 項、上限 6，**可以直接新增**；
GOOG 已滿 5 項 …… 其實也還有一格。兩者都是研究判斷，留給下一次 `/revalue`。

---

## 3. 閘門

```
[ERROR] drivers\hyperscaler-capex.yaml: transmission[8299].affects 的「毛利率」
        不在 state/8299.yaml 的 key_variables 裡 — 扇出指令指著一個不存在的變數
```

反向測試：把 8299 的 `'Q2 2026 毛利率'` 改回 `'毛利率'`，立刻擋下，還原後 0 error。

⚠ 這條檢查與既有的 `driver_refs` ↔ `transmission` 雙向一致檢查是**互補的**：
- 舊檢查問：**這兩個檔案認不認得彼此**
- 新檢查問：**認得之後，指的是不是同一個東西**

**前者通過而後者失敗，正是這 15 項一直沒被發現的原因。**

---

## 4. 它是怎麼被發現的

**S8 是 S7 的副產品。**

修 `hyperscaler-capex` 的 3017 重複鍵時，我為了確認「哪一組 `affects` 才是對的」，
順手把兩組名稱都拿去比對 3017 的 `key_variables` ——
**結果是兩組都對不上。** S7 的報告把它列為「下一個候選檢查」，S8 就是它。

⚠ **這一輪有好幾個發現是同一種來源：修一個東西的時候，順手驗證了一個從沒被驗證過的假設。**
S1 的 986 天、S7 的 2308 價格依據、S8 的 15 項 —— 三個都不是找出來的，是**撞出來的**。

---

## 5. 本輪收工狀態

| 檢查 | 結果 |
|---|---|
| `check_public.py` | 0 block（39 warn 皆為規則文件自述） |
| `check_append_only.py` | 通過 |
| `validate_state.py` | **0 error**，1 warn（`hyperscaler-capex` → AMZN 缺 state 檔） |
| `build_index.py --check` | 205 份 front-matter 全部可解析 |
| `cross_check.py --gate` | 39 檔算術自洽（E1–E4），E4 對照 39/39 |
| `build_site.py` | 兩次 md5 相同 |

**本輪未 push。**

### 仍未處理、且已知

| 項目 | 量 | 性質 |
|---|---:|---|
| `unit` 仍夾帶期間或口徑 | 81 筆 | 逐筆判斷，部分該變成 `series` 點 |
| `signal.basis` | 平均 2,763 字元 | **混著當下判斷與歷史，不能機械搬移** |
| GOOG／META 缺 capex 關鍵變數 | 2 檔 | **研究判斷**（S8 已記進 gaps） |
| 3017 的液冷 vs 水冷口徑落差 | 1 檔 | **研究判斷**（S8 已記進 gaps） |
| 逾 90 天的陳舊變數 | 11 筆（最舊 986 天） | **研究工作** |
| `hyperscaler-capex` → AMZN 缺 state 檔 | 1 | 建檔或移除 transmission，兩者都要人決定 |
