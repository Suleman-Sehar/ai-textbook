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
ccr code
sudo apt update && sudo apt upgrade -y
node -v
npm -v
sudo npm install -g @anthropic-ai/claude-code 
ls -a
cat ~/.claude-code-router/config.json
cat > ~/.claude-code-router/config.json << 'EOF'
{
 "LOG": true,
 "LOG_LEVEL": "info",
 "HOST": "127.0.0.1",
 "PORT": 3456,
 "API_TIMEOUT_MS": 600000,
 "Providers": [
  {
  "provider": "openai",
  "model": "gpt-4o",       // Best balance of speed/cost (replaces "specifyplus")
  "api_key": "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",
  "max_tokens": 4096,      // Max tokens per response
  "temperature": 0.7,      // Creativity level (0.0-1.0)
  "timeout": 600000,       // 10 minutes timeout (matches your error)
  "base_url": "https://api.openai.com/v1"
}
 ],
 "Router": {
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "${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}",  # Auto-injected
  "timeout": 600000
},
}
EOF

cat > ~/.claude-code-router/config.json << 'EOF'
{
 "LOG": true,
 "LOG_LEVEL": "info",
 "HOST": "127.0.0.1",
 "PORT": 3456,
 "API_TIMEOUT_MS": 600000,
 "Providers": [
  {
  "provider": "openai",
  "model": "gpt-4o",       // Best balance of speed/cost (replaces "specifyplus")
  "api_key": "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",
  "max_tokens": 4096,      // Max tokens per response
  "temperature": 0.7,      // Creativity level (0.0-1.0)
  "timeout": 600000,       // 10 minutes timeout (matches your error)
  "base_url": "https://api.openai.com/v1"
}
 ],
 "Router": {
  "provider": "openai",
  "model": "gpt-4o",
  "api_key": "${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}",  # Auto-injected
  "timeout": 600000
},
}
EOF

cat ~/.claude-code-router/config.json
cat > ~/.claude-code-router/config.json << 'EOF'

{  
  "LOG": true,  
  "LOG_LEVEL": "info",  
  "HOST": "127.0.0.1",  
  "PORT": 3456,  
  "API_TIMEOUT_MS": 600000,  
  "Providers": [  
    {  
      "name": "qwen",  
      "api_base_url": "https://portal.qwen.ai/v1/chat/completions",  
      "api_key": "sk-aa99b15fe76d4adabda0b7f072c4a286",  
      "models": [  
        "qwen3-coder-plus",  
        "qwen3-coder-plus",  
        "qwen3-coder-plus"  
      ]  
    }  
  ],  
  "Router": {  
    "default": "qwen,qwen3-coder-plus",  
    "background": "qwen,qwen3-coder-plus",  
    "think": "qwen,qwen3-coder-plus",  
    "longContext": "qwen,qwen3-coder-plus",  
    "longContextThreshold": 60000,  
    "webSearch": "qwen,qwen3-coder-plus"  
  }  
}

EOF

cat ~/.claude-code-router/config.json
echo $SHELL
echo 'export QWEN_API_KEY="sk-af1bdc2cbfb744e586296552e708b6e1"' >> ~/.bashrc
source ~/.bashrc
echo 'export QWEN_API_KEY="sk-af1bdc2cbfb744e586296552e708b6e1"' >> ~/.zshrc
source ~/.zshrc
claude --version
ccr version
echo $QWEN_API_KE
uv tool install specifyplus
specifyplus --help
mkdir physical-ai-textbook
git config --global user.name "Suleman Sehar"
git config --global user.email "solemanseher@gmail.com"
git config --global user.name
git config --global user.email
sp init . --ai claude
explorer.exe .
sudo npm install -g @upstash/context7-mcp
claude mcp add --transport stdio context7 npx @upstash/context7-mcp
claude mcp list
ccr start
qwen
Qwen
qwen
pip install qwen-llm
sudo apt update
sudo apt install python3-pip
pip3 install qwen
pip3 install --user qwen
python3 path/to/qwen.py
python3 -m qwen
pip3 install qwen
qwen
pip3 install --user qwen
pip3 list | grep qwen
which qwen
find / -name "*qwen*" 2>/dev/null
git clone https://github.com/QwenLM/Qwen.git
cd Qwen
pip3 install -r requirements.txt
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
qwen
pip3 list | grep qwen
python3 -m pip show qwen | grep Location
find ~/.local/bin -name "qwen" 2>/dev/null
find /usr/local/bin -name "qwen" 2>/dev/null
echo $PATH
echo $PATH | tr ':' '\n' | grep local
export PATH="$HOME/.local/bin:$PATH"
qwen --version
qwen --help
npm install -g @qwen-code/qwen-code@latest
npm config set prefix '~/.npm-global'
sudo npm install -g @qwen-code/qwen-code@latest
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g @qwen-code/qwen-code@latest
sudo chown -R $USER:$USER ~/.npm
sudo chown -R $USER:$USER ~/.config
sudo chown -R $USER:$USER /usr/lib/node_modules
sudo chown -R $USER:$USER /usr/bin/node
sudo chown -R $USER:$USER /usr/bin/npm
npm install -g @qwen-code/qwen-code@latest
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
npm install -g @qwen-code/qwen-code@latest
qwen --version
qwen
ccr code
ccr stop
qwen
ccr stop
qwen
ccr start
ccr code
ccr stop
ccr code
ccr stop
ccr code
ccr stop
cd /mnt/c/Users/<YourWindowsUsername>/Desktop/ai-textbook
cd /mnt/c/Users/Suleman/Desktop/ai-textbook
ls
npm install
npm run dev
pwd
ls
npm run
ccr start
ccr code
npm install -g @qwen-code/qwen-code@latest
qwen --version
npm install -g @anthropic-ai/claude-code @musistudio/claude-code-router
ccr start
ccr code
ccr stop
npm run
ccr start
qwen
ccr code
ccr stop
qwen
ccr start
ccr code
ccr stop4
ccr stop
qwen
ccr code
ccr stop
ccr start
npm install --save-dev typescript
qwen
ccr code
ccr stop
ccr code
ccr stop
ccr start
