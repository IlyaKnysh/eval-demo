#!/usr/bin/env bash
# Runs this plugin's eval suite. A bare `claude plugin eval .` cannot work here:
#   --allow-tools  Write is gated and must be granted on every run, or review.md /
#                  checklist.md can't be created.
#   --scaffold     runs each case's scaffold.sh, which copies the fixture repo into
#                  the otherwise empty sandbox. Without it the model reviews nothing.
# Extra arguments are passed through, e.g. `bash run-evals.sh --ablation none`.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

claude plugin eval "$HERE" \
  --scaffold \
  --allow-tools "Read,Grep,Glob,Agent,Write,Skill" \
  --concurrency 3 \
  "$@"
