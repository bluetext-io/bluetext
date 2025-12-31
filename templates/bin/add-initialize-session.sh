#!/bin/sh
set -e

TARGET_FILE="${1:-polytope.yml}"

if [ ! -f "$TARGET_FILE" ]; then
  echo "Error: File $TARGET_FILE not found"
  exit 1
fi

# Check if tools block exists
if ! grep -q "^tools:" "$TARGET_FILE"; then
  echo "Adding tools block to $TARGET_FILE"
  echo "" >> "$TARGET_FILE"
  echo "tools:" >> "$TARGET_FILE"
fi

# Check if initialize_session already exists
if grep -q "^  initialize_session:" "$TARGET_FILE" || grep -q "^    initialize_session:" "$TARGET_FILE"; then
  echo "initialize_session already exists in $TARGET_FILE"
  exit 0
fi

# Append initialize_session tool
echo "Adding initialize_session tool to $TARGET_FILE"
cat >> "$TARGET_FILE" << 'EOF'

  initialize_session:
    info: |-
      Initialize **EVERY** session by calling this tool.
      Returns required development context and ensures the project is running.
      This tool always needs to be called before doing anything else, regardless of the tasks complexity.
    run:
      - id: run-stack
        tool: stack
      - id: get-general-context
        after: {step: run-stack}
        tool: get_dev_context
EOF

echo "Successfully added initialize_session to $TARGET_FILE"
