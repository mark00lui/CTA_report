# state 檔欄位定義

每支個股一檔：`state/<ticker>.yaml`。台股用數字代號（`3324.yaml`），美股用 ticker（`MSFT.yaml`）。

## 欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `ticker` | str | 代號 |
| `name` | str | 中文／英文名 |
| `market` | str | `TW` / `US` |
| `factor_tags` | list | 因子標籤，供 portfolio 層彙總。例：`[ai_capex_hw, optical, cpo]` |
| `thesis` | str | **一句話**論點。寫不成一句話代表論點還沒想清楚。 |
| `thesis_since` | date | 論點成立日，用來看論點壽命 |
| `scenarios` | map | `bear` / `base` / `bull`，各含 `p`、`p_basis`、關鍵財務假設、`eps`、`exit_multiple`、**`multiple_basis`**、`tp`（目標價）、`narrative`（一句話） |
| `key_variables` | list | 決定論點成立與否的變數，**上限 6 個**。每個含 `name` / `value` / `unit` / `tier` / `source` / `updated` |
| `cta` | map | `位階`（右側確認／整理／破線）、`key_ma`、`support`、`resistance`、`invalidation`（技術面失效價位）、`confirm_trigger`、`updated` |
| `signal` | map | `rating`（偏多/中性/偏空）、`conviction`（高/中/低）、`basis`、`changes_if` |
| `falsifiers` | list | 否證點。**可驗證、有日期、有數字門檻**。觸發即強制 L3。 |
| `checkpoints` | list | 未來已知的資訊節點（法說、財報、月營收、產業展會、政策日期），含 `date` / `event` / `what_to_watch` |
| `gaps` | list | 已知的未知。含 `question` / `how_to_close`（取得途徑） |
| `event_log` | list | 事件流水。含 `date` / `level` / `summary` / `delta`（一行）。只留最近 20 筆，更早的壓成月摘要。 |
| `last_updated` | date | |

## 填寫規則

**thesis 要可否證。** 「AI 需求強勁受惠」不是論點，是感想。「液冷從選配轉標配，2026 滲透率決定重評價幅度」是論點 — 因為滲透率可以量測，可以證偽。

**key_variables 上限 6 個。** 超過就代表沒有分清主次。分辨標準：這個變數變動 20%，目標價會不會動 10% 以上？不會的話它不是 key variable。

**scenarios 的機率要有依據。** 不是 25/50/25 的預設值。寫 `p_basis` 說明為何是這個機率（歷史頻率？供應鏈訊號？管理層 guidance 的保守程度？）。

**`multiple_basis` 是必填，且 base 的錨不得是現價。** 每個情境都要寫出 exit multiple 錨在哪：自身歷史區間分位、同業／中週期、reverse-DCF 反推的隱含成長、或成長持續期。

bear 與 bull 錨在「市場實際付過的價」是好做法（52 週低點當時的倍數、題材發酵前的倍數、賣方目標價隱含值），但 **base 用現價隱含倍數等於沒有估值** —— 它會讓加權目標價機械性地貼著現價。

四種錨都拿不到時，`multiple_basis` 寫「採用市場定價，非獨立判斷」，並把 `signal.conviction` 上限壓到「低」。這不是懲罰，是讓「沒有意見」在檔案裡看得見 —— 看不見的無知會被當成判斷使用。

完整規則、循環股框架與常見自欺模式見 `references/valuation.md`。

**falsifiers 要有數字與日期。** 「需求轉弱」不可驗證；「Q3 液冷營收占比未達 35%」可驗證。每支個股至少 2 個否證點，其中至少 1 個在未來 6 個月內可驗證。

**tier 標記不可省略。** 事實／推論／假設／缺口。假設值不得單獨支撐 L2 以上的模型變動。

**本 schema 刻意不含倉位欄位。** 沒有成本、張數、權重、Kelly。若你發現需要記錄尺寸，那屬於這個倉庫之外的事。

**signal 是研究結論，不是交易指示。** `rating` 只有偏多／中性／偏空；`changes_if` 必須是具體價格或事件，不是「持續觀察」。

## 台股專用欄位

`monthly_revenue`：最近 3 個月營收與 YoY，每月 10 日前更新。這是台股最高頻的一手數據，優先度高於任何新聞。
`chips`：三大法人買賣超趨勢、融資餘額變化。可選。

## 因子標籤（供 portfolio 層彙總）

- `ai_capex_hw` — 直接受益於資料中心資本支出的硬體（TSM、3324、6442）
- `ai_platform` — 支出方 / 平台（MSFT、GOOG、META）
- `ai_application` — 應用端貨幣化（INTU）
- `thermal` / `optical` / `cpo` / `foundry` / `advertising` / `saas` — 次產業
- `tw_fx` — 獲利對新台幣匯率敏感
- `single_customer` — 單一客戶占比 > 30%

平台端與硬體端不是分散，是**同一條產業鏈的兩端**：capex 縮手時兩邊一起受傷，只是時序不同。

`state/coverage.yaml` 的因子分析以**等權覆蓋**為基準（每檔 1/n）。那是覆蓋清單的結構描述，與任何實際配置無關 — 本倉庫不記錄配置。

## `valuation_frame` — 估值方法組合

**建檔時決定，每次 `/revalue` 複核。** 判準與處方見 `references/valuation-map.md`。

```yaml
valuation_frame:
  quadrant: Q3
  quadrant_basis: "capex／營收 50%（2026 計畫 500 億元 ÷ 營收預估 998 億元）；每股自由現金流 -14.78 元；cyclical"
  quadrant_since: 2026-09-01
  peer_group: 封測 OSAT
  peers: ["日月光 3711", "京元電 2449", "超豐 2441（⚠ 本檔子公司）"]
  rank_metrics: [先進封裝營收占比, 客戶層級, 資本支出強度與 FCF]
  methods:
    primary: 同業中位數 forward PE（官股投顧同一份報告 23.8／28／42x）
    secondary: 自身歷史 trailing PE（3 年平均 16.5x，現況 28.11x）
    check: Gordon 合理 PB（(ROE-g)/(r-g)）
  axes_crossed: [參照]
  excluded: "⚠ 不做 DCF（Q3 循環股，中週期 FCF 拿不到）；不算 PEG（g 在循環兩端趨近 ±∞）"
  reviewed: 2026-09-01
```

**欄位語意**

| 欄位 | 意義 | ⚠ 常見錯誤 |
|---|---|---|
| `quadrant` | Q1–Q4，決定用哪一類方法 | 建檔後就沒再看過。**象限會漂移** |
| `quadrant_basis` | 判準**要指名數值** | 寫「資本密集」而不寫 capex／營收是多少 |
| `quadrant_since` | 進入該象限的日期 | 漂移時忘了改，於是漂移這件事沒有留下痕跡 |
| `peers` | 可比同業 | **多數族群在覆蓋清單內只有 1–2 檔，必須從清單外取** |
| `rank_metrics` | 2–3 個排序指標 | **事後**挑指標來支持已想好的答案 |
| `methods.secondary` | 副錨 | 留 `__` —— 單一方法無法交錯驗證 |
| `axes_crossed` | 主副錨跨了哪些軸 | 兩個方法都只看自身歷史，**軸④沒動** |
| `excluded` | 該象限**不可用**的方法 | 只寫該用什麼，沒寫不該用什麼 |
| `reviewed` | 最近複核日 | 超過 120 天 `validate_state.py` 會警告 |

⚠ **為何要把「不可以用什麼」也寫下來**：估值方法的誤用多半不是「選錯了主錨」，
而是「順手用了一個這個象限本來就不適用的方法」——
例如對循環股算 PEG、對選擇權價值做 forward-DCF、對 fabless 看 PB。
`excluded` 讓這些禁令跟著檔案走，而不是靠記憶。

⚠ **這一欄是 2026-09-01 引入的，既有檔案本來就沒有。**
`validate_state.py` 對缺漏只發 **NOTE 不發 ERROR**（發 ERROR 會一次擋下全部 commit），
但它每次執行都會列出來——**看不見的無知會被當成判斷使用。**
