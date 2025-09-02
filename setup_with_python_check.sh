#!/bin/bash

# Logic Voice Control - Setup Script with Python Version Check
# This script checks for correct Python version and sets up the environment

echo "======================================"
echo "  Logic Voice Control Setup"
echo "  Version: 0.0.1"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    local version=$($python_cmd --version 2>&1 | sed 's/Python //')
    echo $version
}

# Function to compare versions
version_ge() {
    [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

# Find suitable Python installation
echo "Searching for Python 3.10+..."
PYTHON_CMD=""
PYTHON_VERSION=""

# Check different Python commands
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$(check_python_version $cmd)
        echo -e "  Found $cmd: version $version"
        
        if version_ge "$version" "3.10"; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$version
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}✗ Python 3.10 or higher not found!${NC}"
    echo ""
    echo "Please install Python 3.10+ using one of these methods:"
    echo ""
    echo -e "${BLUE}Option 1: Using Homebrew${NC}"
    echo "  brew install python@3.11"
    echo ""
    echo -e "${BLUE}Option 2: Using pyenv${NC}"
    echo "  brew install pyenv"
    echo "  pyenv install 3.11.7"
    echo "  pyenv global 3.11.7"
    echo ""
    echo -e "${BLUE}Option 3: Download from python.org${NC}"
    echo "  https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Using $PYTHON_CMD (version $PYTHON_VERSION)${NC}"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠ Removing existing virtual environment...${NC}"
    rm -rf venv
fi

$PYTHON_CMD -m venv venv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${RED}✗ Failed to create virtual environment${NC}"
    exit 1
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Verify Python version in venv
VENV_PYTHON_VERSION=$(python --version 2>&1 | sed 's/Python //')
echo -e "${GREEN}✓ Virtual environment activated (Python $VENV_PYTHON_VERSION)${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "This may take a few minutes..."

# Install PyAudio dependencies for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Checking macOS audio dependencies..."
    if ! brew list portaudio &>/dev/null; then
        echo "Installing portaudio..."
        brew install portaudio
    else
        echo -e "${GREEN}✓ portaudio already installed${NC}"
    fi
fi

# Install Python packages
echo "Installing Python packages..."
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
python -c "import whisper; whisper.load_model('small')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Whisper model downloaded${NC}"
else
    echo -e "${YELLOW}⚠ Whisper model will be downloaded on first run${NC}"
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

# Test imports
echo ""
echo "Testing Python imports..."
python -c "
import sys
try:
    import pyaudio
    print('  ✓ PyAudio')
except: 
    print('  ✗ PyAudio')
try:
    import whisper
    print('  ✓ Whisper')
except:
    print('  ✗ Whisper')
try:
    import yaml
    print('  ✓ YAML')
except:
    print('  ✗ YAML')
try:
    import click
    print('  ✓ Click')
except:
    print('  ✗ Click')
try:
    import loguru
    print('  ✓ Loguru')
except:
    print('  ✗ Loguru')
"

# Test audio setup
echo ""
echo "Testing audio setup..."
python -c "
import sounddevice as sd
devices = sd.query_devices()
print(f'Default input: {sd.query_devices(kind=\"input\")[\"name\"]}')
for i, dev in enumerate(devices):
    if 'quantum' in dev['name'].lower() or 'presonus' in dev['name'].lower():
        print(f'✓ Found PreSonus device: {dev[\"name\"]}')
        break
" 2>/dev/null

# Final instructions
echo ""
echo "======================================"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "Virtual environment uses Python $VENV_PYTHON_VERSION"
echo ""
echo "Next steps:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Edit .env file with your settings"
echo "3. Test the setup: python cli.py --help"
echo "4. Run dry test: python cli.py --dry-run --verbose"
echo ""
echo "======================================"
