#!/usr/bin/env bash
set -e

# Repository information
REPO="SPTS7/CodeGrapher"
BIN_NAME="cg"
INSTALL_DIR="/usr/local/bin"

# If the user is not root, install to ~/.local/bin instead
if [ "$EUID" -ne 0 ]; then
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

echo "Installing $BIN_NAME from $REPO..."

# Detect OS and architecture
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

if [ "$OS" = "darwin" ]; then
    OS="macos"
elif [ "$OS" = "linux" ]; then
    OS="ubuntu" # GitHub actions runs on ubuntu-latest
elif [[ "$OS" == *"mingw"* ]] || [[ "$OS" == *"msys"* ]]; then
    OS="windows"
    BIN_NAME="cg.exe"
fi

# Fetch the latest release tag
echo "Fetching latest release information..."
LATEST_RELEASE=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_RELEASE" ]; then
    echo "Error: Could not find the latest release for $REPO."
    echo "Make sure there is a published release on GitHub."
    exit 1
fi

echo "Latest release is $LATEST_RELEASE."

# Construct the download URL
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST_RELEASE/cg-$OS"

echo "Downloading binary for $OS ($ARCH)..."
curl -L -o "$INSTALL_DIR/$BIN_NAME" "$DOWNLOAD_URL"

# Make it executable (except on windows where it's not needed/different)
if [ "$OS" != "windows" ]; then
    chmod +x "$INSTALL_DIR/$BIN_NAME"
fi

echo "========================================================="
echo "Installation complete!"
echo "CodeGrapher is installed at: $INSTALL_DIR/$BIN_NAME"
echo ""
echo "To use it, simply type:"
echo "  cg genmd"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "WARNING: $INSTALL_DIR is not in your PATH."
    echo "You may need to add 'export PATH=\"\$PATH:$INSTALL_DIR\"' to your ~/.bashrc or ~/.zshrc."
fi
echo "========================================================="
