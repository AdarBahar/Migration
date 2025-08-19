#!/usr/bin/env python3
"""
🔒 ElastiCache Security Configuration Test

This script demonstrates the security configuration options for ElastiCache provisioning.
It shows how the ELASTICACHE_ALLOW_VPC_CIDR environment variable affects access control.

Usage:
    # Test with default security (security groups only)
    python test_security_config.py

    # Test with VPC-wide access enabled
    ELASTICACHE_ALLOW_VPC_CIDR=true python test_security_config.py

Author: Migration Project
"""

import os
import sys


def test_security_configuration():
    """Test and display security configuration options."""
    print("🔒 ElastiCache Security Configuration Test")
    print("=" * 50)
    
    # Check current environment variable
    allow_vpc_cidr = os.environ.get('ELASTICACHE_ALLOW_VPC_CIDR', 'false').lower() == 'true'
    
    print(f"\n📋 Current Configuration:")
    print(f"   Environment Variable: ELASTICACHE_ALLOW_VPC_CIDR={os.environ.get('ELASTICACHE_ALLOW_VPC_CIDR', 'false')}")
    print(f"   Parsed Value: {allow_vpc_cidr}")
    
    if allow_vpc_cidr:
        print(f"\n🔓 VPC-Wide Access Mode:")
        print(f"   ✅ ElastiCache will accept connections from entire VPC CIDR")
        print(f"   ✅ Supports both IPv4 and IPv6 VPC CIDRs")
        print(f"   ✅ Includes all associated CIDR blocks")
        print(f"   ⚠️  Any EC2 instance in the VPC can connect")
        print(f"   ⚠️  Less secure but more flexible")
        print(f"")
        print(f"   Security Group Rules Created:")
        print(f"   • Inbound TCP 6379 from specific EC2 security groups")
        print(f"   • Inbound TCP 6379 from all VPC IPv4 CIDRs")
        print(f"   • Inbound TCP 6379 from all VPC IPv6 CIDRs (if present)")
    else:
        print(f"\n🔒 Security Group Only Mode (Recommended):")
        print(f"   ✅ ElastiCache only accepts connections from specific security groups")
        print(f"   ✅ Follows least privilege principle")
        print(f"   ✅ More secure and controlled access")
        print(f"   ✅ Recommended for staging and production environments")
        print(f"")
        print(f"   Security Group Rules Created:")
        print(f"   • Inbound TCP 6379 from specific EC2 security groups only")
        print(f"   • No VPC CIDR rules (more restrictive)")
    
    print(f"\n💡 How to Change Configuration:")
    if allow_vpc_cidr:
        print(f"   To disable VPC-wide access:")
        print(f"   unset ELASTICACHE_ALLOW_VPC_CIDR")
        print(f"   # or")
        print(f"   export ELASTICACHE_ALLOW_VPC_CIDR=false")
    else:
        print(f"   To enable VPC-wide access:")
        print(f"   export ELASTICACHE_ALLOW_VPC_CIDR=true")
    
    print(f"\n🔧 Usage Examples:")
    print(f"   # Provision with current settings")
    print(f"   python provision_elasticache.py")
    print(f"")
    print(f"   # Provision with VPC-wide access (one-time)")
    print(f"   ELASTICACHE_ALLOW_VPC_CIDR=true python provision_elasticache.py")
    print(f"")
    print(f"   # Set permanently for session")
    print(f"   export ELASTICACHE_ALLOW_VPC_CIDR=true")
    print(f"   python provision_elasticache.py")
    
    print(f"\n⚠️  Security Recommendations:")
    print(f"   • Development: Either mode is acceptable")
    print(f"   • Staging: Use security group only mode (default)")
    print(f"   • Production: Use security group only mode (default)")
    print(f"   • Only enable VPC CIDR access if you need broad connectivity")
    print(f"   • Consider using specific security group rules instead")
    
    return allow_vpc_cidr


def demonstrate_ip_permissions_structure():
    """Demonstrate the correct IpPermissions structure."""
    print(f"\n📋 Correct AWS IpPermissions Structure:")
    print(f"=" * 50)
    
    print(f"\n✅ Correct Structure (what we use now):")
    print(f"""
    IpPermissions=[
        {{
            'IpProtocol': 'tcp',
            'FromPort': 6379,
            'ToPort': 6379,
            'IpRanges': [
                {{
                    'CidrIp': '10.0.0.0/16',
                    'Description': 'Redis access from VPC CIDR'
                }}
            ],
            'Ipv6Ranges': [
                {{
                    'CidrIpv6': '2001:db8::/32',
                    'Description': 'Redis access from VPC IPv6 CIDR'
                }}
            ]
        }}
    ]
    """)
    
    print(f"\n❌ Incorrect Structure (what was used before):")
    print(f"""
    IpPermissions=[
        {{
            'IpProtocol': 'tcp',
            'FromPort': 6379,
            'ToPort': 6379,
            'CidrIp': '10.0.0.0/16',  # ❌ Invalid - CidrIp not allowed here
            'Description': 'Redis access from VPC CIDR'
        }}
    ]
    """)
    
    print(f"\n💡 Key Differences:")
    print(f"   • CidrIp must be inside IpRanges array, not at top level")
    print(f"   • IPv6 ranges go in separate Ipv6Ranges array")
    print(f"   • Each range can have its own Description")
    print(f"   • Structure supports multiple CIDR blocks per rule")


def main():
    """Main function."""
    print(__doc__)
    
    # Test current configuration
    current_mode = test_security_configuration()
    
    # Demonstrate correct structure
    demonstrate_ip_permissions_structure()
    
    print(f"\n✅ Security configuration test completed!")
    print(f"📍 Current mode: {'VPC-wide access' if current_mode else 'Security group only'}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
