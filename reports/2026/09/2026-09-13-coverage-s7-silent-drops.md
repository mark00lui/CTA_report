---
date: 2026-09-13
ticker: coverage
level: L2
supersedes: reports/2026/09/2026-09-13-coverage-s3c-period-field.md
trigger: "結構調整 S7：讓兩種「靜默丟棄」停止靜默。(a) YAML 重複鍵 —— PyYAML 保留最後一個且不發警告，2308 實測到生效的 price_basis 是舊錨那一段而 cta.price 是新的；(b) 報告 front-matter 解析失敗 —— build_index 只 return None，那份報告不進索引、不被 E4 對照、也不進衍生索引，三處都安靜地少一筆"
summary: "✓✓✓ **S7 完成：兩種靜默丟棄各自升為 error，5 處重複鍵全部清除，`validate_state.py` 的 WARN 自 6 降為 1（僅剩 AMZN 缺 state 檔）。** ｜⚠⚠⚠ **最嚴重的一處有實質後果**：2308 的 `cta.price_basis` 有兩段，**第一段是 2026-09-11 的重錨（與 `cta.price` 的 1,620 一致），第二段是 2026-09-09／09-10 的舊討論 —— 而 PyYAML 保留最後一個，所以生效的是第二段。檔案裡的現價是 09-11 的，描述它的依據卻是 09-09 的，而檔案看起來完全正常。** 被丟棄的兩段已逐字搬進 `2026-09-13-2308-duplicate-key-archive.md`。 ｜⚠⚠ **第二嚴重的一處在 driver 層**：`hyperscaler-capex` 的 3017 條目有兩組 `sensitivity`／`affects`，**2026-09-10 充實時寫的 `[毛利率, 水冷板月產能, 資本支出強度]` 排在前面而完全沒有生效**，勝出的是舊值 `[月營收 YoY, 2026E EPS 市場預估]`——**亦即那次充實對扇出行為毫無作用，而沒有任何東西會說。** 同一條目的 `note` 還寫著「尚無 state/3017.yaml，本條目為刻意保留」，**而同一條目的 `path` 欄位自己就記著 3017 已於 2026-09-10 建檔 —— 那句話在被讀到的時候已經是假的。** 兩者一併更正。 ｜**8299 的兩行 `how_to_close`**：第一行是關閉證據、第二行是原取得途徑，**生效的是第二行 —— 一個已標示「✓ 已關閉 2026-09-12」的缺口，它的 `how_to_close` 顯示的卻是還沒做的事。** 已合併為一行，關閉證據在前。 ｜**兩道閘門**：重複鍵 WARN → **ERROR**（反向測試：在 TSM 塞兩個同名 `note`，兩條 error 皆觸發）；`build_index.py` 的 front-matter 解析失敗 → **exit 1**，並新增 `--check`（只驗證不寫檔）接進 pre-commit hook（反向測試：在一份報告的 `trigger` 裡塞一個壞的反斜線轉義，擋下並指名檔案與成因）。⚠ **後者是 CLAUDE.md 的硬性提醒裡已經記過的坑，而在 S4 與 S6 之後它的後果自一處變成三處。** ｜✓ 六支驗證鏈 0 block／0 error。"
signal: n/a
conviction: n/a
tp_before: n/a
tp_after: n/a
tp_delta: "n/a —— 本報告不動任何標的的情境、倍數、機率或目標價。它讓兩種靜默的資料遺失停止靜默"
sources:
  - "yaml.safe_load 實測（2026-09-13，2308 修正前）— 生效的 price_basis 為 2026-09-09 那一段，而 cta.price 為 1620.0、cta.updated 為 2026-09-11"
  - "yaml.safe_load 實測（2026-09-13，driver 修正前）— hyperscaler-capex 的 3017 條目 affects 生效值為 ['月營收 YoY', '2026E EPS 市場預估']，而 2026-09-10 寫入的 ['毛利率', '水冷板月產能', '資本支出強度'] 未生效"
  - "state/3017.yaml 的 key_variables 名稱（2026-09-13）— Q2 2026 毛利率（對 FY2025 全年 25.79% 的基期）／2026 年 8 月營收／ASIC 營收佔比（管理層前瞻）／年度資本支出／水冷板月產能目標／2026 年法人共識稅後純益。⚠ 與 driver 的 affects 名稱不完全對應，驗證腳本目前不檢查此對應"
  - "scripts/validate_state.py（2026-09-13 改動）— check_dup_keys 自 warns.append 改為 errors.append"
  - "scripts/build_index.py（2026-09-13 改動）— front-matter 解析失敗改為收集進 broken 並 return 1；新增 --check（只驗證不寫檔）"
  - ".githooks/pre-commit（2026-09-13 改動）— 新增 python scripts/build_index.py --check"
  - "反向測試（2026-09-13）— TSM 塞入兩個同名 note：觸發兩條重複鍵 error；某報告 trigger 塞入壞的反斜線轉義：build_index exit=1 並印出「front-matter 解析失敗 — while scanning a double-quoted scalar」，還原後 exit=0"
  - "scripts/validate_state.py（2026-09-13 改動後執行）— 0 error, 1 warn（僅 hyperscaler-capex → AMZN 缺 state 檔）, 11 note, 82 個未填欄位"
---

# coverage —— S7：讓兩種「靜默丟棄」停止靜默

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L2**｜觸發：結構調整 S7
**本報告不動任何標的的情境、倍數、機率或目標價。**

---

## 1. 這一步處理的是同一個形狀的兩個實例

| | 丟掉什麼 | 誰看得到 |
|---|---|---|
| **YAML 重複鍵** | 較早的那個鍵的值 | 沒有人 —— PyYAML 不發警告 |
| **report front-matter 解析失敗** | 整份報告的 metadata | 沒有人 —— `build_index` 只 `return None` |

**兩者的共同點是：檔案看起來完全正常。**

---

## 2. ⚠⚠⚠ 2308：現價是 09-11 的，描述它的依據卻是 09-09 的

`state/2308.yaml` 的 `cta.price_basis` 有兩段：

| | 內容 | |
|---|---|---|
| 第一段 | **2026-09-11 的重錨**：自 1,795.00 改為 **1,620.00**，偏差 −9.75% | 與 `cta.price` 的 1620.0 一致 |
| 第二段 | 2026-09-09／09-10 的舊討論（不採 09-10 盤中價） | **PyYAML 保留最後一個 → 生效的是這段** |

**所以 `cta.price` 是 1,620（09-11），而描述它的 `price_basis` 講的是 09-09 的收盤。**

⚠ **這不是排版問題，是「程式讀到的內容」與「檔案看起來的內容」不一致。**
任何讀這個欄位的人（包括公開站台）拿到的都是舊的那一段。

`signal.changes_if` 也有兩段，但那一組是新版在後 —— 生效的是對的那一段，
**行為無誤純屬運氣**，同樣不該重複。

被丟棄的兩段已逐字搬進
`reports/2026/09/2026-09-13-2308-duplicate-key-archive.md`（沿革檔，`level: L0`）。

---

## 3. ⚠⚠ driver 層：一次「充實」完全沒有生效

`drivers/hyperscaler-capex.yaml` 的 3017 條目：

```yaml
    sensitivity: 高
    affects: [毛利率, 水冷板月產能, 資本支出強度]      # 2026-09-10 充實時寫的
    sensitivity: 高
    affects: [月營收 YoY, 2026E EPS 市場預估]          # 舊值 —— 排在後面，勝出
    note: ⚠ 尚無 state/3017.yaml。本條目為刻意保留 …
```

**2026-09-10 那次充實對扇出行為毫無作用，而沒有任何東西會說。**

`affects` 的用途是「扇出時要更新哪些變數」——
**用錯的清單扇出，會去更新一組不存在的變數名稱，而扇出腳本不會抱怨。**

### 同一條目還帶著一句已經是假的話

`note` 寫著「**尚無 `state/3017.yaml`**。本條目為刻意保留」，
而**同一條目的 `path` 欄位自己就記著**：

> ⚠⚠ **2026-09-10 充實：本條目此前只有一行 path，且該檔沒有 state 檔 ……
> **本日建檔後該警告只剩 AMZN。**

**那句 `note` 在被讀到的時候已經是假的**，而它旁邊三行就寫著它是假的。
已一併更正。

### ⚠ 順帶記一個尚未處理的缺口

現行 `affects` 的名稱（`毛利率`／`水冷板月產能`／`資本支出強度`）
與 `state/3017.yaml` 的 `key_variables` 名稱（`Q2 2026 毛利率…`／`水冷板月產能目標`／`年度資本支出`）
**不完全對應，而驗證腳本目前不檢查這個對應。**
扇出時要自己對上。**這是下一個候選檢查。**

---

## 4. 8299：一個已關閉的缺口，`how_to_close` 顯示的卻是還沒做的事

```yaml
- question: ✓ **已關閉 2026-09-12** —— **價格通道。** …
  how_to_close: ✓ 見 …forward-estimates.md §2 ⑥ 與 reports/…-coverage-exchange-openapi.md
  how_to_close: 測試 wantgoo／財報狗／富果 Fugle／公開資訊觀測站的可抓取性   # ← 生效
```

已合併為一行，**關閉證據在前**，原取得途徑以括號保留。

---

## 5. 兩道閘門

### 5.1 重複鍵：WARN → **ERROR**

```
[ERROR] state\TSM.yaml: 第 150 行的鍵「note」與第 149 行重複 —
        PyYAML 只保留最後一個，前者被靜默丟棄（程式讀到的與檔案看起來的不一樣）
```

**升級的理由就是第 2 節**：一個會讓檔案內容與程式讀到的內容不一致的缺陷，不該只是提示。

`validate_state.py` 的 WARN 因此自 **6 降為 1**（僅剩 `hyperscaler-capex` → AMZN 缺 state 檔）。

### 5.2 front-matter 解析失敗：只提示 → **exit 1**

```
[ERROR] reports\…\2026-09-13-coverage-s3c-period-field.md:
        front-matter 解析失敗 — while scanning a double-quoted scalar

有 1 份報告的 front-matter 壞了。它們不會進索引、不會被 cross_check 的 E4 對照、
也不會進衍生索引 —— 三處都只是安靜地少一筆，所以這裡擋下。
```

⚠⚠ **這是 CLAUDE.md 的硬性提醒裡已經記過的坑**
（「整條驗證鏈 0 block / 0 error 通過，那份報告卻沒進索引」），
**而在 S4（E4 跨層對照）與 S6（衍生索引）之後，它的後果自一處變成三處。**

**加了兩個消費者，就讓同一個舊缺口的代價變成三倍 —— 這件事本身值得記：
每多一個依賴某個資料的東西，那個資料的沉默失敗就多一份代價。**

新增 `--check`（只驗證不寫檔）並接進 pre-commit hook ——
直接在 hook 裡跑完整的 `build_index` 會改動未 staged 的 `INDEX.md`。

---

## 6. 本輪十步全部完成

| 步 | 產出 | 閘門 |
|---|---|---|
| S0 | 修正「`--stale` 無陳舊變數」的覆蓋率宣稱 | — |
| S1 | as-of 涵蓋率 189/232 → **232/232**，11 筆逾期現形 | 2 error ＋ 涵蓋率必印 |
| S2 | `__` → `__` ＋ `none_qualifies`，未填欄位 89 → 81 | 無依據的 `none_qualifies` → error |
| S4 | **E4** 跨層對帳，39/39 相符 | 併入 hook，孤立反向測試證明獨立價值 |
| S3a | `kind` 型別契約（量化 210／質性 22） | 4 error，4 項反向測試 |
| S5 | `event_log[].delta` 40 萬字元 → 39 份沿革檔，state **−25.3%** | 帶 `delta` → error |
| S6 | 衍生索引 `build_db.py`（9 表，不進版控） | 不進鏈（輸出不提交） |
| S3b | `series`／`components`，未型別化 7 → **0** | 3 error，3 項反向測試 |
| S3c | `period` 欄位，拆出 14 筆，餘 81 筆可數 | `[UNIT]` 統計行 |
| **S7** | **5 處重複鍵清除，WARN 6 → 1** | **重複鍵 → error；front-matter 壞 → exit 1** |

⚠ **十步裡有三步是在修我自己這一輪引入或算錯的東西**
（S2 修 S0/S1 的「19 檔 vs 8 檔」、S2 修 S1 的 COARSE 洗版、S3c 修規劃時的「78 vs 81」）。
**那不是額外的工作，那就是工作** —— 而三次都是靠「用第二個口徑複核總數」抓到的。

### 仍未處理、且已知

| 項目 | 量 |
|---|---:|
| `unit` 仍夾帶期間或口徑 | 81 筆 |
| `signal.basis` 平均字數（混著當下判斷與歷史，**不能機械搬移**） | 2,763 |
| driver 的 `affects` 名稱與 `key_variables` 名稱未對齊（**新發現**） | 至少 1 處 |
| 逾 90 天的陳舊變數（**研究工作，不是結構工作**） | 11 筆（最舊 986 天） |
| `hyperscaler-capex` → AMZN 缺 state 檔 | 1 |
