#!/bin/bash
# Script to back up essential configuration files before a graphics driver change.

echo "================================================================================"
echo "Phase A: Preparation - Script 01: Backup Configurations"
echo "================================================================================"
echo "This script backs up key configuration files to a timestamped directory inside"
echo "$HOME/dotfiles/migrate-graphic-drivers/config_backups/."
echo "The backup will emulate the original directory structure."
echo ""
echo "It is recommended to run this as your normal user."
echo ""
echo "Review the CONFIG_PATHS array in this script to ensure it covers all files"
echo "and directories critical to you."
echo ""
echo "General Precautions for the Entire Driver Change Process:"
echo "1. TTY Access: Ensure you are comfortable using a TTY (e.g., Ctrl+Alt+F3)."
echo "   This is crucial if the graphical interface doesn't start later."
echo "2. Backups: This script is one part. Ensure ALL important personal data is"
echo "   backed up separately if not covered by your dotfiles strategy."
echo "3. Read Scripts: Always review scripts before running, especially with sudo."
echo "4. Order & Patience: Follow all steps carefully and in order."
echo "5. Arch Wiki: Refer to it for deeper understanding or troubleshooting."
echo "   (NVIDIA, PRIME, AMDGPU, Xorg articles)."
echo "--------------------------------------------------------------------------------"
echo ""
read -n 1 -s -r -p "Press any key to continue with the backup process, or Ctrl+C to abort..."
echo ""
echo ""

set -e # Exit immediately if a command exits with a non-zero status.

# Resolve HOME for the script's execution context, then define backup base relative to that.
SCRIPT_HOME="$(eval echo ~$USER)" # More robust way to get current user's home
BACKUP_BASE_DIR="$SCRIPT_HOME/dotfiles/migrate-graphic-drivers/config_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$BACKUP_BASE_DIR/pre_driver_change_$TIMESTAMP"
CURRENT_USER=$(whoami) # Get current username for home directory path in backup

# --- Configuration Paths to Backup ---
# Paths are resolved relative to $SCRIPT_HOME for user files, or absolute for system files.
CONFIG_PATHS=(
    # System-wide configurations
    "/etc/X11"
    "/etc/default/grub"
    "/etc/mkinitcpio.conf"

    # User-specific configurations from .cursorrules and common dotfiles
    # Main component config files/dirs (capturing whole dirs for safety)
    "$SCRIPT_HOME/.config/i3"                   # For i3wm config
    "$SCRIPT_HOME/.config/polybar"              # For polybar config & scripts
    "$SCRIPT_HOME/.config/nvim"                 # For neovim config
    "$SCRIPT_HOME/.Xresources"                  # For urxvt, X11 resources
    "$SCRIPT_HOME/.config/rofi"                 # For rofi config & themes
    "$SCRIPT_HOME/.config/picom"                # For picom compositor config
    "$SCRIPT_HOME/.config/dunst"                # For dunst notification config
    "$SCRIPT_HOME/.xinitrc"                     # For X11 session startup
    "$SCRIPT_HOME/.config/libinput-gestures.conf"
    "$SCRIPT_HOME/.config/conky"                # For conky configs (e.g. conky.conf)
    "$SCRIPT_HOME/.conkyrc"                     # Fallback if .conkyrc is directly in HOME

    # Shell profiles
    "$SCRIPT_HOME/.zshrc"
    "$SCRIPT_HOME/.bashrc"
    "$SCRIPT_HOME/.bash_profile"
    
    # Add any other critical files or directories here, e.g.:
    # "$SCRIPT_HOME/.config/some_other_app"
    # "/etc/some_other_service.conf"
)

echo "Creating backup destination: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo "Starting backup process..."

for SOURCE_PATH_ORIG in "${CONFIG_PATHS[@]}"; do
    # Expand ~ or $HOME in SOURCE_PATH_ORIG to an absolute path
    # Using eval for robust tilde expansion, though $SCRIPT_HOME is already absolute.
    # This handles cases where a path might literally be "~/.config/foo" in the array.
    eval SOURCE_PATH="$SOURCE_PATH_ORIG"

    TARGET_SUBPATH=""
    # Determine the target subpath within the backup directory
    if [[ "$SOURCE_PATH" == "$SCRIPT_HOME/"* ]]; then
        # Path is in user's home directory
        path_in_home="${SOURCE_PATH#"$SCRIPT_HOME/"}" # Remove $SCRIPT_HOME/ prefix
        TARGET_SUBPATH="home_${CURRENT_USER}/${path_in_home}"
    elif [[ "$SOURCE_PATH" == /* ]]; then
        # Absolute path not in home (e.g. /etc/X11)
        # Remove leading / to make it relative to BACKUP_DIR
        TARGET_SUBPATH="${SOURCE_PATH#/}"
    else
        echo "Warning: Path '$SOURCE_PATH_ORIG' (expanded to '$SOURCE_PATH') is not an absolute path. Skipping."
        continue
    fi

    DEST_PATH="$BACKUP_DIR/$TARGET_SUBPATH"

    if [ -e "$SOURCE_PATH" ]; then
        echo "Backing up '$SOURCE_PATH' to '$DEST_PATH'..."
        # Create the parent directory structure for the destination
        mkdir -p "$(dirname "$DEST_PATH")"
        # Copy the file or directory. -L dereferences symlinks (copies actual files).
        # -a preserves attributes and copies recursively for directories.
        cp -aL "$SOURCE_PATH" "$DEST_PATH"
    else
        echo "Warning: Source path '$SOURCE_PATH' does not exist. Skipping."
    fi
done

echo ""
echo "Backup completed in: $BACKUP_DIR"
echo "The directory structure within the backup should mirror the original paths."
echo "Please verify the contents of the backup directory."
echo "Consider committing relevant parts of this backup to your main dotfiles repository if this script is for a one-time migration."
echo "================================================================================"
echo ""

# Make the script executable
chmod +x "$0" 