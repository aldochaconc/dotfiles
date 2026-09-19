#!/usr/bin/env bash
set -euo pipefail

# act_list_jobs.sh
# List workflows/jobs available to act.
# Usage:
#   scripts/act_list_jobs.sh
#   scripts/act_list_jobs.sh .github/workflows/ci.yml

WORKFLOW_PATH="${1:-}"

if [[ -n "${WORKFLOW_PATH}" ]]; then
  act -W "${WORKFLOW_PATH}" -l
else
  act -l
fi
