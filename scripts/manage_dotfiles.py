#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import datetime
import argparse
import inquirer
import sys


def handle_keyboard_interrupt():
    """Handle Ctrl+C gracefully"""
    print("\nOperation cancelled by user")
    sys.exit(0)


class DotfileManager:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path).resolve()
        self.dotfiles_dir = self.repo_path / "dotfiles"
        self.backup_dir = self.repo_path / "dotfiles_backup"

    def setup_directories(self):
        """Create necessary directories if they don't exist."""
        self.dotfiles_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def get_relative_path(self, file_path):
        """Get the relative path from home directory."""
        home = Path.home()
        try:
            return file_path.relative_to(home)
        except ValueError:
            return file_path.name

    def backup_existing_path(self, path):
        """Create a backup of an existing file or directory with timestamp."""
        if not path.exists():
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = self.get_relative_path(path)
        backup_path = self.backup_dir / f"{relative_path}_{timestamp}"

        # Create parent directories in backup location
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        if path.is_dir():
            shutil.copytree(path, backup_path, dirs_exist_ok=True)
        else:
            shutil.copy2(path, backup_path)

        return backup_path

    def add_dotfile(self, file_path):
        """Add a dotfile or directory to the repository and create symlinks."""
        file_path = Path(file_path).expanduser().resolve()

        if not file_path.exists():
            print(f"Error: {file_path} does not exist")
            return False

        # Get the path relative to home directory
        relative_path = self.get_relative_path(file_path)
        repo_path = self.dotfiles_dir / relative_path

        # Create parent directories in repo
        repo_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file/directory
        if file_path.exists():
            backup = self.backup_existing_path(file_path)
            if backup:
                print(f"Created backup at {backup}")

        # Handle directories and files
        if file_path.is_dir():
            # Copy directory contents if not already in repo
            if not repo_path.exists():
                shutil.copytree(file_path, repo_path, dirs_exist_ok=True)
                shutil.rmtree(file_path)
            else:
                print(f"Directory already exists in repo: {repo_path}")
        else:
            # Copy file if not already in repo
            if not repo_path.exists():
                shutil.copy2(file_path, repo_path)
                file_path.unlink()

        # Create symlink (handling parent directories)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.exists() and file_path.is_symlink():
            file_path.unlink()
        file_path.symlink_to(repo_path)
        print(f"Created symlink: {file_path} -> {repo_path}")
        return True

    def restore_dotfile(self, file_path):
        """Restore a dotfile or directory from the repository to its original location."""
        # Handle both relative and absolute paths
        if file_path.startswith("/"):
            relative_path = self.get_relative_path(Path(file_path))
        else:
            relative_path = Path(file_path)

        repo_path = self.dotfiles_dir / relative_path
        home_path = Path.home() / relative_path

        if not repo_path.exists():
            print(f"Error: {relative_path} not found in repository")
            return False

        # Backup existing file/directory if it exists
        if home_path.exists() or home_path.is_symlink():
            backup = self.backup_existing_path(home_path)
            if backup:
                print(f"Created backup at {backup}")
            if home_path.is_dir() and not home_path.is_symlink():
                shutil.rmtree(home_path)
            else:
                home_path.unlink()

        # Create parent directories
        home_path.parent.mkdir(parents=True, exist_ok=True)

        # Create symlink
        home_path.symlink_to(repo_path)
        print(f"Restored {relative_path} to {home_path}")
        return True

    def list_dotfiles(self):
        """List all dotfiles in the repository with their symlink status."""
        print("\nManaged dotfiles:")

        def print_tree(directory, prefix=""):
            paths = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            for i, path in enumerate(paths):
                is_last = i == len(paths) - 1
                current_prefix = "└── " if is_last else "├── "

                relative_path = path.relative_to(self.dotfiles_dir)
                home_path = Path.home() / relative_path

                print(f"{prefix}{current_prefix}{relative_path}")

                if home_path.is_symlink():
                    target = home_path.resolve()
                    print(
                        f"{prefix}{'    ' if is_last else '│   '}→ {home_path} -> {target}"
                    )
                else:
                    print(f"{prefix}{'    ' if is_last else '│   '}→ Not linked")

                if path.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(path, new_prefix)

    def get_managed_configs(self):
        """Get list of all managed configurations."""
        configs = []
        for path in self.dotfiles_dir.rglob("*"):
            if path.is_file() or (path.is_dir() and not any(path.iterdir())):
                configs.append(str(path.relative_to(self.dotfiles_dir)))
        return sorted(configs)

    def create_backup(self, config_name, backup_name=None):
        """Create a backup of a managed configuration.

        Args:
            config_name (str): Name of the configuration to backup
            backup_name (str, optional): Custom name for the backup. If None, uses timestamp

        Returns:
            bool: True if backup was successful, False otherwise
        """
        config_path = self.dotfiles_dir / config_name
        if not config_path.exists():
            print(f"Error: Configuration '{config_name}' not found in repository")
            return False

        # Construct home path correctly (handling .config and other nested paths)
        home_path = Path.home() / config_name
        if not home_path.exists():
            print(f"Error: No active configuration at {home_path}")
            return False

        # Create backup with custom name or timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_suffix = backup_name if backup_name else timestamp
        backup_path = self.backup_dir / f"{config_name}_{backup_suffix}"

        # Ensure backup parent directory exists
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if home_path.is_dir():
                shutil.copytree(home_path, backup_path, dirs_exist_ok=True)
            else:
                shutil.copy2(home_path, backup_path)
            print(f"Created backup at {backup_path}")
            return True
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False

            print_tree(self.dotfiles_dir)

    def backup_all(self):
        """Create backups of all managed configurations."""
        configs = self.get_managed_configs()
        backed_up = 0
        failed = 0

        backup_name = None
        questions = [
            inquirer.Text(
                "backup_name",
                message="Enter backup name for all configs (press Enter for timestamp)",
            )
        ]
        try:
            answers = inquirer.prompt(questions)
            if answers is None:  # User pressed Esc/Ctrl+C
                return False
            backup_name = answers["backup_name"]
        except KeyboardInterrupt:
            handle_keyboard_interrupt()

        for config in configs:
            print(f"\nBacking up {config}...")
            if self.create_backup(config, backup_name):
                backed_up += 1
            else:
                failed += 1

        print(f"\nBackup complete: {backed_up} succeeded, {failed} failed")
        return backed_up > 0


def prompt_for_config(manager, message="Select configuration"):
    """Prompt user to select a configuration."""
    configs = manager.get_managed_configs()
    if not configs:
        print("No configurations found in repository")
        return None

    try:
        questions = [
            inquirer.List("config", message=message, choices=configs, carousel=True)
        ]
        answers = inquirer.prompt(questions)
        return answers["config"] if answers else None
    except KeyboardInterrupt:
        handle_keyboard_interrupt()


def show_operation_menu(manager, operation="restore"):
    """Show consistent menu for backup/restore operations."""
    try:
        questions = [
            inquirer.List(
                "choice",
                message=f"{operation.capitalize()} options",
                choices=[
                    f"{operation.capitalize()} all",
                    f"Select specific config to {operation}",
                    "Cancel",
                ],
                carousel=True,
            )
        ]
        answers = inquirer.prompt(questions)
        if answers is None:  # User pressed Esc
            print("\nOperation cancelled by user")
            return None

        return answers["choice"] if answers else None
    except KeyboardInterrupt:
        handle_keyboard_interrupt()


def main():
    parser = argparse.ArgumentParser(
        description="Manage dotfiles and directories with symlinks"
    )
    parser.add_argument(
        "--repo", type=str, default=os.getcwd(), help="Path to the dotfiles repository"
    )
    parser.add_argument(
        "command",
        choices=["add", "restore", "list", "backup"],
        help="Command to execute",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="File/directory to add, restore, or backup (optional for restore/list)",
    )
    parser.add_argument(
        "--name", type=str, help="Custom name for backup (optional, for backup command)"
    )

    args = parser.parse_args()

    manager = DotfileManager(args.repo)
    manager.setup_directories()

    try:
        if args.command == "add":
            if not args.file:
                print("Error: Please specify a file or directory to add")
                return 1
            manager.add_dotfile(args.file)

        elif args.command == "restore":
            if args.file:
                manager.restore_dotfile(args.file)
            else:
                choice = show_operation_menu(manager, "restore")
                if choice == "Restore all":
                    manager.restore_all()
                elif choice == "Select specific config to restore":
                    config = prompt_for_config(
                        manager, "Select configuration to restore"
                    )
                    if config:
                        manager.restore_dotfile(config)

        elif args.command == "backup":
            if args.file:
                manager.create_backup(args.file, args.name)
            else:
                choice = show_operation_menu(manager, "backup")
                if choice == "Backup all":
                    manager.backup_all()
                elif choice == "Select specific config to backup":
                    config = prompt_for_config(
                        manager, "Select configuration to backup"
                    )
                    if config:
                        try:
                            questions = [
                                inquirer.Text(
                                    "backup_name",
                                    message="Enter backup name (press Enter for timestamp)",
                                )
                            ]
                            answers = inquirer.prompt(questions)
                            if answers is None:  # User pressed Esc
                                print("\nOperation cancelled by user")
                                return 0
                            backup_name = (
                                answers.get("backup_name") if answers else None
                            )
                            manager.create_backup(config, backup_name)
                        except KeyboardInterrupt:
                            handle_keyboard_interrupt()

        elif args.command == "list":
            manager.list_dotfiles()

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    main()
