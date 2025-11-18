#!/bin/bash
# Example: Organize all notes using CLI (shell-friendly)

set -e  # Exit on error

NOTES_DIR="${1:-.}"

echo "Organizing notes in: $NOTES_DIR"

for file in "$NOTES_DIR"/*.md; do
    if [ ! -f "$file" ]; then
        continue
    fi
    
    echo "Processing $(basename "$file")..."
    
    # Organize the file
    if honk notes agent-organize "$file" 2>&1; then
        echo "  ✓ Done"
    else
        echo "  ✗ Failed"
    fi
done

echo "All done!"
