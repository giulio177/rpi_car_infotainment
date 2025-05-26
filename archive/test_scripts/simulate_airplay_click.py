#!/usr/bin/env python3

"""
Script to simulate a click on the AirPlay overlay for testing purposes.
This can be useful for testing the popup functionality.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simulate_click():
    """Simulate a click event for testing."""
    print("=== AirPlay Click Simulation ===")
    print()
    
    try:
        # Try to send a signal to the running application
        import subprocess
        
        # Check if application is running
        result = subprocess.run(['pgrep', '-f', 'python3 main.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✅ Found running application (PID: {pid})")
            
            # For now, just print instructions since we can't easily inject events
            print()
            print("📋 **Manual Test Instructions:**")
            print("1. Ensure AirPlay is running and device is connected")
            print("2. Click anywhere on the mirrored screen")
            print("3. The popup should appear with control options")
            print()
            print("🔧 **Alternative Testing Methods:**")
            print("- Use a physical touch on touchscreen")
            print("- Use mouse if connected")
            print("- Use remote desktop and click")
            print()
            
        else:
            print("❌ Application not running")
            print("   Start the application first with:")
            print("   sudo systemctl start rpi-infotainment.service")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        simulate_click()
    except KeyboardInterrupt:
        print("\n⚠️ Simulation interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
