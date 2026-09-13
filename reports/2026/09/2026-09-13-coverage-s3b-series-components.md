---
date: 2026-09-13
ticker: coverage
level: L2
supersedes: reports/2026/09/2026-09-13-coverage-s6-derived-index.md
trigger: "結構調整 S3b：引入 series 與 components 兩個欄位，把 S3a 標記為「未型別化」的 7 筆全部清掉。搬移原則是「原字串裡的每一個數字都要有去處，不是被摘要掉」—— 七筆逐筆按此處理，其中四筆的去處是明寫進 source"
summary: "✓✓✓ **S3b 完成：`未型別化` 自 7 筆清為 0。** 引入兩個欄位，各對應一種「一格裝了不只一個數」的形狀：**`series`（時間序列，`[{period, value}]`，最新的排第一，`value` 就是它）** 與 **`components`（同時存在的多個量，`[{name, value}]`，`value` 若為數值必須等於其中之一）**。 ｜⚠⚠ **搬移原則是「原字串裡的每一個數字都要有去處，不是被摘要掉」** —— 去處只有三種：**(a)** 進 `series`／`components`；**(b)** 本來就已經在 `source` 裡；**(c)** 兩者皆非 → **明寫進 `source` 並註明是型別化時搬過去的**。**七筆逐筆按此處理，其中四筆動用了 (c)**：6239 的 2026 EPS 三估值 10.9／12.96／14.26（**與目標價單位不同，不是同一個變數**）／GOOG 的「正常化後 H1 EPS 約 $5.64、年化約 $11.3」（**那是另一個量，不是本項對 EPS 的影響**）／MSFT 的「FY26 全年營收首破 $100B」與「Q1 FY27 指引的 +45% 為 cc 口徑、共識 41.4%」／2308 與 LITE 兩筆區塊純量裡的整段敘述（原文未改、加註搬移日期）。 ｜**兩筆區塊純量的處置**：2308 AI相關營收占比 → `value: 40`＋`約值`＋components（AI 產品 25、液冷 12）；LITE GAAP淨損的成因 → `value: -6935`＋`點值`。⚠ **2308 的 components 合計 37 低於 value 的 40，差額即三層同心圓口徑的重疊帶 —— 這一點特別寫進 `source`，否則讀者會以為其中一個數字錯了。** ｜⚠ **8046 的 `value: __` ＋ `多值` 是一個結論不是缺口**：兩個產品的漲幅（ABF +50／BT +70）沒有單一代表值，而 `key_variables` 已達上限 6，拆成兩個變數需先汰換一項。**未填欄位統計因此自 81 升為 82，那個 +1 是誠實的。** ｜**三項反向測試**：`value` 與 `series` 第一筆不符 ✓擋下／`多值` 的 `value` 不等於任何 component ✓擋下（訊息：「否則它是憑空多出來的第三個數」）／有 `series` 但未標 `序列最新` ✓擋下。 ｜✓ `build_db.py` 同步新增 `kv_series`（8 列）與 `kv_components`（6 列）兩表，序列現在可以直接 SQL 查詢。 ｜✓ 六支驗證鏈 0 block／0 error。"
signal: n/a
conviction: n/a
tp_before: n/a
tp_after: n/a
tp_delta: "n/a —— 本報告不動任何標的的情境、倍數、機率或目標價。它把七格散文裡的數字放進有型別的欄位"
sources:
  - "scripts/validate_state.py（2026-09-13 改動）— VALID_QUALIFIERS 新增「序列最新」「多值」；新增 series／components 的結構與一致性檢查"
  - "scripts/build_db.py（2026-09-13 改動）— 新增 kv_series 與 kv_components 兩表；--stats 顯示序列點 8、分量 6"
  - ".claude/skills/cta-research/references/state-schema.md（2026-09-13 改動）— 新增 series／components 專節與搬移原則"
  - "七筆遷移逐筆結果（2026-09-13）— 2308 營益率 16.7／序列最新／series 3；2308 AI相關營收占比 40／約值／components 2；6239 市場共識與目標價 335／多值／components 2；8046 ABF與BT漲價幅度 __／多值／components 2；GOOG 股權證券損益對EPS影響 6.24／序列最新／series 2；MSFT Azure成長率 43／序列最新／series 3；LITE GAAP淨損的成因 -6935／點值"
  - "反向測試（2026-09-13，以檔案複本進行）— MSFT value 43→41 觸發「value 41 ≠ series 第一筆 43」；8046 value __→60 觸發「不等於任何一個 component」；MSFT value_qualifier 序列最新→點值 觸發「有 series 但 value_qualifier 不是序列最新」"
  - "scripts/validate_state.py（2026-09-13 改動後執行）— 0 error, 6 warn, 11 note, 82 個未填欄位；[UNTYPED] 區塊已不再出現"
---

# coverage —— S3b：series 與 components，未型別化清為 0

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L2**｜觸發：結構調整 S3b
**本報告不動任何標的的情境、倍數、機率或目標價。**

---

## 1. ⚠⚠ 搬移原則：每一個數字都要有去處

**這一步最容易出錯的方式不是把數字放錯欄位，是把數字摘要掉。**

原字串裡的每一個數字，去處只有三種：

| | 去處 | 這一輪用到幾次 |
|---|---|---:|
| (a) | 進 `series` 或 `components` | 7 筆全部 |
| (b) | 本來就已經在 `source` 裡 | 3 筆（2308 營益率、8046、6239 的 335） |
| (c) | 兩者皆非 → **明寫進 `source`，並註明是型別化時搬過去的** | **4 筆** |

**動用 (c) 的四筆，每一筆都是「它其實是另一個變數」：**

| ticker | 被搬進 `source` 的東西 | 為什麼不能塞進 `series`／`components` |
|---|---|---|
| 6239 | 2026 EPS 三估值 10.9／12.96／14.26（離散度 31%） | **單位是「元／股」，而本格的 `unit` 是「元」（目標價）—— 不是同一個變數** |
| GOOG | 「正常化後 H1 EPS 約 $5.64、年化約 $11.3」 | **那是正常化後的 EPS 本身，不是本項對 EPS 的影響** |
| MSFT | 「FY26 全年營收首破 $100B」「Q1 FY27 的 +45% 為 cc 口徑、共識 41.4%」 | 一個是營收、一個是口徑註記，都不是成長率序列的一點 |
| 2308／LITE | 兩段完整敘述（原文未改） | 那是分析，不是數字 |

---

## 2. 兩個新欄位

```yaml
- name: Azure成長率            # 時間序列
  kind: 量化
  value: 43
  value_qualifier: 序列最新
  series:
  - {period: Q4 FY26, value: 43}       # 最新的排第一，value 就是它
  - {period: FY26 全年, value: 41}
  - {period: Q1 FY27 指引, value: 45}
  unit: '% YoY'

- name: ABF與BT漲價幅度         # 同時存在的多個量，沒有單一代表值
  kind: 量化
  value: __
  value_qualifier: 多值
  components:
  - {name: ABF 載板售價漲幅, value: 50}
  - {name: BT 載板售價漲幅, value: 70}
```

### 七筆的結果

| ticker | 變數 | `value` | 修飾語 | 結構 |
|---|---|---:|---|---|
| 2308 | 營益率 | 16.7 | 序列最新 | series 3 |
| 2308 | AI相關營收占比 | 40 | 約值 | components 2 |
| 6239 | 市場共識與目標價 | 335 | 多值 | components 2 |
| 8046 | ABF與BT漲價幅度 | `__` | 多值 | components 2 |
| GOOG | 股權證券損益對EPS影響 | 6.24 | 序列最新 | series 2 |
| MSFT | Azure成長率 | 43 | 序列最新 | series 3 |
| LITE | GAAP淨損的成因 | −6935 | 點值 | — |

---

## 3. 兩個需要單獨講的判斷

### 3.1 2308 的 components 合計 37，而 `value` 是 40

**這看起來像算錯，但它不是。**

原字串寫的是「約 40%（廣義「AI 相關」）＝ AI 產品**逾** 25% ＋ 液冷產品**逾** 12%」——
兩個分量都是**下界**，合計 37 是下界的和，而 40 是整體的約值。
差額就是那個 `source` 裡已經記著的「三層同心圓」口徑重疊帶。

⚠ **這一點特別寫進 `source`**，否則讀者（或三個月後的自己）
看到 25 + 12 ≠ 40 會以為其中一個數字錯了，
**然後很可能「修正」掉一個本來是對的數字。**

### 3.2 8046 的 `value: __` 是結論，不是缺口

兩個產品的漲幅沒有單一代表值。**這一格該拆成兩個變數** ——
但 `key_variables` 上限是 6，8046 已經滿了，拆分需先汰換一項（那是研究判斷，不是結構工作）。

所以它暫時以 `components` 承載，`value` 維持 `__`。
**未填欄位統計因此自 81 升為 82 —— 那個 +1 是誠實的**，
它記的是「這裡還有一個結構問題沒解決」，而不是「這個數字沒查到」。

⚠ 這與 S2 的 `none_qualifies` 是同一個主題的反面：
**S2 把「已量化的空」從缺口裡拿出來，S3b 把「結構未解的空」放回缺口裡。
兩次都是讓 `__` 只代表它真正代表的東西。**

---

## 4. 三項反向測試

| 測試 | 錯誤訊息 |
|---|---|
| `value` 與 `series` 第一筆不符（MSFT 43→41） | `value 41 ≠ series 第一筆 43 — 序列的第一筆必須是最新的那一筆，而 value 就是它` |
| `多值` 的 `value` 不等於任何 component（8046 `__`→60） | `value 60 不等於任何一個 component — 多值的代表值必須是其中之一，否則它是憑空多出來的第三個數` |
| 有 `series` 但未標 `序列最新`（MSFT 改標點值） | `有 series 但 value_qualifier 不是序列最新` |

---

## 5. 衍生索引同步

`build_db.py` 新增兩表：

```
　　序列點            8
　　分量             6
```

```sql
SELECT ticker, name, period, value FROM kv_series ORDER BY ticker, seq;
```

**2026-09-13 之前，這三條時間序列是三個字串，SQL 看不見它們。**

---

## 6. 本輪七步全部完成

| 步 | 產出 | 閘門 |
|---|---|---|
| S0 | 修正「`--stale` 無陳舊變數」的覆蓋率宣稱 | — |
| S1 | as-of 涵蓋率 189/232 → **232/232**，11 筆逾期現形 | 2 條 error ＋ 涵蓋率必印 |
| S2 | `__` → `__` ＋ `none_qualifies`，未填欄位 89 → 81 | 無依據的 `none_qualifies` → error |
| S4 | **E4** 跨層對帳，39/39 相符 | 併入 pre-commit，孤立反向測試已證獨立價值 |
| S3a | `kind` 型別契約（量化 210／質性 22），6 筆無損遷移 | 4 條 error，4 項反向測試 |
| S5 | `event_log[].delta` 40 萬字元 → 39 份沿革檔，state **−25.3%** | 帶 `delta` → error |
| S6 | 衍生索引 `build_db.py`（9 表，不進版控） | 不進鏈（輸出不提交） |
| **S3b** | **`series`／`components`，未型別化 7 → 0** | 3 條 error，3 項反向測試 |

### 仍未處理、且已知

- **`unit` 108 種相異值**，期間仍夾帶在單位字串裡（`%（2026 Q2）`、`十億美元（2026 全年）`）
  —— 需要一個獨立的 `period` 欄位與受控詞彙。**這是 `key_variables` 剩下的最後一塊。**
- **`signal.basis` 平均 2,763 字元**（合計 107,775）—— 與 `delta` 同形狀，
  **但它混著當下判斷與歷史，不能機械搬移。**
- **`build_index.py` 對 front-matter 解析失敗只 warn 不 error** ——
  一份壞掉的報告不進索引、不被 E4 對照、也不進衍生索引，三處都只是安靜地少一筆。
- **11 筆逾 90 天的陳舊變數**（最舊 986 天）—— 研究工作。
- **5 處 YAML 重複鍵**與 **hyperscaler-capex → AMZN 缺 state 檔**。
