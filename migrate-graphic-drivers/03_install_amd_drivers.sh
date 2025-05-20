#!/bin/bash
# Script to install/ensure AMD GPU drivers (xf86-video-amdgpu, mesa).

echo "================================================================================"
echo "Phase B: Driver Reinstallation - Script 03: Install/Verify AMD Drivers"
echo "================================================================================"
echo "!! IMPORTANT !!"
echo "1. This script should be run from a TTY (e.g., Ctrl+Alt+F3), especially if"
echo "   major driver changes (like uninstalling NVIDIA) just occurred."
echo "2. This script MUST be run with sudo: sudo bash $(basename $0)"
echo ""
echo "Purpose: Ensures the necessary AMD graphics drivers (xf86-video-amdgpu for Xorg,"
echo "         and mesa for OpenGL/Vulkan) are installed and up-to-date."
echo "         This is important for the iGPU to function correctly."
echo "--------------------------------------------------------------------------------"
echo ""

set -e # Exit immediately if a command exits with a non-zero status.

AMD_PACKAGES="xf86-video-amdgpu mesa lib32-mesa"
# vulkan-radeon and lib32-vulkan-radeon are also important for Vulkan support on AMD.
# Adding them here to ensure they are installed if not already present.
AMD_VULKAN_PACKAGES="vulkan-radeon lib32-vulkan-radeon"

echo "This script will ensure the following AMD graphics packages are installed"
echo "and up-to-date:"
echo "Core Xorg/OpenGL: $AMD_PACKAGES"
echo "Vulkan Support:   $AMD_VULKAN_PACKAGES"
echo ""
echo "The pacman command will be: sudo pacman -Syu --needed \$AMD_PACKAGES \$AMD_VULKAN_PACKAGES"
echo "(--needed ensures packages are only installed if not present or if an update is available)"
echo ""
read -p "Are you sure you want to proceed with installing/updating these AMD packages? (y/N): " confirmation
echo ""

if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
    echo "Aborted by user."
    exit 1
fi

echo "Proceeding with AMD package installation/update..."
echo "Executing: sudo pacman -Syu --needed $AMD_PACKAGES $AMD_VULKAN_PACKAGES"
echo ""

# We don't use --noconfirm with -Syu --needed to allow pacman to show what it will do
# and ask for its own confirmation if packages are to be installed/upgraded.
if sudo pacman -Syu --needed $AMD_PACKAGES $AMD_VULKAN_PACKAGES; then
    echo ""
    echo "AMD graphics packages (including Vulkan support) are installed and/or up-to-date."
else
    echo ""
    echo "Error during AMD graphics package installation/update. Please check the output above."
    exit 1
fi

echo ""
echo "AMD driver script finished."
echo "Proceed to script 04_install_nvidia_proprietary.sh next."
echo "================================================================================"
echo ""

# Make the script executable
chmod +x "$0" 