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

        print_tree(self.dotfiles_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Manage dotfiles and directories with symlinks"
    )
    parser.add_argument(
        "--repo", type=str, default=os.getcwd(), help="Path to the dotfiles repository"
    )
    parser.add_argument(
        "command", choices=["add", "restore", "list"], help="Command to execute"
    )
    parser.add_argument(
        "file", nargs="?", help="File/directory to add or restore (not needed for list)"
    )

    args = parser.parse_args()

    manager = DotfileManager(args.repo)
    manager.setup_directories()

    try:
        if args.command == "add":
            if not args.file:
                print("Error: Please specify a file or directory to add")
                return
            manager.add_dotfile(args.file)
        elif args.command == "restore":
            if not args.file:
                print("Error: Please specify a file or directory to restore")
                return
            manager.restore_dotfile(args.file)
        elif args.command == "list":
            manager.list_dotfiles()
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    main()
