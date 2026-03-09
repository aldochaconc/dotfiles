# Path to your Oh My Zsh installation.
ZSH=/usr/share/oh-my-zsh/

ZSH_THEME="robbyrussell"

plugins=(git nvm)

ZSH_CACHE_DIR=$HOME/.cache/oh-my-zsh
if [[ ! -d $ZSH_CACHE_DIR ]]; then
  mkdir $ZSH_CACHE_DIR
fi
source $ZSH/oh-my-zsh.sh

export NVM_DIR=~/.nvm
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fastfetch

export AWS_PAGER=""
export AWS_CLI_AUTO_PROMPT=off
alias aws='aws --no-cli-pager'
export PATH="$HOME/.local/bin:$PATH"
export PATH="$PATH:$(go env GOPATH)/bin"

# pnpm
export PNPM_HOME="/home/crystal/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

# Source local secrets (tokens, API keys) - not committed to git
[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local
