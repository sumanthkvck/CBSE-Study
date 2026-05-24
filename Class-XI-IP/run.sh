#!/bin/bash
echo ""
echo " ===================================="
echo "  IP Learn - Starting..."
echo " ===================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo " ERROR: Python 3 not found."
    echo " Install from https://python.org"
    exit 1
fi

# Install dependencies
echo " Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo ""
echo " Starting app at http://localhost:8501"
echo " Press Ctrl+C to stop."
echo ""
streamlit run app/main.py
