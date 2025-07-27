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
            print("💡 Make sure to configure AWS credentials using one of:")
            print("   - AWS IAM Role (recommended for EC2)")
            print("   - AWS CLI: aws configure")
            print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)

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

    def create_elasticache_cluster(self, cluster_id, security_group_id, subnet_group_name, 
                                 node_type='cache.t3.micro', engine_version='7.0'):
        """Create ElastiCache Redis cluster."""
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
                    {'Key': 'Name', 'Value': f'Redis-{cluster_id}'},
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

    def wait_for_cluster_available(self, cluster_id, timeout_minutes=15):
        """Wait for ElastiCache cluster to become available."""
        print(f"⏳ Waiting for cluster {cluster_id} to become available...")
        print(f"⏱️  Timeout: {timeout_minutes} minutes")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                response = self.elasticache_client.describe_cache_clusters(
                    CacheClusterId=cluster_id,
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
                        'status': status
                    }
                elif status in ['failed', 'incompatible-parameters', 'incompatible-network']:
                    print(f"❌ Cluster creation failed with status: {status}")
                    return None
                
                time.sleep(30)  # Wait 30 seconds before checking again
                
            except Exception as e:
                print(f"⚠️  Error checking cluster status: {e}")
                time.sleep(30)
        
        print(f"⏰ Timeout waiting for cluster to become available")
        return None

    def generate_env_config(self, cluster_info, cluster_id):
        """Generate .env configuration for the ElastiCache cluster."""
        config_lines = [
            f"# ElastiCache Redis Configuration - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Cluster ID: {cluster_id}",
            f"",
            f"# ElastiCache Redis (Destination)",
            f"REDIS_DEST_NAME=ElastiCache-{cluster_id}",
            f"REDIS_DEST_HOST={cluster_info['endpoint']}",
            f"REDIS_DEST_PORT={cluster_info['port']}",
            f"REDIS_DEST_PASSWORD=",
            f"REDIS_DEST_TLS=false",
            f"REDIS_DEST_DB=0",
            f"",
            f"# Connection timeout",
            f"REDIS_TIMEOUT=5",
            f""
        ]

        return "\n".join(config_lines)

    def save_cluster_info(self, cluster_id, cluster_info, security_group_id, subnet_group_name):
        """Save cluster information to a file for future reference."""
        info = {
            'cluster_id': cluster_id,
            'endpoint': cluster_info['endpoint'],
            'port': cluster_info['port'],
            'security_group_id': security_group_id,
            'subnet_group_name': subnet_group_name,
            'created_at': datetime.now().isoformat(),
            'region': self.region,
            'account_id': self.account_id
        }

        filename = f"elasticache_cluster_{cluster_id}.json"
        with open(filename, 'w') as f:
            json.dump(info, f, indent=2)

        print(f"💾 Cluster information saved to: {filename}")
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

        # Step 5: Create ElastiCache cluster
        cluster_id = f"redis-migration-{int(time.time())}"
        print(f"\n📋 Creating ElastiCache cluster...")

        if not self.create_elasticache_cluster(
            cluster_id,
            security_group_id,
            subnet_group_name,
            node_type=config['node_type'],
            engine_version=config['engine_version']
        ):
            return False

        # Step 6: Wait for cluster to be available
        print(f"\n📋 Waiting for cluster to become available...")
        cluster_info = self.wait_for_cluster_available(cluster_id)
        if not cluster_info:
            print("❌ Cluster did not become available within timeout period")
            return False

        # Step 7: Generate configuration
        print(f"\n📋 Generating configuration...")
        env_config = self.generate_env_config(cluster_info, cluster_id)

        # Save to file
        env_filename = f"elasticache_{cluster_id}.env"
        with open(env_filename, 'w') as f:
            f.write(env_config)

        # Save cluster info
        info_filename = self.save_cluster_info(cluster_id, cluster_info, security_group_id, subnet_group_name)

        # Step 8: Display success information
        print("\n" + "=" * 60)
        print("🎉 ElastiCache Redis cluster provisioned successfully!")
        print("=" * 60)
        print(f"📍 Cluster ID: {cluster_id}")
        print(f"📍 Endpoint: {cluster_info['endpoint']}:{cluster_info['port']}")
        print(f"📍 Security Group: {security_group_id}")
        print(f"📍 Subnet Group: {subnet_group_name}")
        print(f"📍 Region: {self.region}")
        print("")
        print("📁 Files created:")
        print(f"   - {env_filename} (Environment configuration)")
        print(f"   - {info_filename} (Cluster information)")
        print("")
        print("🔧 Next steps:")
        print("1. Copy the configuration from the .env file to your main .env file")
        print("2. Use manage_env.py to configure source Redis if needed")
        print("3. Test connection with DB_compare.py or ReadWriteOps.py")
        print("")
        print("💡 To connect to this Redis cluster:")
        print(f"   Host: {cluster_info['endpoint']}")
        print(f"   Port: {cluster_info['port']}")
        print(f"   Password: (none)")
        print(f"   TLS: No")

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
