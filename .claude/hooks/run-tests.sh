#!/bin/bash
# run-tests.sh — PostToolUse pytest validation (governance P06 §1.7.15)
# Runs targeted tests for the file Claude just modified. Does not block
# the write itself (PostToolUse cannot undo a completed tool call);
# reports failure back to Claude via decision:block so it can revise.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0

TARGET=""
if [[ "$FILE_PATH" == tests/* ]]; then
  TARGET="$FILE_PATH"
elif [[ "$FILE_PATH" == src/*/*.py ]]; then
  COMPONENT=$(echo "$FILE_PATH" | cut -d/ -f2)
  [[ -d "tests/${COMPONENT}" ]] && TARGET="tests/${COMPONENT}/"
fi

[[ -z "$TARGET" ]] && exit 0

RESULT=$(python -m pytest "$TARGET" -q 2>&1)
STATUS=$?

if [[ $STATUS -ne 0 ]]; then
  REASON=$(echo "$RESULT" | tail -n 20 | jq -Rs .)
  echo "{\"decision\": \"block\", \"reason\": ${REASON}}"
fi

exit 0
