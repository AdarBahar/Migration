#!/usr/bin/env python3
"""
Example usage of the RIOT-X Migration Pre-flight Checker

This script demonstrates how to use the migration_preflight_check.py script
programmatically and how to integrate it with CloudFormation deployment.

Author: Migration Tool
Version: 1.0.0
"""

import subprocess
import sys
import json
from typing import Dict, Any, Optional

def run_preflight_check(source_cluster: str, target_uri: str, 
                       region: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Run the pre-flight checker and return results.
    
    Args:
        source_cluster: ElastiCache cluster ID
        target_uri: Target Redis Cloud URI
        region: AWS region (optional)
        verbose: Enable verbose output
        
    Returns:
        Dictionary with check results and status
    """
    cmd = [
        'python3', 'migration_preflight_check.py',
        '--source-cluster', source_cluster,
        '--target-uri', target_uri
    ]
    
    if region:
        cmd.extend(['--region', region])
    
    if verbose:
        cmd.append('--verbose')
    
    try:
        print(f"🔍 Running pre-flight check for cluster: {source_cluster}")
        print(f"🎯 Target: {target_uri}")
        print("=" * 60)
        
        # Run the pre-flight checker
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': 'Pre-flight check timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': f'Failed to run pre-flight check: {e}'
        }

def deploy_cloudformation_if_ready(source_cluster: str, target_uri: str, 
                                 stack_name: str = 'riotx-migration',
                                 region: Optional[str] = None) -> bool:
    """
    Run pre-flight check and deploy CloudFormation if all checks pass.
    
    Args:
        source_cluster: ElastiCache cluster ID
        target_uri: Target Redis Cloud URI
        stack_name: CloudFormation stack name
        region: AWS region
        
    Returns:
        True if deployment was successful, False otherwise
    """
    print("🚀 RIOT-X Migration Deployment Pipeline")
    print("=" * 60)
    
    # Step 1: Run pre-flight check
    print("\n📋 Step 1: Running Pre-flight Validation...")
    preflight_result = run_preflight_check(source_cluster, target_uri, region, verbose=False)
    
    # Print the pre-flight output
    if preflight_result['stdout']:
        print(preflight_result['stdout'])
    
    if preflight_result['stderr']:
        print(f"❌ Errors: {preflight_result['stderr']}")
    
    if not preflight_result['success']:
        print("\n❌ Pre-flight check failed. Cannot proceed with deployment.")
        print("🔧 Please fix the issues above and try again.")
        return False
    
    print("\n✅ Pre-flight check passed! Proceeding with CloudFormation deployment...")
    
    # Step 2: Deploy CloudFormation
    print("\n📋 Step 2: Deploying CloudFormation Stack...")
    
    cf_cmd = [
        'aws', 'cloudformation', 'create-stack',
        '--stack-name', stack_name,
        '--template-url', 'https://riot-x.s3.amazonaws.com/ec-sync.yaml',
        '--parameters',
        f'ParameterKey=SourceElastiCacheClusterId,ParameterValue={source_cluster}',
        f'ParameterKey=TargetRedisURI,ParameterValue={target_uri}',
        '--capabilities', 'CAPABILITY_IAM'
    ]
    
    if region:
        cf_cmd.extend(['--region', region])
    
    try:
        print(f"🚀 Creating CloudFormation stack: {stack_name}")
        cf_result = subprocess.run(cf_cmd, capture_output=True, text=True, timeout=60)
        
        if cf_result.returncode == 0:
            print("✅ CloudFormation stack creation initiated successfully!")
            print(f"📊 Stack ARN: {cf_result.stdout.strip()}")
            print(f"\n🔗 Monitor progress at:")
            print(f"   https://console.aws.amazon.com/cloudformation/home?region={region or 'us-east-1'}#/stacks")
            return True
        else:
            print(f"❌ CloudFormation deployment failed:")
            print(f"   Error: {cf_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CloudFormation deployment timed out")
        return False
    except Exception as e:
        print(f"❌ Failed to deploy CloudFormation: {e}")
        return False

def main():
    """Example usage of the pre-flight checker."""
    
    # Example 1: Basic pre-flight check
    print("📋 Example 1: Basic Pre-flight Check")
    print("=" * 50)
    
    # Replace these with your actual values
    example_cluster = "my-elasticache-cluster"
    example_target = "redis://username:password@redis-cloud.com:6379"
    example_region = "us-east-1"
    
    print(f"ℹ️  This is an example. Replace with your actual values:")
    print(f"   Source Cluster: {example_cluster}")
    print(f"   Target URI: redis://username:***@redis-cloud.com:6379")
    print(f"   Region: {example_region}")
    print()
    
    # Uncomment to run actual check:
    # result = run_preflight_check(example_cluster, example_target, example_region)
    # print(f"Check result: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
    
    print("💡 To run actual check, uncomment the lines in this script and provide real values.")
    
    # Example 2: Full deployment pipeline
    print("\n📋 Example 2: Full Deployment Pipeline")
    print("=" * 50)
    
    print("ℹ️  This example shows how to integrate pre-flight check with CloudFormation:")
    print()
    print("```python")
    print("# Run pre-flight check and deploy if successful")
    print("success = deploy_cloudformation_if_ready(")
    print("    source_cluster='my-cluster',")
    print("    target_uri='redis://user:pass@redis-cloud.com:6379',")
    print("    stack_name='my-migration-stack',")
    print("    region='us-east-1'")
    print(")")
    print("```")
    
    # Example 3: Command line usage
    print("\n📋 Example 3: Command Line Usage")
    print("=" * 50)
    
    print("🔧 Direct command line usage:")
    print()
    print("# Basic check")
    print("python3 migration_preflight_check.py \\")
    print("  --source-cluster my-elasticache-cluster \\")
    print("  --target-uri redis://user:pass@redis-cloud.com:6379")
    print()
    print("# With verbose output and specific region")
    print("python3 migration_preflight_check.py \\")
    print("  --source-cluster my-cluster \\")
    print("  --target-uri rediss://user:pass@redis-cloud.com:6380 \\")
    print("  --region us-west-2 \\")
    print("  --verbose")
    
    print("\n✅ Ready to use! Modify the examples above with your actual cluster details.")

if __name__ == "__main__":
    main()
