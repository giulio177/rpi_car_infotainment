#!/usr/bin/env python3

"""
Test script to verify AirPlay overlay functionality
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.airplay_overlay_manager import AirPlayOverlayManager

def test_airplay_overlay():
    """Test the AirPlay overlay manager functionality."""
    print("=== AirPlay Overlay Manager Test ===")
    
    # Create manager
    manager = AirPlayOverlayManager()
    
    # Test availability
    print(f"RPiPlay available: {manager.is_available()}")
    
    if not manager.is_available():
        print("❌ RPiPlay not available - cannot test")
        return False
    
    # Test status
    print(f"Initial status: {manager.get_status()}")
    
    # Test starting AirPlay
    print("\n🚀 Starting AirPlay service...")
    success = manager.start_airplay()
    
    if success:
        print("✅ AirPlay started successfully")
        print(f"Status: {manager.get_status()}")
        
        # Wait a bit
        print("\n⏳ Waiting 10 seconds for service to stabilize...")
        time.sleep(10)
        
        print(f"Status after wait: {manager.get_status()}")
        
        # Test stopping
        print("\n🛑 Stopping AirPlay service...")
        manager.stop_airplay()
        print(f"Final status: {manager.get_status()}")
        
        print("✅ Test completed successfully")
        return True
    else:
        print("❌ Failed to start AirPlay")
        return False

if __name__ == "__main__":
    try:
        success = test_airplay_overlay()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
