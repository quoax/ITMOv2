#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from repo root
repo_dir="$(git rev-parse --show-toplevel)"
cd "$repo_dir"

# 1) Block commits directly to main
branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$branch" = "main" ]; then
  echo "Pre-commit: commits to 'main' are blocked. Use a feature branch."
  exit 1
fi

# 2) Whitespace and basic diff checks on staged changes
git diff --cached --check

# 3) Python syntax check for demo (Feature A area)
python3 -m compileall -q practices/practice_03/lab/demo

# 4) Run unit tests for demo
make -s -C practices/practice_03/lab test

echo "Pre-commit: OK"
