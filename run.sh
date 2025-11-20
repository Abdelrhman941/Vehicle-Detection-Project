#!/bin/bash

# Vehicle Detection System - Launch Script
# Supports optional "deploy" mode"

echo "=========================================="
echo "  Vehicle Detection System - Starting"
echo "=========================================="
echo ""

MODE="$1"   # optional first argument: deploy

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null
then
    echo "❌ Error: Python is not installed or not in PATH"
    exit 1
fi

PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "✓ Using Python: $PYTHON_CMD"
echo ""

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate venv
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "📦 Installing/Updating dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Ensure static directory exists (important for FastAPI front-end)
echo "📁 Checking 'static' directory..."
mkdir -p static
echo "✓ Static directory ready"
echo ""

# Deploy step (only if argument = deploy)
if [ "$MODE" == "deploy" ]; then
    echo "=========================================="
    echo "  🚀 Running DEPLOY steps..."
    echo "=========================================="

    # Deployment logic based on your project tree
    # Example: just confirm static files exist
    if [ -f "static/index.html" ]; then
        echo "✓ Frontend static files found"
    else
        echo "⚠️ Warning: static/index.html not found"
    fi

    echo "✓ Deploy step completed"
    echo ""
fi

# Start server
echo "=========================================="
echo "  🚀 Starting Vehicle Detection Server"
echo "=========================================="
echo "Server at:"
echo "  http://localhost:8000"
echo "  http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

$PYTHON_CMD -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
