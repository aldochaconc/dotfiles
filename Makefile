DOTFILES := $(shell pwd)
CONFIG   := $(HOME)/.config
HOME_DIR := $(HOME)

# ─────────────────────────────────────────────
#  Colors
# ─────────────────────────────────────────────
RESET  := \033[0m
BOLD   := \033[1m
CYAN   := \033[36m
GREEN  := \033[32m
YELLOW := \033[33m
DIM    := \033[2m

define log_link
	@printf "  $(CYAN)→$(RESET)  %-40s $(DIM)→$(RESET)  %s\n" "$(1)" "$(2)"
endef
define log_unlink
	@printf "  $(YELLOW)✗$(RESET)  %s\n" "$(1)"
endef
define log_skip
	@printf "  $(DIM)–  %s (not a symlink, skipped)$(RESET)\n" "$(1)"
endef
define log_done
	@printf "\n  $(GREEN)$(BOLD)✓ done$(RESET)\n\n"
endef

# ─────────────────────────────────────────────
#  Symlink map: SOURCE (relative) → TARGET
# ─────────────────────────────────────────────
LINKS := \
	"chromium-flags.conf|$(CONFIG)/chromium-flags.conf" \
	"dunst/dunstrc|$(CONFIG)/dunst/dunstrc" \
	"cursor/settings.json|$(CONFIG)/Cursor/User/settings.json" \
	"cursor/keybindings.json|$(CONFIG)/Cursor/User/keybindings.json" \
	"hypr/autostart.conf|$(CONFIG)/hypr/autostart.conf" \
	"hypr/bindings.conf|$(CONFIG)/hypr/bindings.conf" \
	"hypr/envs.conf|$(CONFIG)/hypr/envs.conf" \
	"hypr/hypridle.conf|$(CONFIG)/hypr/hypridle.conf" \
	"hypr/hyprland.conf|$(CONFIG)/hypr/hyprland.conf" \
	"hypr/hyprlock.conf|$(CONFIG)/hypr/hyprlock.conf" \
	"hypr/hyprsunset.conf|$(CONFIG)/hypr/hyprsunset.conf" \
	"hypr/input.conf|$(CONFIG)/hypr/input.conf" \
	"hypr/looknfeel.conf|$(CONFIG)/hypr/looknfeel.conf" \
	"hypr/monitors.conf|$(CONFIG)/hypr/monitors.conf" \
	"hypr/workspaces.conf|$(CONFIG)/hypr/workspaces.conf" \
	"kitty/kitty.conf|$(CONFIG)/kitty/kitty.conf" \
	"mimeapps.list|$(CONFIG)/mimeapps.list" \
	"nvim/lua/config/keymaps.lua|$(CONFIG)/nvim/lua/config/keymaps.lua" \
	"nvim/lua/config/options.lua|$(CONFIG)/nvim/lua/config/options.lua" \
	"nvim/lua/config/autocmds.lua|$(CONFIG)/nvim/lua/config/autocmds.lua" \
	"spotify-launcher.conf|$(CONFIG)/spotify-launcher.conf" \
	"swayosd/config.toml|$(CONFIG)/swayosd/config.toml" \
	"fontconfig/fonts.conf|$(CONFIG)/fontconfig/fonts.conf" \
	"rofi/config.rasi|$(CONFIG)/rofi/config.rasi" \
	"rofi/dmenu-crystal.rasi|$(CONFIG)/rofi/dmenu-crystal.rasi" \
	"walker/config.toml|$(CONFIG)/walker/config.toml" \
	"waybar/config.jsonc|$(CONFIG)/waybar/config.jsonc" \
	"waybar/style.css|$(CONFIG)/waybar/style.css" \
	"zshrc|$(HOME_DIR)/.zshrc"

.PHONY: all link unlink help

all: link

help:
	@printf "\n  $(BOLD)crystal dotfiles$(RESET)\n\n"
	@printf "  $(CYAN)make link$(RESET)    symlink dotfiles → ~/.config\n"
	@printf "  $(CYAN)make unlink$(RESET)  remove symlinks  (files are NOT deleted)\n\n"

link:
	@printf "\n  $(BOLD)$(CYAN)linking dotfiles$(RESET)\n\n"
	@$(foreach entry,$(LINKS), \
		src="$(DOTFILES)/$$(echo $(entry) | cut -d'|' -f1)"; \
		dest="$$(echo $(entry) | cut -d'|' -f2)"; \
		mkdir -p "$$(dirname $$dest)"; \
		if [ -e "$$dest" ] && [ ! -L "$$dest" ]; then \
			printf "  \033[33m⚠\033[0m  %-40s \033[2m%s exists and is not a symlink, skipping\033[0m\n" "$$(echo $(entry) | cut -d'|' -f1)" "$$dest"; \
		else \
			ln -sf "$$src" "$$dest"; \
			printf "  \033[36m→\033[0m  %-40s \033[2m→\033[0m  %s\n" "$$(echo $(entry) | cut -d'|' -f1)" "$$dest"; \
		fi; \
	)
	@printf "\n  \033[32m\033[1m✓ done\033[0m\n\n"

unlink:
	@printf "\n  $(BOLD)$(YELLOW)unlinking dotfiles$(RESET)\n\n"
	@$(foreach entry,$(LINKS), \
		dest="$$(echo $(entry) | cut -d'|' -f2)"; \
		if [ -L "$$dest" ]; then \
			unlink "$$dest"; \
			printf "  \033[33m✗\033[0m  %s\n" "$$dest"; \
		else \
			printf "  \033[2m–  %s (not a symlink, skipped)\033[0m\n" "$$dest"; \
		fi; \
	)
	@printf "\n  \033[32m\033[1m✓ done\033[0m\n\n"
