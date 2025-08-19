#!/usr/bin/env python3
"""
🧪 Test Migration Control Center

This script tests the functionality of the Migration Control Center
including environment detection and intelligent suggestions.

Usage:
    python test_migration_center.py

Author: Migration Project
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime


def create_test_env_file(configured=True):
    """Create a test .env file."""
    if configured:
        content = """# Redis Migration Configuration
# Test configuration

# Source Redis Configuration (ElastiCache)
REDIS_SOURCE_NAME=test-source
REDIS_SOURCE_HOST=test-source.cache.amazonaws.com
REDIS_SOURCE_PORT=6379
REDIS_SOURCE_PASSWORD=
REDIS_SOURCE_TLS=false
REDIS_SOURCE_DB=0

# Destination Redis Configuration
REDIS_DEST_NAME=test-dest
REDIS_DEST_HOST=localhost
REDIS_DEST_PORT=6379
REDIS_DEST_PASSWORD=testpass
REDIS_DEST_TLS=false
REDIS_DEST_DB=0

# Migration Settings
REDIS_TIMEOUT=5
LOG_LEVEL=INFO
"""
    else:
        content = """# Redis Migration Configuration
# Empty configuration

# Source Redis Configuration (ElastiCache)
REDIS_SOURCE_NAME=
REDIS_SOURCE_HOST=
REDIS_SOURCE_PORT=6379
REDIS_SOURCE_PASSWORD=
REDIS_SOURCE_TLS=false
REDIS_SOURCE_DB=0

# Destination Redis Configuration
REDIS_DEST_NAME=
REDIS_DEST_HOST=
REDIS_DEST_PORT=6379
REDIS_DEST_PASSWORD=
REDIS_DEST_TLS=false
REDIS_DEST_DB=0
"""
    
    with open('.env.test', 'w') as f:
        f.write(content)


def create_test_elasticache_file(exists=True):
    """Create a test ElastiCache configuration file."""
    if exists:
        config = {
            "cache_name": "test-elasticache",
            "cache_type": "serverless",
            "endpoint": "test-elasticache.serverless.use1.cache.amazonaws.com",
            "port": 6379,
            "security_group_id": "sg-test123",
            "subnet_group_name": "test-subnet-group",
            "created_at": datetime.now().isoformat(),
            "region": "us-east-1",
            "account_id": "123456789012",
            "description": "Test ElastiCache instance"
        }
        
        with open('elasticache_test_instance.json', 'w') as f:
            json.dump(config, f, indent=2)


def test_environment_detection():
    """Test environment detection functionality."""
    print("🧪 Testing Environment Detection")
    print("=" * 40)
    
    # Import the MigrationControlCenter class
    sys.path.insert(0, '.')
    from index import MigrationControlCenter
    
    control_center = MigrationControlCenter()
    
    # Test 1: No configuration
    print("\n📋 Test 1: No configuration files")
    suggestions = control_center.check_environment_status()
    print(f"   Suggestions found: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"   - {suggestion['message']} (Priority: {suggestion['priority']})")
    
    # Test 2: Empty .env file
    print("\n📋 Test 2: Empty .env configuration")
    create_test_env_file(configured=False)
    # Temporarily rename .env to .env.test for testing
    if os.path.exists('.env'):
        os.rename('.env', '.env.backup')
    os.rename('.env.test', '.env')
    
    suggestions = control_center.check_environment_status()
    print(f"   Suggestions found: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"   - {suggestion['message']} (Priority: {suggestion['priority']})")
    
    # Test 3: Configured .env file
    print("\n📋 Test 3: Configured .env file")
    os.rename('.env', '.env.test')
    create_test_env_file(configured=True)
    os.rename('.env.test', '.env')
    
    suggestions = control_center.check_environment_status()
    print(f"   Suggestions found: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"   - {suggestion['message']} (Priority: {suggestion['priority']})")
    
    # Test 4: With ElastiCache instance
    print("\n📋 Test 4: With ElastiCache instance")
    create_test_elasticache_file(exists=True)
    
    suggestions = control_center.check_environment_status()
    print(f"   Suggestions found: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"   - {suggestion['message']} (Priority: {suggestion['priority']})")
    
    # Cleanup
    if os.path.exists('.env.backup'):
        os.rename('.env', '.env.test')
        os.rename('.env.backup', '.env')
    else:
        os.remove('.env')
    
    if os.path.exists('elasticache_test_instance.json'):
        os.remove('elasticache_test_instance.json')
    
    print("\n✅ Environment detection tests completed!")


def test_menu_display():
    """Test menu display functionality."""
    print("\n🧪 Testing Menu Display")
    print("=" * 40)
    
    # Import the MigrationControlCenter class
    from index import MigrationControlCenter
    
    control_center = MigrationControlCenter()
    
    print("\n📋 Testing menu categories:")
    for category_key, category_name in control_center.categories.items():
        scripts_in_category = [s for s in control_center.scripts.values() if s['category'] == category_key]
        print(f"   {category_name}: {len(scripts_in_category)} scripts")
    
    print(f"\n📋 Total scripts available: {len(control_center.scripts)}")
    
    print("\n✅ Menu display tests completed!")


def demonstrate_usage():
    """Demonstrate how to use the Migration Control Center."""
    print("\n💡 Migration Control Center Usage")
    print("=" * 40)
    
    print("""
🚀 Getting Started:
1. Run './Start' to initialize the environment
2. The Start script will:
   - Create Python virtual environment
   - Install dependencies
   - Create initial .env file
   - Launch index.py automatically

🎯 Using the Control Center:
1. The index.py will show intelligent suggestions based on your environment
2. Follow the numbered suggestions for optimal workflow
3. Each script returns to the main menu when completed
4. Use 'h' for help and 'q' to quit

📋 Typical Workflow:
1. Provision ElastiCache (if not exists)
2. Configure Environment (if .env is empty)
3. Generate Test Data (if no data exists)
4. Compare Databases (to verify setup)
5. Run Migration Operations

🔧 Environment Detection:
- ✅/❌ Environment configuration status
- ✅/❌ ElastiCache instance availability
- 🔴/🟡 Priority suggestions (high/medium)
""")


def main():
    """Main function."""
    print("🧪 Migration Control Center Test Suite")
    print("=" * 50)
    
    try:
        # Test environment detection
        test_environment_detection()
        
        # Test menu display
        test_menu_display()
        
        # Demonstrate usage
        demonstrate_usage()
        
        print("\n✅ All tests completed successfully!")
        print("\n🚀 Ready to use Migration Control Center!")
        print("   Run './Start' to begin")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
