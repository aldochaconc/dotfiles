#!/usr/bin/env bash
set -euo pipefail

# act_run_job.sh
# Run a specific GitHub Actions job locally via act.
#
# Usage:
#   scripts/act_run_job.sh -j <job-id> [-W <workflow.yml>] [-e <event.json>] \
#     [-s <secrets.env>] [-E <env.env>] [-- <extra act args>]
#
# Notes:
# - On Apple Silicon (arm64), this script defaults to --container-architecture linux/amd64
#   unless ACT_CONTAINER_ARCH is set. Set ACT_CONTAINER_ARCH=none to disable the flag.

JOB_ID=""
WORKFLOW_PATH=""
EVENT_FILE=""
SECRETS_FILE=""
ENV_FILE=""
ACT_CONTAINER_ARCH="${ACT_CONTAINER_ARCH:-}"

while getopts ":j:W:e:s:E:" opt; do
  case "${opt}" in
    j) JOB_ID="${OPTARG}" ;;
    W) WORKFLOW_PATH="${OPTARG}" ;;
    e) EVENT_FILE="${OPTARG}" ;;
    s) SECRETS_FILE="${OPTARG}" ;;
    E) ENV_FILE="${OPTARG}" ;;
    *)
      echo "Usage: $0 -j <job-id> [-W <workflow.yml>] [-e <event.json>] [-s <secrets.env>] [-E <env.env>] [-- <extra act args>]" >&2
      exit 2
      ;;
  esac
done
shift $((OPTIND - 1))

if [[ -z "${JOB_ID}" ]]; then
  echo "Missing required -j <job-id>." >&2
  exit 2
fi

ARGS=("-j" "${JOB_ID}")

if [[ "${ACT_CONTAINER_ARCH}" == "none" ]]; then
  ACT_CONTAINER_ARCH=""
elif [[ -z "${ACT_CONTAINER_ARCH}" ]]; then
  if [[ "$(uname -m)" == "arm64" ]]; then
    ACT_CONTAINER_ARCH="linux/amd64"
  fi
fi

if [[ -n "${ACT_CONTAINER_ARCH}" ]]; then
  ARGS+=("--container-architecture" "${ACT_CONTAINER_ARCH}")
fi

if [[ -n "${WORKFLOW_PATH}" ]]; then
  ARGS+=("-W" "${WORKFLOW_PATH}")
fi

if [[ -n "${EVENT_FILE}" ]]; then
  if [[ ! -f "${EVENT_FILE}" ]]; then
    echo "Event file not found: ${EVENT_FILE}" >&2
    exit 1
  fi
  ARGS+=("-e" "${EVENT_FILE}")
fi

if [[ -n "${SECRETS_FILE}" ]]; then
  if [[ ! -f "${SECRETS_FILE}" ]]; then
    echo "Secrets file not found: ${SECRETS_FILE}" >&2
    exit 1
  fi
  ARGS+=("--secret-file" "${SECRETS_FILE}")
fi

if [[ -n "${ENV_FILE}" ]]; then
  if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Env file not found: ${ENV_FILE}" >&2
    exit 1
  fi
  ARGS+=("--env-file" "${ENV_FILE}")
fi

if [[ "$#" -gt 0 ]]; then
  ARGS+=("$@")
fi

act "${ARGS[@]}"
