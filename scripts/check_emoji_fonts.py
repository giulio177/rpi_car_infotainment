#!/usr/bin/env python3

"""
Simple command-line emoji font checker
Shows what emoji fonts are available on the system
"""

import subprocess
import os

def check_emoji_fonts():
    print("🍎 Emoji Font Availability Check")
    print("=" * 50)
    
    # Check available emoji fonts using fc-list
    try:
        result = subprocess.run(['fc-list'], capture_output=True, text=True)
        fonts = result.stdout
        
        # Look for emoji-related fonts
        emoji_keywords = ['emoji', 'apple', 'noto', 'twemoji', 'emojione', 'symbola']
        emoji_fonts = []
        
        for line in fonts.split('\n'):
            if any(keyword.lower() in line.lower() for keyword in emoji_keywords):
                emoji_fonts.append(line.strip())
        
        print("📚 Found Emoji-Related Fonts:")
        if emoji_fonts:
            for font in emoji_fonts:
                print(f"  ✅ {font}")
        else:
            print("  ❌ No emoji fonts found")
            
        print("\n🎯 Current Status:")
        
        # Check specifically for Apple Color Emoji
        apple_found = any('apple color emoji' in font.lower() for font in emoji_fonts)
        noto_found = any('noto color emoji' in font.lower() for font in emoji_fonts)
        
        if apple_found:
            print("  🍎 Apple Color Emoji: ✅ AVAILABLE")
            print("     Your app will use Apple-style emoji!")
        else:
            print("  🍎 Apple Color Emoji: ❌ NOT AVAILABLE")
            
        if noto_found:
            print("  🤖 Noto Color Emoji: ✅ AVAILABLE")
            print("     Your app will use Google-style emoji")
        else:
            print("  🤖 Noto Color Emoji: ❌ NOT AVAILABLE")
            
        print("\n📱 Emoji Style Comparison:")
        print("  Apple Emoji:  More rounded, softer colors, 3D appearance")
        print("  Google Emoji: Flatter design, brighter colors, geometric")
        
        print("\n🔧 To Get Apple Emoji:")
        print("  1. You need access to a Mac or iOS device")
        print("  2. Copy: /System/Library/Fonts/Apple Color Emoji.ttc")
        print("  3. Install on Pi:")
        print("     sudo mkdir -p /usr/share/fonts/truetype/apple")
        print("     sudo cp 'Apple Color Emoji.ttc' /usr/share/fonts/truetype/apple/")
        print("     sudo fc-cache -fv")
        print("  4. Restart your app")
        
        print("\n💡 Current App Behavior:")
        if apple_found:
            print("  Your app will automatically use Apple emoji! 🎉")
        elif noto_found:
            print("  Your app uses Google emoji (still looks great!) 😊")
        else:
            print("  Your app will use Unicode fallback symbols (⬇, ↻, ▶, ⏸)")
            
        print("\n🚀 Test Your Current Setup:")
        print("  Run: ./scripts/start_infotainment.sh")
        print("  Look for: 'SymbolManager: Using emoji font: [font name]'")
        
    except Exception as e:
        print(f"❌ Error checking fonts: {e}")

if __name__ == "__main__":
    check_emoji_fonts()
