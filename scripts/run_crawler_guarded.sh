#!/usr/bin/env bash
set -euo pipefail

# Guarded crawler entrypoint for Railway.
# - If RUN_CRAWLER is not true, exit successfully without crawling.
# - If true, execute CRAWLER_COMMAND (or a safe default).

if [[ "${RUN_CRAWLER:-false}" != "true" ]]; then
  echo "RUN_CRAWLER is not true; skipping crawl run."
  exit 0
fi

CRAWLER_COMMAND_DEFAULT="python3 scripts/run_mfa_parser.py --commit"
CRAWLER_COMMAND="${CRAWLER_COMMAND:-$CRAWLER_COMMAND_DEFAULT}"

echo "RUN_CRAWLER=true; executing: ${CRAWLER_COMMAND}"
exec bash -lc "${CRAWLER_COMMAND}"
