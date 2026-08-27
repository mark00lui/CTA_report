---
description: 共用資料收錄 — 預填當日跨標的重點，落到 driver 層並產生扇出待辦
argument-hint: [當日重點：貼上原文、連結或數字，可多則]
---

把以下當日重點收進共用資料層：$ARGUMENTS

## 這個指令存在的理由

`/cta` 是**個股推論**，`/driver` 是**單一因子更新加立即扇出**。兩者都貴，都要寫報告。
但每天真正該做的第一件事是**把共用資料收進來**——四大 capex、加速器營收與 guidance、
下一代平台時程與功耗、匯率。這些不屬於任何單一標的，而且多數日子不值得為它們寫個股報告。

**資料收錄與個股推論分離。** 收錄要快、每天都該做；推論貴、要挑值得的做。
綁在一起的結果一定是其中一個被犧牲——而被犧牲的永遠是收錄。
資料沒進來，後面所有推論都在用過期的數字。

所以本指令**只做收錄，不做扇出**：更新 driver 層、產生待辦佇列、寫一份當日 brief。
個股的定級與報告留給你之後用 `/cta <ticker>` 挑著做。

## 步驟

### 1. 分流 — 每一則先問「這個事實的家在哪一層」

逐則判斷，不要整批套用同一層：

| 這則資訊 | 家在哪 | 怎麼處理 |
|---|---|---|
| 多檔共用、不屬於任何單一標的（capex、加速器營收、平台時程、匯率、產業滲透率） | `drivers/<slug>.yaml` | 本指令處理 |
| 只影響一檔（該公司自己的財報、訂單、法說、籌碼） | `state/<ticker>.yaml` | **本指令不碰**，記進佇列，交給 `/cta <ticker>` |
| 兩者皆是（例如 MSFT 財報同時揭露自家數字與 capex guidance） | 兩層都有事 | driver 的部分本指令做；個股的部分進佇列 |
| 還不知道歸哪裡 | `notes/YYYY-MM.md` | 走 `/note`，不要硬塞進 driver |

**一個共用事實只能有一個家。**若這則資訊已經住在某個 driver，更新那一個，
絕不因為「這次是從別的角度看到的」就再開一個新 driver 或複製進個股 state。

現有 driver：`hyperscaler-capex`（四大 CSP 支出承諾）、`ai-accelerator-demand`（加速器實際出貨與 guidance）、
`accelerator-roadmap`（平台時程與功率密度）。若這則資訊不屬於任何一個，先問我要不要開新 driver，
用 `drivers/_TEMPLATE.yaml`——不要逕自新增。

### 2. 更新 driver

對每個被觸及的 driver：

- 更新 `current`、`components`，逐項標 `tier`、`source`、`as_of`。
- 在 `history` **追加**一筆，保留舊值。對這類變數，修正的方向與速度比絕對值更有訊息量。
- 查不到的填 `__` 並寫進 `gaps`，附取得途徑。**不要用推估值充數**，也不要沿用記憶中的數字。
- 檢查該 driver 的 `falsifiers` 是否觸發。觸發即在 brief 中標紅，並在佇列裡把相關標的的
  `prelim_level` 直接標 L3。
- 若該 driver 有 `cross_check` 欄位，比對另一個 driver 的現值，把背離狀況寫進 brief。
  `ai-accelerator-demand` 與 `hyperscaler-capex` 的背離是這個倉庫最有訊息量的訊號之一：
  承諾與落地不一致時，先動的那一邊通常是對的。
- 追加 `event_log` 一筆，更新 `last_updated`。

### 3. 產生扇出待辦（不執行扇出）

讀每個被更新 driver 的 `transmission`，對每個 ticker：

- 依 `direction` 判斷方向。**同一則消息對硬體端與平台端方向常常相反**，照欄位走，
  不要用新聞的語氣決定方向。
- 依 `lag` 判斷它會落在哪一季的財報上。落在時滯之外的未來季度 → `prelim_level: L0`。
- 給一個 `prelim_level` **初判**，並明寫這只是初判、正式定級由 `/cta` 依門檻重做。
  初判寧可低估——`/cta` 會重新判，但被你標成 L2 的項目會誘導後續流程過度反應。
- 寫進 `drivers/_queue.yaml` 的 `pending`。**佇列只存指標，不存數值。**

多數 driver 變動對多數標的是 L0。**不要為了讓佇列看起來有產出而升級。**
L0 的標的不必進 pending，在 brief 裡列一行「已檢查、無影響」即可。

### 4. 寫當日 brief

寫到 `reports/YYYY/MM/YYYY-MM-DD-brief.md`。這是 `reports/` 底下的檔案，**append-only**，
同日重跑改用 `-brief-2`、`-3`，絕不覆蓋。

front-matter：
```yaml
date: YYYY-MM-DD
type: brief
drivers_touched: [<slug>, ...]
queued: <進佇列的標的數>
falsifiers_triggered: <數量，無則 0>
sources:
  - "<來源名 — 連結 — 取得日期>"
```

正文四節，不要多寫：
1. **本日收錄** — 每個 driver 的舊值 → 新值、tier、來源。表格。
2. **交叉驗證** — 承諾（capex）vs 落地（加速器營收）是否一致；規格時程有無變動。無則寫「無」。
3. **扇出待辦** — 進佇列的標的、方向、初判等級、落在哪一季。含「已檢查無影響」的清單。
4. **本日最重要的一個變化** — 一句話。沒有就寫「無」。硬湊是雜訊來源。

### 5. 驗證與 commit

```bash
python scripts/check_public.py && python scripts/check_append_only.py && python scripts/validate_state.py && python scripts/build_index.py
```

commit：`brief(YYYY-MM-DD): <一句話> → 佇列 N 檔`

不要 push。

## 注意

**本指令不改任何 `state/*.yaml`。**個股 state 的每次改動都必須有對應的個股報告，
而 brief 不是個股報告。若你發現自己想動 state，那代表這件事該走 `/cta`。

**本指令不寫個股報告、不做三情境、不改目標價或訊號。**那是 `/cta` 與 `/revalue` 的工作。

**佇列不是待辦清單的全部，是「已知該看但還沒看」的部分。**`/weekly` 會檢查佇列積壓——
`since` 超過兩週還在 pending 的項目要嘛做掉，要嘛明確標為不做並寫原因。
積壓本身就是訊息：它通常代表某個 driver 的 transmission 定得太敏感。

**若某檔在佇列裡反覆出現卻總是 L0**，那是 transmission 的 `sensitivity` 或 `lag` 設錯了。
在 brief 裡指出來，該修的是 driver，不是每次都重新判一遍。
