#!/usr/bin/env bash
set -euo pipefail

# act_attach_shell.sh
# Attach an interactive shell to an act runner container.
# Usage:
#   scripts/act_attach_shell.sh               # auto-select if single container
#   scripts/act_attach_shell.sh <id-or-name>  # explicit container

TARGET="${1:-}"

if [[ -z "${TARGET}" ]]; then
  CONTAINERS=()
  while IFS= read -r line; do
    [[ -n "${line}" ]] && CONTAINERS+=("${line}")
  done < <(docker ps --filter "name=act" --format "{{.ID}} {{.Names}}")

  if [[ "${#CONTAINERS[@]}" -eq 0 ]]; then
    echo "No running act containers found. Start a job with act first." >&2
    exit 1
  fi

  if [[ "${#CONTAINERS[@]}" -gt 1 ]]; then
    echo "Multiple act containers found. Re-run with a specific container ID or name:" >&2
    printf '%s\n' "${CONTAINERS[@]}" >&2
    exit 2
  fi

  TARGET="${CONTAINERS[0]%% *}"
fi

if docker exec "${TARGET}" /bin/bash -lc "exit" >/dev/null 2>&1; then
  exec docker exec -it "${TARGET}" /bin/bash
else
  exec docker exec -it "${TARGET}" /bin/sh
fi
