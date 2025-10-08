#!/usr/bin/env python3
"""
🔔 Configure ElastiCache Keyspace Notifications via Parameter Groups

ElastiCache doesn't allow direct CONFIG SET commands for security reasons.
This script creates/modifies parameter groups to enable keyspace notifications.

Usage:
    python3 configure_elasticache_keyspace.py --cluster-id redis-elasticache-1759926962
    python3 configure_elasticache_keyspace.py --cluster-id redis-elasticache-1759926962 --region eu-north-1
"""

import boto3
import argparse
import sys
import time
from datetime import datetime

def get_cluster_info(cluster_id, region='eu-north-1'):
    """Get ElastiCache cluster information."""
    try:
        client = boto3.client('elasticache', region_name=region)
        
        # Try replication groups first
        try:
            response = client.describe_replication_groups(ReplicationGroupId=cluster_id)
            if response['ReplicationGroups']:
                rg = response['ReplicationGroups'][0]
                return {
                    'type': 'replication_group',
                    'id': cluster_id,
                    'parameter_group': rg.get('CacheParameterGroup', {}).get('CacheParameterGroupName'),
                    'engine': rg.get('Engine', 'redis'),
                    'engine_version': rg.get('EngineVersion'),
                    'status': rg.get('Status')
                }
        except:
            pass
        
        # Try single clusters
        try:
            response = client.describe_cache_clusters(CacheClusterId=cluster_id)
            if response['CacheClusters']:
                cluster = response['CacheClusters'][0]
                return {
                    'type': 'cluster',
                    'id': cluster_id,
                    'parameter_group': cluster.get('CacheParameterGroup', {}).get('CacheParameterGroupName'),
                    'engine': cluster.get('Engine', 'redis'),
                    'engine_version': cluster.get('EngineVersion'),
                    'status': cluster.get('CacheClusterStatus')
                }
        except:
            pass
        
        # Try serverless
        try:
            response = client.describe_serverless_caches(ServerlessCacheName=cluster_id)
            if response['ServerlessCaches']:
                cache = response['ServerlessCaches'][0]
                return {
                    'type': 'serverless',
                    'id': cluster_id,
                    'parameter_group': None,  # Serverless doesn't use parameter groups
                    'engine': cache.get('Engine', 'redis'),
                    'engine_version': cache.get('EngineVersion'),
                    'status': cache.get('Status')
                }
        except:
            pass
        
        return None
    except Exception as e:
        print(f"❌ Error getting cluster info: {e}")
        return None

def create_parameter_group(client, group_name, family, description):
    """Create a new parameter group."""
    try:
        response = client.create_cache_parameter_group(
            CacheParameterGroupName=group_name,
            CacheParameterGroupFamily=family,
            Description=description
        )
        print(f"✅ Created parameter group: {group_name}")
        return True
    except client.exceptions.CacheParameterGroupAlreadyExistsFault:
        print(f"ℹ️  Parameter group already exists: {group_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to create parameter group: {e}")
        return False

def modify_parameter_group(client, group_name):
    """Modify parameter group to enable keyspace notifications."""
    try:
        response = client.modify_cache_parameter_group(
            CacheParameterGroupName=group_name,
            ParameterNameValues=[
                {
                    'ParameterName': 'notify-keyspace-events',
                    'ParameterValue': 'KEA'
                }
            ]
        )
        print(f"✅ Modified parameter group: {group_name}")
        print(f"   📋 Set notify-keyspace-events = KEA")
        return True
    except Exception as e:
        print(f"❌ Failed to modify parameter group: {e}")
        return False

def apply_parameter_group_to_cluster(client, cluster_info, parameter_group_name):
    """Apply parameter group to cluster."""
    try:
        if cluster_info['type'] == 'replication_group':
            response = client.modify_replication_group(
                ReplicationGroupId=cluster_info['id'],
                CacheParameterGroupName=parameter_group_name,
                ApplyImmediately=True
            )
        elif cluster_info['type'] == 'cluster':
            response = client.modify_cache_cluster(
                CacheClusterId=cluster_info['id'],
                CacheParameterGroupName=parameter_group_name,
                ApplyImmediately=True
            )
        else:
            print(f"❌ Serverless caches don't support custom parameter groups")
            return False
        
        print(f"✅ Applied parameter group to cluster: {cluster_info['id']}")
        print(f"   📋 Parameter group: {parameter_group_name}")
        print(f"   ⚡ Applied immediately: Yes")
        return True
    except Exception as e:
        print(f"❌ Failed to apply parameter group: {e}")
        return False

def wait_for_cluster_modification(client, cluster_info, timeout_minutes=10):
    """Wait for cluster modification to complete."""
    print(f"⏳ Waiting for cluster modification to complete...")
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while time.time() - start_time < timeout_seconds:
        try:
            if cluster_info['type'] == 'replication_group':
                response = client.describe_replication_groups(ReplicationGroupId=cluster_info['id'])
                status = response['ReplicationGroups'][0]['Status']
            else:
                response = client.describe_cache_clusters(CacheClusterId=cluster_info['id'])
                status = response['CacheClusters'][0]['CacheClusterStatus']
            
            print(f"   📊 Status: {status}")
            
            if status == 'available':
                print(f"✅ Cluster modification completed successfully")
                return True
            elif status in ['failed', 'incompatible-parameters']:
                print(f"❌ Cluster modification failed with status: {status}")
                return False
            
            time.sleep(30)
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
            time.sleep(30)
    
    print(f"⏰ Timeout waiting for modification to complete")
    return False

def main():
    parser = argparse.ArgumentParser(description='Configure ElastiCache keyspace notifications via parameter groups')
    parser.add_argument('--cluster-id', required=True, help='ElastiCache cluster ID')
    parser.add_argument('--region', default='eu-north-1', help='AWS region (default: eu-north-1)')
    parser.add_argument('--parameter-group-name', help='Custom parameter group name (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    print("🔔 ElastiCache Keyspace Notifications Configuration")
    print("=" * 60)
    print(f"📍 Cluster ID: {args.cluster_id}")
    print(f"📍 Region: {args.region}")
    print()
    
    # Get cluster information
    print("🔍 Getting cluster information...")
    cluster_info = get_cluster_info(args.cluster_id, args.region)
    
    if not cluster_info:
        print(f"❌ Could not find cluster: {args.cluster_id}")
        sys.exit(1)
    
    print(f"✅ Found cluster:")
    print(f"   📋 Type: {cluster_info['type']}")
    print(f"   📋 Engine: {cluster_info['engine']} {cluster_info['engine_version']}")
    print(f"   📋 Status: {cluster_info['status']}")
    print(f"   📋 Current parameter group: {cluster_info['parameter_group']}")
    
    # Check if serverless
    if cluster_info['type'] == 'serverless':
        print(f"\n❌ ElastiCache Serverless doesn't support custom parameter groups")
        print(f"💡 Keyspace notifications cannot be configured on serverless caches")
        print(f"💡 Consider using a node-based cluster for live migration features")
        sys.exit(1)
    
    # Determine parameter group family
    engine_version = cluster_info['engine_version']
    if engine_version.startswith('7.'):
        family = 'redis7.x'
    elif engine_version.startswith('6.'):
        family = 'redis6.x'
    elif engine_version.startswith('5.'):
        family = 'redis5.0'
    else:
        family = 'redis7.x'  # Default to latest
    
    print(f"   📋 Parameter group family: {family}")
    
    # Generate parameter group name if not provided
    if not args.parameter_group_name:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        parameter_group_name = f"{args.cluster_id}-keyspace-{timestamp}"
    else:
        parameter_group_name = args.parameter_group_name
    
    print(f"   📋 Target parameter group: {parameter_group_name}")
    
    # Create ElastiCache client
    client = boto3.client('elasticache', region_name=args.region)
    
    # Step 1: Create parameter group
    print(f"\n🔧 Creating parameter group...")
    success = create_parameter_group(
        client, 
        parameter_group_name, 
        family, 
        f"Keyspace notifications for {args.cluster_id} - Created {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if not success:
        sys.exit(1)
    
    # Step 2: Modify parameter group
    print(f"\n🔧 Configuring keyspace notifications...")
    success = modify_parameter_group(client, parameter_group_name)
    
    if not success:
        sys.exit(1)
    
    # Step 3: Apply to cluster
    print(f"\n🔧 Applying parameter group to cluster...")
    success = apply_parameter_group_to_cluster(client, cluster_info, parameter_group_name)
    
    if not success:
        sys.exit(1)
    
    # Step 4: Wait for completion
    print(f"\n⏳ Waiting for changes to take effect...")
    success = wait_for_cluster_modification(client, cluster_info)
    
    if success:
        print(f"\n🎉 SUCCESS: Keyspace notifications enabled!")
        print(f"✅ Configuration: notify-keyspace-events = KEA")
        print(f"✅ Your ElastiCache cluster is now ready for RIOT-X live migration")
        print(f"\n🚀 Next steps:")
        print(f"1. Run pre-flight check: python3 migration_preflight_check.py")
        print(f"2. Deploy RIOT-X with live migration enabled")
        print(f"3. Enjoy minimal downtime migration!")
    else:
        print(f"\n❌ Configuration may have failed or timed out")
        print(f"💡 Check the AWS Console for cluster status")
        print(f"💡 Parameter group: {parameter_group_name}")

if __name__ == "__main__":
    main()
