# Troubleshooting Guide

Common issues and solutions for Universal Recycle.

If `recycle` is not found, use **`python -m recycle`** with the same arguments, or ensure your environment’s `Scripts` / `bin` directory (where pip installs console scripts) is on `PATH`.

## Quick Fixes

### Repository Sync Issues

**Problem**: Repository sync fails with permission errors

```bash
PermissionError: [WinError 5] Access is denied: 'path/to/repo/.git/hooks'
```

**Solution**:

```bash
# Remove problematic repository
rm -rf repos/problematic-repo

# Re-sync with force flag
recycle sync --force
```

**Problem**: Git clone fails with network errors

```bash
fatal: unable to access 'https://github.com/org/repo.git/': Failed to connect
```

**Solution**:

```bash
# Check network connectivity
git clone https://github.com/org/repo.git

# Use SSH instead of HTTPS in repos.yaml
git: git@github.com:org/repo.git

# Or configure git proxy
git config --global http.proxy http://proxy.company.com:8080
```

### Adapter Issues

**Problem**: Adapter not found

```bash
WARNING: Adapter 'ruff' not found
```

**Solution**:

```bash
# Install missing adapter
pip install ruff mypy bandit

# For C++ adapters
# Install clang-tidy and vcpkg
# Windows: choco install llvm
# macOS: brew install llvm
# Linux: apt-get install clang-tidy
```

**Problem**: Adapter fails with configuration errors

```bash
ERROR: [RuffAdapter] Configuration file not found
```

**Solution**:

```bash
# Create adapter configuration
echo 'line-length = 88' > pyproject.toml

# Or use default configuration
recycle adapt --adapter ruff --fix
```

### Build Issues

**Problem**: Build fails with missing dependencies

```bash
ERROR: Target 'cpp-engine' build failed: missing compiler
```

**Solution**:

```bash
# Install build tools
# Windows: Install Visual Studio Build Tools
# macOS: xcode-select --install
# Linux: apt-get install build-essential

# Check build profile
cat build_profiles.yaml

# Try different profile
recycle build --target cpp-engine --profile debug
```

**Problem**: Bazel not found

```bash
WARNING: Bazel not available, falling back to simulation
```

**Solution**:

```bash
# Install Bazel
# Windows: choco install bazel
# macOS: brew install bazel
# Linux: curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg

# Or continue without Bazel
recycle build --target cpp-engine
```

### Cache Issues

**Problem**: Cache corruption

```bash
ERROR: Cache backend 'local' failed to initialize
```

**Solution**:

```bash
# Clear cache
recycle cache --cache-command clear

# Check cache status
recycle cache --cache-command status
```

**Problem**: Remote cache connection fails

```bash
ERROR: Failed to connect to Redis cache backend
```

**Solution**:

```bash
# Check cache configuration
cat cache_config.yaml

# Use local cache only
export UNIVERSAL_RECYCLE_CACHE_BACKEND=local

# Or fix remote cache settings
```

## 🔧 Common Error Messages

### Configuration Errors

**Error**: `Configuration file not found`

```bash
FileNotFoundError: repos.yaml not found
```

**Solution**:

```bash
# Create default configuration
recycle init

# Or specify config file
recycle sync --config my-repos.yaml
```

**Error**: `Invalid YAML syntax`

```bash
yaml.YAMLError: mapping values are not allowed here
```

**Solution**:

```bash
# Validate YAML syntax
recycle validate

# Check for common YAML issues:
# - Proper indentation (use spaces, not tabs)
# - Correct list syntax (- item)
# - Proper string quoting
```

### Permission Errors

**Error**: `Permission denied`

```bash
PermissionError: [Errno 13] Permission denied: 'path/to/file'
```

**Solution**:

```bash
# Check file permissions
ls -la path/to/file

# Fix permissions
chmod 644 path/to/file

# On Windows, run as administrator
# Right-click Command Prompt -> Run as Administrator
```

**Error**: `Access denied to cache directory`

```bash
OSError: [Errno 13] Permission denied: '.cache/universal_recycle'
```

**Solution**:

```bash
# Create cache directory with proper permissions
mkdir -p .cache/universal_recycle
chmod 755 .cache/universal_recycle

# Or change cache location
export UNIVERSAL_RECYCLE_CACHE_DIR=/tmp/universal_recycle
```

### Network Errors

**Error**: `Connection timeout`

```bash
requests.exceptions.ConnectTimeout: HTTPSConnectionPool
```

**Solution**:

```bash
# Check network connectivity
ping github.com

# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Increase timeout
export UNIVERSAL_RECYCLE_TIMEOUT=300
```

**Error**: `SSL certificate verification failed`

```bash
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solution**:

```bash
# Update certificates
# Windows: Update Windows
# macOS: /Applications/Python\ 3.x/Install\ Certificates.command
# Linux: apt-get install ca-certificates

# Or disable verification (not recommended)
export REQUESTS_CA_BUNDLE=/path/to/cert.pem
```

## Debugging

### Enable Verbose Logging

```bash
# Enable verbose output
recycle sync --verbose

# Set log level
recycle sync --log-level DEBUG

# Or use environment variable
export UNIVERSAL_RECYCLE_LOG_LEVEL=DEBUG
recycle sync
```

### Check System Information

```bash
# Check Python version
python --version

# Check installed packages
pip list | grep universal-recycle

# Check system resources
# Windows: taskmgr
# macOS: Activity Monitor
# Linux: htop
```

### Validate Configuration

```bash
# Validate manifest
recycle validate --manifest repos.yaml

# Validate build profiles
recycle validate --config build_profiles.yaml

# Strict validation
recycle validate --strict
```

## Performance Issues

### Slow Repository Sync

**Symptoms**: Sync takes too long

```bash
# Check network speed
curl -o /dev/null -s -w "%{speed_download}\n" https://github.com

# Use shallow clones
recycle sync --shallow

# Parallel sync
recycle sync --jobs 8
```

### Slow Builds

**Symptoms**: Builds take too long

```bash
# Use distributed builds
recycle build --distributed --jobs 8

# Enable caching
recycle cache --cache-command status

# Use Bazel for faster builds
recycle build --bazel
```

### High Memory Usage

**Symptoms**: Out of memory errors

```bash
# Reduce parallel jobs
recycle sync --jobs 2
recycle adapt --parallel false

# Clear cache
recycle cache --cache-command clear

# Monitor memory usage
# Windows: taskmgr
# macOS: Activity Monitor
# Linux: htop
```

## 🛠️ Platform-Specific Issues

### Windows

**Problem**: Path length limitations

```bash
ERROR: Path too long
```

**Solution**:

```bash
# Use shorter paths
export UNIVERSAL_RECYCLE_CACHE_DIR=C:\tmp\ur

# Or enable long paths
# Registry: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1
```

**Problem**: Git credential issues

```bash
ERROR: Git authentication failed
```

**Solution**:

```bash
# Configure Git credentials
git config --global credential.helper manager-core

# Or use SSH keys
# Generate SSH key: ssh-keygen -t rsa -b 4096
# Add to GitHub: https://github.com/settings/keys
```

### macOS

**Problem**: Python path issues

```bash
ERROR: Python not found
```

**Solution**:

```bash
# Use pyenv
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0

# Or use system Python
/usr/bin/python3 -m recycle sync
```

**Problem**: Xcode command line tools

```bash
ERROR: clang not found
```

**Solution**:

```bash
# Install Xcode command line tools
xcode-select --install

# Or install specific version
xcode-select --switch /Applications/Xcode.app
```

### Linux

**Problem**: Missing system dependencies

```bash
ERROR: libgit2 not found
```

**Solution**:

```bash
# Install dependencies
# Ubuntu/Debian
sudo apt-get install libgit2-dev build-essential

# CentOS/RHEL
sudo yum install libgit2-devel gcc-c++

# Arch
sudo pacman -S libgit2 base-devel
```

**Problem**: SELinux restrictions

```bash
ERROR: Permission denied
```

**Solution**:

```bash
# Check SELinux status
sestatus

# Temporarily disable SELinux
sudo setenforce 0

# Or configure SELinux policies
sudo setsebool -P httpd_can_network_connect 1
```

## Getting Help

### Before Asking for Help

1. **Check this guide** for your specific error
2. **Enable verbose logging** to get more details
3. **Validate your configuration** files
4. **Check system requirements** are met
5. **Try with minimal configuration** to isolate the issue

### Collecting Information

When reporting issues, include:

```bash
# System information
python --version
pip list | grep universal-recycle
uname -a  # Linux/macOS
systeminfo  # Windows

# Configuration files
cat repos.yaml
cat build_profiles.yaml

# Error logs
recycle sync --verbose --log-level DEBUG 2>&1 | tee error.log
```

### Issue Templates

When creating GitHub issues, use these templates:

**Bug Report**:

````markdown
## Bug Description

Brief description of the issue

## Steps to Reproduce

1. Run `recycle sync`
2. See error: `...`

## Expected Behavior

What should happen

## Actual Behavior

What actually happens

## Environment

- OS: Windows 10
- Python: 3.11.0
- Universal Recycle: 1.0.0

## Configuration

```yaml
# repos.yaml content
```
````

## Logs

```
# Verbose output
```

````

**Feature Request**:
```markdown
## Feature Description
Brief description of the feature

## Use Case
Why this feature is needed

## Proposed Solution
How it could be implemented

## Alternatives Considered
Other approaches you've considered
````

## Prevention Tips

### Best Practices

1. **Keep configurations simple** - Start with minimal configs
2. **Use version control** - Track configuration changes
3. **Test incrementally** - Add repositories one by one
4. **Monitor resources** - Watch disk space and memory usage
5. **Backup regularly** - Keep backups of important configurations

### Regular Maintenance

```bash
# Weekly maintenance
recycle cache --cache-command clear
recycle validate --strict

# Monthly maintenance
recycle sync --force
recycle plugin --plugin-command check --plugin-name all
```

### Monitoring

```bash
# Check system health
recycle cache --cache-command stats
recycle build --build-command status

# Monitor performance
recycle performance --performance-command stats
```
