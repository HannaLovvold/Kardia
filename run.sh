#!/bin/bash
# Kardia - AI Companion GTK4 Application Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚀 Starting Kardia - AI Companion GTK4 Application"
echo "📁 Project directory: $SCRIPT_DIR"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Run the application
cd "$SCRIPT_DIR"
python3 main.py "$@"
