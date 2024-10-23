# Setup fzf
# ---------
if [[ ! "$PATH" == */home/wolf/.fzf/bin* ]]; then
  PATH="${PATH:+${PATH}:}/home/wolf/.fzf/bin"
fi

eval "$(fzf --zsh)"
