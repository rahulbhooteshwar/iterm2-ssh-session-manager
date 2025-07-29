# Installation Guide

Install the SSH Session Manager as a standalone `launch` command on macOS.

## Standalone Executable

Creates a completely standalone executable that doesn't require Python or virtual environments.

### Benefits:
- ✅ No Python environment needed
- ✅ Single file executable (~20-30MB)
- ✅ Can be distributed easily
- ✅ Works on any macOS system

## Prerequisites

- **uv** - Fast Python package manager (handles Python version automatically)
- macOS system

### Install uv (if not already installed)

```bash
# Using Homebrew (recommended)
brew install uv

# Or using curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Installation

```bash
# Clone repository and install
git clone <repository-url>
cd iterm2-ssh-session-manager
make install
```

This will:
1. Set up Python environment with uv
2. Install PyInstaller and dependencies
3. Build the standalone executable
4. Install it globally as `launch` command

## Manual Installation Steps

```bash
# Set up environment
uv sync

# Install PyInstaller
uv add pyinstaller

# Build executable
uv run pyinstaller launch.spec

# Install globally
sudo cp ./dist/launch /usr/local/bin/launch
```

## Usage

Once installed, you can use the `launch` command from anywhere:

```bash
launch                    # Interactive host selection
launch production         # Filter hosts containing "production"
launch --add              # Add a new host
launch --list             # List all hosts
launch --debug            # Debug keychain issues
```

## Build Commands

```bash
make build      # Build executable only
make install    # Build and install globally
make clean      # Remove build artifacts
```

## Uninstalling

```bash
sudo rm /usr/local/bin/launch
```

## Auto-Start Configuration

Configure SSH Session Manager to automatically start on macOS login for instant SSH management.

### Quick Setup (Login Items)

1. **Open System Preferences:**
   - **System Preferences** → **Users & Groups** → **Login Items**

2. **Add launch command:**
   - Click **"+"** → Browse to `/usr/local/bin/launch`
   - Edit command to: `/usr/local/bin/launch --silent`
   - Check **"Hide"** option

3. **Verify:**
   - After reboot, visit: **http://localhost:7890**

### Advanced Setup (launchd)

For production deployment, create a launchd service:

```bash
# Create service file
cat > ~/Library/LaunchAgents/com.rb.ssh-session-manager.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rb.ssh-session-manager</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/launch</string>
        <string>--silent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load service
launchctl load ~/Library/LaunchAgents/com.rb.ssh-session-manager.plist

# Verify running
launchctl list | grep ssh-session-manager
```

The web interface will be available at **http://localhost:7890** after login.

## Troubleshooting

1. **Command not found:**
   - Make sure `/usr/local/bin` is in your PATH
   - Try `echo $PATH` to verify

2. **Permission denied:**
   - Run installation with `sudo` for global installation
   - Or install to user directory: `cp ./dist/launch ~/.local/bin/launch`

3. **PyInstaller issues:**
   - Try rebuilding: `make clean && make build`
   - Check that all dependencies are installed