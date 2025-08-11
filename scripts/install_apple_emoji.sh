#!/bin/bash

# Apple Color Emoji Installation Script for Raspberry Pi
# This script helps install Apple Color Emoji font for the infotainment system

set -e  # Exit on any error

echo "🍎 Apple Color Emoji Installation for RPi Car Infotainment"
echo "=========================================================="
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  This script should NOT be run as root (don't use sudo)"
   echo "   The script will ask for sudo when needed"
   exit 1
fi

# Function to check if Apple Color Emoji is already installed
check_apple_emoji() {
    if fc-list | grep -i "apple color emoji" > /dev/null; then
        echo "✅ Apple Color Emoji is already installed!"
        return 0
    else
        echo "❌ Apple Color Emoji not found"
        return 1
    fi
}

# Function to install from local file
install_from_file() {
    local font_file="$1"
    
    if [[ ! -f "$font_file" ]]; then
        echo "❌ Font file not found: $font_file"
        return 1
    fi
    
    echo "📦 Installing Apple Color Emoji from: $font_file"
    
    # Create font directory
    sudo mkdir -p /usr/share/fonts/truetype/apple
    
    # Copy font file
    sudo cp "$font_file" /usr/share/fonts/truetype/apple/
    
    # Set proper permissions
    sudo chmod 644 /usr/share/fonts/truetype/apple/*
    
    # Update font cache
    echo "🔄 Updating font cache..."
    sudo fc-cache -fv
    
    # Verify installation
    if check_apple_emoji; then
        echo "🎉 Apple Color Emoji installed successfully!"
        return 0
    else
        echo "❌ Installation failed - font not detected"
        return 1
    fi
}

# Function to download Apple Color Emoji (if available from open source)
download_apple_emoji() {
    echo "🌐 Attempting to download Apple-compatible emoji font..."
    
    # Try to download from GitHub (open source Apple-style emoji)
    local temp_dir="/tmp/apple_emoji_install"
    mkdir -p "$temp_dir"
    
    # Note: This is a placeholder - actual Apple Color Emoji is proprietary
    echo "⚠️  Apple Color Emoji is proprietary and cannot be downloaded freely"
    echo "   You need to obtain it from a Mac or iOS device you own"
    
    return 1
}

# Main installation logic
main() {
    echo "🔍 Checking current emoji font status..."
    
    if check_apple_emoji; then
        echo "✅ Apple Color Emoji is already available!"
        echo "🚀 Your app should automatically use Apple emoji"
        echo ""
        echo "🧪 Test your setup:"
        echo "   ./scripts/start_infotainment.sh"
        echo "   Look for: 'SymbolManager: Using emoji font: Apple Color Emoji'"
        exit 0
    fi
    
    echo ""
    echo "📋 Installation Options:"
    echo "1. Install from local file (if you have Apple Color Emoji.ttc)"
    echo "2. Get instructions for obtaining the font"
    echo "3. Exit"
    echo ""
    
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo ""
            echo "📁 Please provide the path to your Apple Color Emoji font file"
            echo "   Common names: 'Apple Color Emoji.ttc' or 'AppleColorEmoji.ttc'"
            echo ""
            read -p "Enter full path to font file: " font_path
            
            if install_from_file "$font_path"; then
                echo ""
                echo "🎉 SUCCESS! Apple Color Emoji is now installed!"
                echo ""
                echo "🔄 Next steps:"
                echo "1. Restart your infotainment app"
                echo "2. Check console for: 'SymbolManager: Using emoji font: Apple Color Emoji'"
                echo "3. Enjoy Apple-style emoji in your car! 🚗"
            else
                echo "❌ Installation failed. Please check the font file path."
                exit 1
            fi
            ;;
        2)
            echo ""
            echo "📖 How to Obtain Apple Color Emoji Font:"
            echo ""
            echo "🍎 From macOS:"
            echo "   1. On your Mac, open Terminal"
            echo "   2. Run: cp '/System/Library/Fonts/Apple Color Emoji.ttc' ~/Desktop/"
            echo "   3. Transfer the file to your Raspberry Pi"
            echo "   4. Run this script again with option 1"
            echo ""
            echo "📱 From iOS Device:"
            echo "   1. Use tools like iMazing or 3uTools to extract system fonts"
            echo "   2. Look for 'Apple Color Emoji.ttc'"
            echo "   3. Transfer to your Raspberry Pi"
            echo "   4. Run this script again with option 1"
            echo ""
            echo "⚖️  Legal Note:"
            echo "   Apple Color Emoji font is proprietary. Only use it if you"
            echo "   legally own a Mac or iOS device."
            echo ""
            ;;
        3)
            echo "👋 Exiting. Your app will continue using Google emoji (Noto Color Emoji)"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Exiting."
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
