#!/usr/bin/env sh
# Create a symlink ~/.ideavimrc -> <repo>/.ideavimrc  (macOS / Linux)
# If a regular file already sits at the target, it is backed up first.
set -eu

# Directory where this script lives = repo root
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE="$SCRIPT_DIR/.ideavimrc"
TARGET="$HOME/.ideavimrc"

if [ ! -f "$SOURCE" ]; then
  echo "Error: source file not found: $SOURCE" >&2
  exit 1
fi

if [ -L "$TARGET" ]; then
  # Already a symlink — just replace it
  echo "Removing existing symlink: $TARGET"
  rm -f "$TARGET"
elif [ -e "$TARGET" ]; then
  # Real file/dir — back it up before replacing
  BACKUP="$TARGET.backup.$(date +%Y%m%d%H%M%S)"
  echo "Backing up existing file: $TARGET -> $BACKUP"
  mv -- "$TARGET" "$BACKUP"
fi

ln -s -- "$SOURCE" "$TARGET"
echo "Linked: $TARGET -> $SOURCE"
