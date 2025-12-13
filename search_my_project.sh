#!/bin/bash
echo "=== Searching for project folders ==="

echo "1. Looking in current directory ($(pwd)):"
find . -type f -name "package.json" -o -name "*.js" -o -name "*.py" 2>/dev/null | head -20

echo -e "\n2. Looking in home directory:"
find ~/ -type f -name "package.json" 2>/dev/null | head -10

echo -e "\n3. Looking for Node projects:"
find ~/ -name "node_modules" -type d 2>/dev/null | head -10

echo -e "\n4. Looking for Git repositories:"
find ~/ -name ".git" -type d 2>/dev/null | xargs -I {} dirname {} | head -10

echo -e "\n5. Checking common locations:"
for dir in projects workspace code dev Documents Desktop; do
    if [ -d "$HOME/$dir" ]; then
        echo "  Checking ~/$dir:"
        ls -la "$HOME/$dir/" | grep -i textbook
    fi
done
