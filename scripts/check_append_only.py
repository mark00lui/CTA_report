#!/usr/bin/env python3
"""確保 reports/ 是 append-only — 已提交的報告不得修改或刪除。

用法:
    python scripts/check_append_only.py            # 檢查 staged 變更
    python scripts/check_append_only.py --all      # 掃全 history（稽核用）

reports/INDEX.md 是自動產生的索引，例外允許修改。

為什麼要機械化強制：append-only 原本只是寫在 CLAUDE.md 的約定，
而約定會在「只是改個錯字」的時候被繞過 — 那正是研究記錄開始失去
校準價值的方式。改一個字和改一個結論，在 git 眼中都是修改。
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEMPT = {"reports/INDEX.md"}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


def check_staged():
    try:
        git("rev-parse", "--verify", "HEAD")
    except subprocess.CalledProcessError:
        return []          # 首次 commit，全部都是新增
    out = git("diff", "--cached", "--name-status", "--diff-filter=MDR", "--", "reports/")
    bad = []
    for line in out.splitlines():
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        if path in EXEMPT:
            continue
        verb = {"M": "修改", "D": "刪除", "R": "改名"}.get(status[0], status)
        bad.append(f"{path}: 已提交的報告被{verb}了")
    return bad


def check_all_history():
    out = git("log", "--diff-filter=MDR", "--name-status", "--pretty=format:%h %s", "--", "reports/")
    return [l for l in out.splitlines() if l.strip()]


def main():
    if "--all" in sys.argv:
        lines = check_all_history()
        clean = [l for l in lines if "INDEX.md" not in l]
        print("=== history 中曾修改／刪除報告的紀錄 ===")
        print("\n".join(clean) if clean else "無（append-only 未被破壞）")
        return 0

    bad = check_staged()
    for m in bad:
        print(f"[BLOCK] {m}")
    if bad:
        print(
            "\nreports/ 是 append-only。判斷錯了請寫新報告修正，"
            "並在新報告的 front-matter 填 supersedes 指向舊檔。\n"
            "舊的留在原地 — 事後修飾過的研究記錄沒有校準價值。"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
