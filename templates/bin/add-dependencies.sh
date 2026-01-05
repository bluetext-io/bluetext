#!/bin/sh
set -e

TARGET="${1}"
PACKAGES="${2}"

if [ -z "$TARGET" ] || [ -z "$PACKAGES" ]; then
  echo "Error: Missing required arguments"
  echo "Usage: add-dependencies.sh <target> <packages>"
  exit 1
fi

echo "Adding packages to ${TARGET}: ${PACKAGES}"

cd /target/modules/${TARGET}

# Run the appropriate package manager based on target
case "$TARGET" in
  api)
    echo "Installing uv..."
    apk add --no-cache curl python3
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/root/.local/bin:$PATH"
    echo "Running: uv add ${PACKAGES}"
    uv add ${PACKAGES}
    ;;
  frontend)
    echo "Installing bun..."
    apk add --no-cache curl unzip
    curl -fsSL https://bun.sh/install | sh
    export PATH="/root/.bun/bin:$PATH"
    echo "Running: bun add ${PACKAGES}"
    bun add ${PACKAGES}
    ;;
  *)
    echo "Error: Unknown target '${TARGET}'"
    echo "Supported targets: api, frontend"
    exit 1
    ;;
esac

echo "Successfully added packages to ${TARGET}"
