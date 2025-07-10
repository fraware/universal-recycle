# Installation Guide

Complete installation guide for Universal Recycle across all platforms.

## System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **Git**: 2.20 or higher
- **Memory**: 4GB RAM (8GB recommended)
- **Disk Space**: 2GB free space
- **Network**: Internet connection for repository syncing

### Recommended Requirements

- **Python**: 3.11 or higher
- **Git**: 2.30 or higher
- **Memory**: 16GB RAM
- **Disk Space**: 10GB free space
- **CPU**: Multi-core processor
- **Network**: High-speed internet connection

## Platform-Specific Installation

### Windows

#### Option 1: Using Chocolatey (Recommended)

```bash
# Install Chocolatey first (if not installed)
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Universal Recycle
choco install universal-recycle

# Or install from source
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle
pip install -r requirements.txt
```

#### Option 2: Manual Installation

```bash
# Install Python (if not installed)
# Download from https://www.python.org/downloads/

# Install Git (if not installed)
# Download from https://git-scm.com/download/win

# Clone repository
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Install dependencies
pip install -r requirements.txt

# Add to PATH (optional)
# Add C:\path\to\universal-recycle to your PATH environment variable
```

#### Windows-Specific Dependencies

```bash
# Install Visual Studio Build Tools (for C++ compilation)
# Download from https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

# Install LLVM (for clang-tidy)
choco install llvm

# Install Bazel (optional)
choco install bazel

# Install vcpkg (for C++ package management)
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

### macOS

#### Option 1: Using Homebrew (Recommended)

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Universal Recycle
brew install universal-recycle

# Or install from source
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle
pip install -r requirements.txt
```

#### Option 2: Manual Installation

```bash
# Install Python (if not installed)
brew install python@3.11

# Install Git (if not installed)
brew install git

# Clone repository
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Install dependencies
pip install -r requirements.txt
```

#### macOS-Specific Dependencies

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install LLVM (for clang-tidy)
brew install llvm

# Install Bazel (optional)
brew install bazel

# Install vcpkg (for C++ package management)
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.sh
./vcpkg integrate install
```

### Linux (Ubuntu/Debian)

#### Option 1: Using Package Manager

```bash
# Add repository (if available)
curl -fsSL https://packages.universal-recycle.org/gpg | sudo gpg --dearmor -o /usr/share/keyrings/universal-recycle-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/universal-recycle-archive-keyring.gpg] https://packages.universal-recycle.org/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/universal-recycle.list

# Install Universal Recycle
sudo apt update
sudo apt install universal-recycle
```

#### Option 2: Manual Installation

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3 python3-pip git build-essential

# Install Python dependencies
sudo apt install -y python3-venv python3-dev

# Clone repository
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Linux-Specific Dependencies

```bash
# Install LLVM (for clang-tidy)
sudo apt install -y clang-tidy libclang-dev

# Install Bazel (optional)
curl -fsSL https://bazel.build/bazel-release.pub.gpg | sudo gpg --dearmor -o /usr/share/keyrings/bazel-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | sudo tee /etc/apt/sources.list.d/bazel.list
sudo apt update
sudo apt install -y bazel

# Install vcpkg (for C++ package management)
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.sh
./vcpkg integrate install
```

### Linux (CentOS/RHEL/Fedora)

```bash
# Install system dependencies
sudo yum install -y python3 python3-pip git gcc-c++ make
# Or for Fedora: sudo dnf install -y python3 python3-pip git gcc-c++ make

# Install Python dependencies
sudo yum install -y python3-devel
# Or for Fedora: sudo dnf install -y python3-devel

# Clone repository
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Docker Installation

### Using Docker Hub

```bash
# Pull the official image
docker pull universalrecycle/universal-recycle:latest

# Run Universal Recycle
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.gitconfig:/root/.gitconfig \
  universalrecycle/universal-recycle:latest \
  python recycle/cli.py init
```

### Building from Source

```bash
# Clone repository
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Build Docker image
docker build -t universal-recycle .

# Run Universal Recycle
docker run -it --rm \
  -v $(pwd):/workspace \
  universal-recycle \
  python recycle/cli.py init
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  universal-recycle:
    image: universalrecycle/universal-recycle:latest
    volumes:
      - .:/workspace
      - ~/.gitconfig:/root/.gitconfig
    working_dir: /workspace
    environment:
      - UNIVERSAL_RECYCLE_CACHE_DIR=/workspace/.cache
    command: python recycle/cli.py sync
```

```bash
# Run with Docker Compose
docker-compose up
```

## Python Package Installation

### From PyPI

```bash
# Install Universal Recycle
pip install universal-recycle

# Verify installation
python -c "import universal_recycle; print(universal_recycle.__version__)"
```

### From Source

```bash
# Clone repository
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Install in development mode
pip install -e .

# Or install in production mode
pip install .
```

### Using pipx (Recommended for CLI tools)

```bash
# Install pipx (if not installed)
python -m pip install --user pipx
python -m pipx ensurepath

# Install Universal Recycle
pipx install universal-recycle

# Verify installation
universal-recycle --version
```

## Configuration

### Environment Variables

```bash
# Set environment variables
export UNIVERSAL_RECYCLE_CONFIG=my-repos.yaml
export UNIVERSAL_RECYCLE_CACHE_DIR=/path/to/cache
export UNIVERSAL_RECYCLE_LOG_LEVEL=INFO
export UNIVERSAL_RECYCLE_PLUGIN_DIR=/path/to/plugins
```

### Configuration Files

```bash
# Create configuration directory
mkdir -p ~/.config/universal-recycle

# Create global configuration
cat > ~/.config/universal-recycle/config.yaml << EOF
cache:
  backend: local
  directory: ~/.cache/universal-recycle

logging:
  level: INFO
  file: ~/.cache/universal-recycle/logs/universal-recycle.log

plugins:
  directory: ~/.config/universal-recycle/plugins
EOF
```

## Verification

### Test Installation

```bash
# Check Python version
python --version

# Check Git version
git --version

# Test Universal Recycle
python recycle/cli.py --version

# Test basic functionality
python recycle/cli.py init --non-interactive
python recycle/cli.py validate
```

### Test Dependencies

```bash
# Test Python adapters
python -c "import ruff; print('Ruff OK')"
python -c "import mypy; print('MyPy OK')"
python -c "import bandit; print('Bandit OK')"

# Test C++ tools (if installed)
clang-tidy --version
vcpkg --version

# Test Bazel (if installed)
bazel --version
```

## Troubleshooting

### Common Installation Issues

**Python not found:**

```bash
# Check Python installation
which python
python --version

# Install Python if missing
# Windows: Download from python.org
# macOS: brew install python@3.11
# Linux: sudo apt install python3
```

**Git not found:**

```bash
# Check Git installation
which git
git --version

# Install Git if missing
# Windows: Download from git-scm.com
# macOS: brew install git
# Linux: sudo apt install git
```

**Permission errors:**

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/.cache/universal-recycle
chmod 755 ~/.cache/universal-recycle

# Or use user installation
pip install --user universal-recycle
```

**Network issues:**

```bash
# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or use alternative package index
pip install -i https://pypi.org/simple/ universal-recycle
```

### Platform-Specific Issues

**Windows:**

```bash
# Path too long error
# Enable long paths in registry or use shorter paths
export UNIVERSAL_RECYCLE_CACHE_DIR=C:\tmp\ur

# Git credential issues
git config --global credential.helper manager-core
```

**macOS:**

```bash
# Python path issues
# Use pyenv for Python version management
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0

# Xcode command line tools
xcode-select --install
```

**Linux:**

```bash
# Missing system dependencies
sudo apt install -y libgit2-dev build-essential
# Or: sudo yum install -y libgit2-devel gcc-c++

# SELinux restrictions
sudo setenforce 0  # Temporarily disable
# Or configure SELinux policies
```

## Updating

### Update Universal Recycle

```bash
# Update from PyPI
pip install --upgrade universal-recycle

# Update from source
cd universal-recycle
git pull origin main
pip install -r requirements.txt

# Update Docker image
docker pull universalrecycle/universal-recycle:latest
```

### Update Dependencies

```bash
# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update system packages
# Ubuntu/Debian
sudo apt update && sudo apt upgrade

# CentOS/RHEL
sudo yum update

# macOS
brew update && brew upgrade
```

## Next Steps

After successful installation:

1. **Initialize your first project:**

   ```bash
   python recycle/cli.py init
   ```

2. **Read the Quick Start Guide:**
   See [Quick Start Tutorial](quickstart.md)

3. **Explore the CLI Reference:**
   See [CLI Reference](cli-reference.md)

4. **Join the Community:**
   - [GitHub Discussions](https://github.com/your-org/universal-recycle/discussions)
   - [Discord Server](https://discord.gg/universal-recycle)
   - [Mailing List](https://groups.google.com/g/universal-recycle)

## Support

If you encounter installation issues:

1. **Check this guide** for your specific platform
2. **Review troubleshooting section** above
3. **Search existing issues** on GitHub
4. **Create a new issue** with detailed information

For more help, see our [Troubleshooting Guide](troubleshooting.md).

**Installation complete!** 🎉 Now you're ready to start using Universal Recycle. Check out our [Quick Start Tutorial](quickstart.md) to get started!
