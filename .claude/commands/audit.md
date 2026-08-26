---
description: 論點稽核 — 用 git history 檢驗過去的判斷準不準
argument-hint: [ticker，省略則全部]
---

對 $ARGUMENTS 做論點稽核（省略則全部標的）。

這不是產生新推論，是**檢驗舊推論**：

1. `git log --follow state/<ticker>.yaml` 取得該檔的完整變更史。
2. 對每個曾經設定的 `falsifiers`：當初的門檻是什麼？後來實際發生了什麼？我有沒有在觸發時真的執行 L3？
3. 對每次 L2 以上的目標價與訊號變動：事後看，那次調整方向對嗎？幅度過大還是過小？
4. 統計：L0/L1/L2/L3 各多少次？是否有「事後看該升級卻定成 L1」的案例？
5. 找出**論點漂移** — thesis 文字沒改，但 key_variables 已被逐次微調到與原論點不符。這是最危險的失效模式，因為它不會觸發任何否證點。

6. **倉位資訊稽核**：抽查整條 history 是否曾有倉位資訊被 commit：
   `git grep -n -iE "成本|部位|倉位|權重|kelly|加碼|減碼|[0-9]+ ?張" $(git rev-list --all) -- state/ reports/ | head -50`
   若有，立即告知我 — 那需要改寫 history 並強推，而且必須假設已被 clone 過。
7. **訊號一致性**：檢查 `signal.rating` 的變動是否都有對應報告，以及是否曾在未達右側確認時就翻多。

寫到 `reports/YYYY/MM/YYYY-MM-DD-audit-<ticker>.md`。

誠實優先於好看。稽核報告若通篇都是「判斷正確」，那多半是稽核做得不夠。
