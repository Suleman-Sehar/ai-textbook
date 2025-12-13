man sudo_root
sudo find / -type d -name "ai-textbook" 2>/dev/null
find ~/ -type d -name "ai-textbook" 2>/dev/null
find ~/ -type d -iname "ai-textbook" 2>/dev/null
sudo updatedb
locate ai-textbook
sudo apt install plocate
locate ai-textbook
ls -laR ~/ 2>/dev/null | grep "ai-textbook"
ls -la ~/
ls -la ~/Documents/
ls -la ~/Desktop/
ls -la ~/projects/
ls -la ~/code/
ls -la ~/dev/
ls -la ~/workspace/
ls -la /mnt/c/Users/YOUR_WINDOWS_USERNAME/
ls -la /mnt/c/Users/YOUR_WINDOWS_USERNAME/Documents/
ls -la /mnt/c/Users/YOUR_WINDOWS_USERNAME/Desktop/
cd ~/a
history | grep cd | grep -i textbook
cd -
search_folder() {     echo "Searching for 'ai-textbook'...";          echo "1. Searching in home directory...";     find ~/ -type d -name "*ai*textbook*" 2>/dev/null;          echo "2. Searching in Windows directories...";     find /mnt/c/Users -type d -name "*ai*textbook*" 2>/dev/null 2>/dev/null;          echo "3. Using locate...";     locate ai-textbook 2>/dev/null; }
search_folder
find ~/ -type d -name ".git" 2>/dev/null | xargs -I {} dirname {}
sudo apt update && sudo apt install tree
tree -d ~/ | grep -i textbook
ls -la ~/ai-textbook/
ls -la /home/$USER/ai-textbook/
pwd
ls -la /mnt/c/Users/$USER/ai-textbook/ 2>/dev/null
for drive in c d e f; do     if [ -d "/mnt/$drive" ]; then         echo "Searching drive $drive...";         find "/mnt/$drive" -type d -name "ai-textbook" 2>/dev/null | head -5;     fi; done
sudo apt update && sudo apt upgrade -y
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
mkdir -p ~/.claude-code-router ~/.claude
ls -a
qwen
cd /path/to/ai-textbook
cd "/mnt/c/Users/YourWindowsUsername/Documents/ai-textbook"
find ~/ -name "package.json" -type f 2>/dev/null | grep -i textbook
pwd
ls -la ~/
ls -la
ls ../
find . -type d -name "*ai*textbook*" 2>/dev/null
find . -type d -iname "*textbook*" 2>/dev/null
find /home/ai-textbook -type d -name "*project*" 2>/dev/null
find /home/ai-textbook -type d -name "*code*" 2>/dev/null
find /home/ai-textbook -type d -name "*dev*" 2>/dev/null
ls -la *.json *.js *.py *.md 2>/dev/null
cat > search_my_project.sh << 'EOF'
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
EOF

chmod +x search_my_project.sh
./search_my_project.sh
tree -L 2 ~/
ls -la ~/
for item in ~/*/; do echo "=== $(basename "$item") ==="; ls -la "$item" 2>/dev/null | head -5; done
history | grep -i "cd\|git\|npm\|node" | tail -20
ls /mnt/
ls /mnt/c/Users/
WINDOWS_USER=$(ls /mnt/c/Users/ | grep -v "Default\|Public" | head -1)
echo "Windows user appears to be: $WINDOWS_USER"
find "/mnt/c/Users/$WINDOWS_USER" -type d -name "*textbook*" 2>/dev/null | head -10
check_places() {     echo "Checking common project locations...";          PLACES=(         "$HOME/projects"         "$HOME/Documents"         "$HOME/Desktop"          "$HOME/workspace"         "$HOME/code"         "$HOME/dev"         "$HOME/git"         "$HOME/repos"         "/mnt/c/Users/$WINDOWS_USER/Desktop"         "/mnt/c/Users/$WINDOWS_USER/Documents"         "/mnt/c/Users/$WINDOWS_USER/OneDrive"     );          for place in "${PLACES[@]}"; do         if [ -d "$place" ]; then             echo "=== $place ===";             ls -la "$place/" | grep -i textbook
            find "$place" -maxdepth 2 -type d -name "*textbook*" 2>/dev/null;         fi;     done; }
check_places
echo "All directories in your home:"
ls -la ~/ | grep "^d"
du -sh ~/* 2>/dev/null | sort -hr | head -20
pwd
ls -la
ls -la ~/projects/ 2>/dev/null || echo "No projects folder"
echo "=== Home directory contents ==="
ls ~/
find ~/ -maxdepth 3 -type d -name "*textbook*" 2>/dev/null
ls /mnt/c/Users/
