# CTA 推論專案

增量式個股研究記錄。每則新資訊產生一份差分推論，不重建整份報告。

覆蓋清單：TSM、MSFT、GOOG、META、INTU、雙鴻 3324、光聖 6442

推論索引在 [reports/INDEX.md](reports/INDEX.md)。免責聲明見 [DISCLAIMER.md](DISCLAIMER.md)。

## 這個倉庫不含任何倉位資訊

沒有成本、沒有部位規模、沒有配置權重、沒有損益，也沒有「作者是否持有」的揭露。追蹤清單是**研究覆蓋範圍**，不是持股清單。

這由三道機制維持：

1. schema 層面不存在相關欄位——`state/*.yaml` 只有論點、情境、變數、否證點、CTA 位階、訊號評級
2. `scripts/check_public.py` 掃描所有受控檔案，發現持倉表述就 BLOCK
3. pre-commit hook 自動跑第 2 項，未通過無法 commit

第 3 項要手動裝一次：

```bash
bash scripts/install_hooks.sh
```

掃描器抓的是措辭。它抓不到的是**結構性洩漏**——某檔報告特別密集、訊號翻多後就不再更新，這些模式同樣可能被推論。那要靠自己維持一致的更新節奏。

### 訊號，不是動作

報告給的是 `signal: 偏多 / 中性 / 偏空` 加上信心度與翻轉條件，不是「加碼／減碼」。後者暗示已有部位，前者不會。同理，技術面用 `invalidation`（失效價位）而非「停損」。

倉位如何配置是讀者自己的事。本倉庫不提供也不記錄任何尺寸資訊。

## 安裝

```bash
git clone <this-repo> cta-research && cd cta-research
pip install pyyaml
bash scripts/install_hooks.sh
claude          # 在根目錄啟動，CLAUDE.md 自動載入
```

## 倉庫結構

```
CLAUDE.md                      專案指令，Claude Code 自動載入
DISCLAIMER.md                  免責聲明
.claude/
  skills/cta-research/         分級規則、schema、報告模板
  commands/                    /cta  /weekly  /audit  /new-ticker
state/<ticker>.yaml            論點、情境、變數、否證點、CTA 位階、訊號
state/coverage.yaml            覆蓋清單的等權因子結構與共同前提
reports/YYYY/MM/*.md           推論文件，append-only
reports/INDEX.md               自動產生
scripts/check_public.py        倉位資訊掃描（擋 commit）
scripts/validate_state.py      結構驗證（擋 commit）
scripts/build_index.py         重建索引
.githooks/pre-commit           自動跑前兩項
```

## 日常用法

```bash
/cta 3324 https://...          # 丟一則資訊，其餘自動
/weekly                        # 週報：事件流 + 共同前提檢核 + 檢驗點
/audit 3324                    # 論點稽核 + 歷史倉位資訊抽查
/new-ticker 2330 台積電        # 新增覆蓋標的
```

`/cta` 會做：讀 state → 影響掃描 → 定級 L0–L3 → 依級修正 → 寫報告 → 更新 state → 掃描 → 驗證 → commit。

L0/L1 只寫變更單，L2 才重算模型，L3 才做論點層重寫。分級門檻是數字（機率變動 ≥ 5pp、目標價變動 ≥ 5%），不是形容詞——這樣事後可以檢驗判斷有沒有偷懶或反應過度。

## 手動指令

```bash
python scripts/check_public.py             # 倉位資訊掃描，有 BLOCK 時 exit 1
python scripts/check_public.py --staged    # 只掃 staged（hook 用）
python scripts/validate_state.py           # 結構驗證
python scripts/validate_state.py --stale   # 列出 >90 天未更新的變數
python scripts/validate_state.py --gaps    # 各檔未填欄位統計
python scripts/build_index.py              # 重建 reports/INDEX.md
```

驗證會擋下的硬錯誤：三情境機率合計 ≠ 1.00、key_variables 超過 6 個、有效否證點少於 2 條、`signal.rating` 值不合法、缺必要欄位、tier 值不合法。

## 為什麼公開

`git blame state/3324.yaml` 能回答「這個 55% 的機率是哪一天、因為哪則消息變成這樣的」。

公開的價值在於**無法事後修飾**。已提交的報告不修改；判斷錯了寫新報告修正，舊的留在 history 裡。一份只留下正確判斷的研究記錄沒有校準價值——你需要能回頭問「我當時憑什麼那樣想」，而公開讓這件事對自己也對讀者成立。

`/audit` 就是為此設計的：它專門找**論點漂移**——thesis 文字沒改，但 key_variables 被逐次微調到已與原論點不符。這是最危險的失效模式，因為它不觸發任何否證點，只是慢慢把一個死掉的論點養成看起來還活著的樣子。

## 覆蓋清單的結構性偏誤

`state/coverage.yaml` 記了一件個股層看不見的事：7 檔中有 6 檔共用同一前提——AI 資料中心資本支出在未來 8 個季度不會實質減速。

等權基準下，硬體端（TSM／3324／6442）與平台端（MSFT／GOOG／META）各佔 42.9%，但這兩組不是分散，是同一條產業鏈的兩端。真正低相關的只有 INTU 一檔。非 AI 曝險為零。

讀者應把這個偏誤納入對本倉庫所有結論的加權。

## 目前狀態

state 檔是骨架，多數欄位是 `__`（刻意留白——填假數字會被模型放大成看起來很精確的目標價）。

下一步是填初始值，建議從 3324 和 6442 開始——台股月營收是高頻一手數據，基準線建起來後續增量最省力。
