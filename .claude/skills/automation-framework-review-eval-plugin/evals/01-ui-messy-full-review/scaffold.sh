#!/usr/bin/env bash
# Runs inside the run's empty sandbox cwd (only with `claude plugin eval --scaffold`).
# Nothing next to prompt.md is copied into the sandbox automatically, so put the
# fixture repo there; otherwise the model reviews an empty directory and no
# review.md / checklist.md is ever written.
set -euo pipefail
CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cp -R "$CASE_DIR/ui-messy/." .
