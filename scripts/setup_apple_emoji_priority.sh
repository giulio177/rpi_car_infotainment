#!/bin/bash

# Setup Apple Emoji Priority for RPi Car Infotainment
# This script configures the system to prioritize Apple Color Emoji when available

echo "🍎 Setting up Apple Color Emoji Priority"
echo "========================================"

# Create Apple font directory
echo "📁 Creating Apple font directory..."
sudo mkdir -p /usr/share/fonts/truetype/apple

# Set proper permissions
sudo chmod 755 /usr/share/fonts/truetype/apple

# Create fontconfig configuration to prioritize Apple emoji
echo "⚙️  Creating fontconfig priority configuration..."
sudo tee /etc/fonts/local.conf > /dev/null << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- Prioritize Apple Color Emoji over other emoji fonts -->
  <alias>
    <family>emoji</family>
    <prefer>
      <family>Apple Color Emoji</family>
      <family>Noto Color Emoji</family>
      <family>Segoe UI Emoji</family>
    </prefer>
  </alias>
  
  <!-- Ensure Apple Color Emoji is used for emoji characters -->
  <match target="pattern">
    <test name="family">
      <string>emoji</string>
    </test>
    <edit name="family" mode="prepend" binding="strong">
      <string>Apple Color Emoji</string>
    </edit>
  </match>
</fontconfig>
EOF

# Update font cache
echo "🔄 Updating font cache..."
sudo fc-cache -fv

echo ""
echo "✅ Apple Color Emoji priority setup complete!"
echo ""
echo "📋 Current Status:"

# Check if Apple Color Emoji is available
if fc-list | grep -i "apple color emoji" > /dev/null; then
    echo "  🍎 Apple Color Emoji: ✅ INSTALLED AND READY"
    echo "     Your app will use Apple-style emoji!"
else
    echo "  🍎 Apple Color Emoji: ⏳ READY FOR INSTALLATION"
    echo "     System is configured to use Apple emoji when available"
fi

# Check current emoji font
if fc-list | grep -i "noto color emoji" > /dev/null; then
    echo "  🤖 Noto Color Emoji: ✅ Available as fallback"
else
    echo "  🤖 Noto Color Emoji: ❌ Not available"
fi

echo ""
echo "🔧 To Install Apple Color Emoji:"
echo "  1. Get the font file from a Mac: /System/Library/Fonts/Apple Color Emoji.ttc"
echo "  2. Copy to Pi: sudo cp 'Apple Color Emoji.ttc' /usr/share/fonts/truetype/apple/"
echo "  3. Update cache: sudo fc-cache -fv"
echo "  4. Restart your app"
echo ""
echo "🧪 Test Your Setup:"
echo "  Run: python3 scripts/check_emoji_fonts.py"
echo "  Or:  ./scripts/start_infotainment.sh"
echo ""
echo "🎯 Expected Result:"
echo "  Console should show: 'SymbolManager: Using emoji font: Apple Color Emoji'"
echo ""
