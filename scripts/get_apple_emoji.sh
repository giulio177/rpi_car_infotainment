#!/bin/bash

# Apple Color Emoji Installation Guide
# This script provides step-by-step instructions to get Apple emoji working

echo "🍎 Apple Color Emoji Installation Guide"
echo "======================================="
echo ""

# Check current status
echo "🔍 Current Status Check:"
if fc-list | grep -i "apple color emoji" > /dev/null; then
    echo "  ✅ Apple Color Emoji: INSTALLED"
    echo "  🎉 Your app should be using Apple emoji!"
else
    echo "  ❌ Apple Color Emoji: NOT INSTALLED"
    echo "  📱 Your app is using Google emoji (Noto Color Emoji)"
fi

echo ""
echo "🎯 What You Need:"
echo "  The file: Apple Color Emoji.ttc (about 40-70MB)"
echo "  From: Mac, iPhone, or iPad that you legally own"
echo ""

echo "📋 Step-by-Step Instructions:"
echo ""

echo "🍎 Option 1: From Mac Computer"
echo "  1. On your Mac, open Terminal"
echo "  2. Run: cp '/System/Library/Fonts/Apple Color Emoji.ttc' ~/Desktop/"
echo "  3. Transfer file to your Raspberry Pi:"
echo "     scp ~/Desktop/Apple\\ Color\\ Emoji.ttc pi@YOUR_PI_IP:~/"
echo "  4. On Pi, run: sudo cp ~/Apple\\ Color\\ Emoji.ttc /usr/share/fonts/truetype/apple/"
echo "  5. Update cache: sudo fc-cache -fv"
echo "  6. Restart your infotainment app"
echo ""

echo "📱 Option 2: From iPhone/iPad"
echo "  1. Install iMazing or 3uTools on your computer"
echo "  2. Connect your iPhone/iPad"
echo "  3. Navigate to System Files > Fonts"
echo "  4. Extract 'Apple Color Emoji.ttc'"
echo "  5. Transfer to Pi and follow steps 4-6 from Option 1"
echo ""

echo "🔄 Option 3: Use Current Google Emoji"
echo "  Your current emoji work perfectly! They're just Google-style:"
echo "  💾 🔄 ▶️ ⏸️ ⏮️ ⏭️ ✅ ➖"
echo "  These are professional and functional."
echo ""

echo "🧪 Test After Installation:"
echo "  1. Restart your app: ./scripts/start_infotainment.sh"
echo "  2. Look for: 'SymbolManager: ✅ FOUND and using emoji font: Apple Color Emoji'"
echo "  3. Your buttons will now show Apple-style emoji!"
echo ""

echo "⚖️  Legal Note:"
echo "  Apple Color Emoji font is proprietary. Only use it if you"
echo "  legally own a Mac, iPhone, or iPad."
echo ""

# Offer to prepare the system
read -p "🔧 Would you like me to prepare your system for Apple emoji? (y/n): " prepare

if [[ $prepare =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Preparing system for Apple Color Emoji..."
    
    # Ensure directory exists
    sudo mkdir -p /usr/share/fonts/truetype/apple
    sudo chmod 755 /usr/share/fonts/truetype/apple
    
    # Create fontconfig to prioritize Apple emoji
    sudo tee /etc/fonts/local.conf > /dev/null << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias>
    <family>emoji</family>
    <prefer>
      <family>Apple Color Emoji</family>
      <family>Noto Color Emoji</family>
    </prefer>
  </alias>
</fontconfig>
EOF
    
    echo "✅ System prepared! Now you just need the Apple Color Emoji.ttc file"
    echo ""
    echo "📁 When you get the font file, install it with:"
    echo "   sudo cp 'Apple Color Emoji.ttc' /usr/share/fonts/truetype/apple/"
    echo "   sudo fc-cache -fv"
    echo ""
else
    echo "👋 No changes made. Your current Google emoji work great!"
fi

echo "🚀 Current app status: Working perfectly with available emoji fonts"
