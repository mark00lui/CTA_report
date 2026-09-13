---
date: 2026-09-13
ticker: coverage
level: L2
supersedes: reports/2026/09/2026-09-13-coverage-s5-eventlog-archive.md
trigger: "結構調整 S6：新增 scripts/build_db.py，把 state/、drivers/、reports/ 攤平成一個可查詢的衍生索引（.cache/research.sqlite，不進版控）。它同時是「要不要改用 markdown database」這個問題的答案 —— 不要，因為那會拿掉 append-only 的機械強制去換一個查詢語法"
summary: "✓✓✓ **S6 完成：`scripts/build_db.py` 把 39 檔 state、3 個 driver、200 份報告攤平成 7 個資料表（標的 39／三情境 117／key_variables 232／事件 250／缺口 625／driver 引用 88／報告 200），輸出 `.cache/research.sqlite` 不進版控、每次執行整個砍掉重建。** ⚠⚠ **它是衍生層不是真相，而那個分界是整件事的重點**：來源真相仍是 `state/*.yaml`（可變、當下最佳判斷）與 `reports/**/*.md`（不可改、append-only），**資料庫裡做的任何修改都會在下次執行時消失** —— 與 `build_index.py`／`build_site.py` 同規格，但**不在 commit 前的驗證鏈上**，因為它的輸出不被提交。 ｜**它解決的是來源層答不出來的那一類問題**：跨標的比較、依日期排序、**把散文條件與數值條件做交集**。三個實測例子：**(a) base 的 `multiple_basis` 提到「同業」的有 22/39 檔** —— 這是「錨 B 到底有沒有真的用過」第一次被機械數出來；**(b) 訊號為偏多、但 `invalidation` 是 `none_qualifies` 的有 0 檔** —— 與「升級為偏多需右側技術確認」的紀律一致，而在此之前這件事只能逐檔看；**(c) 目標價相異值最多的是 COHR 6 個、6239 5 個、3008 與 6442 各 4 個** —— 由報告的 `tp_after` 序列得出，那是一條只存在於 report 層的時間序列。 ｜⚠⚠⚠ **而這一步同時回答了「推理字句有沒有更適合的儲存方式，例如 MD 的 database」**：**不要換。** 那種做法要把來源真相換成 front-matter ＋ 查詢語法，**會失去 `check_append_only.py` 的機械不可變性與 `git blame` 的逐行可追溯性，換來的只是一個查詢語法 —— 淨損。** **正確的做法是來源真相一個字不動，在旁邊長一層可以隨時砍掉重建的索引。** 本倉庫既有的 155/155 份報告 front-matter 齊備度，正是這個做法可行的前提。 ｜✓ 可再生性已驗證（連跑兩次計數相同）、`.gitignore` 已加 `.cache/`、`git check-ignore` 確認不會誤入版控。 ｜✓ 六支驗證鏈 0 block／0 error。"
signal: n/a
conviction: n/a
tp_before: n/a
tp_after: n/a
tp_delta: "n/a —— 本報告不動任何標的的情境、倍數、機率或目標價。它新增一層可再生的衍生索引"
sources:
  - "scripts/build_db.py（2026-09-13 新增）— 7 個資料表；輸出 .cache/research.sqlite；每次執行先 os.remove 再重建"
  - "python scripts/build_db.py --stats（2026-09-13 執行）— 標的 39／三情境 117／key_variables 232（量化 210、質性 22）／事件 250／缺口 625／driver 引用 88／報告 200"
  - "示範查詢（2026-09-13）— base 的 multiple_basis 含「同業」者 22 檔：2317／2337／2345／3017／3030／3037／3131／3363／3533／3583／3665／6187／6239／6531／6805／CEG／COHR／GOOG／INTU／META／MSFT／SNDK"
  - "示範查詢（2026-09-13）— signal_rating='偏多' 且 invalidation='none_qualifies' 者：0 檔"
  - "示範查詢（2026-09-13）— 報告 tp_after 相異值最多者：COHR 6／6239 5／3008 4／6442 4／3324 3"
  - "示範查詢（2026-09-13）— 缺口數最多者：3324 25／6239 25／3363 24／CEG 22／2308 21"
  - "可再生性驗證（2026-09-13）— 連續執行兩次，key_variables 計數皆為 232；git check-ignore -v .cache/research.sqlite 回 .gitignore:13:.cache/"
  - "CLAUDE.md（2026-09-13 改動）— 新增 build_db.py 的說明與「不要改用 markdown database」的理由"
---

# coverage —— S6：衍生索引，以及「要不要改用 markdown database」的答案

> 本文為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
> 讀者不應假設作者持有或不持有本標的。詳見 [DISCLAIMER.md](../../../DISCLAIMER.md)。

**等級 L2**｜觸發：結構調整 S6
**本報告不動任何標的的情境、倍數、機率或目標價。**

---

## 1. ⚠⚠⚠ 先回答那個問題：不要改用 markdown database

**理由不是品味，是會失去什麼。**

| | 現況 | 換成 markdown database 之後 |
|---|---|---|
| 報告不可改 | `check_append_only.py` **機械強制** | 只剩慣例 |
| 「這個 55% 是哪天因為哪則消息變成這樣的」 | `git blame state/3324.yaml` **逐行可答** | 同左（若仍用 git） |
| 查詢 | 只能 grep | front-matter 查詢語法 |

**換過去拿掉的是第一項，換來的是第三項 —— 淨損。**

而第三項**不需要靠換掉來源真相來取得**：
本倉庫的 155/155 份報告 front-matter 欄位齊備，
**已經足以在旁邊長出一層索引，而來源真相一個字都不用動。**

**正確的形狀：**

```
來源真相（可手寫、進 git、hook 把關）
  state/*.yaml      ← 當下最佳判斷，可變
  reports/**/*.md   ← 推論與歷史，append-only、機械強制不可改
        │
        ▼  scripts/build_db.py（單向產生）
  .cache/research.sqlite   ← 唯讀、每次砍掉重建、不進版控
```

---

## 2. 它裝了什麼

| 表 | 列數 | 內容 |
|---|---:|---|
| `tickers` | 39 | 論點、訊號、象限、加權目標價、現價、ATR、失效價位 |
| `scenarios` | 117 | 三情境的機率、EPS、倍數、目標價、**倍數的錨** |
| `key_variables` | 232 | 型別化後的變數（量化 210／質性 22） |
| `events` | 250 | `event_log` 的 date／level／summary |
| `gaps` | 625 | 已知的未知 |
| `driver_refs` | 88 | 個股 → driver 的引用與方向 |
| `reports` | 200 | 每份報告的 front-matter（含 `tp_before`／`tp_after`） |

---

## 3. 只有衍生層才問得出來的三個例子

### 3.1 「錨 B 到底有沒有真的用過」——第一次被機械數出來

```sql
SELECT ticker FROM scenarios WHERE cell='base' AND multiple_basis LIKE '%同業%'
```

**22/39 檔。**

`/revalue` 的規則寫著「只宣告錨 A 時，`multiple_basis` 必須同時寫出**為什麼不需要錨 B**」。
**這個查詢讓「有幾檔真的談過同業」變成一個數字，而不是一個印象。**
（⚠ 它只證明字面提到，不證明談得好 —— 但那是下一層的問題，而在此之前連第一層都沒有。）

### 3.2 訊號偏多但沒有合格失效價位的標的：**0 檔**

```sql
SELECT ticker FROM tickers WHERE signal_rating='偏多' AND invalidation='none_qualifies'
```

與 CLAUDE.md 的「**訊號升級為偏多需右側技術確認**」一致 ——
**而這個一致性在此之前只能逐檔看，現在是一句 SQL。**

⚠ 這個查詢之所以寫得出來，**完全是因為 S2 把 `none_qualifies` 從 `__` 裡拆了出來**。
在拆開之前，這一條的 WHERE 子句無法區分「量過了、沒有合格位階」與「還沒量」。
**前面幾步不是為了整齊，是為了讓這種問題可以被問。**

### 3.3 目標價被改過最多次的標的

| ticker | 相異 `tp_after` |
|---|---:|
| COHR | 6 |
| 6239 | 5 |
| 3008 | 4 |
| 6442 | 4 |
| 3324 | 3 |

**這是一條只存在於 report 層的時間序列** —— state 只有當下的 `weighted_tp`，
而每一次改動都留在一份不可改的報告裡。**校準價值就在這條序列上。**

---

## 4. 分界要守住

⚠⚠ **資料庫不是真相。**

- 每次執行先 `os.remove(OUT_DB)` 再重建 —— **裡面做的任何修改都會消失**。
- `.gitignore` 已加 `.cache/`（`git check-ignore` 驗證通過）。
- **不放進 commit 前的六支驗證鏈** —— 因為它的輸出不被提交，
  沒有「產生器輸出與提交內容不一致」這個失效模式要防。

---

## 5. 本輪結構調整總結

| 步 | 產出 | 閘門 |
|---|---|---|
| S0 | 修正「`--stale` 無陳舊變數」的覆蓋率宣稱 | — |
| S1 | as-of 型別嚴格化，涵蓋率 189/232 → **232/232**，11 筆逾期現形 | 兩條 error ＋ 涵蓋率必印 |
| S2 | `__` 拆成 `__` 與 `none_qualifies`，未填欄位 89 → **81** | `none_qualifies` 無依據 → error |
| S4 | **E4** 跨層對帳（state ↔ 不可改的報告），39/39 相符 | 併入 pre-commit，孤立反向測試已證獨立價值 |
| S3a | `key_variables` 型別契約，`kind` 量化 210／質性 22 | 四條 error，四項反向測試 |
| S5 | `event_log[].delta` 40 萬字元搬進 39 份沿革檔，state **−25.3%** | 帶 `delta` → error |
| **S6** | **衍生索引 `build_db.py`** | 不進鏈（輸出不提交） |

⚠ **每一步都是成對的：搬移／修正處理已經發生的，閘門處理「它會不會再發生」。**
只做前者，同樣的形狀會在幾個月後長回來 —— **`delta` 在 39 檔裡各長了一份，
正是因為當初只寫了規定（「一行」）而沒有寫檢查。**

### 未做，且已知

- **S3b**：7 筆 `未型別化`（需 `series`／`components` 欄位）、
  `unit` 108 種相異值、期間仍夾帶在單位字串裡（`%（2026 Q2）`）。
- **`signal.basis` 平均 2,763 字元**（合計 107,775）—— 與 `delta` 同形狀，
  **但它混著當下判斷與歷史，不能機械搬移，要逐檔判讀。**
- **`build_index.py` 對 front-matter 解析失敗只 warn 不 error** ——
  一份壞掉的報告既不進索引、也不被 E4 對照、也不進衍生索引，**三處都只是安靜地少一筆。**
- **11 筆逾 90 天的陳舊變數**（最舊 986 天）—— 研究工作，不是結構工作。
- **5 處 YAML 重複鍵**與 **hyperscaler-capex → AMZN 缺 state 檔**。
