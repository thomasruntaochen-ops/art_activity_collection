#!/usr/bin/env bash
set -euo pipefail

# Guarded crawler entrypoint for Railway.
# - If RUN_CRAWLER is not true, exit successfully without crawling.
# - If true, execute CRAWLER_COMMAND (or a safe default).

echo "Dependency check:"
python3 - <<'PY'
import importlib
import platform

packages = [
    ("fastapi", "fastapi"),
    ("sqlalchemy", "sqlalchemy"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),
    ("pymysql", "pymysql"),
    ("httpx", "httpx"),
    ("bs4", "beautifulsoup4"),
]

print(f"- python: {platform.python_version()}")
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

CRAWLER_COMMAND_DEFAULT="python3 scripts/run_mfa_parser.py --commit"
CRAWLER_COMMAND="${CRAWLER_COMMAND:-$CRAWLER_COMMAND_DEFAULT}"

echo "RUN_CRAWLER=true; executing: ${CRAWLER_COMMAND}"
exec bash -lc "${CRAWLER_COMMAND}"
