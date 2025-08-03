# SSH Session Manager - Standalone Executable

.PHONY: help setup build install clean dev ui

help:
	@echo "SSH Session Manager - Build and Install:"
	@echo ""
	@echo "  make setup           Set up development environment"
	@echo "  make dev             Run in development mode (terminal)"
	@echo "  make ui              Launch web interface"
	@echo "  make build           Build standalone executable"
	@echo "  make install         Build and install globally"
	@echo "  make clean           Clean build artifacts"
	@echo ""

setup:
	@echo "🔧 Setting up development environment with uv..."
	@uv sync
	@echo "✅ Environment setup complete!"

dev:
	@echo "🚀 Running in development mode..."
	@uv run python main.py

ui:
	@echo "🌐 Launching web interface..."
	@uv run python main.py --ui

build:
	@echo "📦 Building standalone executable..."
	@echo "🔧 Using enhanced PyInstaller configuration..."
	@uv run pyinstaller launch.spec
	@echo "✅ Executable built: ./dist/launch"

install: build
	@echo "🚀 Installing globally..."
	@sudo cp ./dist/launch /usr/local/bin/launch
	@echo "✅ Installation complete! Run 'launch' from anywhere."

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf build/ dist/ __pycache__/ *.egg-info/
	@echo "✅ Clean complete."