#!/usr/bin/env bash
set -euo pipefail

# Guarded crawler entrypoint for Railway.
# - If RUN_CRAWLER is not true, exit successfully without crawling.
# - If true, execute CRAWLER_COMMAND (or a safe default).

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "No python interpreter found in PATH."
    exit 1
  fi
fi

echo "Dependency check:"
"${PYTHON_BIN}" -u - <<'PY'
import importlib
import platform
import subprocess
import sys
import bs4

packages = [
    ("sys", "sys"),
    ("fastapi", "fastapi"),
    ("sqlalchemy", "sqlalchemy"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),
    ("pymysql", "pymysql"),
    ("httpx", "httpx"),
    ("bs4", "beautifulsoup4"),
]

print(f"- python: {platform.python_version()}")
print(f"- executable: {sys.executable}")
try:
    pip_version = subprocess.check_output(
        [sys.executable, "-m", "pip", "--version"], text=True
    ).strip()
    print(f"- pip: {pip_version}")
except Exception as exc:
    print(f"- pip: MISSING ({exc})")

for module_name, label in packages:
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "unknown")
        print(f"- {label}: OK ({version})")
    except Exception as exc:
        print(f"- {label}: MISSING ({exc})")
PY

if [[ "${RUN_CRAWLER:-false}" != "true" ]]; then
  echo "RUN_CRAWLER is not true; skipping crawl run."
  exit 0
fi

CRAWLER_COMMAND_DEFAULT="${PYTHON_BIN} scripts/run_mfa_parser.py --commit"
CRAWLER_COMMAND="${CRAWLER_COMMAND:-$CRAWLER_COMMAND_DEFAULT}"

echo "RUN_CRAWLER=true; executing: ${CRAWLER_COMMAND}"
exec bash -lc "${CRAWLER_COMMAND}"
