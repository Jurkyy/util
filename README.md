# util

Personal Linux utility scripts and configuration manager. Primarily focused on managing dotfiles and system configurations with automated backup and symlinking.

NOTE: I also use this repo to store my own scripts and dotfiles, so be aware of that when cloning.

## Config Manager

The heart of this repository is a robust configuration management system that handles:

- Individual dotfiles (`.zshrc`, `.bashrc`, etc.)
- Complete config directories (`~/.config/nvim`, etc.)
- Nested configurations with proper path handling
- Automatic backups with timestamps
- One-click restore from backups

### Usage

```bash
# Add a single dotfile
./scripts/manage_dotfiles.py add ~/.zshrc

# Add entire configuration directories
./scripts/manage_dotfiles.py add ~/.config/nvim
./scripts/manage_dotfiles.py add ~/.config/alacritty

# Restore configurations
./scripts/manage_dotfiles.py restore .zshrc
./scripts/manage_dotfiles.py restore .config/nvim

# List all managed configurations
./scripts/manage_dotfiles.py list
```

### Features

- ✨ Maintains directory structure
- 🔄 Creates symbolic links automatically
- 📦 Preserves original paths
- 🔒 Automatic backups before any operation
- 🌳 Tree-style visualization of managed files
- 🏗️ Creates parent directories as needed

## Additional Utilities

### Environment Variable Loader

Load .env files into your shell environment, I recommend putting this into your .zshrc or different shell start file:

```bash
source scripts/load_env.sh ~/.env
list_vars  # Show loaded variables
```

### Claude AI Interface

CLI tool for interacting with Claude AI, useful for asking quick questions on the fly:

```bash
./scripts/ask_claude.py "Your question here"
./scripts/ask_claude.py -p "Write a Python function"  # Programming mode
./scripts/ask_claude.py -i image.jpg "Describe this"  # Image analysis
```

## Structure

```
.
├── dotfiles/           # Stored configurations
├── dotfiles_backup/    # Automatic backups
├── scripts/
│   ├── manage_dotfiles.py  # Config management system
│   ├── load_env.sh         # Environment loader
│   ├── ask_claude.py       # AI interface
│   └── start_tmux.sh       # TMux starter
├── pixi.lock
└── pyproject.toml
```

## Setup

1. Clone the repository:

```bash
git clone git@github.com:Jurkyy/util.git
cd util
```

2. Make scripts executable:

```bash
chmod +x scripts/*
```

3. Initialize config management:

```bash
# Start by adding your most important configs
./scripts/manage_dotfiles.py add ~/.zshrc
./scripts/manage_dotfiles.py add ~/.config/nvim
```

## Backup System

Backups are automatically created in `dotfiles_backup/` with timestamps:

- Before any file/directory is modified
- When restoring configurations
- When adding new dotfiles

Example backup structure:

```
dotfiles_backup/
├── zshrc_20240423_143022
└── config/
    └── nvim_20240423_143022/
```

## Best Practices

1. Add new configurations:

   ```bash
   ./scripts/manage_dotfiles.py add ~/.new_config
   ```

2. Check status regularly:

   ```bash
   ./scripts/manage_dotfiles.py list
   ```

3. Restore after fresh install:

   ```bash
   # Restore your entire configuration
   for config in $(./scripts/manage_dotfiles.py list | grep "^-" | cut -d" " -f2); do
       ./scripts/manage_dotfiles.py restore "$config"
   done
   ```

## Note

This is a personal utility repository; scripts and configurations are tailored for Debian systems (because it is what I like using) but can be adapted for other Unix-like environments.
