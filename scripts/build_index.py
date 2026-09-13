#!/usr/bin/env python3
"""從 reports/**/*.md 的 front-matter 產生 reports/INDEX.md。

每份報告開頭需有 YAML front-matter（見 templates/report.md）。
"""
import os
import sys
import glob

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML： pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVEL_ORDER = {"L3": 0, "L2": 1, "L1": 2, "L0": 3}


# 有 front-matter 但解析失敗者 —— 2026-09-13 起是 error，不再只是「未納入索引」。
broken = []


def parse_front_matter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        # ⚠ 最常見的成因是雙引號純量裡的反斜線（`\s` 會噴 unknown escape character）。
        #   在此之前這裡只是 return None，於是整條驗證鏈 0 block / 0 error 通過，
        #   而那份報告不進索引、不被 E4 對照、也不進衍生索引 —— 三處都安靜地少一筆。
        broken.append((path, str(e).split("\n")[0]))
        return None
    if not isinstance(fm, dict):
        broken.append((path, "front-matter 不是 mapping"))
        return None
    return fm


def main():
    # --check：只驗證 front-matter，不寫 INDEX.md。供 pre-commit 使用 ——
    # 直接在 hook 裡跑完整的 build_index 會改動未 staged 的 INDEX.md。
    check_only = "--check" in sys.argv
    rows, skipped = [], []
    pattern = os.path.join(ROOT, "reports", "**", "*.md")
    for path in sorted(glob.glob(pattern, recursive=True)):
        rel = os.path.relpath(path, ROOT)
        if os.path.basename(path) == "INDEX.md":
            continue
        fm = parse_front_matter(path)
        if not fm:
            skipped.append(rel)
            continue
        rows.append(
            {
                "date": str(fm.get("date", "")),
                "ticker": str(fm.get("ticker", "")),
                "level": str(fm.get("level", "")),
                "summary": str(fm.get("summary", "")).replace("|", "／"),
                "signal": str(fm.get("signal", "")),
                "conviction": str(fm.get("conviction", "")),
                "tp_delta": str(fm.get("tp_delta", "")),
                "supersedes": str(fm.get("supersedes", "")).replace(os.sep, "/"),
                "path": rel.replace(os.sep, "/"),
            }
        )

    rows.sort(key=lambda r: (r["date"], LEVEL_ORDER.get(r["level"], 9)), reverse=True)

    # 被其他報告 supersedes 指到的，標記為已取代
    superseded = {r["supersedes"] for r in rows if r["supersedes"]}
    for r in rows:
        r["status"] = "已取代" if r["path"] in superseded else "現行"

    out = ["# 推論索引", "", "由 `scripts/build_index.py` 自動產生，勿手改。", ""]

    by_ticker = {}
    for r in rows:
        by_ticker.setdefault(r["ticker"], []).append(r)
    out.append("## 各標的最近一次推論")
    out.append("")
    out.append("| 標的 | 最近日期 | 等級 | 現行訊號 | 累計報告數 | L2+ 次數 |")
    out.append("|---|---|---|---|---|---|")
    for t, rs in sorted(by_ticker.items()):
        heavy = sum(1 for x in rs if x["level"] in ("L2", "L3"))
        out.append(
            f"| {t} | {rs[0]['date']} | {rs[0]['level']} | {rs[0]['signal']} "
            f"| {len(rs)} | {heavy} |"
        )
    out.append("")

    out.append("## 全部推論（新到舊）")
    out.append("")
    out.append("| 日期 | 標的 | 等級 | 摘要 | 訊號 | 信心 | 目標價Δ | 狀態 | 檔案 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        out.append(
            f"| {r['date']} | {r['ticker']} | {r['level']} | {r['summary']} "
            f"| {r['signal']} | {r['conviction']} | {r['tp_delta']} "
            f"| {r['status']} | [連結]({r['path']}) |"
        )
    out.append("")

    if skipped:
        out.append("## ⚠ 缺少 front-matter（未索引）")
        out.append("")
        for s in skipped:
            out.append(f"- `{s}`")
        out.append("")

    if not check_only:
        index_path = os.path.join(ROOT, "reports", "INDEX.md")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out))

    print(("已檢查 %d 份報告的 front-matter（--check，未寫檔）" % len(rows))
          if check_only else f"已索引 {len(rows)} 份報告 → reports/INDEX.md")
    if skipped:
        print(f"⚠ {len(skipped)} 份缺少 front-matter，未納入索引")
    if broken:
        print("")
        for path, msg in broken:
            print(f"[ERROR] {os.path.relpath(path, ROOT)}: front-matter 解析失敗 — {msg}")
        print(f"\n有 {len(broken)} 份報告的 front-matter 壞了。"
              "它們不會進索引、不會被 cross_check 的 E4 對照、也不會進衍生索引 —— "
              "三處都只是安靜地少一筆，所以這裡擋下。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
