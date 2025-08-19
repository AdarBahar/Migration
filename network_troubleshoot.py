#!/usr/bin/env python3
"""
🔍 Network Troubleshooting Tool for ElastiCache Connectivity

This script helps diagnose network connectivity issues between EC2 and ElastiCache.
It checks security groups, NACLs, routing, and performs connectivity tests.

Author: Migration Project
"""

import boto3
import json
import socket
import subprocess
import sys
from botocore.exceptions import ClientError, NoCredentialsError


class NetworkTroubleshooter:
    def __init__(self):
        """Initialize the network troubleshooter."""
        try:
            # Get region from EC2 metadata or default
            self.region = self.get_current_region()
            
            # Initialize AWS clients
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.elasticache_client = boto3.client('elasticache', region_name=self.region)
            
            print(f"✅ AWS clients initialized for region: {self.region}")
            
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)

    def get_current_region(self):
        """Get the current AWS region."""
        try:
            import urllib.request
            
            # Try IMDSv2 first
            try:
                token_request = urllib.request.Request(
                    'http://169.254.169.254/latest/api/token',
                    headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
                )
                token_request.get_method = lambda: 'PUT'
                
                with urllib.request.urlopen(token_request, timeout=5) as response:
                    token = response.read().decode().strip()
                
                region_request = urllib.request.Request(
                    'http://169.254.169.254/latest/meta-data/placement/region',
                    headers={'X-aws-ec2-metadata-token': token}
                )
                
                with urllib.request.urlopen(region_request, timeout=5) as response:
                    return response.read().decode().strip()
                    
            except:
                # Fallback to boto3 session
                session = boto3.Session()
                return session.region_name or 'us-east-1'
                
        except:
            return 'us-east-1'

    def get_current_instance_info(self):
        """Get current EC2 instance information."""
        try:
            import urllib.request
            
            # Get instance ID using IMDSv2
            token_request = urllib.request.Request(
                'http://169.254.169.254/latest/api/token',
                headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
            )
            token_request.get_method = lambda: 'PUT'
            
            with urllib.request.urlopen(token_request, timeout=5) as response:
                token = response.read().decode().strip()
            
            instance_request = urllib.request.Request(
                'http://169.254.169.254/latest/meta-data/instance-id',
                headers={'X-aws-ec2-metadata-token': token}
            )
            
            with urllib.request.urlopen(instance_request, timeout=5) as response:
                instance_id = response.read().decode().strip()
            
            # Get instance details
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                'instance_id': instance_id,
                'vpc_id': instance['VpcId'],
                'subnet_id': instance['SubnetId'],
                'security_groups': [sg['GroupId'] for sg in instance['SecurityGroups']],
                'private_ip': instance['PrivateIpAddress'],
                'public_ip': instance.get('PublicIpAddress', 'None')
            }
            
        except Exception as e:
            print(f"❌ Could not get EC2 instance info: {e}")
            return None

    def check_security_groups(self, instance_info, elasticache_sg_id=None):
        """Check security group configurations."""
        print("\n🔒 Checking Security Groups...")
        print("=" * 50)
        
        # Check EC2 security groups
        for sg_id in instance_info['security_groups']:
            try:
                response = self.ec2_client.describe_security_groups(GroupIds=[sg_id])
                sg = response['SecurityGroups'][0]
                
                print(f"\n📋 EC2 Security Group: {sg_id}")
                print(f"   Name: {sg.get('GroupName', 'N/A')}")
                print(f"   Description: {sg.get('Description', 'N/A')}")
                
                # Check outbound rules for Redis
                redis_outbound = False
                for rule in sg.get('SecurityGroupEgress', []):
                    if (rule.get('FromPort') == 6379 or 
                        rule.get('IpProtocol') == '-1' or
                        (rule.get('FromPort', 0) <= 6379 <= rule.get('ToPort', 65535))):
                        redis_outbound = True
                        print(f"   ✅ Outbound Redis (6379) allowed: {rule}")
                        break
                
                if not redis_outbound:
                    print(f"   ⚠️  No explicit outbound rule for Redis port 6379")
                    print(f"   💡 Consider adding outbound rule for port 6379")
                
            except Exception as e:
                print(f"   ❌ Error checking security group {sg_id}: {e}")
        
        # Check ElastiCache security group if provided
        if elasticache_sg_id:
            try:
                response = self.ec2_client.describe_security_groups(GroupIds=[elasticache_sg_id])
                sg = response['SecurityGroups'][0]
                
                print(f"\n📋 ElastiCache Security Group: {elasticache_sg_id}")
                print(f"   Name: {sg.get('GroupName', 'N/A')}")
                print(f"   Description: {sg.get('Description', 'N/A')}")
                
                # Check inbound rules for Redis
                redis_inbound = False
                for rule in sg.get('SecurityGroupIngress', []):
                    if rule.get('FromPort') == 6379:
                        redis_inbound = True
                        print(f"   ✅ Inbound Redis (6379) allowed: {rule}")
                
                if not redis_inbound:
                    print(f"   ❌ No inbound rule for Redis port 6379")
                
            except Exception as e:
                print(f"   ❌ Error checking ElastiCache security group: {e}")

    def check_network_acls(self, instance_info):
        """Check Network ACL configurations."""
        print("\n🛡️  Checking Network ACLs...")
        print("=" * 50)
        
        try:
            # Get subnet's network ACL
            response = self.ec2_client.describe_network_acls(
                Filters=[
                    {'Name': 'association.subnet-id', 'Values': [instance_info['subnet_id']]}
                ]
            )
            
            for nacl in response['NetworkAcls']:
                print(f"\n📋 Network ACL: {nacl['NetworkAclId']}")
                print(f"   VPC: {nacl['VpcId']}")
                print(f"   Default: {nacl.get('IsDefault', False)}")
                
                # Check for Redis port rules
                redis_rules = []
                for entry in nacl.get('Entries', []):
                    port_range = entry.get('PortRange', {})
                    from_port = port_range.get('From', 0)
                    to_port = port_range.get('To', 65535)
                    
                    if (entry.get('Protocol') == '6' and  # TCP
                        from_port <= 6379 <= to_port):
                        redis_rules.append(entry)
                
                if redis_rules:
                    print(f"   📍 Rules affecting Redis port 6379:")
                    for rule in redis_rules:
                        action = "ALLOW" if rule['RuleAction'] == 'allow' else "DENY"
                        direction = "Inbound" if rule['Egress'] == False else "Outbound"
                        print(f"      {direction} {action}: {rule}")
                else:
                    print(f"   ✅ Default NACL (allows all traffic)")
                    
        except Exception as e:
            print(f"❌ Error checking Network ACLs: {e}")

    def test_connectivity(self, host, port=6379, timeout=10):
        """Test TCP connectivity to a host and port."""
        print(f"\n🔍 Testing connectivity to {host}:{port}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f"✅ TCP connection successful")
                
                # Try Redis PING
                try:
                    sock.send(b"PING\r\n")
                    response = sock.recv(1024)
                    if b"PONG" in response:
                        print(f"✅ Redis PING successful")
                    else:
                        print(f"⚠️  Redis PING failed, but TCP works")
                except:
                    print(f"⚠️  Could not send Redis PING")
                
                return True
            else:
                print(f"❌ TCP connection failed (error code: {result})")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
        finally:
            try:
                sock.close()
            except:
                pass

    def run_diagnostics(self, elasticache_endpoint=None, elasticache_sg_id=None):
        """Run comprehensive network diagnostics."""
        print("🔍 Network Troubleshooting for ElastiCache Connectivity")
        print("=" * 60)
        
        # Get current instance info
        instance_info = self.get_current_instance_info()
        if not instance_info:
            print("❌ Could not get EC2 instance information")
            return False
        
        print(f"\n📍 Current EC2 Instance:")
        print(f"   Instance ID: {instance_info['instance_id']}")
        print(f"   VPC: {instance_info['vpc_id']}")
        print(f"   Subnet: {instance_info['subnet_id']}")
        print(f"   Private IP: {instance_info['private_ip']}")
        print(f"   Public IP: {instance_info['public_ip']}")
        print(f"   Security Groups: {instance_info['security_groups']}")
        
        # Check security groups
        self.check_security_groups(instance_info, elasticache_sg_id)
        
        # Check Network ACLs
        self.check_network_acls(instance_info)
        
        # Test connectivity if endpoint provided
        if elasticache_endpoint:
            self.test_connectivity(elasticache_endpoint)
        
        print(f"\n💡 Troubleshooting Tips:")
        print(f"   1. Ensure EC2 security groups allow outbound traffic on port 6379")
        print(f"   2. Ensure ElastiCache security group allows inbound traffic on port 6379")
        print(f"   3. Check that both EC2 and ElastiCache are in the same VPC")
        print(f"   4. Verify Network ACLs are not blocking traffic")
        print(f"   5. Ensure ElastiCache is in 'available' state")
        
        return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🔍 Network Troubleshooting Tool for ElastiCache",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--endpoint', 
                       help='ElastiCache endpoint to test connectivity')
    parser.add_argument('--elasticache-sg', 
                       help='ElastiCache security group ID to check')
    
    args = parser.parse_args()
    
    try:
        troubleshooter = NetworkTroubleshooter()
        success = troubleshooter.run_diagnostics(
            elasticache_endpoint=args.endpoint,
            elasticache_sg_id=args.elasticache_sg
        )
        
        if success:
            print("\n✅ Diagnostics completed")
        else:
            print("\n❌ Diagnostics failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Diagnostics interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
