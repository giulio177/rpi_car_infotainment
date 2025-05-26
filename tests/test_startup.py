#!/usr/bin/env python3
"""
Test script to verify startup configuration
"""

import os
import subprocess
import sys
from pathlib import Path

def test_script_exists():
    """Test that the startup script exists and is executable"""
    script_path = Path("/home/pi/rpi_car_infotainment/scripts/start_infotainment.sh")
    
    if not script_path.exists():
        print("❌ FAIL: Startup script does not exist at", script_path)
        return False
    
    if not os.access(script_path, os.X_OK):
        print("❌ FAIL: Startup script is not executable")
        return False
    
    print("✅ PASS: Startup script exists and is executable")
    return True

def test_bash_profile():
    """Test that bash profile has correct path"""
    bash_profile = Path.home() / ".bash_profile"
    
    if not bash_profile.exists():
        print("❌ FAIL: .bash_profile does not exist")
        return False
    
    content = bash_profile.read_text()
    if "./scripts/start_infotainment.sh" in content:
        print("✅ PASS: .bash_profile has correct script path")
        return True
    else:
        print("❌ FAIL: .bash_profile has incorrect script path")
        print("Expected: ./scripts/start_infotainment.sh")
        return False

def test_service_file():
    """Test that service file has correct configuration"""
    service_file = Path("/etc/systemd/system/rpi-infotainment.service")
    
    if not service_file.exists():
        print("❌ FAIL: Service file does not exist")
        return False
    
    content = service_file.read_text()
    if "/home/pi/rpi_car_infotainment/scripts/start_infotainment.sh" in content:
        print("✅ PASS: Service file has correct script path")
        return True
    else:
        print("❌ FAIL: Service file has incorrect script path")
        return False

def test_service_status():
    """Test that service is enabled and can be started"""
    try:
        # Check if service is enabled
        result = subprocess.run(
            ["systemctl", "is-enabled", "rpi-infotainment"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0 and "enabled" in result.stdout:
            print("✅ PASS: Service is enabled for boot")
        else:
            print("❌ FAIL: Service is not enabled for boot")
            return False
        
        # Check if service can start (without actually starting it for long)
        result = subprocess.run(
            ["sudo", "systemctl", "status", "rpi-infotainment"],
            capture_output=True, text=True
        )
        
        if "could not be found" in result.stderr:
            print("❌ FAIL: Service is not properly installed")
            return False
        
        print("✅ PASS: Service is properly configured")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error checking service status: {e}")
        return False

def main():
    """Run all startup tests"""
    print("🔍 Testing RPi Car Infotainment Startup Configuration")
    print("=" * 60)
    
    tests = [
        test_script_exists,
        test_bash_profile,
        test_service_file,
        test_service_status
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All startup tests passed! The app should start on boot.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
