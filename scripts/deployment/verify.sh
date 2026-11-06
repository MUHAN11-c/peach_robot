#!/usr/bin/env bash
set -Eeuo pipefail
workspace="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$workspace"
set +u
source scripts/deployment/env.bash
set -u
exec python3 scripts/deployment/verify_mock.py "$@"
