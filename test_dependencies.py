#!/usr/bin/env python3

import sys
import importlib

def check_module(module_name):
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} is installed")
        return True
    except ImportError as e:
        print(f"❌ {module_name} is NOT installed: {e}")
        return False

def main():
    print("Checking dependencies for RPi Car Infotainment...")
    
    # Core dependencies
    core_modules = [
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtWidgets",
        "PyQt6.QtGui",
        "obd",
        "requests"
    ]
    
    # Optional dependencies
    optional_modules = [
        "PyQt6.QtMultimedia",
        "PyQt6.QtNetwork"
    ]
    
    print("\nChecking core dependencies:")
    core_ok = all(check_module(module) for module in core_modules)
    
    print("\nChecking optional dependencies:")
    optional_ok = all(check_module(module) for module in optional_modules)
    
    print("\nSummary:")
    if core_ok:
        print("✅ All core dependencies are installed")
    else:
        print("❌ Some core dependencies are missing")
    
    if optional_ok:
        print("✅ All optional dependencies are installed")
    else:
        print("⚠️ Some optional dependencies are missing")
    
    print("\nSystem information:")
    print(f"Python version: {sys.version}")
    
    return 0 if core_ok else 1

if __name__ == "__main__":
    sys.exit(main())
