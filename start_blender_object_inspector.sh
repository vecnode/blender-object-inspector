#!/bin/bash

# Blender Object Inspector - Startup Script
# This script detects Linux, checks for Blender, and starts a Blender project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Blender Object Inspector - Startup Script"
echo "=========================================="

# Step 1: Detect if Linux
echo -n "Checking OS: "
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "linux-musl"* ]]; then
    echo -e "${GREEN}Linux detected ✓${NC}"
else
    echo -e "${RED}Error: This script is designed for Linux systems${NC}"
    echo "Detected OS type: $OSTYPE"
    exit 1
fi

# Step 2: Check if Blender is installed
echo -n "Checking for Blender installation: "

BLENDER_PATH=""
if command -v blender &> /dev/null; then
    # Blender found in PATH
    BLENDER_PATH=$(command -v blender)
    echo -e "${GREEN}Found in PATH${NC}"
    echo "  Location: $BLENDER_PATH"
elif [ -f "/usr/bin/blender" ]; then
    BLENDER_PATH="/usr/bin/blender"
    echo -e "${GREEN}Found at /usr/bin/blender${NC}"
elif [ -f "/usr/local/bin/blender" ]; then
    BLENDER_PATH="/usr/local/bin/blender"
    echo -e "${GREEN}Found at /usr/local/bin/blender${NC}"
elif [ -d "$HOME/blender" ]; then
    # Try to find blender executable in ~/blender directory
    BLENDER_PATH=$(find "$HOME/blender" -name "blender" -type f -executable 2>/dev/null | head -n 1)
    if [ -n "$BLENDER_PATH" ]; then
        echo -e "${GREEN}Found in $HOME/blender${NC}"
        echo "  Location: $BLENDER_PATH"
    fi
fi

if [ -z "$BLENDER_PATH" ]; then
    echo -e "${RED}Blender not found!${NC}"
    echo ""
    echo "Please install Blender using one of the following methods:"
    echo "  - Ubuntu/Debian: sudo apt-get install blender"
    echo "  - Fedora: sudo dnf install blender"
    echo "  - Arch: sudo pacman -S blender"
    echo "  - Or download from: https://www.blender.org/download/"
    exit 1
fi

# Get Blender version for confirmation
echo -n "Verifying Blender version: "
BLENDER_VERSION=$($BLENDER_PATH --version 2>/dev/null | head -n 1 || echo "unknown")
echo -e "${GREEN}$BLENDER_VERSION${NC}"

# Step 3: Start Blender project
echo ""
echo "Starting Blender project"
echo "============================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/blender/load_object1.py"
BLEND_FILE="$SCRIPT_DIR/blender/main.blend"
GLB_FILE="$SCRIPT_DIR/3d/object1.glb"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}Error: Python script not found at $PYTHON_SCRIPT${NC}"
    exit 1
fi

# Check if the main.blend file exists
if [ ! -f "$BLEND_FILE" ]; then
    echo -e "${YELLOW}Warning: main.blend file not found at $BLEND_FILE${NC}"
    echo "Creating new project file..."
    # Create empty blend file if it doesn't exist
    touch "$BLEND_FILE"
fi

# Check if the .glb file exists
if [ ! -f "$GLB_FILE" ]; then
    echo -e "${YELLOW}Warning: GLB file not found at $GLB_FILE${NC}"
    echo "Blender will start but may not import the object."
else
    echo -e "${GREEN}Found GLB file: 3d/object1.glb${NC}"
fi

# Start Blender with main.blend and Python script to create scene and import object
echo -e "${GREEN}Starting Blender with main.blend${NC}"
echo "  - Opening project: blender/main.blend"
echo "  - Creating/using scene: object_1"
echo "  - Importing: 3d/object1.glb"
echo "  - Running Python script: blender/load_object1.py"
echo ""
echo -e "${YELLOW}Note: Python script output will appear in Blender's console${NC}"
echo -e "${YELLOW}To see it: In Blender, go to Window > Toggle System Console${NC}"
echo ""

# Start Blender with main.blend file and Python script
# The script will run after the blend file is loaded
# We keep it in foreground temporarily to catch any immediate errors
# Then background it if needed - but first let's try without & to see output
echo -e "${GREEN}Launching Blender...${NC}"
echo "============================================================"

# Run Blender and capture output
"$BLENDER_PATH" "$BLEND_FILE" --python "$PYTHON_SCRIPT" 2>&1 | tee /tmp/blender_output.log &
BLENDER_PID=$!

echo -e "${GREEN}Blender started (PID: $BLENDER_PID)${NC}"
echo "Python script output is being logged to: /tmp/blender_output.log"
echo ""
echo "To view the log in real-time, run in another terminal:"
echo "  tail -f /tmp/blender_output.log"
echo ""
echo -e "${YELLOW}Or check Blender's console: Window > Toggle System Console${NC}"

