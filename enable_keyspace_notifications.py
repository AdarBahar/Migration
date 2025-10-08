#!/usr/bin/env python3
"""
🔔 Enable Keyspace Notifications for RIOT-X Live Migration

This script enables Redis keyspace notifications on ElastiCache clusters
to support RIOT-X live migration functionality.

Usage:
    python3 enable_keyspace_notifications.py
    python3 enable_keyspace_notifications.py --host your-cluster.cache.amazonaws.com
    python3 enable_keyspace_notifications.py --cluster-id your-cluster-id
"""

import redis
import argparse
import os
import sys
from dotenv import load_dotenv

def load_env_config():
    """Load configuration from .env file."""
    load_dotenv()
    return {
        'host': os.getenv('REDIS_SOURCE_HOST'),
        'port': int(os.getenv('REDIS_SOURCE_PORT', 6379)),
        'password': os.getenv('REDIS_SOURCE_PASSWORD') or None,
        'use_tls': os.getenv('REDIS_SOURCE_TLS', 'false').lower() == 'true',
        'cluster_id': os.getenv('ELASTICACHE_CLUSTER_ID')
    }

def get_cluster_endpoint(cluster_id, region='eu-north-1'):
    """Get ElastiCache cluster endpoint from cluster ID."""
    try:
        import boto3
        client = boto3.client('elasticache', region_name=region)
        
        # Try replication groups first
        try:
            response = client.describe_replication_groups(ReplicationGroupId=cluster_id)
            if response['ReplicationGroups']:
                endpoint = response['ReplicationGroups'][0]['NodeGroups'][0]['PrimaryEndpoint']['Address']
                port = response['ReplicationGroups'][0]['NodeGroups'][0]['PrimaryEndpoint']['Port']
                return endpoint, port
        except:
            pass
        
        # Try single clusters
        try:
            response = client.describe_cache_clusters(CacheClusterId=cluster_id, ShowCacheNodeInfo=True)
            if response['CacheClusters']:
                cluster = response['CacheClusters'][0]
                endpoint = cluster['CacheNodes'][0]['Endpoint']['Address']
                port = cluster['CacheNodes'][0]['Endpoint']['Port']
                return endpoint, port
        except:
            pass
        
        # Try serverless
        try:
            response = client.describe_serverless_caches(ServerlessCacheName=cluster_id)
            if response['ServerlessCaches']:
                endpoint = response['ServerlessCaches'][0]['Endpoint']['Address']
                port = response['ServerlessCaches'][0]['Endpoint']['Port']
                return endpoint, port
        except:
            pass
        
        return None, None
    except Exception as e:
        print(f"❌ Error getting cluster endpoint: {e}")
        return None, None

def enable_keyspace_notifications(host, port=6379, password=None, use_tls=False):
    """Enable keyspace notifications on Redis/ElastiCache."""
    try:
        print(f"🔗 Connecting to Redis at {host}:{port}")

        # Create Redis connection
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=use_tls,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )

        # Test connection
        r.ping()
        print("✅ Connected successfully")

        # Check if this is ElastiCache by testing CONFIG command availability
        try:
            # Get current keyspace notifications setting
            current_setting = r.config_get('notify-keyspace-events')
            current_value = current_setting.get('notify-keyspace-events', '')

            print(f"\n📋 Current keyspace notifications: '{current_value}'")

            # Recommended setting for RIOT-X live migration
            recommended_setting = 'KEA'  # K=keyspace, E=keyevent, A=all events

            if current_value == recommended_setting:
                print(f"✅ Keyspace notifications already configured correctly: '{current_value}'")
                return True

            print(f"\n🔧 Setting keyspace notifications to: '{recommended_setting}'")
            print("   K = Keyspace events (published with __keyspace@<db>__ prefix)")
            print("   E = Keyevent events (published with __keyevent@<db>__ prefix)")
            print("   A = All events (alias for g$lshztdxe)")

            # Set keyspace notifications
            r.config_set('notify-keyspace-events', recommended_setting)

            # Verify the setting
            new_setting = r.config_get('notify-keyspace-events')
            new_value = new_setting.get('notify-keyspace-events', '')

            if new_value == recommended_setting:
                print(f"✅ Keyspace notifications enabled successfully: '{new_value}'")
                print("\n🎉 Your Redis instance is now ready for RIOT-X live migration!")
                print("\n📖 What this enables:")
                print("   • Real-time key change notifications")
                print("   • Live data synchronization during migration")
                print("   • Minimal downtime migration capability")
                return True
            else:
                print(f"❌ Failed to set keyspace notifications. Current: '{new_value}'")
                return False

        except redis.ResponseError as e:
            if "unknown command" in str(e).lower() or "config" in str(e).lower():
                print(f"\n❌ ElastiCache detected: CONFIG commands are restricted")
                print(f"🔧 ElastiCache requires parameter groups to configure Redis settings")
                print(f"\n💡 Use the ElastiCache parameter group configuration instead:")
                print(f"   python3 configure_elasticache_keyspace.py --cluster-id YOUR_CLUSTER_ID")
                print(f"\n📖 Or configure via AWS Console:")
                print(f"   1. Go to ElastiCache → Parameter Groups")
                print(f"   2. Create new parameter group or modify existing")
                print(f"   3. Set notify-keyspace-events = KEA")
                print(f"   4. Apply parameter group to your cluster")
                return False
            else:
                raise e
            
    except redis.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check if:")
        print("   • Host and port are correct")
        print("   • Security groups allow access")
        print("   • ElastiCache cluster is running")
        return False
    except redis.AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check if password is correct")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Enable keyspace notifications for RIOT-X live migration')
    parser.add_argument('--host', help='Redis host (overrides .env)')
    parser.add_argument('--port', type=int, default=6379, help='Redis port (default: 6379)')
    parser.add_argument('--password', help='Redis password (overrides .env)')
    parser.add_argument('--tls', action='store_true', help='Use TLS connection')
    parser.add_argument('--cluster-id', help='ElastiCache cluster ID (will lookup endpoint)')
    parser.add_argument('--region', default='eu-north-1', help='AWS region (default: eu-north-1)')
    
    args = parser.parse_args()
    
    print("🔔 RIOT-X Live Migration: Enable Keyspace Notifications")
    print("=" * 60)
    
    # Load configuration from .env if available
    env_config = load_env_config()
    
    # Determine connection details
    host = args.host or env_config['host']
    port = args.port if args.port != 6379 else env_config['port']
    password = args.password or env_config['password']
    use_tls = args.tls or env_config['use_tls']
    cluster_id = args.cluster_id or env_config['cluster_id']
    
    # If cluster ID provided, lookup endpoint
    if cluster_id and not host:
        print(f"🔍 Looking up endpoint for cluster: {cluster_id}")
        endpoint, endpoint_port = get_cluster_endpoint(cluster_id, args.region)
        if endpoint:
            host = endpoint
            port = endpoint_port or port
            print(f"✅ Found endpoint: {host}:{port}")
        else:
            print(f"❌ Could not find endpoint for cluster: {cluster_id}")
            sys.exit(1)
    
    if not host:
        print("❌ No Redis host specified. Use --host or configure .env file")
        print("\n💡 Examples:")
        print("   python3 enable_keyspace_notifications.py --host redis-cluster.cache.amazonaws.com")
        print("   python3 enable_keyspace_notifications.py --cluster-id my-cluster-id")
        sys.exit(1)
    
    print(f"📍 Target: {host}:{port}")
    print(f"🔐 TLS: {'Enabled' if use_tls else 'Disabled'}")
    print(f"🔑 Password: {'Set' if password else 'None'}")
    
    # Enable keyspace notifications
    success = enable_keyspace_notifications(host, port, password, use_tls)
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Run pre-flight check: python3 migration_preflight_check.py")
        print("2. Deploy RIOT-X migration with live sync enabled")
        print("3. Enjoy minimal downtime migration!")
    else:
        print("\n🔧 Troubleshooting:")
        print("• Check security groups allow access from your location")
        print("• Verify ElastiCache cluster is running and accessible")
        print("• Ensure correct host, port, and credentials")
        sys.exit(1)

if __name__ == "__main__":
    main()
