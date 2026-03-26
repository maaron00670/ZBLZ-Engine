#!/bin/bash
# ZBLZ Engine - Build speedhack library
# 
# Prerequisites:
#   sudo apt install gcc build-essential
#
# Usage:
#   ./build.sh
#   ./build.sh install  (installs to ~/.local/lib/zblz/)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}"
INSTALL_DIR="${HOME}/.local/lib/zblz"

echo "=== ZBLZ Speedhack Library Builder ==="
echo ""

# Check for gcc
if ! command -v gcc &> /dev/null; then
    echo "ERROR: gcc not found. Please install build-essential:"
    echo "  sudo apt install build-essential"
    exit 1
fi

# Compile 64-bit version
echo "[1/2] Compiling 64-bit library..."
gcc -shared -fPIC -O2 -o "${OUTPUT_DIR}/libspeedhack.so" "${SCRIPT_DIR}/speedhack.c" -ldl -lpthread
echo "      Created: libspeedhack.so"

# Try to compile 32-bit version (optional)
echo "[2/2] Compiling 32-bit library..."
if gcc -m32 -shared -fPIC -O2 -o "${OUTPUT_DIR}/libspeedhack32.so" "${SCRIPT_DIR}/speedhack.c" -ldl -lpthread 2>/dev/null; then
    echo "      Created: libspeedhack32.so"
else
    echo "      Skipped: 32-bit compilation failed (install gcc-multilib for 32-bit support)"
fi

echo ""
echo "=== Build Complete ==="
echo ""
echo "Library location: ${OUTPUT_DIR}/libspeedhack.so"
echo ""

# Install if requested
if [ "$1" = "install" ]; then
    echo "Installing to ${INSTALL_DIR}..."
    mkdir -p "${INSTALL_DIR}"
    cp "${OUTPUT_DIR}/libspeedhack.so" "${INSTALL_DIR}/"
    if [ -f "${OUTPUT_DIR}/libspeedhack32.so" ]; then
        cp "${OUTPUT_DIR}/libspeedhack32.so" "${INSTALL_DIR}/"
    fi
    echo "Installed!"
    echo ""
    echo "Add this to your Steam launch options:"
    echo "  LD_PRELOAD=\"${INSTALL_DIR}/libspeedhack.so\" SPEED=1.0 ZBLZ_PID=\$\$ %command%"
    echo ""
    echo "Then use the ZBLZ Engine GUI to control speed in real-time!"
else
    echo "To install system-wide, run:"
    echo "  ./build.sh install"
    echo ""
    echo "Or use directly with:"
    echo "  LD_PRELOAD=\"${OUTPUT_DIR}/libspeedhack.so\" SPEED=2.0 %command%"
fi
