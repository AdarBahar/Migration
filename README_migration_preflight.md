# RIOT-X Migration Pre-flight Checker

A comprehensive validation tool that ensures all requirements are met before running the RIOT-X CloudFormation migration template for ElastiCache to Redis Cloud migration.

## 🎯 Purpose

This script validates all prerequisites for the RIOT-X CloudFormation template to ensure successful migration from AWS ElastiCache to Redis Cloud. It checks:

- ✅ AWS credentials and IAM permissions
- ✅ ElastiCache cluster accessibility and configuration
- ✅ VPC and network connectivity requirements
- ✅ Target Redis Cloud connectivity
- ✅ ECS service prerequisites
- ✅ CloudFormation permissions

## 🚀 Quick Start

### Recommended: Use .env Configuration

```bash
# 1. Configure your .env file (see .env.migration example)
cp .env.migration .env
# Edit .env with your actual cluster ID and Redis Cloud details

# 2. Run pre-flight check
python3 migration_preflight_check.py
```

### Alternative: Command Line Parameters

```bash
python3 migration_preflight_check.py \
  --source-cluster my-elasticache-cluster \
  --target-uri redis://username:password@redis-cloud.com:6379
```

### With Verbose Output

```bash
python3 migration_preflight_check.py --verbose
```

## 📋 Command Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--source-cluster` | ❌* | ElastiCache cluster ID or replication group ID |
| `--target-uri` | ❌* | Target Redis Cloud URI (redis:// or rediss://) |
| `--region` | ❌ | AWS region (defaults to AWS config) |
| `--env-file` | ❌ | Path to .env configuration file (default: .env) |
| `--verbose` | ❌ | Enable detailed output with additional information |

*Required only if not configured in .env file

## 🔍 What It Checks

### 1. Configuration Source
- Validates .env file loading and parsing
- Shows which configuration variables were found
- Identifies missing required configuration

### 2. AWS Credentials & Basic Access
- Validates AWS credentials are configured
- Verifies STS access and identity

### 3. IAM Permissions
Tests all required permissions for CloudFormation template:
- **ElastiCache**: DescribeCacheClusters, DescribeReplicationGroups, DescribeServerlessCaches
- **EC2**: DescribeVpcs, DescribeSubnets, DescribeSecurityGroups, DescribeRouteTables
- **ECS**: DescribeClusters, ListClusters
- **CloudFormation**: CreateStack, DescribeStacks

### 4. ElastiCache Discovery
- Discovers source cluster (replication group, single cluster, or serverless)
- Extracts endpoint, port, VPC, subnets, and security groups
- Validates cluster accessibility and configuration

### 5. VPC & Network Discovery
- Discovers VPC details from ElastiCache configuration
- Identifies subnets and security groups
- Validates network configuration

### 6. Internet Connectivity
- Checks for Internet Gateway in VPC
- Validates default route for container image downloads
- Identifies if CloudFormation will need to create connectivity

### 7. Target Redis Validation
- Parses target Redis URI format (built from .env or provided directly)
- Tests TCP/TLS connectivity to target
- Validates hostname resolution

### 8. ECS Prerequisites
- Verifies ECS service availability in region
- Checks Fargate capacity provider access

### 9. CloudFormation Permissions
- Validates CloudFormation stack creation permissions

## ⚙️ .env Configuration

The script automatically reads configuration from a `.env` file, making it much easier to use. Copy `.env.migration` to `.env` and configure:

### Required Variables

```bash
# Source ElastiCache (choose one)
ELASTICACHE_CLUSTER_ID=my-elasticache-cluster
# OR
REDIS_SOURCE_HOST=my-cluster.abc123.cache.amazonaws.com

# Target Redis Cloud
REDIS_DEST_HOST=redis-15678.c123.eu-west-1-2.ec2.redns.redis-cloud.com
REDIS_DEST_PORT=15678
REDIS_DEST_PASSWORD=your-redis-cloud-password
REDIS_DEST_TLS=true
```

### Optional Variables

```bash
# Additional Redis settings
REDIS_SOURCE_PORT=6379
REDIS_SOURCE_PASSWORD=
REDIS_SOURCE_TLS=false
REDIS_SOURCE_DB=0
REDIS_DEST_DB=0
REDIS_TIMEOUT=5
LOG_LEVEL=INFO

# AWS settings (uses AWS CLI defaults if not specified)
AWS_REGION=us-east-1
AWS_PROFILE=default
```

### Benefits of .env Configuration

- ✅ **No command-line parameters needed** - just run `python3 migration_preflight_check.py`
- ✅ **Secure password handling** - passwords stay in .env file (add to .gitignore)
- ✅ **Consistent configuration** - same settings for pre-flight check and actual migration
- ✅ **Easy to share** - team members can use same configuration template

## 📊 Output Format

### Success Example
```
🚀 RIOT-X Migration Pre-flight Checker
==================================================
📁 Configuration: Loaded from .env
Source Cluster: my-redis-cluster
Target URI: rediss://***@redis-cloud.com:15678
Region: us-east-1
==================================================

📋 1. Configuration Source
✅ Configuration Source: Configuration loaded from .env

📋 2. AWS Credentials & Basic Access
✅ AWS Credentials: Valid credentials for arn:aws:iam::123456789012:user/migration-user

📋 3. IAM Permissions
✅ IAM Permission: DescribeCacheClusters: Permission verified for elasticache:DescribeCacheClusters
✅ IAM Permission: DescribeReplicationGroups: Permission verified for elasticache:DescribeReplicationGroups
...

📋 4. ElastiCache Discovery
✅ ElastiCache Discovery: Found replication group: my-cluster.abc123.cache.amazonaws.com:6379

==================================================
📊 SUMMARY
==================================================
✅ Passed: 16
❌ Failed: 0
⚠️  Warnings: 1
📊 Total: 17

🎉 SUCCESS: All critical checks passed!
✅ CloudFormation migration template should work successfully.
⚠️  Some warnings were found - review them above.
```

### Failure Example
```
❌ FAILURE: 3 critical issues found.
🔧 Fix the issues above before running CloudFormation template.

🔧 REMEDIATION SUMMARY:
   • IAM Permission: DescribeCacheClusters: Add IAM permission: elasticache:DescribeCacheClusters to your role/user
   • ElastiCache Discovery: Verify cluster ID exists in region us-east-1
   • Target Connectivity: Check target Redis Cloud configuration and network access
```

## 🔧 Common Issues & Solutions

### Missing IAM Permissions
**Issue**: `❌ IAM Permission: DescribeCacheClusters: Missing permission`

**Solution**: Add required permissions to your IAM role/user:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticache:DescribeCacheClusters",
                "elasticache:DescribeReplicationGroups",
                "elasticache:DescribeServerlessCaches",
                "elasticache:DescribeCacheSubnetGroups",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeRouteTables",
                "ec2:DescribeInternetGateways",
                "ecs:DescribeClusters",
                "ecs:ListClusters",
                "cloudformation:CreateStack",
                "cloudformation:DescribeStacks"
            ],
            "Resource": "*"
        }
    ]
}
```

### ElastiCache Cluster Not Found
**Issue**: `❌ ElastiCache Discovery: ElastiCache cluster 'my-cluster' not found`

**Solution**: 
1. Verify cluster ID: `aws elasticache describe-replication-groups`
2. Check region: `aws elasticache describe-cache-clusters --region us-west-2`
3. Ensure cluster is in `available` state

### Target Connectivity Issues
**Issue**: `❌ Target Connectivity: Connection timeout to redis-cloud.com:6379`

**Solutions**:
1. Check network connectivity from EC2 instance
2. Verify Redis Cloud firewall/security group settings
3. Test with `telnet redis-cloud.com 6379`
4. Ensure correct hostname and port

### No Internet Connectivity
**Issue**: `⚠️ Internet Connectivity: VPC has no Internet Gateway`

**Solution**: The CloudFormation template will automatically create Internet Gateway if `AutoCreateInternetAccess=true` (default).

## 🔄 Integration with CloudFormation

After successful pre-flight check, use the discovered values in your CloudFormation parameters:

```bash
# Run pre-flight check first
python3 migration_preflight_check.py \
  --source-cluster my-cluster \
  --target-uri redis://user:pass@redis-cloud.com:6379

# If successful, deploy CloudFormation
aws cloudformation create-stack \
  --stack-name riotx-migration \
  --template-url https://riot-x.s3.amazonaws.com/ec-sync.yaml \
  --parameters \
    ParameterKey=SourceElastiCacheClusterId,ParameterValue=my-cluster \
    ParameterKey=TargetRedisURI,ParameterValue=redis://user:pass@redis-cloud.com:6379 \
  --capabilities CAPABILITY_IAM
```

## 🐛 Troubleshooting

### Enable Verbose Mode
```bash
python3 migration_preflight_check.py \
  --source-cluster my-cluster \
  --target-uri redis://user:pass@redis-cloud.com:6379 \
  --verbose
```

### Check AWS Configuration
```bash
aws sts get-caller-identity
aws configure list
```

### Test Individual Components
```bash
# Test ElastiCache access
aws elasticache describe-replication-groups --replication-group-id my-cluster

# Test target connectivity
telnet redis-cloud.com 6379
```

## 📞 Support

If the pre-flight checker identifies issues that you cannot resolve:

1. **Review the remediation suggestions** provided for each failed check
2. **Check AWS documentation** for the specific services mentioned
3. **Verify your AWS credentials and permissions** have the required access
4. **Test connectivity manually** using the suggested commands

The pre-flight checker is designed to catch all potential issues before CloudFormation deployment, ensuring a smooth migration experience.
