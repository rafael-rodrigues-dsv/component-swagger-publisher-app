#!/bin/bash
# ============================================================
#  OpenAPI Documentation Publisher - Auto Execution Script
#  Linux/Mac Shell Script
# ============================================================

echo ""
echo "============================================================"
echo "  OpenAPI Documentation Publisher"
echo "  Auto-setup and Execution"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if .venv exists
if [ -d ".venv" ]; then
    print_info "Virtual environment found at .venv"
    echo ""
else
    print_info "Virtual environment not found. Creating..."
    echo ""

    # Create virtual environment
    python3 -m venv .venv

    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment!"
        print_error "Make sure Python 3 and venv module are installed"
        exit 1
    fi

    print_success "Virtual environment created successfully!"
    echo ""
fi

# Activate virtual environment first
print_info "Activating virtual environment..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    print_error "Failed to activate virtual environment!"
    exit 1
fi

print_success "Virtual environment activated"
echo ""

# Always check and install dependencies
print_info "Checking and installing dependencies from requirements.txt..."
echo ""

python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies!"
    exit 1
fi

print_success "Dependencies are up to date!"
echo ""

# Execute main.py
echo "============================================================"
echo "  Starting OpenAPI Documentation Publisher"
echo "============================================================"
echo ""

python main.py
EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    print_success "Execution completed successfully!"
else
    print_error "Execution failed with exit code: $EXIT_CODE"
fi
echo "============================================================"
echo ""

exit $EXIT_CODE

