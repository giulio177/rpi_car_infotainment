#!/bin/bash

# Script to install Apple-style emoji fonts on Raspberry Pi OS Lite
# This installs open-source alternatives that look similar to Apple emoji

echo "🍎 Installing Apple-style emoji fonts for Raspberry Pi..."
echo "=================================================="

# Update package list
echo "📦 Updating package list..."
apt update

# Install Apple-style emoji alternatives
echo "🎨 Installing Apple-style emoji fonts..."

# Try to install Twemoji (Twitter's emoji, similar to Apple style)
if apt-cache search fonts-twemoji | grep -q fonts-twemoji; then
    echo "Installing Twemoji (Twitter emoji)..."
    apt install -y fonts-twemoji-svginot
else
    echo "Twemoji not available in repositories"
fi

# Try to install EmojiOne/JoyPixels
if apt-cache search fonts-emojione | grep -q fonts-emojione; then
    echo "Installing EmojiOne (JoyPixels emoji)..."
    apt install -y fonts-emojione
else
    echo "EmojiOne not available in repositories"
fi

# Install Noto Color Emoji as fallback
echo "Installing Noto Color Emoji as fallback..."
apt install -y fonts-noto-color-emoji

# Install font utilities if not present
echo "🔧 Installing font utilities..."
apt install -y fontconfig

# Update font cache
echo "🔄 Updating font cache..."
fc-cache -fv

# List available emoji fonts to verify installation
echo "📋 Checking installed emoji fonts..."
fc-list | grep -i -E "(emoji|twemoji|emojione)" | head -10

echo ""
echo "✅ Apple-style emoji font installation complete!"
echo ""
echo "📝 Available options installed:"
echo "1. Twemoji - Twitter's emoji (Apple-like style)"
echo "2. EmojiOne - JoyPixels emoji (Apple-like style)" 
echo "3. Noto Color Emoji - Google's emoji (fallback)"
echo ""
echo "🔄 Next steps:"
echo "1. Restart your application to detect new fonts"
echo "2. Check console output for 'SymbolManager: Using emoji font: [font name]'"
echo "3. The app will automatically use the best available Apple-style font"
echo ""
echo "💡 Note: For true Apple Color Emoji, you need to manually install"
echo "   the Apple Color Emoji.ttc file from a macOS system (if legally owned)"
echo ""

# Instructions for manual Apple Color Emoji installation
echo "📖 Manual Apple Color Emoji Installation (if you have access to macOS):"
echo "1. On macOS: cp '/System/Library/Fonts/Apple Color Emoji.ttc' ~/Desktop/"
echo "2. Transfer file to Raspberry Pi"
echo "3. sudo mkdir -p /usr/share/fonts/truetype/apple"
echo "4. sudo cp 'Apple Color Emoji.ttc' /usr/share/fonts/truetype/apple/"
echo "5. sudo fc-cache -fv"
echo "6. Restart the application"
echo ""
