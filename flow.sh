#!/usr/bin/env bash
set -e

VENV_DIR=".venv"
COMMAND="$1"

# -----------------------------
# Create or activate virtualenv
# -----------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "✅ Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip quietly
python -m pip install --upgrade pip >/dev/null

# -----------------------------
# Ensure required tools exist
# -----------------------------
python -m pip install --quiet build pytest

# -----------------------------
# Functions
# -----------------------------
build_package() {
    echo "🧹 Cleaning previous builds..."
    rm -rf dist build *.egg-info

    echo "📦 Installing project in editable mode..."
    pip install -e .

    echo "📦 Building package..."
    python -m build

    echo "✅ Build complete"
}

run_tests() {
    echo "🧪 Installing project in editable mode..."
    pip install -e .

    echo "🧪 Running tests..."
    pytest -vv
}

# -----------------------------
# Command dispatcher
# -----------------------------
case "$COMMAND" in
    build)
        build_package
        ;;
    test)
        run_tests
        ;;
    run)
        build_package
        echo "Run: $(which hdlr)"
        ./.venv/bin/hdlr
        ;;
    *)
        echo "Usage: $0 {build|test|run}"
        exit 1
        ;;
esac

