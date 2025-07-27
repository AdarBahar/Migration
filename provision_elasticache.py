#!/usr/bin/env python3
"""
🚀 ElastiCache Redis Provisioning Tool

This script provisions an AWS ElastiCache Redis instance with proper configuration
to allow the current EC2 instance to connect to it.

Features:
- Creates ElastiCache Redis cluster
- Configures security groups for EC2 access
- Sets up subnet groups for proper networking
- Provides connection details for .env configuration
- Handles both single-node and cluster configurations

Author: Migration Project
"""

import boto3
import json
import time
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime
from elasticache_config import (
    DEFAULT_CONFIG,
    get_recommended_config,
    interactive_config_builder,
    validate_node_type,
    validate_engine_version,
    get_cost_estimate
)


class ElastiCacheProvisioner:
    def __init__(self):
        """Initialize the ElastiCache provisioner with AWS clients."""
        try:
            # Get region from EC2 metadata or default
            self.region = self.get_current_region()

            # Initialize AWS clients with explicit region
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.elasticache_client = boto3.client('elasticache', region_name=self.region)
            self.sts_client = boto3.client('sts', region_name=self.region)

            # Get current AWS account info
            self.account_id = self.sts_client.get_caller_identity()['Account']

            print(f"✅ AWS clients initialized successfully")
            print(f"📍 Account: {self.account_id}")
            print(f"📍 Region: {self.region}")

        except NoCredentialsError:
            print("❌ AWS credentials not found!")
            print("💡 Make sure to configure AWS credentials using one of:")
            print("   - AWS IAM Role (recommended for EC2)")
            print("   - AWS CLI: aws configure")
            print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)

    def get_current_region(self):
        """Get the current AWS region from various sources."""
        try:
            # Try to get region from EC2 metadata (works on EC2 instances)
            import urllib.request
            import urllib.error

            try:
                region = urllib.request.urlopen(
                    'http://169.254.169.254/latest/meta-data/placement/region',
                    timeout=2
                ).read().decode()
                print(f"🌍 Detected region from EC2 metadata: {region}")
                return region
            except (urllib.error.URLError, urllib.error.HTTPError):
                pass

            # Try to get from boto3 session
            session = boto3.Session()
            if session.region_name:
                print(f"🌍 Using region from boto3 session: {session.region_name}")
                return session.region_name

            # Try to get from AWS CLI config
            try:
                import subprocess
                result = subprocess.run(['aws', 'configure', 'get', 'region'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    region = result.stdout.strip()
                    print(f"🌍 Using region from AWS CLI config: {region}")
                    return region
            except:
                pass

            # Default to us-east-1
            print(f"🌍 Using default region: us-east-1")
            return 'us-east-1'

        except Exception as e:
            print(f"⚠️  Could not determine region, using default: us-east-1")
            return 'us-east-1'

    def get_current_instance_info(self):
        """Get information about the current EC2 instance."""
        try:
            # Try to get instance metadata (only works on EC2)
            import urllib.request
            import urllib.error
            
            # Get instance ID
            try:
                instance_id = urllib.request.urlopen(
                    'http://169.254.169.254/latest/meta-data/instance-id',
                    timeout=2
                ).read().decode()
                
                # Get VPC ID and subnet ID from instance
                response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
                instance = response['Reservations'][0]['Instances'][0]
                
                vpc_id = instance['VpcId']
                subnet_id = instance['SubnetId']
                security_groups = [sg['GroupId'] for sg in instance['SecurityGroups']]
                
                print(f"✅ Current EC2 instance detected: {instance_id}")
                print(f"📍 VPC: {vpc_id}")
                print(f"📍 Subnet: {subnet_id}")
                print(f"📍 Security Groups: {security_groups}")
                
                return {
                    'instance_id': instance_id,
                    'vpc_id': vpc_id,
                    'subnet_id': subnet_id,
                    'security_groups': security_groups
                }
                
            except (urllib.error.URLError, urllib.error.HTTPError):
                print("⚠️  Not running on EC2 or metadata service unavailable")
                return None
                
        except Exception as e:
            print(f"⚠️  Could not get EC2 instance info: {e}")
            return None

    def get_vpc_subnets(self, vpc_id):
        """Get all subnets in the VPC for subnet group creation."""
        try:
            response = self.ec2_client.describe_subnets(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            subnets = []
            for subnet in response['Subnets']:
                subnets.append({
                    'subnet_id': subnet['SubnetId'],
                    'availability_zone': subnet['AvailabilityZone'],
                    'cidr': subnet['CidrBlock']
                })
            
            print(f"✅ Found {len(subnets)} available subnets in VPC {vpc_id}")
            return subnets
            
        except Exception as e:
            print(f"❌ Failed to get VPC subnets: {e}")
            return []

    def create_security_group(self, vpc_id, source_security_groups):
        """Create a security group for ElastiCache that allows access from EC2."""
        sg_name = f"elasticache-redis-{int(time.time())}"
        sg_description = "Security group for ElastiCache Redis - allows access from EC2 instances"
        
        try:
            # Create security group
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description=sg_description,
                VpcId=vpc_id
            )
            
            sg_id = response['GroupId']
            print(f"✅ Created security group: {sg_id}")
            
            # Add inbound rule for Redis port (6379) from source security groups
            for source_sg in source_security_groups:
                self.ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 6379,
                            'ToPort': 6379,
                            'UserIdGroupPairs': [
                                {
                                    'GroupId': source_sg,
                                    'Description': f'Redis access from EC2 security group {source_sg}'
                                }
                            ]
                        }
                    ]
                )
                print(f"✅ Added inbound rule for Redis port 6379 from SG {source_sg}")
            
            # Tag the security group
            self.ec2_client.create_tags(
                Resources=[sg_id],
                Tags=[
                    {'Key': 'Name', 'Value': f'ElastiCache-Redis-{sg_name}'},
                    {'Key': 'Purpose', 'Value': 'ElastiCache Redis Access'},
                    {'Key': 'CreatedBy', 'Value': 'Migration-Tool'}
                ]
            )
            
            return sg_id
            
        except Exception as e:
            print(f"❌ Failed to create security group: {e}")
            return None

    def create_subnet_group(self, vpc_id, subnets):
        """Create ElastiCache subnet group."""
        subnet_group_name = f"redis-subnet-group-{int(time.time())}"
        
        try:
            # Use at least 2 subnets from different AZs for high availability
            subnet_ids = [subnet['subnet_id'] for subnet in subnets[:3]]  # Use up to 3 subnets
            
            if len(subnet_ids) < 2:
                print("⚠️  Warning: Less than 2 subnets available. ElastiCache requires multiple AZs for production.")
            
            response = self.elasticache_client.create_cache_subnet_group(
                CacheSubnetGroupName=subnet_group_name,
                CacheSubnetGroupDescription=f"Subnet group for ElastiCache Redis - VPC {vpc_id}",
                SubnetIds=subnet_ids
            )
            
            print(f"✅ Created subnet group: {subnet_group_name}")
            print(f"📍 Using subnets: {subnet_ids}")
            
            return subnet_group_name
            
        except Exception as e:
            print(f"❌ Failed to create subnet group: {e}")
            return None

    def create_elasticache_serverless(self, cache_name, security_group_id, subnet_group_name):
        """Create ElastiCache Serverless Redis cache."""
        try:
            print(f"🚀 Creating ElastiCache Serverless Redis cache: {cache_name}")
            print(f"📍 Engine: Redis OSS")
            print(f"📍 Type: Serverless")

            response = self.elasticache_client.create_serverless_cache(
                ServerlessCacheName=cache_name,
                Description="Migration testing",
                Engine='redis',
                CacheUsageLimits={
                    'DataStorage': {
                        'Maximum': 1,
                        'Unit': 'GB'
                    },
                    'ECPUPerSecond': {
                        'Maximum': 1000
                    }
                },
                SecurityGroupIds=[security_group_id],
                SubnetIds=self.get_subnet_ids_from_group(subnet_group_name),
                Tags=[
                    {'Key': 'Name', 'Value': f'Source-ElastiCache'},
                    {'Key': 'Purpose', 'Value': 'Migration Testing'},
                    {'Key': 'CreatedBy', 'Value': 'Migration-Tool'},
                    {'Key': 'Environment', 'Value': 'Development'}
                ]
            )

            print(f"✅ ElastiCache Serverless cache creation initiated: {cache_name}")
            return cache_name

        except Exception as e:
            print(f"❌ Failed to create ElastiCache Serverless cache: {e}")
            print(f"💡 Falling back to traditional cluster...")
            return self.create_elasticache_cluster_fallback(cache_name, security_group_id, subnet_group_name)

    def create_elasticache_cluster_fallback(self, cluster_id, security_group_id, subnet_group_name,
                                          node_type='cache.t3.micro', engine_version='7.0'):
        """Create traditional ElastiCache Redis cluster as fallback."""
        try:
            print(f"🚀 Creating ElastiCache Redis cluster: {cluster_id}")
            print(f"📍 Node Type: {node_type}")
            print(f"📍 Engine Version: {engine_version}")

            response = self.elasticache_client.create_cache_cluster(
                CacheClusterId=cluster_id,
                Engine='redis',
                EngineVersion=engine_version,
                CacheNodeType=node_type,
                NumCacheNodes=1,
                Port=6379,
                CacheSubnetGroupName=subnet_group_name,
                SecurityGroupIds=[security_group_id],
                Tags=[
                    {'Key': 'Name', 'Value': f'Source-ElastiCache'},
                    {'Key': 'Purpose', 'Value': 'Migration Testing'},
                    {'Key': 'CreatedBy', 'Value': 'Migration-Tool'},
                    {'Key': 'Environment', 'Value': 'Development'}
                ]
            )

            print(f"✅ ElastiCache cluster creation initiated: {cluster_id}")
            return cluster_id

        except Exception as e:
            print(f"❌ Failed to create ElastiCache cluster: {e}")
            return None

    def get_subnet_ids_from_group(self, subnet_group_name):
        """Get subnet IDs from a subnet group."""
        try:
            response = self.elasticache_client.describe_cache_subnet_groups(
                CacheSubnetGroupName=subnet_group_name
            )

            subnet_group = response['CacheSubnetGroups'][0]
            subnet_ids = [subnet['SubnetId'] for subnet in subnet_group['Subnets']]
            return subnet_ids

        except Exception as e:
            print(f"⚠️  Could not get subnet IDs from group: {e}")
            return []

    def wait_for_cache_available(self, cache_name, is_serverless=True, timeout_minutes=15):
        """Wait for ElastiCache (serverless or cluster) to become available."""
        cache_type = "serverless cache" if is_serverless else "cluster"
        print(f"⏳ Waiting for {cache_type} {cache_name} to become available...")
        print(f"⏱️  Timeout: {timeout_minutes} minutes")

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            try:
                if is_serverless:
                    # Check serverless cache status
                    response = self.elasticache_client.describe_serverless_caches(
                        ServerlessCacheName=cache_name
                    )

                    cache = response['ServerlessCaches'][0]
                    status = cache['Status']

                    print(f"📊 Serverless cache status: {status}")

                    if status == 'available':
                        endpoint = cache['Endpoint']
                        print(f"✅ Serverless cache is available!")
                        print(f"📍 Endpoint: {endpoint['Address']}:{endpoint['Port']}")
                        return {
                            'endpoint': endpoint['Address'],
                            'port': endpoint['Port'],
                            'status': status,
                            'type': 'serverless'
                        }
                    elif status in ['failed', 'deleting']:
                        print(f"❌ Serverless cache creation failed with status: {status}")
                        return None
                else:
                    # Check traditional cluster status
                    response = self.elasticache_client.describe_cache_clusters(
                        CacheClusterId=cache_name,
                        ShowCacheNodeInfo=True
                    )

                    cluster = response['CacheClusters'][0]
                    status = cluster['CacheClusterStatus']

                    print(f"📊 Cluster status: {status}")

                    if status == 'available':
                        endpoint = cluster['CacheNodes'][0]['Endpoint']
                        print(f"✅ Cluster is available!")
                        print(f"📍 Endpoint: {endpoint['Address']}:{endpoint['Port']}")
                        return {
                            'endpoint': endpoint['Address'],
                            'port': endpoint['Port'],
                            'status': status,
                            'type': 'cluster'
                        }
                    elif status in ['failed', 'incompatible-parameters', 'incompatible-network']:
                        print(f"❌ Cluster creation failed with status: {status}")
                        return None

                time.sleep(30)  # Wait 30 seconds before checking again

            except Exception as e:
                print(f"⚠️  Error checking {cache_type} status: {e}")
                time.sleep(30)

        print(f"⏰ Timeout waiting for {cache_type} to become available")
        return None

    def generate_env_config(self, cache_info, cache_name):
        """Generate .env configuration for the ElastiCache cache."""
        cache_type = "Serverless" if cache_info.get('type') == 'serverless' else "Cluster"
        config_lines = [
            f"# ElastiCache Redis Configuration - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Cache Name: {cache_name}",
            f"# Type: Redis OSS {cache_type}",
            f"# Description: Migration testing",
            f"",
            f"# ElastiCache Redis (Source)",
            f"REDIS_SOURCE_NAME={cache_name}",
            f"REDIS_SOURCE_HOST={cache_info['endpoint']}",
            f"REDIS_SOURCE_PORT={cache_info['port']}",
            f"REDIS_SOURCE_PASSWORD=",
            f"REDIS_SOURCE_TLS=false",
            f"REDIS_SOURCE_DB=0",
            f"",
            f"# Connection timeout",
            f"REDIS_TIMEOUT=5",
            f"",
            f"# Note: Configure your destination Redis using manage_env.py",
            f""
        ]

        return "\n".join(config_lines)

    def save_cache_info(self, cache_name, cache_info, security_group_id, subnet_group_name):
        """Save cache information to a file for future reference."""
        info = {
            'cache_name': cache_name,
            'cache_type': cache_info.get('type', 'cluster'),
            'endpoint': cache_info['endpoint'],
            'port': cache_info['port'],
            'security_group_id': security_group_id,
            'subnet_group_name': subnet_group_name,
            'created_at': datetime.now().isoformat(),
            'region': self.region,
            'account_id': self.account_id,
            'description': 'Migration testing'
        }

        filename = f"elasticache_{cache_name.replace('-', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(info, f, indent=2)

        print(f"💾 Cache information saved to: {filename}")
        return filename

    def provision_elasticache(self, config=None, interactive=True):
        """Main method to provision ElastiCache with proper configuration."""
        print("🚀 Starting ElastiCache Redis provisioning...")
        print("=" * 60)

        # Get configuration
        if config is None:
            if interactive:
                print("🔧 Let's configure your ElastiCache instance...")
                config = interactive_config_builder()
            else:
                config = get_recommended_config('development')
                print(f"📋 Using default development configuration")

        print(f"\n📋 Configuration Summary:")
        print(f"   Node Type: {config['node_type']}")
        print(f"   Engine Version: {config['engine_version']}")
        print(f"   Port: {config['port']}")

        # Show cost estimate
        cost_info = get_cost_estimate(config['node_type'])
        if cost_info:
            print(f"   Estimated Monthly Cost: ${cost_info['monthly']:.2f}")

        # Confirm before proceeding
        if interactive:
            confirm = input(f"\n🤔 Proceed with provisioning? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Provisioning cancelled by user")
                return False

        # Step 1: Get current instance information
        instance_info = self.get_current_instance_info()

        if not instance_info:
            print("❌ Could not determine EC2 instance information.")
            print("💡 Please ensure you're running this on an EC2 instance or provide VPC details manually.")
            return False

        vpc_id = instance_info['vpc_id']
        source_security_groups = instance_info['security_groups']

        # Step 2: Get VPC subnets
        subnets = self.get_vpc_subnets(vpc_id)
        if not subnets:
            print("❌ No available subnets found in VPC")
            return False

        # Step 3: Create security group
        print("\n📋 Creating security group...")
        security_group_id = self.create_security_group(vpc_id, source_security_groups)
        if not security_group_id:
            return False

        # Step 4: Create subnet group
        print("\n📋 Creating subnet group...")
        subnet_group_name = self.create_subnet_group(vpc_id, subnets)
        if not subnet_group_name:
            return False

        # Step 5: Create ElastiCache (Serverless by default)
        cache_name = "Source-ElastiCache"
        print(f"\n📋 Creating ElastiCache...")

        # Try serverless first, fallback to cluster if needed
        created_cache = self.create_elasticache_serverless(
            cache_name,
            security_group_id,
            subnet_group_name
        )

        if not created_cache:
            return False

        # Determine if it's serverless or cluster
        is_serverless = created_cache == cache_name

        # Step 6: Wait for cache to be available
        print(f"\n📋 Waiting for cache to become available...")
        cache_info = self.wait_for_cache_available(created_cache, is_serverless)
        if not cache_info:
            print("❌ Cache did not become available within timeout period")
            return False

        # Step 7: Generate configuration
        print(f"\n📋 Generating configuration...")
        env_config = self.generate_env_config(cache_info, created_cache)

        # Save to file
        env_filename = f"elasticache_{created_cache.replace('-', '_')}.env"
        with open(env_filename, 'w') as f:
            f.write(env_config)

        # Save cache info
        info_filename = self.save_cache_info(created_cache, cache_info, security_group_id, subnet_group_name)

        # Step 8: Display success information
        cache_type = "Serverless Cache" if cache_info.get('type') == 'serverless' else "Redis Cluster"
        print("\n" + "=" * 60)
        print(f"🎉 ElastiCache {cache_type} provisioned successfully!")
        print("=" * 60)
        print(f"📍 Cache Name: {created_cache}")
        print(f"📍 Type: Redis OSS {cache_type}")
        print(f"📍 Endpoint: {cache_info['endpoint']}:{cache_info['port']}")
        print(f"📍 Security Group: {security_group_id}")
        print(f"📍 Subnet Group: {subnet_group_name}")
        print(f"📍 Region: {self.region}")
        print("")
        print("📁 Files created:")
        print(f"   - {env_filename} (Environment configuration)")
        print(f"   - {info_filename} (Cache information)")
        print("")
        print("🔧 Next steps:")
        print("1. Copy the configuration from the .env file to your main .env file")
        print("2. Use manage_env.py to configure destination Redis if needed")
        print("3. Test connection with DB_compare.py or ReadWriteOps.py")
        print("")
        print("💡 To connect to this Redis cache:")
        print(f"   Host: {cache_info['endpoint']}")
        print(f"   Port: {cache_info['port']}")
        print(f"   Password: (none)")
        print(f"   TLS: No")
        print(f"   Description: Migration testing")

        return True


def main():
    """Main function to run the ElastiCache provisioner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🔧 ElastiCache Redis Provisioning Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python provision_elasticache.py                    # Interactive mode
  python provision_elasticache.py --auto             # Auto mode with defaults
  python provision_elasticache.py --node-type cache.t3.small --engine-version 7.0
        """
    )

    parser.add_argument('--auto', action='store_true',
                       help='Run in automatic mode with default configuration')
    parser.add_argument('--node-type', default=None,
                       help='ElastiCache node type (e.g., cache.t3.micro)')
    parser.add_argument('--engine-version', default=None,
                       help='Redis engine version (e.g., 7.0)')
    parser.add_argument('--environment', choices=['development', 'staging', 'production'],
                       default='development', help='Environment type for recommended settings')

    args = parser.parse_args()

    print("🔧 ElastiCache Redis Provisioning Tool")
    print("=" * 50)
    print("")

    # Prepare configuration
    config = None
    interactive = not args.auto

    if args.auto or args.node_type or args.engine_version:
        # Use command line arguments or defaults
        config = get_recommended_config(args.environment)

        if args.node_type:
            if validate_node_type(args.node_type):
                config['node_type'] = args.node_type
            else:
                print(f"❌ Invalid node type: {args.node_type}")
                sys.exit(1)

        if args.engine_version:
            if validate_engine_version(args.engine_version):
                config['engine_version'] = args.engine_version
            else:
                print(f"❌ Invalid engine version: {args.engine_version}")
                sys.exit(1)

        interactive = False
        print(f"📋 Using {args.environment} configuration with command line overrides")

    # Check if running with proper permissions
    try:
        provisioner = ElastiCacheProvisioner()
        success = provisioner.provision_elasticache(config=config, interactive=interactive)

        if success:
            print("\n✅ Provisioning completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Provisioning failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Provisioning interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
