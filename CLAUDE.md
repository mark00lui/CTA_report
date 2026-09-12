# CTA 推論專案

這是一個**增量式**個股研究倉庫，完全公開。每則新資訊只產生一份差分推論，不重建整份報告。

覆蓋清單：TSM、MSFT、GOOG、META、INTU、雙鴻 3324、光聖 6442

## 最重要的規則：這個倉庫不含任何倉位資訊

不寫成本、不寫張數、不寫權重、不寫 Kelly、不寫損益，也不揭露作者是否持有。

這不只是「不寫數字」，而是**不寫任何能推論持倉的東西**：

| 可以寫 | 不可以寫 |
|---|---|
| 論點、情境機率、目標價、EPS 假設 | 成本、張數、配置比重 |
| 否證點、檢驗點、缺口 | Kelly edge / odds / 建議權重 |
| CTA 位階、支撐壓力、技術面失效價位 | 「我的持倉」「作者持有」 |
| 訊號評級（偏多／中性／偏空） | 加碼、減碼、建倉、平倉、進場、出場 |
| 覆蓋清單的等權因子分布 | 實際配置權重、單一標的上限 |

**訊號不等於動作。** 「偏多」是研究結論；「加碼」是持倉動作，暗示已有部位。永遠用前者。同理，`invalidation`（技術面失效價位）是規則參數，`停損` 則暗示持倉——用前者。

`state/coverage.yaml` 是**研究覆蓋清單**，不是投資組合。因子分析以等權為基準，那是清單的結構描述。

寫完跑 `python scripts/check_public.py`。它是正則比對不是理解，擋不住所有間接洩漏——最後一道防線是你自己逐句問：這行能不能被拿來推論持倉？

## 倉庫結構

```
state/<ticker>.yaml       個股狀態 — 個股層唯一真實來源，可寫
state/coverage.yaml       覆蓋清單的因子結構與共同前提
drivers/<slug>.yaml       共用驅動因子 — 跨標的變數的唯一真實來源
drivers/_queue.yaml       扇出待辦佇列 — /brief 產生，/cta 消費；只存指標不存數值
notes/YYYY-MM.md          暫存收件匣 — 還不知道該歸哪裡的觀察
reports/YYYY/MM/*.md      推論文件與沿革檔 — append-only，不修改已提交的報告
reports/INDEX.md          自動產生，勿手改
docs/index.html           GitHub Pages 門面 — 自動產生，勿手改
scripts/                  驗證、索引、站台、倉位資訊掃描
.claude/skills/           cta-research skill（分級規則、模板、schema）
```

**`docs/index.html` 是洩漏面積最大的檔案。** 它把 state 與 drivers 整頁攤開給不讀 YAML 的人看，
且掛在 `https://mark00lui.github.io/CTA_report/` 這個比 repo 本身更容易被看到的網址上。
`check_public.py` 已於 2026-08-27 納入 `.html` —— 在那之前它只掃 `.md`／`.yaml`／`.yml`，
等於整個規則對這個介面是失效的。改動產生器時務必確認掃描仍然涵蓋輸出。

## 三層資料模型

| 層 | 存什麼 | 誰擁有 |
|---|---|---|
| `drivers/` | 多檔共用、不屬於任何單一標的的變數（四大 capex、匯率、產業滲透率） | 跨標的 |
| `state/` | 該標的專屬的論點、情境、變數、否證點 | 單一標的 |
| `notes/` | 還不成熟、尚未歸屬的觀察 | 未定 |

現有 driver：`hyperscaler-capex`（四大 CSP 支出**承諾**）、`ai-accelerator-demand`（加速器**實際出貨**與 guidance）、`accelerator-roadmap`（平台**時程與功率密度**）。前兩者互為交叉驗證——承諾與落地背離時，先動的那一邊通常是對的。

**一個共用事實只能有一個家。** 四大 CSP capex 住在 `drivers/hyperscaler-capex.yaml`，個股用 `driver_refs` 引用，**絕不複製數值進 state**。複製會讓四份檔案各自漂移，而漂移不會報錯——只會安靜地讓某檔的模型停止更新。

`validate_state.py` 檢查 `driver_refs` 與 driver 的 `transmission` **雙向一致**：方向不一致、引用了沒有回指的 driver、指向不存在的 driver 都是 error，會擋 commit；反方向的單向引用（driver 指向某檔、但該檔沒有回引）是 warn，因為新增 driver 時本來就會先出現這個狀態——但它不該長期存在，`/cta` 首次處理該檔時就要補上 `driver_refs`。

**同一則消息對不同標的方向可能相反。** capex 上修對硬體端（TSM／3324／3017／6442）是需求利多，對平台端（MSFT／GOOG／META／AMZN）是折舊與 ROI 利空。driver 的 `transmission` 逐檔記了 `direction` 與 `lag`——扇出時照它走，不要套用同一個結論。若你發現自己對兩端寫出同方向的結果，先停下來確認那是真的。

## 核心迴圈

```
收錄：  /brief  → 更新 driver 層 → 產生扇出待辦（不碰 state、不寫個股報告）
推論：  /cta    → 讀 state + driver → 影響掃描 → 定級 L0–L3 → 依級修正
                → 寫報告 → 更新 state → 消化佇列 → 掃描驗證 → commit
```

**收錄與推論刻意分離。** 收錄要每天做、要快；推論貴、要挑值得的做。
綁在一起的結果一定是其中一個被犧牲——而被犧牲的永遠是收錄，
然後所有推論都在用過期的數字。

分級門檻、證據分層、模板都在 `.claude/skills/cta-research/SKILL.md`。處理任何個股資訊前先讀它。

## 這個倉庫的特殊約定

**報告是 append-only，由 pre-commit hook 機械強制。** 已 commit 的報告不修改、不刪除、不改名——`check_append_only.py` 會擋下（`reports/INDEX.md` 例外，它是自動產生的）。

判斷錯了就寫新報告修正，並在新報告的 front-matter 填 `supersedes` 指向舊檔，索引會把舊的標為「已取代」。舊報告留在原地。事後修飾過的研究記錄沒有校準價值——你需要能回頭問「我當時憑什麼那樣想」，而「只是改個錯字」正是這種記錄開始腐爛的方式。

**state 則相反：原地修改。** 一份檔案代表當下最佳判斷，歷史由 git diff 保存。這是兩種物件的分工——報告不可變、state 可變且被版控。

**state 可寫，但每次改動必須有對應報告。** 沒有報告佐證的 state 變動不該存在。若 state 與 reports 不一致，以 reports 為準並補寫修正報告。

**`reports/` 也放沿革檔，而它不是推論文件。** 沿革檔只做一件事：把某個 state 欄位累積的歷史判讀逐字搬過來，原文一個字不改、不刪、不摘要。front-matter 的 `level` 填 `L0`，`signal`／`conviction`／`tp_*` 一律 `n/a`——**因為它不新增、不修改、不撤回任何判斷，只搬動文字。**

⚠⚠ **搬到 `reports/` 的理由不是瘦身，是上面那條 append-only 規則本身。** 歷史判讀留在一個**可變的** state 檔裡，本來就有被事後修飾的空間；而 `reports/` 由 `check_append_only.py` 機械強制不可改。**所以搬過去之後它們才真正不可改——校準價值是變強，不是變弱。** 這一點反直覺，但它正是「報告不可變、state 可變」那個分工要處理的情況：**當 state 裡的某個欄位開始承擔「記錄歷史」的職責時，它就站錯地方了。**

⚠ **不放 `notes/`：** 那裡是「還不知道該歸哪裡的觀察」，而沿革檔的歸屬非常明確。

⚠⚠⚠ **而沿革檔之所以會需要，通常是因為某個 state 欄位長成了 prepend-only 的 append-log——那本身是要避免的形狀。** `state/coverage.yaml` 的 `equal_weight_factor_mix[].note` 曾每次新增標的就把新判讀疊在字串最前面、舊的用「原註：」串在後面全留，到 39 檔時 `ai_capex_hw` 一格已 7,051 字／22 段，且**會隨覆蓋清單無上限成長**。**state 的一個欄位代表「當下最佳判斷」，不是一條日誌——歷史由 git diff 與報告保存。** 發現自己在往某個欄位前面疊字串時，停下來：該寫的是新報告，不是更長的字串。

**commit 前一定跑：**
```bash
python scripts/check_public.py && python scripts/check_append_only.py && python scripts/validate_state.py && python scripts/cross_check.py && python scripts/build_index.py && python scripts/build_site.py
```
`build_index.py` 與 `build_site.py` 都是**單向產生**：輸出被手改會在下次執行時覆蓋，
且 CI 會用 `git diff --exit-code` 擋下產生器輸出與提交內容不一致的 commit。
pre-commit hook 會自動跑前四項（`bash scripts/install_hooks.sh` 安裝一次）。

`cross_check.py` 是**跨清單重算**：把每一項聚合檢查對「全部」標的跑一次，而不是只對剛改的那幾檔。
它擋下三種算術不自洽 —— E1 機率合計 ≠ 1.00、**E2 `weighted_tp` 與三格算出的值不符、
E3 某格 `tp` ≠ `eps × exit_multiple`**；後兩項在它併入閘門之前沒有任何機械檢查。
另有七條**不擋 commit** 的旗標（F1 算術與幾何加權跨越零／F2 全距 ≥5x／
F3 倍數段佔對數全距 ≥70%／F4 base 落在現價 ±5% 內／F5 |加權 − base| ≤2pp／
F6 三情境分母完全相同／F7 反推分母非單調遞增）。
hook 裡用 `--gate` 只印硬錯；**要看旗標與序數排名就自己跑一次不帶參數的版本**。

⚠⚠ **它存在的理由是一類實際犯過的錯：拿子集合下全集合的結論。**
「首見／最高／最低」是這份研究記錄標示方法層演進的主要標記，而我三次把它下錯 ——
兩次是只對「檢查建立之後處理的標的」算過，一次是把機率硬寫成眾數 0.25/0.50/0.25
而沒去讀那三檔非標準的值。**所以下任何序數結論之前，先跑一次不帶參數的 `cross_check.py`，
看它印出來的排名區塊。** 可機械化的檢查不要留給紀律。

**commit message 格式**（讓 `git log` 本身成為研究日誌），同樣不得含倉位資訊：
```
cta(3324): L2 液冷滲透率上修 → 加權目標價 +7%
cta(6442): L0 光通訊族群新聞，不動模型
coverage: 週報 2026-W35，共同前提未鬆動
state(TSM): 補齊初始值
```

**每個報告一個 commit。** 不要把三檔的變更單塞進同一次提交——那會讓 `git log --follow state/3324.yaml` 失去追溯價值。

## 為什麼用 git 做這件事

`git blame state/3324.yaml` 可以回答「這個 55% 的機率是哪一天、因為哪則消息變成這樣的」。這是純檔案系統做不到的事，也是這個專案值得放進版本控制的唯一理由。

公開更進一步：**歷史無法事後修飾**。對自己的校準價值來自於此。

定期做的事：
- `git log --oneline state/<ticker>.yaml` — 看單一標的的論點演化
- `python scripts/validate_state.py --stale` — 找出超過 90 天沒更新的變數
- `/audit` — 對照當初的否證點與實際結果，並抽查歷史是否曾洩漏倉位資訊

## Guardrails

- **不編造數字。** 未知填 `__` 並列進 `gaps`。
- **訊號升級為偏多需右側技術確認**，基本面理由再強也不跳過。這是 CTA 紀律的核心。
- **三情境機率合計恆為 1.00**，驗證腳本會擋。
- **機率不因價格波動而調整。** 股價漲跌本身不是新資訊，除非構成 CTA 位階變化（那走 L2）。
- **需要現價、月營收、財報數字就去查**，不要用記憶中的數字。查到後標來源與日期。
