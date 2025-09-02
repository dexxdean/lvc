#!/bin/bash

# Logic Voice Control - Setup Script
# This script sets up the development environment

echo "======================================"
echo "  Logic Voice Control Setup"
echo "  Version: 0.0.1"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | sed 's/Python //' | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python $REQUIRED_VERSION or higher required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "This may take a few minutes..."

# Install PyAudio dependencies for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing macOS audio dependencies..."
    brew list portaudio &>/dev/null || brew install portaudio
fi

# Install Python packages
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install some dependencies${NC}"
    echo "Please check the error messages above"
    exit 1
fi

# Download Whisper model
echo ""
echo "Downloading Whisper model (small)..."
python3 -c "import whisper; whisper.load_model('small')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Whisper model downloaded${NC}"
else
    echo -e "${YELLOW}⚠ Could not download Whisper model (will download on first run)${NC}"
fi

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p logs
mkdir -p models/wake_words
mkdir -p debug/audio
mkdir -p output
echo -e "${GREEN}✓ Directories created${NC}"

# Copy environment file
echo ""
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Environment file created${NC}"
    echo -e "${YELLOW}  Please edit .env to configure your settings${NC}"
else
    echo -e "${YELLOW}⚠ Environment file already exists${NC}"
fi

# Test audio setup
echo ""
echo "Testing audio setup..."
python3 -c "import sounddevice as sd; print(f'Default input device: {sd.query_devices(kind=\"input\")[\"name\"]}')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Audio system accessible${NC}"
else
    echo -e "${YELLOW}⚠ Could not access audio system${NC}"
fi

# Final instructions
echo ""
echo "======================================"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your settings"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python cli.py --help"
echo "4. Start with: python cli.py --dry-run"
echo ""
echo "For testing without Logic Pro:"
echo "  python cli.py --dry-run --verbose"
echo ""
echo "======================================"
