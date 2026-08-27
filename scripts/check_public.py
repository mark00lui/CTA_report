#!/usr/bin/env python3
"""倉位資訊掃描器 — 確保本倉庫完全不含任何持倉、成本、尺寸、損益資料。

用法:
    python scripts/check_public.py            # 掃描所有受控檔案
    python scripts/check_public.py --staged   # 只掃 git staged（pre-commit hook 用）

有任何 BLOCK 時 exit code = 1。

設計原則：寧可誤擋也不要漏放。誤擋只花你三十秒改寫措辭，
漏放的東西一旦推上 public remote 就永遠留在 history 裡 —
刪檔不會刪掉歷史，你得改寫整條 history 並強推，還得假設已被 clone 過。
"""
import os
import re
import sys
import subprocess

# Windows 主控台預設 cp950，遇到報告裡的 ⚠、—、全形符號會在 print 當下拋
# UnicodeEncodeError。那會讓掃描器**在印出 BLOCK 訊息的瞬間崩潰** —— exit code
# 仍非 0（fail-closed，commit 還是被擋住），但操作者看不到究竟是哪一行被擋，
# 只能改用 PYTHONIOENCODING=utf-8 重跑一次才知道原因。
# 一個擋得住卻說不出理由的守門員，實務上會被繞過。故強制 stdout 走 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):   # 舊版 Python 或非標準串流，維持原行為
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 這些 YAML key 一旦出現在 state/ 就是倉位資訊
FORBIDDEN_KEYS = [
    "position", "cost_basis", "lots_or_shares", "current_weight",
    "unrealized_pl", "pnl", "kelly", "suggested_weight", "avg_price",
    "entry_price", "holdings", "disclosure", "factor_weights", "sizing_log",
]

# 直接指涉持倉／尺寸／損益的表述 → BLOCK
BLOCK_PATTERNS = [
    (r"(?:我|本人|作者)(?:的)?(?:部位|持股|倉位|持倉)", "第一人稱持倉"),
    (r"(?:部位|倉位|持倉)\s*[:：]?\s*\d", "部位 + 數字"),
    (r"\d+(?:\.\d+)?\s*%\s*(?:的)?(?:部位|持股|倉位|權重)", "百分比 + 部位"),
    (r"成本\s*(?:價|基礎)?\s*[:：]?\s*\d", "成本 + 數字"),
    (r"(?:加碼|減碼|加倉|減倉|建倉|平倉|進場|出場|停利|抱股|套牢)", "持倉動作用語"),
    (r"quarter[- ]?kelly|full[- ]?kelly|kelly\s*[:：]", "Kelly 尺寸"),
    (r"\d+\s*張(?!力|貼)", "張數"),
    (r"(?:未實現|已實現)\s*(?:損益|獲利|虧損)", "損益"),
    (r"(?:報酬率|投報率)\s*[:：]?\s*[+\-]?\d", "報酬率"),
    (r"(?:賺|賠)\s*(?:了)?\s*(?:約)?\s*[\d,]+\s*(?:元|萬|USD|NT)", "損益金額"),
    (r"我(?:買|賣|持有|加了|減了)", "第一人稱交易"),
]

# 可能是分析用語也可能是持倉用語 → WARN，人工判斷
WARN_PATTERNS = [
    (r"持股", "『持股』可能指他人股權（如大股東），也可能指自己 — 確認語意"),
    (r"停損", "『停損』暗示持倉；技術面失效價位建議寫 invalidation"),
    (r"最大(?:單一)?(?:標的|檔)", "相對規模描述 — 確認未暗示配置"),
]

# 說明文件與模板需要引用這些詞來說明規則本身
DOC_ALLOWLIST = {
    "README.md", "CLAUDE.md", "DISCLAIMER.md",
    "templates/report.md",
    "scripts/check_public.py", "scripts/validate_state.py",
    ".claude/skills/cta-research/SKILL.md",
    ".claude/skills/cta-research/references/state-schema.md",
    ".claude/skills/cta-research/references/report-templates.md",
    ".claude/commands/cta.md", ".claude/commands/weekly.md",
    ".claude/commands/audit.md", ".claude/commands/new-ticker.md",
    ".github/workflows/validate.yml",
}

blocks, warns = [], []


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def tracked_files(staged_only):
    """staged 檔案清單。

    首次 commit 時尚無 HEAD，`git diff --cached` 會失敗 —
    此時必須退回 `git ls-files --cached`，否則掃描器會掃到零個檔案然後放行，
    那正是最危險的時刻（第一次 push 的內容最不容易被檢查）。
    """
    try:
        if not staged_only:
            return [f for f in _git("ls-files").splitlines() if f.strip()]
        try:
            _git("rev-parse", "--verify", "HEAD")
        except subprocess.CalledProcessError:
            out = _git("ls-files", "--cached")   # 首次 commit
        else:
            out = _git("diff", "--cached", "--name-only", "--diff-filter=ACM")
        return [f for f in out.splitlines() if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 寧可什麼都不知道時中止，也不要靜默放行
        print("[BLOCK] 無法取得 git 檔案清單 — 中止以策安全")
        blocks.append("git 指令失敗")
        return []


def check_yaml_keys(f, text):
    if not f.startswith("state/") or not f.endswith((".yaml", ".yml")):
        return
    for key in FORBIDDEN_KEYS:
        if re.search(rf"^\s*{re.escape(key)}\s*:", text, re.MULTILINE):
            blocks.append(f"{f}: 不得含欄位 `{key}` — 本倉庫不保存任何倉位資訊")


def check_patterns(f, text):
    if not f.endswith((".md", ".yaml", ".yml")):
        return
    lenient = f in DOC_ALLOWLIST
    lines = text.splitlines()
    for patterns, bucket in ((BLOCK_PATTERNS, blocks), (WARN_PATTERNS, warns)):
        for pat, label in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                ln = text[: m.start()].count("\n") + 1
                snippet = lines[ln - 1].strip()[:88] if ln <= len(lines) else ""
                msg = f"{f}:{ln}: {label} — 「{snippet}」"
                (warns if lenient else bucket).append(msg)


def main():
    files = tracked_files("--staged" in sys.argv)
    if not files:
        print("沒有要掃描的檔案。")
        return 0

    for f in files:
        path = os.path.join(ROOT, f)
        if not os.path.isfile(path):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        check_yaml_keys(f, text)
        check_patterns(f, text)

    for m in warns:
        print(f"[WARN ] {m}")
    for m in blocks:
        print(f"[BLOCK] {m}")

    print(f"\n掃描 {len(files)} 個檔案：{len(blocks)} block, {len(warns)} warn")
    if blocks:
        print(
            "\n有 BLOCK，commit 已中止。\n"
            "改寫措辭，或若確認是誤判，把該檔加進 check_public.py 的 DOC_ALLOWLIST —\n"
            "但先問一次：這行推上 public 之後就洗不掉了，真的沒問題嗎？"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
