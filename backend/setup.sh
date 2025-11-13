#!/bin/bash

# Setup script for agentic chatbot backend

echo "🚀 Setting up Agentic Chatbot Backend..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  Warning: .env file not found"
    echo "Please edit backend/.env and add your Gemini API key:"
    echo "  GEMINI_API_KEY=your_actual_api_key_here"
    echo ""
    echo "Get your key from: https://makersuite.google.com/app/apikey"
else
    echo ""
    echo "✓ .env file found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  python api.py"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"

