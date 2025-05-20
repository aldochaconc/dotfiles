#!/bin/bash
# Script to install NVIDIA proprietary drivers (nvidia-dkms).

echo "================================================================================"
echo "Phase B: Driver Reinstallation - Script 04: Install NVIDIA Proprietary (DKMS) Drivers"
echo "================================================================================"
echo "!! IMPORTANT !!"
echo "1. This script MUST be run from a TTY (e.g., Ctrl+Alt+F3)."
echo "2. Ensure previous NVIDIA drivers (especially nvidia-open-dkms) were uninstalled"
echo "   by script 02, and AMD drivers were verified/installed by script 03."
echo "3. This script MUST be run with sudo: sudo bash $(basename $0)"
echo ""
echo "Purpose: Installs the NVIDIA proprietary drivers using DKMS (nvidia-dkms),"
echo "         along with nvidia-utils, lib32-nvidia-utils, and nvidia-settings."
echo "         The 'nvidia-dkms' package will compile the kernel module for your"
echo "         currently running kernel. Ensure your kernel headers are installed"
echo "         (e.g., linux-lts-headers for the LTS kernel)."
echo "--------------------------------------------------------------------------------"
echo ""

set -e # Exit immediately if a command exits with a non-zero status.

NVIDIA_PROPRIETARY_PACKAGES="nvidia-dkms nvidia-utils lib32-nvidia-utils nvidia-settings"
# Ensure you have the headers for your kernel. For LTS kernel, this is linux-lts-headers.
# The script assumes they are already installed or will be handled by dependencies if not.

echo "This script will install the following NVIDIA proprietary graphics packages:"
echo "$NVIDIA_PROPRIETARY_PACKAGES"
echo ""
echo "The 'nvidia-dkms' package will compile the kernel module against your"
echo "currently running kernel. This process can take some time."
echo "Please ensure you have the correct kernel headers installed (e.g., 'linux-lts-headers')."
echo ""
echo "The pacman command will be: sudo pacman -Syu --needed \$NVIDIA_PROPRIETARY_PACKAGES"
echo "(--needed ensures packages are only installed if not present or if an update is available)"
echo ""
read -p "Are you sure you want to proceed with installing these NVIDIA packages? (y/N): " confirmation
echo ""

if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
    echo "Aborted by user."
    exit 1
fi

echo "Proceeding with NVIDIA proprietary package installation..."
echo "Executing: sudo pacman -Syu --needed $NVIDIA_PROPRIETARY_PACKAGES"
echo "Watch the output carefully for any DKMS build errors."
echo ""

# We use -Syu --needed. --noconfirm is omitted to allow pacman's own review.
if sudo pacman -Syu --needed $NVIDIA_PROPRIETARY_PACKAGES; then
    echo ""
    echo "NVIDIA proprietary graphics packages (nvidia-dkms and utils) installed successfully."
    echo "The DKMS module should have been built and installed for your current kernel."
else
    echo ""
    echo "Error during NVIDIA proprietary package installation. Please check the output above."
    echo "Pay special attention to any errors from DKMS. If DKMS fails, the driver will not load."
    echo "Ensure you have the correct kernel headers installed for your running kernel."
    exit 1
fi

echo ""
echo "NVIDIA proprietary driver installation script finished."
echo "Proceed to script 05_configure_system_nvidia.sh next."
echo "================================================================================"
echo ""

# Make the script executable
chmod +x "$0" 