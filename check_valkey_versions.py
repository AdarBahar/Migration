#!/usr/bin/env python3
"""
Check available Valkey versions in AWS ElastiCache
"""

import boto3
import json

def check_valkey_versions(region='eu-north-1'):
    """Check what Valkey versions are available in ElastiCache."""
    try:
        client = boto3.client('elasticache', region_name=region)
        
        print(f"🔍 Checking available Valkey versions in {region}...")
        
        # Get Valkey engine versions
        response = client.describe_cache_engine_versions(Engine='valkey')
        
        if response['CacheEngineVersions']:
            print(f"✅ Found {len(response['CacheEngineVersions'])} Valkey versions:")
            print()
            
            for version_info in response['CacheEngineVersions']:
                version = version_info['EngineVersion']
                description = version_info.get('CacheEngineDescription', 'N/A')
                parameter_group_family = version_info.get('CacheParameterGroupFamily', 'N/A')
                
                print(f"📦 Valkey {version}")
                print(f"   Description: {description}")
                print(f"   Parameter Group Family: {parameter_group_family}")
                print()
                
            # Get the latest version
            latest_version = response['CacheEngineVersions'][-1]['EngineVersion']
            print(f"🎯 Latest Valkey version: {latest_version}")
            return latest_version
        else:
            print("❌ No Valkey versions found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking Valkey versions: {e}")
        return None

def check_redis_versions(region='eu-north-1'):
    """Check Redis versions for comparison."""
    try:
        client = boto3.client('elasticache', region_name=region)
        
        print(f"🔍 Checking available Redis versions in {region}...")
        
        # Get Redis engine versions
        response = client.describe_cache_engine_versions(Engine='redis')
        
        if response['CacheEngineVersions']:
            print(f"✅ Found {len(response['CacheEngineVersions'])} Redis versions:")
            
            # Show only the latest few versions
            latest_versions = response['CacheEngineVersions'][-5:]
            for version_info in latest_versions:
                version = version_info['EngineVersion']
                parameter_group_family = version_info.get('CacheParameterGroupFamily', 'N/A')
                print(f"   📦 Redis {version} (Family: {parameter_group_family})")
                
    except Exception as e:
        print(f"❌ Error checking Redis versions: {e}")

if __name__ == "__main__":
    print("🔧 AWS ElastiCache Engine Version Checker")
    print("=" * 50)
    
    # Check Valkey versions
    valkey_version = check_valkey_versions()
    
    print()
    print("-" * 50)
    
    # Check Redis versions for comparison
    check_redis_versions()
    
    if valkey_version:
        print()
        print("💡 Recommended fix:")
        print(f"   Update DEFAULT_CONFIG['engine_version'] to '{valkey_version}' for Valkey")
        print("   Or add Valkey-specific version handling in the code")
