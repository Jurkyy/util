# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH
export PATH="$HOME/.local/bin:$PATH"

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="powerlevel10k/powerlevel10k"
typeset -g POWERLEVEL9K_INSTANT_PROMPT=off
# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-vi-mode ssh-agent)
# doing this via brew cuz this shit don work
source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# Aliases
alias zshrc="nvim ~/.zshrc"

alias gb="git switch -c"
alias gs="git status"
alias gd="git diff ."
alias pd="git_pull_default_branch"

alias n="nvim"
alias g="git"

alias woto="cd ~/projects/woto"
alias ca="cd ~/projects/code-avonturen"
alias util="cd ~/projects/util"
alias docs="cd /mnt/c/Users/wolfb/Documents/!Personal"
alias uni="cd /mnt/c/Users/wolfb/Documents/!Uni"
alias bat="batcat"
alias ask="nvim -c \"PChatNew\""
alias catclip='f() { cat "$@" | xclip -selection clipboard; }; f'

alias pic="pic" 
alias pii="pixi add" # rework into func such that it restart "pixi shell"
alias pir="pixi run python" #Might be useless

alias st="~/starttmux.sh"
alias ls="eza -l --group-directories-first -s date"
alias ll="eza -al --group-directories-first -s date"

# Functions
function pic() {
  # Display the prompt using echo
  echo -n "Enter your project name: "
  # Read the user's input
  read project_name

  # Check if the project name is empty
  if [ -z "$project_name" ]; then
    echo "Project name cannot be empty. Aborting."
    return 1 # Exit the function with an error status
  fi

  # Run the pixi init command with the specified project name
  pixi init --format pyproject "$project_name"
}
function git_pull_default_branch() {
  # Check if we are in a git repository
  if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not inside a git repository."
    return 1
  fi

  local branch_to_checkout=""

  # Check if 'main' branch exists locally
  if git show-ref --verify --quiet refs/heads/main; then
    branch_to_checkout="main"
  # If 'main' doesn't exist, check if 'master' branch exists locally
  elif git show-ref --verify --quiet refs/heads/master; then
    branch_to_checkout="master"
  else
    # If neither exists locally, try to find the default branch from origin
    local default_remote_branch
    default_remote_branch=$(git ls-remote --symref origin HEAD | sed -nE 's|^.*refs/heads/(\S+).+$|\1|p')

    if [ -n "$default_remote_branch" ]; then
      echo "Neither 'main' nor 'master' found locally. Checking out default branch from origin: '$default_remote_branch'."
      branch_to_checkout="$default_remote_branch"
    else
      echo "Could not determine a default branch to checkout (neither 'main', 'master' nor origin/HEAD found)."
      echo "Running git pull on the current branch."
      git pull
      return 0
    fi
  fi

  # Checkout the determined branch if it's not the current branch
  local current_branch
  current_branch=$(git rev-parse --abbrev-ref HEAD)

  if [ "$branch_to_checkout" != "$current_branch" ]; then
    if git checkout "$branch_to_checkout"; then
      echo "Checked out branch '$branch_to_checkout'."
    else
      echo "Error: Could not checkout branch '$branch_to_checkout'."
      return 1
    fi
  else
    echo "Already on branch '$branch_to_checkout'."
  fi

  # Finally, run git pull
  echo "Running git pull..."
  git pull
}

function acp() {
	git add .
	git commit -am "$1"
	if [ -z "$2" ]
		then
			git push
		else
			git push -u origin $(git rev-parse --abbrev-ref HEAD)
	fi
}

function gitinit() {
    # Check if gh (GitHub CLI) is installed
    if ! command -v gh &> /dev/null; then
        echo "GitHub CLI (gh) is not installed. Please install it first:"
        echo "https://cli.github.com/"
        return 1
    fi
    
    # Check if a repository name was provided
    if [ -z "$1" ]; then
        echo "Please provide a repository name"
        return 1
    fi
    
    REPO_NAME="$1"
    
    # Get GitHub username from git config
    GITHUB_USERNAME=$(git config --get github.user)
    if [ -z "$GITHUB_USERNAME" ]; then
        echo "GitHub username not found in git config"
        echo "Please set it with: git config --global github.user YOUR_USERNAME"
        return 1
    fi
    
    # Create and enter directory
    mkdir -p "$REPO_NAME" || return 1
    cd "$REPO_NAME" || return 1
    
    # Create the repository on GitHub first
    echo "Creating repository on GitHub..."
    gh repo create "$REPO_NAME" --private --confirm || return 1
    
    # Initialize git repository
    git init
    
    # Create and add README if it doesn't exist
    if [ ! -f "README.md" ]; then
        echo "# $REPO_NAME" > README.md
    fi
    
    # Add all files and make initial commit
    git add .
    git commit -m ":tada: Initial commit"
    
    # Rename the default branch to main
    git branch -M main
    
    # Add remote and push
    git remote add origin "git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"
    
    if git push -u origin main; then
        echo "Successfully initialized and pushed to GitHub repository: $REPO_NAME"
        echo "Repository URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
        echo "Local directory: $(pwd)"
    else
        echo "Failed to push to GitHub. Please ensure:"
        echo "1. Your SSH key is properly configured"
        echo "2. You have the correct permissions"
        echo "3. Your GitHub username ($GITHUB_USERNAME) is correct"
        # Return to original directory on failure
        cd - > /dev/null
        return 1
    fi
}
# Load ~/.env files for exports
source ~/projects/util/scripts/load_env.sh ~/.env
list_vars

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

export FZF_DEFAULT_COMMAND='fd --type file --color=always --follow --hidden --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_DEFAULT_OPTS="--ansi"

export NVM_DIR="$HOME/.nvm"
[ -s "/home/linuxbrew/.linuxbrew/opt/nvm/nvm.sh" ] && \. "/home/linuxbrew/.linuxbrew/opt/nvm/nvm.sh"  # This loads nvm
[ -s "/home/linuxbrew/.linuxbrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/home/linuxbrew/.linuxbrew/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

eval "$(atuin init zsh)"
export PATH="$PATH:/home/wolf/.pixi/bin"
eval "$(pixi completion --shell zsh)"

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

eval $(thefuck --alias)

eval "$(direnv hook zsh)"

#ssh agent bullshit to make stuff work when using git across ssh
#eval "$(ssh-agent -s)"
#ssh-add ~/.ssh/id_ed25519

# Prepend system directories to PATH
export PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
