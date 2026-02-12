#!/usr/bin/env bash
# 便捷运行：在项目根目录执行 ./run.sh --lakebook xxx.lakebook --output ./out
set -e
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
PYTHONPATH=src .venv/bin/python -m yuque_export "$@"
