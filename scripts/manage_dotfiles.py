#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import datetime
import argparse


class DotfileManager:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path).resolve()
        self.dotfiles_dir = self.repo_path / "dotfiles"
        self.backup_dir = self.repo_path / "dotfiles_backup"

    def setup_directories(self):
        """Create necessary directories if they don't exist."""
        self.dotfiles_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def backup_existing_file(self, file_path):
        """Create a backup of an existing file with timestamp."""
        if not file_path.exists():
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{file_path.name}_{timestamp}"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def add_dotfile(self, file_path):
        """Add a dotfile to the repository and create a symlink."""
        file_path = Path(file_path).expanduser().resolve()

        if not file_path.exists():
            print(f"Error: {file_path} does not exist")
            return False

        # Determine the target path in the repo
        repo_file = self.dotfiles_dir / file_path.name

        # Backup existing file in home directory
        if file_path.exists():
            backup = self.backup_existing_file(file_path)
            if backup:
                print(f"Created backup at {backup}")

        # Move the file to the repo if it's not already there
        if not repo_file.exists():
            shutil.copy2(file_path, repo_file)
            file_path.unlink()

        # Create symlink
        file_path.symlink_to(repo_file)
        print(f"Created symlink: {file_path} -> {repo_file}")
        return True

    def restore_dotfile(self, file_name):
        """Restore a dotfile from the repository to home directory."""
        repo_file = self.dotfiles_dir / file_name
        home_file = Path.home() / f".{file_name}"

        if not repo_file.exists():
            print(f"Error: {file_name} not found in repository")
            return False

        if home_file.exists() or home_file.is_symlink():
            backup = self.backup_existing_file(home_file)
            if backup:
                print(f"Created backup at {backup}")
            home_file.unlink()

        home_file.symlink_to(repo_file)
        print(f"Restored {file_name} to {home_file}")
        return True

    def list_dotfiles(self):
        """List all dotfiles in the repository."""
        print("\nManaged dotfiles:")
        for file_path in self.dotfiles_dir.iterdir():
            if file_path.is_file() or file_path.is_dir():
                print(f"- {file_path.name}")
                symlink = Path.home() / f".{file_path.name}"
                if symlink.is_symlink():
                    print(f"  └── Linked: {symlink} -> {symlink.resolve()}")
                else:
                    print("  └── Not linked")


def main():
    parser = argparse.ArgumentParser(description="Manage dotfiles with symlinks")
    parser.add_argument(
        "--repo", type=str, default=os.getcwd(), help="Path to the dotfiles repository"
    )
    parser.add_argument(
        "command", choices=["add", "restore", "list"], help="Command to execute"
    )
    parser.add_argument(
        "file", nargs="?", help="File to add or restore (not needed for list)"
    )

    args = parser.parse_args()

    manager = DotfileManager(args.repo)
    manager.setup_directories()

    if args.command == "add":
        if not args.file:
            print("Error: Please specify a file to add")
            return
        manager.add_dotfile(args.file)
    elif args.command == "restore":
        if not args.file:
            print("Error: Please specify a file to restore")
            return
        manager.restore_dotfile(args.file)
    elif args.command == "list":
        manager.list_dotfiles()


if __name__ == "__main__":
    main()
