#!/bin/bash

# Script to check internal and external links in the Physical AI & Humanoid Robotics Textbook
# This script scans markdown files for broken links

set -e

DOCS_DIR=${1:-"docs"}
TEMP_FILE=$(mktemp)
BROKEN_LINKS_FILE=$(mktemp)

echo "Checking links in $DOCS_DIR directory..."

# Find all markdown files
find "$DOCS_DIR" -name "*.md" -o -name "*.mdx" > "$TEMP_FILE"

BROKEN_LINKS=0

while IFS= read -r file; do
    echo "Checking file: $file"

    # Extract internal links [text](path) where path doesn't start with http
    grep -oE '\[([^\]]+)\]\(([^)]+)\)' "$file" | while read -r link; do
        # Extract the URL part
        url=$(echo "$link" | sed -E 's/.*\[(.*)\]\((.*)\).*/\2/')

        # Skip external links (starting with http)
        if [[ "$url" =~ ^https?:// ]]; then
            continue
        fi

        # Skip anchor links (starting with #)
        if [[ "$url" =~ ^# ]]; then
            continue
        fi

        # Handle relative links
        dir=$(dirname "$file")
        target_path="$dir/$url"

        # If it's an absolute path from docs root
        if [[ "$url" =~ ^/ ]]; then
            target_path="$(dirname "$DOCS_DIR")${url}"
        fi

        # Remove fragment if present
        clean_target_path=$(echo "$target_path" | sed 's/#.*//')

        # Check if file exists
        if [[ ! -f "$clean_target_path" ]]; then
            echo "❌ Broken link in $file -> $url (resolved to: $clean_target_path)" >> "$BROKEN_LINKS_FILE"
            ((BROKEN_LINKS++))
        fi
    done
done < "$TEMP_FILE"

# Clean up temp file
rm "$TEMP_FILE"

# Report results
if [ $BROKEN_LINKS -gt 0 ]; then
    echo
    echo "❌ Found $BROKEN_LINKS broken links:"
    cat "$BROKEN_LINKS_FILE"
    rm "$BROKEN_LINKS_FILE"
    exit 1
else
    echo
    echo "✅ All links are valid!"
    rm "$BROKEN_LINKS_FILE"
    exit 0
fi