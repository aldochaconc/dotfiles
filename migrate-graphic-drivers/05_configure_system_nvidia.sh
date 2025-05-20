#!/bin/bash
# Script to configure system for NVIDIA proprietary drivers (GRUB, Xorg, modprobe, mkinitcpio).

echo "================================================================================="
echo "Phase C: System Configuration - Script 05: Configure System for NVIDIA Drivers"
echo "================================================================================="
echo "!! IMPORTANT !!"
echo "1. This script MUST be run from a TTY (e.g., Ctrl+Alt+F3)."
echo "2. Ensure NVIDIA proprietary drivers (nvidia-dkms) were installed by script 04."
echo "3. This script MUST be run with sudo: sudo bash $(basename $0)"
echo ""
echo "Purpose: Configures GRUB for NVIDIA DRM modesetting, sets up Xorg for hybrid"
echo "         graphics (AMD primary, NVIDIA for offload/external), blacklists the"
echo "         nouveau driver, and rebuilds the initramfs."
echo "---------------------------------------------------------------------------------"
echo ""

# Function to prompt before continuing
press_any_key_to_continue() {
    echo ""
    read -n 1 -s -r -p "Press any key to continue to the next step..."
    echo ""
    echo "---------------------------------------------------------------------------------"
}

# Initial sudo check
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: This script must be run as root. Please use sudo."
  exit 1
fi

echo "Step 1: Configure GRUB for NVIDIA DRM Kernel Mode Setting (KMS)"
echo "---------------------------------------------------------------------------------"
echo "This step will add 'nvidia_drm.modeset=1' to GRUB_CMDLINE_LINUX_DEFAULT"
echo "in /etc/default/grub and then regenerate grub.cfg."
echo "A backup of /etc/default/grub will be made as /etc/default/grub.backup."
press_any_key_to_continue

# Backup existing grub config
if [ -f /etc/default/grub ]; then
    echo "Backing up /etc/default/grub to /etc/default/grub.backup..."
    cp /etc/default/grub /etc/default/grub.backup
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to back up /etc/default/grub. Aborting GRUB modification."
        # Decide if we should exit or just skip this part
    else
        echo "Backup successful."
    fi
else
    echo "Warning: /etc/default/grub not found. Skipping backup."
fi

echo "Modifying /etc/default/grub..."
# Check if nvidia_drm.modeset=1 is already there
if grep -q "nvidia_drm.modeset=1" /etc/default/grub; then
    echo "'nvidia_drm.modeset=1' already present in /etc/default/grub."
else
    # Add it. This is a common way, but might not be robust for all grub configs.
    # It assumes GRUB_CMDLINE_LINUX_DEFAULT is present and ends with a quote.
    sed -i 's/\(GRUB_CMDLINE_LINUX_DEFAULT="[^"]*\)/\1 nvidia_drm.modeset=1"/' /etc/default/grub
    # Fallback if the above didn't work (e.g. if the line was empty GRUB_CMDLINE_LINUX_DEFAULT="")
    if ! grep -q "nvidia_drm.modeset=1" /etc/default/grub; then
        sed -i 's/\(GRUB_CMDLINE_LINUX_DEFAULT="\)/\1nvidia_drm.modeset=1"/' /etc/default/grub
    fi
    echo "'nvidia_drm.modeset=1' added to GRUB_CMDLINE_LINUX_DEFAULT."
fi

echo "Regenerating GRUB configuration (grub.cfg)..."
grub-mkconfig -o /boot/grub/grub.cfg
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to regenerate GRUB configuration. Check for errors above."
    echo "You may need to manually edit /etc/default/grub and run grub-mkconfig -o /boot/grub/grub.cfg"
else
    echo "GRUB configuration updated successfully."
fi
press_any_key_to_continue

echo "Step 2: Create Xorg configuration for AMD/NVIDIA Hybrid Graphics"
echo "---------------------------------------------------------------------------------"
echo "This will create /etc/X11/xorg.conf.d/10-gpu-setup.conf to set the AMD iGPU"
echo "as the primary GPU and enable the NVIDIA dGPU for PRIME render offload and"
echo "its connected outputs (if any)."
press_any_key_to_continue

XORG_CONF_DIR="/etc/X11/xorg.conf.d"
XORG_CONF_FILE="$XORG_CONF_DIR/10-gpu-setup.conf"

mkdir -p "$XORG_CONF_DIR"

echo "Creating $XORG_CONF_FILE..."
cat <<EOF > "$XORG_CONF_FILE"
# /etc/X11/xorg.conf.d/10-gpu-setup.conf
# Sets AMD as PrimaryGPU and allows NVIDIA GPU screens.

Section "OutputClass"
    Identifier "AMD"
    MatchDriver "amdgpu"
    Driver "amdgpu"
    Option "PrimaryGPU" "yes"
EndSection

Section "OutputClass"
    Identifier "NVIDIA"
    MatchDriver "nvidia-drm"
    Driver "nvidia"
    # Option "AllowNVIDIAGPUScreens" # This is often implicit or not needed
                                     # depending on xorg version and setup.
                                     # Add if external monitors on NVIDIA are not working.
    # Option "AllowEmptyInitialConfiguration" # May be needed if NVIDIA has no screens initially.
EndSection

# Potentially add BusID for NVIDIA if issues arise, but usually not needed with Prime.
# You can find BusID with 'lspci | grep -E "VGA|3D"'
# Example:
# Section "Device"
#     Identifier "Nvidia Card"
#     Driver "nvidia"
#     BusID "PCI:X:Y:Z" # Replace X:Y:Z with actual BusID
# EndSection
EOF

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create $XORG_CONF_FILE."
else
    echo "$XORG_CONF_FILE created successfully."
    echo "Review its contents if you have a non-standard setup."
fi
press_any_key_to_continue

echo "Step 3: Blacklist the nouveau driver"
echo "---------------------------------------------------------------------------------"
echo "This will create /etc/modprobe.d/blacklist-nouveau.conf to prevent the"
echo "open-source nouveau driver from loading, which can conflict with the"
echo "proprietary NVIDIA driver."
press_any_key_to_continue

BLACKLIST_FILE="/etc/modprobe.d/blacklist-nouveau.conf"

echo "Creating $BLACKLIST_FILE..."
cat <<EOF > "$BLACKLIST_FILE"
# /etc/modprobe.d/blacklist-nouveau.conf
# Prevents the nouveau driver from loading.
blacklist nouveau
options nouveau modeset=0
EOF

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create $BLACKLIST_FILE."
else
    echo "$BLACKLIST_FILE created successfully."
fi
press_any_key_to_continue

echo "Step 4: Rebuild initramfs"
echo "---------------------------------------------------------------------------------"
echo "This step runs mkinitcpio to rebuild the initial RAM disk. This is important"
echo "to ensure changes to kernel modules (like blacklisting nouveau or new NVIDIA modules)"
echo "are effective at boot."
echo "This will use your default preset (usually /etc/mkinitcpio.d/linux-lts.preset if you use LTS kernel)."
press_any_key_to_continue

echo "Rebuilding initramfs for all installed kernels (e.g., linux-lts)..."
# This command typically rebuilds for all presets found in /etc/mkinitcpio.d/
# e.g., linux.preset, linux-lts.preset, etc.
mkinitcpio -P

if [ $? -ne 0 ]; then
    echo "ERROR: mkinitcpio -P failed. Check for errors above."
    echo "You might need to run 'sudo mkinitcpio -p <your-kernel-preset>' manually (e.g., 'sudo mkinitcpio -p linux-lts')."
else
    echo "Initramfs rebuild completed successfully."
fi
press_any_key_to_continue

echo "================================================================================="
echo "Phase C: System Configuration - Script 05: COMPLETED"
echo "================================================================================="
echo ""
echo "Next steps:"
echo "1. CRITICAL: Reboot your system for all changes to take effect."
echo "   Command: sudo reboot"
echo "2. After rebooting, run script 06_verify_setup.sh (as your normal user, NOT sudo)"
echo "   to check if the drivers and configuration are working as expected."
echo ""
echo "If you encounter issues during boot (e.g., black screen, can't start X):"
echo "  - Try booting with the 'nomodeset' kernel parameter (edit GRUB at boot)."
echo "  - Access a TTY (Ctrl+Alt+F3) to troubleshoot."
echo "  - Review Xorg logs: /var/log/Xorg.0.log (or ~/.local/share/xorg/Xorg.0.log)"
echo "  - Review kernel logs: journalctl -b -k"
echo "  - You might need to revert changes using the backups from script 01 or by"
echo "    booting into a live USB to repair."
echo "---------------------------------------------------------------------------------"

# Make the script executable
chmod +x "$0" # This is not strictly necessary if called with 'bash scriptname.sh'
              # but good practice if one intends to run it directly like './scriptname.sh'

exit 0 