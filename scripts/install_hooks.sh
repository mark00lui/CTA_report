#!/usr/bin/env bash
# 安裝 git hooks。clone 之後跑一次即可。
set -e
cd "$(dirname "$0")/.."
git config core.hooksPath .githooks
chmod +x .githooks/*
echo "✓ hooks 已安裝（core.hooksPath = .githooks）"
echo "  每次 commit 前會自動跑 check_public.py --staged 與 validate_state.py"
