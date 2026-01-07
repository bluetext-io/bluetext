#!/bin/sh
set -e

MODULE_PATH="${1}"
POLYTOPE_FILE="${2:-polytope.yml}"

if [ -z "$MODULE_PATH" ]; then
  echo "Error: Missing required argument 'module_path'"
  echo "Usage: add-to-includes.sh <module-path> [polytope-file]"
  exit 1
fi

if [ ! -f "$POLYTOPE_FILE" ]; then
  echo "Error: File $POLYTOPE_FILE not found"
  exit 1
fi

# Check if include block exists
if ! grep -q "^include:" "$POLYTOPE_FILE"; then
  echo "Adding include block to $POLYTOPE_FILE"
  sed -i '1i include:' "$POLYTOPE_FILE"
fi

# Check if module is already included
if grep -q "^  - ${MODULE_PATH}$" "$POLYTOPE_FILE"; then
  echo "Module '${MODULE_PATH}' is already in includes"
  exit 0
fi

# Add the module to includes
echo "Adding '${MODULE_PATH}' to includes in $POLYTOPE_FILE"
awk -v path="$MODULE_PATH" '
/^include:/ { print; print "  - " path; next }
{ print }
' "$POLYTOPE_FILE" > "${POLYTOPE_FILE}.tmp" && mv "${POLYTOPE_FILE}.tmp" "$POLYTOPE_FILE"

echo "Successfully added '${MODULE_PATH}' to includes"
