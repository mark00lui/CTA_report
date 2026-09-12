---
date: 2026-09-12
ticker: coverage
level: L2
trigger: "審核一個美股財經 MCP（AI-Hub-Admin/finance-agent-mcp-server）的安全性。結論是不安裝，而替代路徑與台股那一輪同一個原則：去源頭"
summary: "**審核結論：不安裝 —— 但不是因為有惡意程式碼。逐行讀過 `server.py`（4.9KB）與 PyPI `financeagent` 0.0.6 的整個 31KB wheel，沒有。** 無 `eval`／`exec`／`pickle`／`subprocess`，無 proxy 設定，無讀環境變數或 `.env`，無憑證存取；10 個外連主機全是它宣告的資料源，**無遙測、無作者自有端點**。 ｜**不採用的四個理由全部與「它現在做什麼」無關**：(1) ⚠⚠⚠ 依賴未鎖版本（`financeagent>=0.0.1`）而 PyPI 後設資料完全匿名（無作者、無 email、**無授權**）—— **今天的 0.0.6 乾淨，明天的 0.0.7 以我的權限執行而我不會看到**；(2) MCP 倉庫與 PyPI 套件的 license 皆為 `None`，沒有授權就沒有使用許可，而這是公開倉庫；(3) 包裝最後推送 2025-10-23 而它會裝到 2026-03-30 的版本，作者沒測過的組合；(4) **它只有一個工具**，而那個能力我用 WebFetch 打 stockanalysis 就有 —— **零新增能力對上一條看不見的供應鏈。** ｜⚠ 並記一個宣稱與實作不符：README 說「fetched with proxy settings」而程式碼裡沒有任何 proxy，`load_dotenv` 是死碼。 ｜**✓ 替代路徑已實測並寫進 references**：SEC EDGAR XBRL（`data.sec.gov`，結構化財報逐期序列）、SEC submissions（回 **fiscalYearEnd**，直接解掉「曆年 vs 財年」陷阱）、美國財政部每日殖利率曲線。 ｜⚠⚠⚠ **而財政部那條修正了一個比算錯更難發現的錯**：§2 ② 原用「4.97% 無風險利率」錨定台股 2308 的折現率 —— 美國 10Y 當日是 **4.96%**，**所以那個數字是個正當的美國利率，錯的只有國別**（台幣 10Y 1.94%，差 3.02pp）。**「數字是對的、用錯了地方」經得起一次數值核對，所以它比錯的數字更難發現。**"
signal: n/a
conviction: n/a
tp_before: n/a
tp_after: n/a
tp_delta: "n/a —— 本報告審核一個外部套件並建立三條官方美股通道，不動任何標的的數字"
sources:
  - "github.com/AI-Hub-Admin/finance-agent-mcp-server — 2026-09-12 審核。GitHub API：created_at 2025-06-18、pushed_at 2025-10-23、9 stars／2 forks／0 watchers、license None、全倉 3 個檔案（README 3,045B／pyproject.toml 241B／server.py 4,868B）"
  - "pypi.org/pypi/financeagent/json — 2026-09-12 查詢。version 0.0.6、上傳 2026-03-30、wheel 31,259B、author/author_email/home_page/license/summary 皆為 None、依賴 requests／beautifulsoup4／cachetools／func_timeout"
  - "financeagent-0.0.6-py3-none-any.whl — 2026-09-12 下載並解壓，10 個 .py 全部讀過（最大 request_us_stock_price_py3.py 30,298B）"
  - "data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/Revenues.json — 2026-09-12 實測，需帶 User-Agent"
  - "data.sec.gov/submissions/CIK0000789019.json — 2026-09-12 實測，回 name MICROSOFT CORP／tickers ['MSFT']／exchanges ['Nasdaq']／fiscalYearEnd 0630，最新申報 2026-09-11"
  - "home.treasury.gov/.../daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&_format=csv — 2026-09-12 實測，175 列。2026-09-11：2Y 4.63／10Y 4.96／30Y 5.35"
---

# 審核一個美股 MCP —— 沒有惡意程式碼，但還是不裝

## 1. 先說結論

**不安裝 `AI-Hub-Admin/finance-agent-mcp-server`。**

⚠ **而理由不是「它有惡意程式碼」。我逐行讀過，沒有。** 這一點要先說清楚，
因為把「不採用」說成「不安全」會讓下一次的審核失去標準 ——
**幾乎所有小型開源套件都沒有惡意程式碼，所以那個問題的答案幾乎總是「沒有」，
它不能當成決策依據。**

---

## 2. 實際讀了什麼

整個攻擊面只有兩塊，兩塊都小到可以全讀：

| 檔案 | 大小 | 結果 |
|---|---|---|
| `src/finance-agent-mcp-server/server.py` | 4,868 B | 薄包裝，真正邏輯只有一行 `fa.api(...)` |
| PyPI `financeagent` 0.0.6 wheel（10 個 `.py`）| 31,259 B | 爬蟲，最大 `request_us_stock_price_py3.py` 30,298 B |

**整個 GitHub 倉庫只有 3 個檔案**（README、`pyproject.toml`、`server.py`）——
亦即 MCP 本身幾乎什麼都沒做，**所有行為都在一個不在該倉庫裡的 PyPI 套件中。**

### 檢查項與結果

| 檢查 | 結果 |
|---|---|
| `eval`／`exec`／`compile`／`pickle`／`marshal` | ✓ **無** |
| `subprocess`／`os.system`／`os.popen`／`__import__` | ✓ **無** |
| proxy 設定 | ✓ **無** |
| 讀取環境變數／`.env`／憑證 | ✓ **無** |
| 外連主機 | ✓ **10 個全是宣告的資料源**，無遙測、無作者自有端點 |

外連主機完整清單（次數）：`hkex.com.hk`(12)、`zacks.com`(5)、`marketbeat.com`(4)、
`stockanalysis.com`(4)、`xueqiu.com`(2)、`www1.hkex.com.hk`(2)、`morningstar.com`(2)、
`moneycontrol.com`(2)、`stock.xueqiu.com`(2)、`nasdaq.com`(1)。
唯一的 `token` 是 HKEX 自己的 widget token，從 HKEX 本身取得 —— 該站的正常機制。

### ⚠ 但發現兩處宣稱與實作不符（兩個方向都要記）

1. README 與 system prompt 都寫 **「data from realtime fetched from website with proxy settings」**
   —— **程式碼裡沒有任何 proxy。** 宣稱了一個不存在的機制。
2. `server.py` 匯入 `from dotenv import load_dotenv`，**但從未呼叫**，
   而且 `dotenv` **不在 `pyproject.toml` 的依賴裡** —— 亦即這個 import 會讓安裝後直接 ImportError。
   **一個跑不起來的 import 留在主檔案裡，說明它沒有被端到端測過。**

---

## 3. 不採用的四個理由，全部與「它現在做什麼」無關

### (1) ⚠⚠⚠ 依賴未鎖版本，而維護者完全匿名

`pyproject.toml` 寫 **`financeagent>=0.0.1`** —— 下界，沒有上界、沒有 hash。

PyPI 後設資料：

| 欄位 | 值 |
|---|---|
| author | **None** |
| author_email | **None** |
| home_page | **None** |
| summary | **None** |
| license | **None** |

**今天的 0.0.6 是乾淨的。明天的 0.0.7 會以我的權限執行，而我不會看到它改了什麼。**

⚠⚠ **這才是決定性的那一條：風險不在程式碼是什麼，在於沒有任何東西約束它會變成什麼。**
一個匿名維護者、未鎖版本、無 hash 驗證的依賴，其未來狀態不在任何人的監督之下。

### (2) ⚠⚠ 兩邊都沒有授權條款

GitHub 倉庫的 `license` 是 `None`，PyPI 套件的 `license` 也是 `None`。
**沒有授權就沒有使用、修改或再散布的許可** —— 而這是一個完全公開的倉庫。

### (3) ⚠ 時序不對

| | 日期 |
|---|---|
| MCP 包裝最後推送 | **2025-10-23** |
| 它會裝到的套件版本發布於 | **2026-03-30** |

**包裝比它的依賴舊了 5 個月，而因為沒鎖版本，`uv sync` 今天會裝出一個作者自己沒測過的組合。**

### (4) ⚠⚠ 它只有一個工具，而那個能力我已經有了

`get_stock_price_global_market(symbol_list, market)` —— 回即時價、PE、市值。**就這一個。**

而這些我用 WebFetch 打 `stockanalysis.com` 就有
（**上櫃 404 的問題只存在於台股，美股完全正常**）。
諷刺的是這個套件的 LSE 資料源**也是** `stockanalysis.com`。

**→ 零新增能力，對上一條看不見的供應鏈。任何非零風險都不值得。**

⚠ 而它的美股資料源（`morningstar.com`／`zacks.com`／`marketbeat.com`）
**正是本週所有資料錯誤的來源那一類：中間層。**
作者自己在 system prompt 裡寫：
**「this repo is not responsible for proxy or any data correctness related issues」。**

---

## 4. ⚠ 審核第三方資料套件的規則（本次的方法層產出）

> **「有沒有惡意程式碼」只是第一題，而且通常答案是沒有 —— 所以它不能當決策依據。**
> **第二題才是決定性的：依賴鎖不鎖、維護者具不具名、授權在不在、以及它換來什麼。**
> **一個零新增能力的套件，任何非零風險都不值得。**

---

## 5. ✓ 替代路徑：美股也去源頭

台股那一輪的結論是「交易所自己有公開 API」。**美股的對應物不是交易所，是 SEC 與財政部。**
三條全部 2026-09-12 實測通過，免帳號、免 key：

| 用途 | 端點 | 實測結果 |
|---|---|---|
| **結構化財報**（XBRL 單一科目逐期序列）| `data.sec.gov/api/xbrl/companyconcept/CIK<10碼>/us-gaap/<tag>.json` | ✓ MSFT `Revenues` 回完整序列含定義 |
| 全部科目一次取 | `data.sec.gov/api/xbrl/companyfacts/CIK<10碼>.json` | — |
| **申報索引與基本資料** | `data.sec.gov/submissions/CIK<10碼>.json` | ✓ MICROSOFT CORP／`['MSFT']`／`['Nasdaq']`／**`fiscalYearEnd: 0630`**，最新申報 2026-09-11 |
| **公債殖利率曲線**（每日、全年期）| `home.treasury.gov/.../daily-treasury-rates.csv/<年>/all?type=daily_treasury_yield_curve&_format=csv` | ✓ 175 列。**2026-09-11：2Y 4.63／10Y 4.96／30Y 5.35** |

⚠ **`data.sec.gov` 要求帶 `User-Agent`（含聯絡方式），否則拒絕。**

⚠⚠ **`submissions` 的 `fiscalYearEnd` 直接解掉 `source-verifier` 檢查清單上的「曆年 vs 財年」陷阱。**
MSFT 回 `0630` —— 它的「FY2026」結束於 2026 年 6 月。
**那個口徑分岔此前只能靠記憶，現在有一手欄位可查。**

---

## 6. ⚠⚠⚠ 而財政部那條修正了一個比算錯更難發現的錯

`forward-estimates.md` §2 ② 原寫：2308（**台股**）的折現率可用
**「4.97% 無風險利率 ＋ 1.50 × ERP 網格」**錨定。

我上一輪（`0d3e934`）把它記成「那是美國的利率，用在台股上差 3.03pp」。**本次查證讓它更精確：**

| | 值 | 日期 |
|---|---|---|
| 美國 10Y（財政部） | **4.96%** | 2026-09-11 |
| 原文寫的 | 4.97% | 無出處 |
| 台幣 10Y | **1.94%** | 2026-09-11 |

**所以那個 4.97% 是一個正當的美國利率（與官方 4.96% 相差 0.01pp），錯的只有國別。**

⚠⚠⚠ **「數字是對的、用錯了地方」比「數字是錯的」更難發現，因為它經得起一次數值核對**
—— 去查 4.97% 會查到它確實存在、確實是 10 年期公債殖利率。
**唯一能抓到它的檢查是問「這個率是哪一國的，標的是哪一國的」。**

**→ 規則：核對一個率時，先核對它的國別，再核對它的數值。**
無風險利率必須與標的的計價幣別同國。

⚠ **而兩國的折現率都仍算不出來** —— 缺的是 beta，不是無風險利率
（beta 在這份清單上不可用：幾檔只有 0.24–0.62 而年振幅與其他檔同樣落在 2.3–3.8 倍）。
**兩個缺的輸入變成一個，美股台股都一樣。**

---

## 7. 本報告不做什麼

- **不安裝被審核的那個 MCP**，也不寫進 `.mcp.json`。
- **不改任何標的的數字。** US 10Y 記在 `coverage.yaml` 的 `shared_macro_inputs`（共用事實的唯一的家），
  不複製進 15 份美股 state。
- **不開始算任何標的的錨 C** —— beta 的問題未解，見 §6 末。
