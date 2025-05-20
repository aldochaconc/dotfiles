#!/bin/bash
# Script to verify the NVIDIA proprietary driver and hybrid graphics setup.

echo "================================================================================="
echo "Phase D: Verification - Script 06: Verify Graphics Setup"
echo "================================================================================="
echo "!! IMPORTANT !!"
echo "1. This script MUST be run AFTER rebooting the system from script 05."
echo "2. This script should be run as your NORMAL USER (no sudo required initially)."
echo "3. Ensure you are in a graphical session (e.g., i3 started via .xinitrc)."
echo ""
echo "Purpose: Checks various aspects of the system to confirm that the NVIDIA"
echo "         proprietary drivers are loaded, hybrid graphics (PRIME) is functional,"
echo "         and there are no obvious errors."
echo "---------------------------------------------------------------------------------"
echo ""

# Function to prompt before continuing
press_any_key_to_continue() {
    echo ""
    read -n 1 -s -r -p "Press any key to continue to the next check..."
    echo ""
    echo "---------------------------------------------------------------------------------"
}

press_any_key_to_continue

echo "Step 1: Check Loaded Kernel Modules (NVIDIA vs Nouveau)"
echo "---------------------------------------------------------------------------------"
echo "We expect to see 'nvidia' modules loaded and NO 'nouveau' modules."
echo "Command: lsmod | grep -E \"nvidia|nouveau\" | cat"
lsmod | grep -E "nvidia|nouveau" | cat
MODULES_OUTPUT=$(lsmod | grep -E "nvidia|nouveau")
if echo "$MODULES_OUTPUT" | grep -q "nvidia"; then
    echo "INFO: 'nvidia' module(s) found. This is good."
else
    echo "WARNING: 'nvidia' module(s) NOT found. This could indicate a problem."
fi
if echo "$MODULES_OUTPUT" | grep -q "nouveau"; then
    echo "WARNING: 'nouveau' module is still loaded! This is not expected and can cause conflicts."
    echo "         Ensure it was blacklisted correctly in script 05 and you rebooted."
else
    echo "INFO: 'nouveau' module not found. This is good."
fi
press_any_key_to_continue

echo "Step 2: Check Xorg Providers (AMD/modesetting and NVIDIA)"
echo "---------------------------------------------------------------------------------"
echo "Checking Xorg providers. Expecting AMD/modesetting (primary, e.g., Provider 0) and NVIDIA."
echo "Command: xrandr --listproviders | cat"
xrandr --listproviders | cat
XRANDR_OUTPUT=$(xrandr --listproviders)

HAS_AMD=$(echo "$XRANDR_OUTPUT" | grep -q -i -E "AMD|amdgpu|modesetting"; echo $?)
HAS_NVIDIA=$(echo "$XRANDR_OUTPUT" | grep -q -i "NVIDIA"; echo $?)

if [ "$HAS_AMD" -eq 0 ] && [ "$HAS_NVIDIA" -eq 0 ]; then
    echo "INFO: Both AMD/modesetting and NVIDIA providers are listed by xrandr. This is the expected outcome."
    # Check if AMD/modesetting is Provider 0
    if echo "$XRANDR_OUTPUT" | grep -i "Provider 0:" | grep -q -i -E "AMD|amdgpu|modesetting"; then
        echo "INFO: AMD/modesetting appears to be Provider 0, which is correct for primary."
    else
        echo "WARNING: AMD/modesetting is present but does not appear to be Provider 0. Review 'xrandr --listproviders' output carefully."
    fi
elif [ "$HAS_AMD" -eq 0 ]; then
    echo "WARNING: Only AMD/modesetting provider found. NVIDIA provider is missing. Check Xorg logs, NVIDIA driver installation, and blacklist status."
elif [ "$HAS_NVIDIA" -eq 0 ]; then
    echo "WARNING: Only NVIDIA provider found. AMD/modesetting provider is missing. Check Xorg logs, amdgpu driver installation (mkinitcpio), and 10-gpu-setup.conf."
else
    echo "ERROR: Could not find AMD/modesetting or NVIDIA providers with xrandr. Xorg might not be running correctly, or drivers are not loaded/configured properly."
fi
press_any_key_to_continue

echo "Step 3: Check OpenGL Renderer (AMD iGPU - Default)"
echo "---------------------------------------------------------------------------------"
echo "Checking default OpenGL renderer (expected: AMD)."
echo "Command: glxinfo | grep \"OpenGL renderer string\" | cat"
GLX_AMD_OUTPUT=$(glxinfo | grep "OpenGL renderer string")
echo "$GLX_AMD_OUTPUT" | cat
if echo "$GLX_AMD_OUTPUT" | grep -q -i "AMD"; then # Check for AMD, Radeon, or similar names
    echo "INFO: OpenGL renderer appears to be AMD. This is correct for the default session."
else
    echo "WARNING: OpenGL renderer does NOT appear to be AMD. It shows: $GLX_AMD_OUTPUT"
    echo "         This could indicate an issue with the Xorg configuration or AMD drivers."
fi
press_any_key_to_continue

echo "Step 4: Check OpenGL Renderer (NVIDIA dGPU - PRIME Render Offload)"
echo "---------------------------------------------------------------------------------"
echo "Checking PRIME offload OpenGL renderer (expected: NVIDIA)."
echo "Command: prime-run glxinfo | grep \"OpenGL renderer string\" | cat"
GLX_NVIDIA_OUTPUT=$(prime-run glxinfo | grep "OpenGL renderer string")
echo "$GLX_NVIDIA_OUTPUT" | cat
if echo "$GLX_NVIDIA_OUTPUT" | grep -q -i "NVIDIA"; then # Check for NVIDIA, GeForce, or similar names
    echo "INFO: OpenGL renderer via prime-run appears to be NVIDIA. PRIME offload is working."
else
    echo "WARNING: OpenGL renderer via prime-run does NOT appear to be NVIDIA. It shows: $GLX_NVIDIA_OUTPUT"
    echo "         PRIME render offload might not be working. Check NVIDIA drivers and Xorg setup."
fi
press_any_key_to_continue

echo "Step 5: Check NVIDIA GPU Status with nvidia-smi"
echo "---------------------------------------------------------------------------------"
echo "Checking NVIDIA GPU status with nvidia-smi."
echo "Command: nvidia-smi | cat"
nvidia-smi | cat
if [ $? -ne 0 ]; then
    echo "ERROR: nvidia-smi command failed. This indicates a problem with the NVIDIA driver or its communication."
else
    echo "INFO: nvidia-smi executed. Review the output for GPU details, temperature, and processes."
    echo "      If you see 'Failed to initialize NVML: Driver/library version mismatch', a reboot might still be pending or there was an issue during DKMS build/install."
fi
press_any_key_to_continue

echo "Step 6: Check Xorg Log for Errors"
echo "---------------------------------------------------------------------------------"
echo "Checking Xorg log for errors/warnings ((EE) or (WW))."
echo "Common locations: /var/log/Xorg.0.log or ~/.local/share/xorg/Xorg.0.log"
XORG_LOG1="/var/log/Xorg.0.log"
XORG_LOG2="$HOME/.local/share/xorg/Xorg.0.log"
TARGET_XORG_LOG=""

if [ -f "$XORG_LOG1" ]; then
    TARGET_XORG_LOG="$XORG_LOG1"
elif [ -f "$XORG_LOG2" ]; then
    TARGET_XORG_LOG="$XORG_LOG2"
fi

if [ -n "$TARGET_XORG_LOG" ]; then
    echo "INFO: Found Xorg log at: $TARGET_XORG_LOG"
    echo "Command: grep -E \"\(EE\)|\(WW\)\" \"$TARGET_XORG_LOG\" | tail -n 20 | cat"
    grep -E "\(EE\)|\(WW\)" "$TARGET_XORG_LOG" | tail -n 20 | cat
    echo ""
    echo "Review the output above. (WW) are warnings, (EE) are errors."
    echo "Some warnings are normal, but errors (EE) should be investigated."

    echo ""
    echo "Checking specifically for 'flip' or 'present' related messages in Xorg log (last 30 lines):"
    echo "Command: grep -i -E 'flip|present' \"$TARGET_XORG_LOG\" | tail -n 30 | cat"
    grep -i -E 'flip|present' "$TARGET_XORG_LOG" | tail -n 30 | cat
else
    echo "WARNING: Could not find Xorg.0.log at common locations."
fi
press_any_key_to_continue

echo "Step 7: Check Kernel Log (dmesg) for Errors"
echo "---------------------------------------------------------------------------------"
echo "Checking kernel log (dmesg) for GPU/DRM related messages (nvidia, amdgpu, drm, error)."
echo "Command: sudo dmesg | grep -E -i \"nvidia|amdgpu|drm|error\" | tail -n 20 | cat"
echo "You might be prompted for your sudo password for dmesg."
read -n 1 -s -r -p "Press any key to run dmesg (may require sudo password)..."
echo ""
sudo dmesg | grep -E -i "nvidia|amdgpu|drm|error" | tail -n 20 | cat
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to get kernel log via dmesg (perhaps sudo failed or other issue)."
else
    echo "INFO: Kernel log snippet displayed. Look for any error messages related to GPU drivers."
fi
press_any_key_to_continue

echo "================================================================================="
echo "Phase D: Verification - Script 06: COMPLETED"
echo "================================================================================="
echo ""
echo "Verification script finished."
echo "- If all checks above look good (mostly INFO messages, NVIDIA and AMD appearing where expected),"
echo "  your new graphics driver setup is likely working correctly!"
echo "- If you see WARNINGS or ERRORS, carefully review the output and the corresponding log files."
echo "  Consult Arch Wiki NVIDIA, PRIME, and Xorg pages for troubleshooting."
echo "- Remember to test applications that use the GPU, e.g., games with 'prime-run game_executable',"
echo "  and check external display connections if you use them."
echo ""
echo "If significant issues persist, you may need to:
*   Re-check the steps in script 05.
*   Restore backups from script 01 and attempt the process again.
*   Seek help on Arch Linux forums or relevant communities with detailed logs."
echo "---------------------------------------------------------------------------------"

# Make the script executable
chmod +x "$0"

exit 0 