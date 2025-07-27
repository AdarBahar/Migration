#!/usr/bin/env python3
"""
🧹 ElastiCache Cleanup Tool

This script helps clean up ElastiCache resources created by the provisioning tool.
It can delete clusters, security groups, and subnet groups.

Features:
- List all ElastiCache clusters
- Delete specific clusters
- Clean up associated security groups and subnet groups
- Batch cleanup operations

Author: Migration Project
"""

import boto3
import json
import time
import sys
import os
import glob
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime


class ElastiCacheCleanup:
    def __init__(self):
        """Initialize the ElastiCache cleanup tool with AWS clients."""
        try:
            # Initialize AWS clients
            self.ec2_client = boto3.client('ec2')
            self.elasticache_client = boto3.client('elasticache')
            self.sts_client = boto3.client('sts')
            
            # Get current AWS account and region info
            self.account_id = self.sts_client.get_caller_identity()['Account']
            self.region = boto3.Session().region_name or 'us-east-1'
            
            print(f"✅ AWS clients initialized successfully")
            print(f"📍 Account: {self.account_id}")
            print(f"📍 Region: {self.region}")
            
        except NoCredentialsError:
            print("❌ AWS credentials not found!")
            print("💡 Make sure to configure AWS credentials")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)

    def list_elasticache_clusters(self):
        """List all ElastiCache clusters."""
        try:
            response = self.elasticache_client.describe_cache_clusters(ShowCacheNodeInfo=True)
            clusters = response['CacheClusters']
            
            if not clusters:
                print("📭 No ElastiCache clusters found")
                return []
            
            print(f"\n📋 Found {len(clusters)} ElastiCache cluster(s):")
            print("=" * 80)
            
            for cluster in clusters:
                cluster_id = cluster['CacheClusterId']
                status = cluster['CacheClusterStatus']
                node_type = cluster['CacheNodeType']
                engine = cluster['Engine']
                engine_version = cluster['EngineVersion']
                created = cluster['CacheClusterCreateTime'].strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"\n🔧 Cluster ID: {cluster_id}")
                print(f"   Status: {status}")
                print(f"   Engine: {engine} {engine_version}")
                print(f"   Node Type: {node_type}")
                print(f"   Created: {created}")
                
                if cluster['CacheNodes']:
                    endpoint = cluster['CacheNodes'][0]['Endpoint']
                    print(f"   Endpoint: {endpoint['Address']}:{endpoint['Port']}")
                
                # Check if this looks like a migration tool cluster
                if 'redis-migration-' in cluster_id:
                    print(f"   🏷️  Created by Migration Tool")
            
            return clusters
            
        except Exception as e:
            print(f"❌ Failed to list clusters: {e}")
            return []

    def delete_cluster(self, cluster_id, skip_final_snapshot=True):
        """Delete an ElastiCache cluster."""
        try:
            print(f"🗑️  Deleting cluster: {cluster_id}")
            
            response = self.elasticache_client.delete_cache_cluster(
                CacheClusterId=cluster_id,
                FinalSnapshotIdentifier=None if skip_final_snapshot else f"{cluster_id}-final-snapshot"
            )
            
            print(f"✅ Cluster deletion initiated: {cluster_id}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CacheClusterNotFoundFault':
                print(f"⚠️  Cluster not found: {cluster_id}")
            else:
                print(f"❌ Failed to delete cluster {cluster_id}: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to delete cluster {cluster_id}: {e}")
            return False

    def wait_for_cluster_deletion(self, cluster_id, timeout_minutes=10):
        """Wait for cluster to be deleted."""
        print(f"⏳ Waiting for cluster {cluster_id} to be deleted...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                response = self.elasticache_client.describe_cache_clusters(
                    CacheClusterId=cluster_id
                )
                
                if response['CacheClusters']:
                    status = response['CacheClusters'][0]['CacheClusterStatus']
                    print(f"📊 Cluster status: {status}")
                    
                    if status == 'deleting':
                        time.sleep(30)
                        continue
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'CacheClusterNotFoundFault':
                    print(f"✅ Cluster {cluster_id} has been deleted")
                    return True
            
            time.sleep(30)
        
        print(f"⏰ Timeout waiting for cluster deletion")
        return False

    def find_migration_security_groups(self):
        """Find security groups created by the migration tool."""
        try:
            response = self.ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'tag:CreatedBy', 'Values': ['Migration-Tool']},
                    {'Name': 'tag:Purpose', 'Values': ['ElastiCache Redis Access']}
                ]
            )
            
            return response['SecurityGroups']
            
        except Exception as e:
            print(f"❌ Failed to find security groups: {e}")
            return []

    def delete_security_group(self, sg_id):
        """Delete a security group."""
        try:
            print(f"🗑️  Deleting security group: {sg_id}")
            
            self.ec2_client.delete_security_group(GroupId=sg_id)
            print(f"✅ Security group deleted: {sg_id}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DependencyViolation':
                print(f"⚠️  Cannot delete security group {sg_id}: still in use")
            else:
                print(f"❌ Failed to delete security group {sg_id}: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to delete security group {sg_id}: {e}")
            return False

    def list_subnet_groups(self):
        """List ElastiCache subnet groups."""
        try:
            response = self.elasticache_client.describe_cache_subnet_groups()
            subnet_groups = response['CacheSubnetGroups']
            
            migration_groups = []
            for group in subnet_groups:
                if 'redis-subnet-group-' in group['CacheSubnetGroupName']:
                    migration_groups.append(group)
            
            return migration_groups
            
        except Exception as e:
            print(f"❌ Failed to list subnet groups: {e}")
            return []

    def delete_subnet_group(self, subnet_group_name):
        """Delete a subnet group."""
        try:
            print(f"🗑️  Deleting subnet group: {subnet_group_name}")
            
            self.elasticache_client.delete_cache_subnet_group(
                CacheSubnetGroupName=subnet_group_name
            )
            print(f"✅ Subnet group deleted: {subnet_group_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CacheSubnetGroupInUse':
                print(f"⚠️  Cannot delete subnet group {subnet_group_name}: still in use")
            else:
                print(f"❌ Failed to delete subnet group {subnet_group_name}: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to delete subnet group {subnet_group_name}: {e}")
            return False

    def load_cluster_info_files(self):
        """Load cluster information from saved JSON files."""
        info_files = glob.glob("elasticache_cluster_*.json")
        cluster_info = []
        
        for file_path in info_files:
            try:
                with open(file_path, 'r') as f:
                    info = json.load(f)
                    cluster_info.append({
                        'file': file_path,
                        'info': info
                    })
            except Exception as e:
                print(f"⚠️  Could not load {file_path}: {e}")
        
        return cluster_info

    def cleanup_migration_resources(self):
        """Clean up all resources created by the migration tool."""
        print("🧹 Starting cleanup of migration tool resources...")
        print("=" * 60)
        
        # Load cluster info from files
        cluster_info_files = self.load_cluster_info_files()
        
        if cluster_info_files:
            print(f"\n📁 Found {len(cluster_info_files)} cluster info file(s)")
            for item in cluster_info_files:
                info = item['info']
                print(f"   - {info['cluster_id']} (created: {info['created_at']})")
        
        # List current clusters
        clusters = self.list_elasticache_clusters()
        migration_clusters = [c for c in clusters if 'redis-migration-' in c['CacheClusterId']]
        
        if not migration_clusters and not cluster_info_files:
            print("✅ No migration tool resources found to clean up")
            return True
        
        # Confirm cleanup
        print(f"\n🤔 This will delete:")
        if migration_clusters:
            print(f"   - {len(migration_clusters)} ElastiCache cluster(s)")
        
        security_groups = self.find_migration_security_groups()
        if security_groups:
            print(f"   - {len(security_groups)} security group(s)")
        
        subnet_groups = self.list_subnet_groups()
        if subnet_groups:
            print(f"   - {len(subnet_groups)} subnet group(s)")
        
        confirm = input(f"\n⚠️  Are you sure you want to proceed? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Cleanup cancelled by user")
            return False
        
        # Delete clusters first
        deleted_clusters = []
        for cluster in migration_clusters:
            cluster_id = cluster['CacheClusterId']
            if self.delete_cluster(cluster_id):
                deleted_clusters.append(cluster_id)
        
        # Wait for clusters to be deleted
        for cluster_id in deleted_clusters:
            self.wait_for_cluster_deletion(cluster_id)
        
        # Delete security groups
        for sg in security_groups:
            self.delete_security_group(sg['GroupId'])
        
        # Delete subnet groups
        for sg in subnet_groups:
            self.delete_subnet_group(sg['CacheSubnetGroupName'])
        
        # Clean up info files
        for item in cluster_info_files:
            try:
                os.remove(item['file'])
                print(f"🗑️  Removed info file: {item['file']}")
            except Exception as e:
                print(f"⚠️  Could not remove {item['file']}: {e}")
        
        print("\n✅ Cleanup completed!")
        return True


def main():
    """Main function for the cleanup tool."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🧹 ElastiCache Cleanup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all ElastiCache clusters')
    parser.add_argument('--delete', metavar='CLUSTER_ID',
                       help='Delete a specific cluster')
    parser.add_argument('--cleanup-all', action='store_true',
                       help='Clean up all migration tool resources')
    
    args = parser.parse_args()
    
    print("🧹 ElastiCache Cleanup Tool")
    print("=" * 40)
    print("")
    
    try:
        cleanup = ElastiCacheCleanup()
        
        if args.list:
            cleanup.list_elasticache_clusters()
        elif args.delete:
            if cleanup.delete_cluster(args.delete):
                cleanup.wait_for_cluster_deletion(args.delete)
        elif args.cleanup_all:
            cleanup.cleanup_migration_resources()
        else:
            # Interactive mode
            cleanup.list_elasticache_clusters()
            print("\n💡 Use --help to see available options")
            
    except KeyboardInterrupt:
        print("\n⚠️  Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
