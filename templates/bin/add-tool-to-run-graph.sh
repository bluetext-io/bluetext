#!/bin/sh
set -e

TARGET="${1}"
GRAPH="${2:-stack}"
POLYTOPE_FILE="${3:-polytope.yml}"

if [ -z "$TARGET" ]; then
  echo "Error: Missing required argument 'target'"
  echo "Usage: add-tool-to-run-graph.sh <target> [graph] [polytope-file]"
  exit 1
fi

if [ ! -f "$POLYTOPE_FILE" ]; then
  echo "Error: File $POLYTOPE_FILE not found"
  exit 1
fi

# Check if tools block exists
if ! grep -q "^tools:" "$POLYTOPE_FILE"; then
  echo "Adding tools block to $POLYTOPE_FILE"
  echo "" >> "$POLYTOPE_FILE"
  echo "tools:" >> "$POLYTOPE_FILE"
fi

# Check if the graph tool exists, if not create it
if ! grep -q "^  ${GRAPH}:" "$POLYTOPE_FILE"; then
  echo "Creating '${GRAPH}' tool in $POLYTOPE_FILE"
  cat >> "$POLYTOPE_FILE" << EOF

  ${GRAPH}:
    run:
      - tool: ${TARGET}
EOF
  echo "Successfully created '${GRAPH}' and added '${TARGET}'"
  exit 0
fi

# Check if target is already in the graph
if grep -A 20 "^  ${GRAPH}:" "$POLYTOPE_FILE" | grep -q "tool: ${TARGET}"; then
  echo "Tool '${TARGET}' is already in the '${GRAPH}' graph"
  exit 0
fi

# Add the target to the graph's run section
echo "Adding '${TARGET}' to '${GRAPH}' run graph in $POLYTOPE_FILE"

# Find the run: section under the graph and add the tool
awk -v target="$TARGET" -v graph="$GRAPH" '
BEGIN { in_graph=0; in_run=0; added=0 }
/^  '"$GRAPH"':/ { in_graph=1; print; next }
in_graph && /^    run:/ { in_run=1; print; next }
in_graph && in_run && /^      - tool:/ && !added {
  print
  print "      - tool: " target
  added=1
  next
}
in_graph && /^  [a-zA-Z]/ && !/^    / { in_graph=0; in_run=0 }
{ print }
END {
  if (in_graph && in_run && !added) {
    print "      - tool: " target
  }
}
' "$POLYTOPE_FILE" > "${POLYTOPE_FILE}.tmp" && mv "${POLYTOPE_FILE}.tmp" "$POLYTOPE_FILE"

echo "Successfully added '${TARGET}' to '${GRAPH}' graph"
