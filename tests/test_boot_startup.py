#!/usr/bin/env python3
"""
Test script to verify boot startup configuration
"""

import os
import subprocess
import sys
from pathlib import Path

def test_autologin_config():
    """Test that auto-login is properly configured"""
    print("🔍 Testing Auto-Login Configuration")
    print("=" * 50)
    
    autologin_file = Path("/etc/systemd/system/getty@tty1.service.d/autologin.conf")
    
    if not autologin_file.exists():
        print("❌ FAIL: Auto-login configuration file does not exist")
        return False
    
    content = autologin_file.read_text()
    if "--autologin pi" in content:
        print("✅ PASS: Auto-login is configured for user 'pi'")
        return True
    else:
        print("❌ FAIL: Auto-login is not properly configured")
        print(f"Content: {content}")
        return False

def test_bash_profile():
    """Test that bash profile is configured correctly"""
    print("\n🔍 Testing Bash Profile Configuration")
    print("=" * 50)
    
    bash_profile = Path.home() / ".bash_profile"
    
    if not bash_profile.exists():
        print("❌ FAIL: .bash_profile does not exist")
        return False
    
    content = bash_profile.read_text()
    
    checks = [
        ("tty1 check", 'if [ "$(tty)" = "/dev/tty1" ]'),
        ("script path", "./scripts/start_infotainment.sh"),
        ("process check", 'pgrep -f "python.*main.py"')
    ]
    
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ PASS: {check_name} found in bash profile")
        else:
            print(f"❌ FAIL: {check_name} not found in bash profile")
            all_passed = False
    
    return all_passed

def test_startup_script():
    """Test that startup script exists and is executable"""
    print("\n🔍 Testing Startup Script")
    print("=" * 50)
    
    script_path = Path("/home/pi/rpi_car_infotainment/scripts/start_infotainment.sh")
    
    if not script_path.exists():
        print("❌ FAIL: Startup script does not exist")
        return False
    
    if not os.access(script_path, os.X_OK):
        print("❌ FAIL: Startup script is not executable")
        return False
    
    print("✅ PASS: Startup script exists and is executable")
    return True

def test_framebuffer_access():
    """Test framebuffer access permissions"""
    print("\n🔍 Testing Framebuffer Access")
    print("=" * 50)
    
    fb_device = Path("/dev/fb0")
    
    if not fb_device.exists():
        print("❌ FAIL: Framebuffer device /dev/fb0 does not exist")
        return False
    
    # Check if pi user is in video group
    try:
        result = subprocess.run(["groups", "pi"], capture_output=True, text=True)
        if "video" in result.stdout:
            print("✅ PASS: User 'pi' is in video group")
        else:
            print("❌ FAIL: User 'pi' is not in video group")
            print(f"Groups: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Could not check user groups: {e}")
        return False
    
    # Check framebuffer permissions
    stat_info = fb_device.stat()
    mode = oct(stat_info.st_mode)[-3:]
    if mode[1] in ['6', '7']:  # Group write permission
        print("✅ PASS: Framebuffer has group write permissions")
        return True
    else:
        print(f"❌ FAIL: Framebuffer permissions insufficient: {mode}")
        return False

def test_virtual_environment():
    """Test that virtual environment exists and has required packages"""
    print("\n🔍 Testing Virtual Environment")
    print("=" * 50)
    
    venv_path = Path("/home/pi/rpi_car_infotainment/venv")
    
    if not venv_path.exists():
        print("❌ FAIL: Virtual environment does not exist")
        return False
    
    python_path = venv_path / "bin" / "python3"
    if not python_path.exists():
        print("❌ FAIL: Python executable not found in virtual environment")
        return False
    
    print("✅ PASS: Virtual environment exists with Python executable")
    return True

def main():
    """Run all boot startup tests"""
    print("🧪 RPi Car Infotainment Boot Startup Tests")
    print("=" * 60)
    
    tests = [
        test_autologin_config,
        test_bash_profile,
        test_startup_script,
        test_framebuffer_access,
        test_virtual_environment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All boot startup tests passed!")
        print("   The application should start automatically on boot.")
        print("   If you're still seeing a black screen, try rebooting the system.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the configuration above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
