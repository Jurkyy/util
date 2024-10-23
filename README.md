# util

Personal Linux utility scripts and configuration manager. Primarily focused on managing dotfiles and system configurations with automated backup and symlinking.

NOTE: I also use this repo to store my own scripts and dotfiles, so be aware of that when cloning.

## Config Manager

The heart of this repository is a robust configuration management system that handles:

- Individual dotfiles (`.zshrc`, `.bashrc`, etc.)
- Complete config directories (`~/.config/nvim`, etc.)
- Nested configurations with proper path handling
- Automatic backups with timestamps
- Quickly setting up via restore
- Interactive menu system for easy management
- Bulk operations support

### Usage

```bash
# Add a single dotfile
./scripts/manage_dotfiles.py add ~/.zshrc

# Add entire configuration directories
./scripts/manage_dotfiles.py add ~/.config/nvim
./scripts/manage_dotfiles.py add ~/.config/alacritty

# Backup configurations
./scripts/manage_dotfiles.py backup              # Interactive menu
./scripts/manage_dotfiles.py backup .zshrc       # Specific config
./scripts/manage_dotfiles.py backup --name save1 # Custom backup name

# Restore configurations
./scripts/manage_dotfiles.py restore             # Interactive menu
./scripts/manage_dotfiles.py restore .zshrc      # Specific config
./scripts/manage_dotfiles.py restore             # Select 'Restore all' for bulk restore

# List all managed configurations
./scripts/manage_dotfiles.py list
```

### Interactive Features

The config manager now includes an interactive menu system:

1. Backup operations:

   ```
   Backup options:
   > Backup all
   > Select specific config to backup
   > Cancel
   ```

2. Restore operations:

   ```
   Restore options:
   > Restore all
   > Select specific config to restore
   > Cancel
   ```

- Navigate with arrow keys
- Select with Enter
- Exit with Ctrl+C
- Custom backup names supported

### Features

- ✨ Maintains directory structure
- 🔄 Creates symbolic links automatically
- 📦 Preserves original paths
- 🔒 Automatic backups before any operation
- 🌳 Tree-style visualization of managed files
- 🏗️ Creates parent directories as needed
- 🎯 Interactive selection menus
- 📦 Bulk backup/restore operations
- 🏷️ Custom backup naming

[Previous Additional Utilities section remains the same]

## Structure

```
.
├── dotfiles/           # Stored configurations
├── dotfiles_backup/    # Automatic backups with timestamps/names
├── scripts/
│   ├── manage_dotfiles.py  # Config management system
│   ├── load_env.sh         # Environment loader
│   ├── ask_claude.py       # AI interface
│   └── start_tmux.sh       # TMux starter
├── pixi.lock
└── pyproject.toml
```

## Setup

This project uses [Pixi](https://pixi.sh) for environment and dependency management.

1. Install Pixi:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

2. Install direnv (recommended):

```bash
# Debian/Ubuntu
sudo apt install direnv

# MacOS
brew install direnv

# Add to your shell config (~/.zshrc, ~/.bashrc, etc.):
eval "$(direnv hook zsh)"  # or bash/fish/etc.
```

3. Clone the repository:

```bash
git clone git@github.com:Jurkyy/util.git
cd util
```

4. Set up direnv (recommended):

```bash
# Create .envrc file
echo "watch_file pixi.lock\n
eval "$(pixi shell-hook)"" > .envrc

# Allow direnv for this directory
direnv allow
```

This will automatically activate the Pixi environment when you enter the directory.

5. Or manually activate Pixi environment:

```bash
pixi shell
```

6. Make scripts executable:

```bash
chmod +x scripts/*
```

7. Initialize config management:

```bash
# Start by adding your most important configs
./scripts/manage_dotfiles.py add ~/.zshrc
./scripts/manage_dotfiles.py add ~/.config/nvim
```

### Why Pixi with direnv?

Pixi manages project dependencies and creates isolated environments, while direnv automatically activates/deactivates these environments when you enter/exit the project directory. This combination ensures:

- Consistent development environment
- Automatic environment activation
- Isolated project dependencies
- Cross-platform compatibility

For more information about using Pixi with direnv, see the [official documentation](https://pixi.sh/dev/features/environment/#using-pixi-with-direnv).

If you want to manage the dependencies yourself, please checkout the `pyproject.toml`.  

## Backup System

The backup system now offers more flexibility:

- **Automatic Backups**: Created before any modification
- **Manual Backups**: Create on-demand backups with custom names
- **Bulk Backups**: Backup all configs at once
- **Timestamp Format**: `filename_YYYYMMDD_HHMMSS`
- **Custom Names**: Use `--name` flag or interactive prompt

Example backup structure:

```
dotfiles_backup/
├── zshrc_20240423_143022          # Automatic backup
├── zshrc_pre_update               # Custom named backup
└── config/
    └── nvim_20240423_143022/      # Directory backup
    └── nvim_experimental/         # Custom named directory backup
```

## Best Practices

1. Add new configurations:

   ```bash
   ./scripts/manage_dotfiles.py add ~/.new_config
   ```

2. Create named backups before major changes:

   ```bash
   ./scripts/manage_dotfiles.py backup --name pre_update
   ```

3. Check status regularly:

   ```bash
   ./scripts/manage_dotfiles.py list
   ```

4. Restore after fresh install:

   ```bash
   # Interactive restore all
   ./scripts/manage_dotfiles.py restore
   # Select "Restore all" from the menu
   ```

## Note

This is a personal utility repository; scripts and configurations are tailored for Debian systems (because it is what I like using) but can be adapted for other Unix-like environments.
