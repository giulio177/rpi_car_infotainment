#!/bin/bash

# Script to install emoji fonts on Raspberry Pi OS Lite for proper emoji rendering
# Run this script with: sudo bash scripts/install_emoji_fonts.sh

echo "🚀 Installing emoji fonts for Raspberry Pi OS Lite..."
echo "=================================================="

# Update package list
echo "📦 Updating package list..."
apt update

# Install emoji fonts
echo "🎨 Installing emoji fonts..."
apt install -y fonts-noto-color-emoji fonts-noto-emoji

# Install additional emoji fonts for better coverage
echo "✨ Installing additional emoji fonts..."
apt install -y fonts-emojione

# Install font utilities if not present
echo "🔧 Installing font utilities..."
apt install -y fontconfig

# Create emoji font configuration for better Qt support
echo "⚙️  Configuring emoji fonts for Qt applications..."
mkdir -p /etc/fonts/conf.d

# Create emoji font configuration file
cat > /etc/fonts/conf.d/01-emoji.conf << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- Add emoji fonts to the default font families -->
  <alias>
    <family>sans-serif</family>
    <prefer>
      <family>DejaVu Sans</family>
      <family>Noto Color Emoji</family>
      <family>Noto Emoji</family>
      <family>EmojiOne</family>
    </prefer>
  </alias>
  
  <alias>
    <family>serif</family>
    <prefer>
      <family>DejaVu Serif</family>
      <family>Noto Color Emoji</family>
      <family>Noto Emoji</family>
      <family>EmojiOne</family>
    </prefer>
  </alias>
  
  <alias>
    <family>monospace</family>
    <prefer>
      <family>DejaVu Sans Mono</family>
      <family>Noto Color Emoji</family>
      <family>Noto Emoji</family>
      <family>EmojiOne</family>
    </prefer>
  </alias>

  <!-- Ensure emoji fonts are used for emoji characters -->
  <match target="pattern">
    <test name="family">
      <string>emoji</string>
    </test>
    <edit name="family" mode="prepend" binding="strong">
      <string>Noto Color Emoji</string>
      <string>Noto Emoji</string>
      <string>EmojiOne</string>
    </edit>
  </match>
</fontconfig>
EOF

# Update font cache
echo "🔄 Updating font cache..."
fc-cache -fv

# List available emoji fonts to verify installation
echo "📋 Checking installed emoji fonts..."
fc-list | grep -i emoji

echo ""
echo "✅ Emoji font installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Restart your X server: sudo systemctl restart lightdm"
echo "2. OR simply reboot: sudo reboot"
echo "3. After restart, emoji should render properly in your Qt application"
echo ""
echo "🧪 To test emoji support, you can run:"
echo "   echo '💾 🔄 ✅ ➖' | cat"
echo ""
