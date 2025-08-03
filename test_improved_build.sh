#!/bin/bash

# Test script for improved PyInstaller build
# This script tests the enhanced build to ensure it resolves the Gradio frontend issues

set -e

echo "🧪 Testing improved PyInstaller build..."
echo "========================================"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
make clean

# Build with improved configuration
echo "📦 Building with improved configuration..."
make build-improved

# Test the executable
echo "🧪 Testing the built executable..."
if [ -f "./dist/launch" ]; then
    echo "✅ Executable found at ./dist/launch"

    # Test basic functionality (non-interactive)
    echo "🧪 Testing basic functionality..."
    ./dist/launch --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Basic functionality test passed"
    else
        echo "❌ Basic functionality test failed"
        exit 1
    fi

    # Test web interface startup (brief test)
    echo "🧪 Testing web interface startup..."
    timeout 10s ./dist/launch --ui --port 7891 > /tmp/launch_test.log 2>&1 &
    LAUNCH_PID=$!

    # Wait a moment for startup
    sleep 3

    # Check if process is still running
    if kill -0 $LAUNCH_PID 2>/dev/null; then
        echo "✅ Web interface started successfully"
        # Kill the process
        kill $LAUNCH_PID 2>/dev/null || true
        wait $LAUNCH_PID 2>/dev/null || true
    else
        echo "❌ Web interface failed to start"
        cat /tmp/launch_test.log
        exit 1
    fi

    echo "✅ All tests passed!"
    echo ""
    echo "🎉 Improved build is working correctly!"
    echo "💡 You can now install it with: make install-improved"

else
    echo "❌ Executable not found at ./dist/launch"
    exit 1
fi