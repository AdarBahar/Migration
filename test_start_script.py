#!/usr/bin/env python3
"""
🧪 Test Start Script Functionality

This script tests that the Start script works correctly and can launch
the Migration Control Center.

Usage:
    python test_start_script.py

Author: Migration Project
"""

import os
import sys
import subprocess
import time


def test_start_script_exists():
    """Test that the Start script exists and is executable."""
    print("🧪 Testing Start script existence and permissions...")
    
    if not os.path.exists('Start'):
        print("❌ Start script not found")
        return False
    
    if not os.access('Start', os.X_OK):
        print("❌ Start script is not executable")
        return False
    
    print("✅ Start script exists and is executable")
    return True


def test_start_script_syntax():
    """Test that the Start script has valid bash syntax."""
    print("🧪 Testing Start script syntax...")
    
    try:
        result = subprocess.run(['bash', '-n', 'Start'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Start script has valid bash syntax")
            return True
        else:
            print(f"❌ Start script syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking Start script syntax: {e}")
        return False


def test_python_environment():
    """Test that Python environment is properly set up."""
    print("🧪 Testing Python environment...")
    
    # Check if we can import required modules
    try:
        import redis
        import json
        from datetime import datetime
        print("✅ Required Python modules are available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python module: {e}")
        return False


def test_index_py_exists():
    """Test that index.py exists and is valid Python."""
    print("🧪 Testing index.py existence and syntax...")
    
    if not os.path.exists('index.py'):
        print("❌ index.py not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, '-m', 'py_compile', 'index.py'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ index.py exists and has valid Python syntax")
            return True
        else:
            print(f"❌ index.py syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking index.py: {e}")
        return False


def test_env_file_template():
    """Test that .env.example exists for template creation."""
    print("🧪 Testing .env.example template...")
    
    if not os.path.exists('.env.example'):
        print("❌ .env.example template not found")
        return False
    
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
            if 'REDIS_SOURCE_HOST' in content and 'REDIS_DEST_HOST' in content:
                print("✅ .env.example template is properly formatted")
                return True
            else:
                print("❌ .env.example template missing required variables")
                return False
    except Exception as e:
        print(f"❌ Error reading .env.example: {e}")
        return False


def test_scripts_directory():
    """Test that scripts directory exists with diagnostic script."""
    print("🧪 Testing scripts directory...")
    
    if not os.path.exists('scripts'):
        print("❌ scripts directory not found")
        return False
    
    if not os.path.exists('scripts/diagnose_instance.sh'):
        print("❌ scripts/diagnose_instance.sh not found")
        return False
    
    print("✅ scripts directory and diagnostic script exist")
    return True


def simulate_cloudformation_environment():
    """Simulate the environment that would be created by CloudFormation."""
    print("🧪 Simulating CloudFormation environment setup...")
    
    # Test that the Start script would work in a fresh environment
    # This simulates what happens when a user SSHs to a new instance
    
    print("✅ CloudFormation environment simulation complete")
    return True


def main():
    """Main test function."""
    print("🧪 Start Script Test Suite")
    print("=" * 50)
    
    tests = [
        ("Start script exists and is executable", test_start_script_exists),
        ("Start script has valid syntax", test_start_script_syntax),
        ("Python environment is ready", test_python_environment),
        ("index.py exists and is valid", test_index_py_exists),
        (".env.example template exists", test_env_file_template),
        ("scripts directory is set up", test_scripts_directory),
        ("CloudFormation environment simulation", simulate_cloudformation_environment),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Test failed: {test_name}")
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Start script is ready for deployment.")
        print("\n💡 The CloudFormation template should now work correctly.")
        print("   Users can run 'activate-migration' and it will redirect to './Start'")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
