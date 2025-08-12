#!/bin/bash

# Move all contents from multi-step-llm-app to parent directory
# This script will be run from within multi-step-llm-app

set -e  # Exit on error

echo "Moving all contents from multi-step-llm-app to repository root..."

# We're currently in multi-step-llm-app, need to work from parent
REPO_ROOT="/Users/williamprior/Development/GitHub/blue-ocean-research"
CURRENT_DIR="$REPO_ROOT/multi-step-llm-app"

# Use git mv to preserve history for tracked files
echo "Moving tracked files..."
for file in multi-step-llm-app/*; do
    if [ -e "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "move_to_root.sh" ]; then
            echo "Moving $file to ./$filename"
            git mv "$file" "./$filename" 2>/dev/null || mv "$file" "./$filename"
        fi
    fi
done

# Move hidden files
echo "Moving hidden files..."
for file in multi-step-llm-app/.*; do
    filename=$(basename "$file")
    if [ "$filename" != "." ] && [ "$filename" != ".." ] && [ -e "$file" ]; then
        echo "Moving $file to ./$filename"
        git mv "$file" "./$filename" 2>/dev/null || mv "$file" "./$filename"
    fi
done

# Move subdirectories with special handling for .github
echo "Moving subdirectories..."
if [ -d "multi-step-llm-app/.github" ]; then
    echo "Merging .github directories..."
    # Move workflows
    if [ -d "multi-step-llm-app/.github/workflows" ]; then
        mkdir -p .github/workflows
        git mv multi-step-llm-app/.github/workflows/* .github/workflows/ 2>/dev/null || \
        mv multi-step-llm-app/.github/workflows/* .github/workflows/
    fi
    # Move other .github contents
    for item in multi-step-llm-app/.github/*; do
        if [ -e "$item" ] && [ "$(basename "$item")" != "workflows" ]; then
            git mv "$item" .github/ 2>/dev/null || mv "$item" .github/
        fi
    done
fi

# Move other directories
for dir in multi-step-llm-app/*/; do
    if [ -d "$dir" ] && [ "$(basename "$dir")" != ".github" ]; then
        dirname=$(basename "$dir")
        echo "Moving directory $dir to ./$dirname"
        git mv "$dir" "./$dirname" 2>/dev/null || mv "$dir" "./"
    fi
done

# Remove the now-empty multi-step-llm-app directory
echo "Removing empty multi-step-llm-app directory..."
rm -f multi-step-llm-app/move_to_root.sh
rmdir multi-step-llm-app 2>/dev/null || echo "Directory not empty or already removed"

echo "Done! All contents have been moved to the repository root."
echo ""
echo "Next steps:"
echo "1. Review the changes with: git status"
echo "2. Commit the changes with: git add -A && git commit -m 'refactor: Move all contents from multi-step-llm-app to repository root'"
echo "3. Push to remote with: git push origin main"