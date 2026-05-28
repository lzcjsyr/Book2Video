#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXE="$REPO_ROOT/.venv/bin/python"
REQUIRE_API_KEYS="${1:-}"

if [ ! -x "$PYTHON_EXE" ]; then
  echo "未找到虚拟环境，请先运行 scripts/install_macos.sh"
  exit 1
fi

cd "$REPO_ROOT"

if [ "$REQUIRE_API_KEYS" = "--require-api-keys" ]; then
  "$PYTHON_EXE" -m core.dependency_check --repo-root "$REPO_ROOT" --require-api-keys
else
  "$PYTHON_EXE" -m core.dependency_check --repo-root "$REPO_ROOT"
fi

"$PYTHON_EXE" -m pytest
