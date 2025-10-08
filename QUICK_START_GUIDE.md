# 🚀 Quick Start Guide: RIOT-X Migration Pre-flight Checker

## 📋 Overview

The RIOT-X Migration Pre-flight Checker now supports automatic configuration loading from `.env` files, making it incredibly easy to validate your migration setup.

## ⚡ Super Quick Start (3 Steps)

### 1. Configure Your Environment

```bash
# Copy the template
cp .env.migration .env

# Edit with your actual values
nano .env
```

**Required Configuration:**
```bash
# Your ElastiCache cluster ID
ELASTICACHE_CLUSTER_ID=my-actual-cluster-id

# Your Redis Cloud details
REDIS_DEST_HOST=redis-12345.c123.us-east-1-2.ec2.redns.redis-cloud.com
REDIS_DEST_PORT=12345
REDIS_DEST_PASSWORD=your-actual-password
REDIS_DEST_TLS=true
```

### 2. Run Pre-flight Check

```bash
python3 migration_preflight_check.py
```

That's it! No command-line parameters needed.

### 3. Fix Any Issues & Deploy

If all checks pass:
```bash
aws cloudformation create-stack \
  --stack-name riotx-migration \
  --template-url https://riot-x.s3.amazonaws.com/ec-sync.yaml \
  --parameters \
    ParameterKey=SourceElastiCacheClusterId,ParameterValue=my-actual-cluster-id \
    ParameterKey=TargetRedisURI,ParameterValue=rediss://user:pass@redis-cloud.com:12345 \
  --capabilities CAPABILITY_IAM
```

## 🔧 Advanced Usage

### Verbose Output
```bash
python3 migration_preflight_check.py --verbose
```

### Custom .env File
```bash
python3 migration_preflight_check.py --env-file /path/to/custom.env
```

### Override Specific Parameters
```bash
python3 migration_preflight_check.py --source-cluster different-cluster --verbose
```

### Command Line Only (No .env)
```bash
python3 migration_preflight_check.py \
  --source-cluster my-cluster \
  --target-uri rediss://user:pass@redis-cloud.com:12345
```

## 📊 What You'll See

### ✅ Success Output
```
🚀 RIOT-X Migration Pre-flight Checker
==================================================
📁 Configuration: Loaded from .env
Source Cluster: my-actual-cluster-id
Target URI: rediss://***@redis-cloud.com:12345
Region: us-east-1
==================================================

📋 1. Configuration Source
✅ Configuration Source: Configuration loaded from .env

📋 2. AWS Credentials & Basic Access
✅ AWS Credentials: Valid credentials for arn:aws:iam::123456789012:user/migration-user

... (all checks) ...

📊 SUMMARY
✅ Passed: 16 | ❌ Failed: 0 | ⚠️ Warnings: 1

🎉 SUCCESS: All critical checks passed!
✅ CloudFormation migration template should work successfully.
```

### ❌ Failure Output
```
❌ FAILURE: 3 critical issues found.
🔧 Fix the issues above before running CloudFormation template.

🔧 REMEDIATION SUMMARY:
   • ElastiCache Discovery: Verify cluster ID exists in region us-east-1
   • Target Connectivity: Check target Redis Cloud configuration
   • IAM Permission: Add elasticache:DescribeCacheClusters permission
```

## 🔍 Configuration Detection

The script automatically detects your configuration:

### Source Cluster Detection
- **Option 1**: `ELASTICACHE_CLUSTER_ID=my-cluster` (recommended)
- **Option 2**: `REDIS_SOURCE_HOST=my-cluster.abc123.cache.amazonaws.com` (extracts cluster ID)

### Target URI Construction
Builds from individual components:
```bash
REDIS_DEST_HOST=redis-cloud.com
REDIS_DEST_PORT=12345
REDIS_DEST_PASSWORD=secret
REDIS_DEST_TLS=true
# → rediss://:secret@redis-cloud.com:12345
```

## 🛡️ Security Features

- **Password masking** in all output
- **Secure .env handling** (add to .gitignore)
- **No passwords in command history**
- **Credential validation** without exposure

## 🎯 Benefits

### Before (Command Line)
```bash
python3 migration_preflight_check.py \
  --source-cluster my-very-long-cluster-name-with-timestamp-12345 \
  --target-uri rediss://username:very-long-complex-password@redis-15678.c123.eu-west-1-2.ec2.redns.redis-cloud.com:15678 \
  --region us-east-1 \
  --verbose
```

### After (.env Configuration)
```bash
python3 migration_preflight_check.py
```

### Key Advantages
- ✅ **Zero typing** - just run the script
- ✅ **No password exposure** in command history
- ✅ **Team sharing** via .env templates
- ✅ **Consistent configuration** across tools
- ✅ **Error reduction** - no typos in long URIs

## 🚨 Troubleshooting

### "Source cluster ID not found"
```bash
# Check your .env file has one of:
ELASTICACHE_CLUSTER_ID=your-cluster-id
# OR
REDIS_SOURCE_HOST=your-cluster.cache.amazonaws.com
```

### "Target Redis URI not found"
```bash
# Check your .env file has:
REDIS_DEST_HOST=your-redis-cloud-host
REDIS_DEST_PORT=port
REDIS_DEST_PASSWORD=password
REDIS_DEST_TLS=true
```

### "Configuration loaded but checks fail"
- Verify cluster ID exists: `aws elasticache describe-replication-groups`
- Test target connectivity: `telnet redis-cloud-host port`
- Check IAM permissions as suggested in remediation

## 🎉 Ready to Migrate!

Once all pre-flight checks pass, your CloudFormation migration will succeed on the first try! 

The pre-flight checker eliminates guesswork and ensures a smooth migration experience. 🚀✨
