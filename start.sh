#!/bin/bash

# Logic Voice Control - Start Script

echo "======================================"
echo "  🎙️  LOGIC VOICE CONTROL"
echo "  Version: 0.0.1"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | sed 's/Python //')
echo "📌 Python version: $PYTHON_VERSION"
echo ""

# Start options
echo "How would you like to start?"
echo "1) Test Mode (dry-run, no Logic Pro needed)"
echo "2) Production Mode (requires Logic Pro)"
echo "3) Component Test"
echo "4) Verbose Test Mode (with debug output)"
echo ""
read -p "Select option (1-4): " option

case $option in
    1)
        echo "🧪 Starting in Test Mode..."
        python cli.py --dry-run
        ;;
    2)
        echo "🚀 Starting in Production Mode..."
        python cli.py
        ;;
    3)
        echo "🔧 Running Component Tests..."
        python test_components.py
        ;;
    4)
        echo "🔍 Starting in Verbose Test Mode..."
        python cli.py --dry-run --verbose
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac
