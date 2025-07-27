#!/usr/bin/env python3
"""
🚀 Quick ElastiCache Provisioning Script

This script provisions ElastiCache with your exact requirements:
1. Redis OSS cache
2. Serverless
3. New Cache
4. Name: Source-ElastiCache
5. Description: Migration testing

Author: Migration Project
"""

from provision_elasticache import ElastiCacheProvisioner

def main():
    """Quick provisioning with predefined settings."""
    print("🚀 Quick ElastiCache Provisioning")
    print("=" * 40)
    print("")
    print("📋 Configuration:")
    print("   • Engine: Redis OSS")
    print("   • Type: Serverless")
    print("   • Name: Source-ElastiCache")
    print("   • Description: Migration testing")
    print("")
    
    try:
        # Initialize provisioner
        provisioner = ElastiCacheProvisioner()
        
        # Run provisioning with non-interactive mode
        success = provisioner.provision_elasticache(config=None, interactive=False)
        
        if success:
            print("\n✅ Quick provisioning completed successfully!")
            print("\n🔧 Next steps:")
            print("1. Check the generated .env file")
            print("2. Copy configuration to your main .env file")
            print("3. Test with: python DB_compare.py")
        else:
            print("\n❌ Quick provisioning failed!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Provisioning interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
