#!/bin/bash
# Script to uninstall NVIDIA open-source drivers and related packages.

echo "================================================================================"
echo "Phase B: Driver Reinstallation - Script 02: Uninstall NVIDIA Open-Source Drivers"
echo "================================================================================"
echo "!! IMPORTANT !!"
echo "1. This script MUST be run from a TTY (e.g., Ctrl+Alt+F3)."
echo "2. Ensure your graphical session (Xorg/i3) is STOPPED before running."
echo "   (Switching to TTY from an active i3 session started via .xinitrc should stop it)."
echo "3. This script MUST be run with sudo: sudo bash $(basename $0)"
echo ""
echo "Purpose: Removes existing NVIDIA open-source drivers and related utilities to"
echo "         prepare for the installation of proprietary NVIDIA drivers."
echo "--------------------------------------------------------------------------------"
echo ""

set -e # Exit immediately if a command exits with a non-zero status.

# Packages to uninstall. This list was based on previous investigations.
# nvidia-prime is a small script, other container packages might not be in use.
PACKAGES_TO_REMOVE="nvidia-open-dkms nvidia-utils lib32-nvidia-utils nvidia-prime nvidia-settings"
# Removed nvidia-container-toolkit and libnvidia-container as per user confirmation of not using NVIDIA containers.
# If you use NVIDIA containers (e.g. with Docker), you might need to adjust this or reinstall specific container packages later.

echo "This script will attempt to remove the following NVIDIA open-source drivers"
echo "and related packages:"
echo "$PACKAGES_TO_REMOVE"
echo ""
echo "The pacman command will be: sudo pacman -Rns \$PACKAGES_TO_REMOVE"
echo ""
echo "Review the list CAREFULLY. If critical packages like 'xorg-server' or 'mesa'"
echo "are listed for removal (unlikely, but be cautious), ABORT and investigate."
echo "This script uses 'pacman -Rns' which removes specified packages, their"
echo "dependencies not required by other packages, and configuration files."
echo ""
read -p "Are you sure you want to proceed with removing the listed packages? (y/N): " confirmation
echo ""

if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
    echo "Aborted by user."
    exit 1
fi

echo "Proceeding with package removal..."
echo "Executing: sudo pacman -Rns $PACKAGES_TO_REMOVE"
echo ""

# Attempt to remove the packages.
# We don't use --noconfirm here to allow pacman to show its own prompts and allow for a final review.
# The user has already confirmed their intent to this script.
if sudo pacman -Rns $PACKAGES_TO_REMOVE; then
    echo ""
    echo "Packages removed successfully (or were not installed)."
else
    echo ""
    echo "Error during package removal, or some packages were not found."
    echo "Please check the output from pacman above."
    echo "If essential packages (like nvidia-utils from a previous proprietary install) were not found, that might be okay."
    echo "If there were errors removing packages that WERE installed, troubleshoot before proceeding."
    # It's often safe to continue if some packages in the list were not installed.
    # Pacman will report which ones.
fi

echo ""
echo "Uninstallation script finished."
echo "Proceed to script 03_install_amd_drivers.sh next."
echo "================================================================================"
echo ""

# Make the script executable
chmod +x "$0" 