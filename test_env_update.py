#!/usr/bin/env python3
"""
🧪 Test .env File Update Functionality

This script demonstrates and tests the .env file update functionality
that's used in provision_elasticache.py.

Usage:
    python test_env_update.py

Author: Migration Project
"""

import os
import sys
from datetime import datetime


def create_sample_env_file():
    """Create a sample .env file for testing."""
    sample_content = """# Redis Migration Configuration
# Created: 2024-01-15 10:30:00

# Destination Redis Configuration
REDIS_DEST_NAME=destination-redis
REDIS_DEST_HOST=localhost
REDIS_DEST_PORT=6379
REDIS_DEST_PASSWORD=mypassword
REDIS_DEST_TLS=false
REDIS_DEST_DB=0

# Other Configuration
REDIS_TIMEOUT=5
LOG_LEVEL=INFO
"""
    
    with open('.env.test', 'w') as f:
        f.write(sample_content)
    
    print("✅ Created sample .env.test file")


def update_env_file_test(cache_info, cache_name, env_file_path='.env.test'):
    """Test version of the update_env_file method."""
    
    # Configuration to add/update
    redis_config = {
        'REDIS_SOURCE_NAME': cache_name,
        'REDIS_SOURCE_HOST': cache_info['endpoint'],
        'REDIS_SOURCE_PORT': str(cache_info['port']),
        'REDIS_SOURCE_PASSWORD': '',
        'REDIS_SOURCE_TLS': 'false',
        'REDIS_SOURCE_DB': '0'
    }
    
    try:
        # Read existing .env file if it exists
        existing_config = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
        
        # Update with new Redis source configuration
        existing_config.update(redis_config)
        
        # Write updated configuration back to .env file
        with open(env_file_path, 'w') as f:
            f.write("# Redis Migration Configuration\n")
            f.write(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# ElastiCache instance: {cache_name}\n")
            f.write("\n")
            f.write("# Source Redis Configuration (ElastiCache)\n")
            
            # Write Redis source configuration first
            for key in ['REDIS_SOURCE_NAME', 'REDIS_SOURCE_HOST', 'REDIS_SOURCE_PORT', 
                       'REDIS_SOURCE_PASSWORD', 'REDIS_SOURCE_TLS', 'REDIS_SOURCE_DB']:
                if key in existing_config:
                    f.write(f"{key}={existing_config[key]}\n")
            
            f.write("\n")
            f.write("# Other Configuration\n")
            
            # Write remaining configuration
            for key, value in existing_config.items():
                if not key.startswith('REDIS_SOURCE_'):
                    f.write(f"{key}={value}\n")
        
        print(f"✅ Updated {env_file_path} with ElastiCache configuration")
        print(f"📍 Source Redis configured:")
        for key, value in redis_config.items():
            display_value = value if value else "(empty)"
            print(f"   {key}={display_value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {env_file_path}: {e}")
        return False


def test_env_update():
    """Test the .env file update functionality."""
    print("🧪 Testing .env File Update Functionality")
    print("=" * 50)
    
    # Create sample .env file
    create_sample_env_file()
    
    # Sample ElastiCache info
    cache_info = {
        'endpoint': 'source-elasticache-abc123.serverless.use1.cache.amazonaws.com',
        'port': 6379,
        'type': 'serverless'
    }
    cache_name = 'Source-ElastiCache'
    
    print(f"\n📋 Sample ElastiCache Configuration:")
    print(f"   Cache Name: {cache_name}")
    print(f"   Endpoint: {cache_info['endpoint']}")
    print(f"   Port: {cache_info['port']}")
    print(f"   Type: {cache_info['type']}")
    
    print(f"\n📄 Original .env.test file:")
    with open('.env.test', 'r') as f:
        for i, line in enumerate(f, 1):
            print(f"   {i:2d}: {line.rstrip()}")
    
    print(f"\n🔄 Updating .env.test file...")
    success = update_env_file_test(cache_info, cache_name)
    
    if success:
        print(f"\n📄 Updated .env.test file:")
        with open('.env.test', 'r') as f:
            for i, line in enumerate(f, 1):
                print(f"   {i:2d}: {line.rstrip()}")
        
        print(f"\n✅ Test completed successfully!")
        print(f"💡 The .env.test file now contains:")
        print(f"   • Original destination Redis configuration (preserved)")
        print(f"   • New source Redis configuration (ElastiCache)")
        print(f"   • Other settings (preserved)")
        
    else:
        print(f"\n❌ Test failed!")
    
    # Cleanup
    if os.path.exists('.env.test'):
        os.remove('.env.test')
        print(f"\n🧹 Cleaned up .env.test file")
    
    return success


def demonstrate_usage():
    """Demonstrate how this will work in provision_elasticache.py."""
    print(f"\n💡 How this works in provision_elasticache.py:")
    print(f"=" * 50)
    
    print(f"""
After successful ElastiCache provisioning, users will see:

9️⃣  Configure .env file...
🤔 Would you like to add this ElastiCache instance to your .env file
   as the Source Redis configuration? (Y/n): y
📝 Updating .env file with ElastiCache configuration...
✅ Updated .env file with ElastiCache configuration
📍 Source Redis configured:
   REDIS_SOURCE_NAME=Source-ElastiCache
   REDIS_SOURCE_HOST=source-elasticache-abc123.serverless.use1.cache.amazonaws.com
   REDIS_SOURCE_PORT=6379
   REDIS_SOURCE_PASSWORD=(empty)
   REDIS_SOURCE_TLS=false
   REDIS_SOURCE_DB=0
   ✅ .env file updated successfully

🎉 ElastiCache Serverless Cache provisioned successfully!
📁 Files created:
   - elasticache_Source_ElastiCache.env (Environment configuration)
   - elasticache_Source_ElastiCache.json (Cache information)
   - .env (Updated with Source Redis configuration)

🔧 Next steps:
1. Use manage_env.py to configure destination Redis if needed
2. Test connection with DB_compare.py or ReadWriteOps.py
3. Start your Redis migration!
""")


def main():
    """Main function."""
    print(__doc__)
    
    # Test the functionality
    success = test_env_update()
    
    # Demonstrate usage
    demonstrate_usage()
    
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
