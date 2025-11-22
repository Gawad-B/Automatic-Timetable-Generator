#!/bin/bash

echo "🚀 Starting ATTG - Automatic Timetable Generator"
echo "================================================"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Check if app.js exists
if [ ! -f "static/js/app.js" ]; then
    echo "🔨 Compiling TypeScript..."
    npx tsc
fi

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✨ Starting Flask server..."
echo "🌐 Open your browser at: http://localhost:5000"
echo "📚 Legacy UI available at: http://localhost:5000/old"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python server.py
