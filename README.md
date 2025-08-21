# 🔁 Redis Sync & Load Testing Toolkit

![Python](https://img.shields.io/badge/python-3.7%2B-blue?logo=python)
![Redis](https://img.shields.io/badge/redis-tested-green?logo=redis)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)
[![Deploy CloudFormation](https://github.com/AdarBahar/Migration/actions/workflows/deploy-cloudformation.yml/badge.svg)](https://github.com/AdarBahar/Migration/actions/workflows/deploy-cloudformation.yml)

A collection of Python tools to manage, test, and verify synchronization between two Redis databases.

---

## 📖 **NEW: Complete Walkthrough Guide**

🎯 **[WALKTHROUGH.md](Help_docs/WALKTHROUGH.md)** - **Complete step-by-step guide** from deployment to migration testing!

This comprehensive guide covers:
- ✅ CloudFormation deployment with exact commands
- ✅ Instance verification and connection
- ✅ ElastiCache provisioning (out-of-the-box)
- ✅ Environment configuration and testing
- ✅ Data generation and performance benchmarking
- ✅ Troubleshooting and best practices

---

## 🚀 Quick AWS Setup with CloudFormation

Want to quickly set up an AWS EC2 instance with everything pre-configured? Use our CloudFormation template:

👉 **[Launch Stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/create/review?templateURL=https://adar-testing.s3.eu-north-1.amazonaws.com/migration-instance.yaml)**

📖 **[Detailed Setup Guide](Help_docs/migration-instance.md)** - Complete walkthrough including manual setup steps

### ✨ What the CloudFormation Template Does:
- **Creates Ubuntu EC2 instance** with default AMI `ami-042b4708b1d05f512` (Ubuntu 22.04 LTS)
- **Default stack name**: `Redis-Migration-Tool`
- **Installs all dependencies**: Python 3, pip, venv, Git, curl, wget
- **Clones this repository** automatically
- **Sets up virtual environment** and installs requirements
- **Configures security groups** for SSH access from your IP
- **Creates convenience scripts** for easy environment activation
- **Sets proper file ownership** for the ubuntu user

### 🎯 After Deployment:
1. **SSH to your instance**: `ssh -i /path/to/your-key.pem ubuntu@<public-ip>`
2. **Run the start script**: `cd Migration && ./Start`
3. **Follow intelligent suggestions**: The Migration Control Center will guide you through the optimal workflow
4. **Use the interactive menu**: All tools accessible through the central interface

### ⚡ One-Command Startup:
```bash
# After SSH to instance
cd /home/ubuntu/Migration && ./Start
```

**What the Start script does:**
- ✅ Sets up Python virtual environment
- ✅ Installs all dependencies
- ✅ Creates initial .env configuration
- ✅ Launches Migration Control Center
- ✅ Provides intelligent workflow suggestions

### 🎯 Migration Control Center Features:
- 🧠 **Intelligent Suggestions**: Detects environment state and suggests next steps
- 📋 **Organized Menu**: Scripts categorized by Setup, Data, Migration, Maintenance, Troubleshooting
- 🔄 **Automatic Return**: Each script returns to main menu when completed
- ✅ **Status Indicators**: Real-time environment and ElastiCache status
- 💡 **Smart Workflow**: Guides you through optimal migration process

**Available Operations:**
```
🚀 Setup & Configuration
  1. Provision ElastiCache - Create AWS ElastiCache Redis instance
  2. Manage Environment - Configure Redis connection settings

📊 Data Management
  3. Generate Test Data - Create sample data for migration testing

🔄 Migration Operations
  4. Compare Databases - Compare source and destination Redis instances
  5. Migration Operations - Perform read/write operations and migration

🧹 Maintenance
  6. Flush Database - Clear all data from Redis database
  7. Cleanup ElastiCache - Remove ElastiCache instances and resources

🔧 Troubleshooting
  8. Network Troubleshooting - Diagnose network connectivity issues
  9. Test Security Config - Test ElastiCache security configuration
```

### 🧠 Intelligent Workflow Management:

The Migration Control Center automatically detects your environment state and provides smart suggestions:

- **🔴 High Priority**: Missing ElastiCache instance → Suggests provisioning
- **🔴 High Priority**: Empty .env file → Suggests environment configuration
- **🟡 Medium Priority**: No test data → Suggests data generation
- **✅ Ready**: All configured → Suggests migration operations

**Example workflow:**
1. Run `./Start` → Launches control center
2. See suggestion: "No ElastiCache instance found" → Run option 1
3. See suggestion: "Environment not configured" → Run option 2
4. See suggestion: "No test data found" → Run option 3
5. Environment ready → Run migration operations (options 4-5)

### 💡 Manual Environment Activation (if needed):
```bash
# Method 1: Manual activation (recommended)
cd /home/ubuntu/Migration && source venv/bin/activate

# Method 2: Use the convenience alias (after logout/login)
activate-migration

# Method 3: Run the info script
./start-migration.sh
```

---

## 📦 Requirements

Install required dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 **Automatic CloudFormation Deployment**

The repository includes GitHub Actions that automatically deploy the CloudFormation template to S3 whenever `migration-instance.yaml` is updated:

- ✅ **Secure S3 Upload**: Template uploaded to private S3 bucket on every change
- ✅ **Template Validation**: CloudFormation syntax validated before deployment
- ✅ **Pre-signed URLs**: Secure, time-limited URLs generated automatically (30-day and 24-hour)
- ✅ **One-Click Deploy**: Direct AWS Console deployment links with embedded pre-signed URLs
- ✅ **Deployment Tracking**: Timestamped logs with URL expiration tracking
- ✅ **Enterprise Security**: Private bucket with block public access enabled

### 🔧 **GitHub Actions Workflow**

**Workflow File**: `.github/workflows/deploy-cloudformation.yml`

**Triggers**:
- Push to `main` branch with changes to `migration-instance.yaml`
- Pull requests to `main` with changes to `migration-instance.yaml`

**Required GitHub Secrets**:
- `AWS_ACCESS_KEY_ID` - AWS access key for S3 deployment
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for S3 deployment
- `S3_BUCKET_NAME` - Target S3 bucket name
- `AWS_REGION` - AWS region for S3 bucket

**Workflow Steps**:
1. 📥 **Checkout Repository** - Downloads latest code
2. 🔧 **Configure AWS Credentials** - Sets up AWS access
3. ✅ **Validate Template** - Validates CloudFormation syntax
4. 📤 **Upload to S3** - Uploads template with metadata
5. 🔗 **Generate Secure URLs** - Creates pre-signed URLs (30-day & 24-hour)
6. 📝 **Create Deployment Log** - Logs deployment with expiration tracking

**Generated URLs**:
- 🔒 **30-day pre-signed URL** - For sharing and long-term access
- 🕐 **24-hour pre-signed URL** - For immediate deployment
- 🚀 **One-click deploy URL** - Direct AWS Console deployment link

**Setup**: See [GITHUB_S3_DEPLOYMENT.md](Help_docs/GITHUB_S3_DEPLOYMENT.md) for complete configuration instructions.

### 📊 **Monitoring Deployments**

**View Workflow Runs**:
1. Go to repository **Actions** tab
2. Click on **"🚀 Deploy CloudFormation Template to S3"** workflow
3. View individual runs with detailed logs and generated URLs

**Deployment Logs**: Stored in S3 at `s3://your-bucket/deployment-logs/` with:
- Commit SHA and message
- Deployment timestamp
- Pre-signed URL expiration times
- Template size and metadata

**Testing the Workflow**:
```bash
# Make a small change to trigger deployment
echo "# Updated $(date)" >> migration-instance.yaml
git add migration-instance.yaml
git commit -m "Test automatic S3 deployment"
git push origin main

# Watch the workflow in GitHub Actions tab
```

---

- 🔍 Compare two Redis databases
    
- ⚙️ Run configurable read/write load operations
    
- 🧹 Flush Redis data from one or both databases
    
- 🔧 Easily manage Redis connection settings via a CLI-based `.env` manager
    
- 📊 Generate fake data for testing using `datafaker`

- 🚀 Provision AWS ElastiCache Redis instances automatically

---

## 📦 Project Objectives

- Validate sync between **source** and **destination** Redis instances
    
- Perform **stress tests** via randomized key read/write batches
    
- Measure **latency per Redis** instance and **log performance**
    
- Enable secure and reusable connection handling using `.env` files
    
- Generate realistic test data for Redis using `datafaker`

---

## 🗂 Project Structure

|File|Description|
|---|---|
|`DB_compare.py`|Live compare keys/tables between source and destination Redis|
|`ReadWriteOps.py`|Run multi-threaded read/write tests on one or both Redis databases, logs latency per op|
|`flushDBData.py`|Interactively flush one or both databases|
|`manage_env.py`|CLI tool to manage Redis connection strings and friendly names in a `.env` file|
|`datafaker.py`|Generate fake data for Redis testing|
|`provision_elasticache.py`|🆕 Provision AWS ElastiCache Redis instances with proper configuration|
|`cleanup_elasticache.py`|🆕 Clean up ElastiCache resources and associated AWS components|
|`elasticache_config.py`|🆕 Configuration options and interactive builder for ElastiCache|
|`.env`|Environment file used by all scripts for Redis configuration (auto-generated/edited)|

---

## 🔧 Configuration

All scripts use a common `.env` file to manage connection details. You can create or update this file by running:

```bash
python manage_env.py
```

This lets you define:

- `REDIS_SOURCE_NAME`, `REDIS_DEST_NAME`
    
- `REDIS_SOURCE_HOST`, `REDIS_DEST_HOST`
    
- `REDIS_SOURCE_PORT`, `REDIS_DEST_PORT`
    
- `REDIS_SOURCE_PASSWORD`, `REDIS_DEST_PASSWORD`
    
- `REDIS_SOURCE_TLS`, `REDIS_DEST_TLS`
    
- **New Options**:
  - `REDIS_SOURCE_DB`, `REDIS_DEST_DB`: Specify the database index for source and destination Redis instances.
  - `REDIS_TIMEOUT`: Set a timeout value for Redis connections.

---

## 📄 Scripts Overview

---

### `DB_compare.py`

📌 **Live comparison of source and destination Redis**

- Lists total keys and table prefixes
    
- Shows differences (missing keys, mismatched tables)
    
- Refreshes every 5 seconds
    
- Uses `SCAN` to avoid performance issues with `KEYS *`
    

Run it:

```bash
python DB_compare.py
```

---

### `ReadWriteOps.py`

⚙️ **Multi-threaded read/write stress test and performance logger**

- Write and read random keys to/from selected DB(s)
    
- Track latency and operation count
    
- Logs all activity to a timestamped CSV (e.g., `redis_perf_log_20250403_120000.csv`)
    
- Handles exceptions and logs failures too
    

Run it:

```bash
python ReadWriteOps.py
```

---

### `flushDBData.py`

🧹 **Flush one or both Redis databases**

- Interactive selection: flush source, destination, or both
    
- Uses `flushall()` on selected targets
    
- Uses `.env` config for connection
    

Run it:

```bash
python flushDBData.py
```

---

### `manage_env.py`

🛠 **CLI tool to manage your `.env` config**

- Set or update source/destination Redis connections
    
- Friendly name, host, port, password, TLS support
    
- Specify database index (`REDIS_SOURCE_DB`, `REDIS_DEST_DB`)
    
- Set connection timeout (`REDIS_TIMEOUT`)
    
- Saves everything to `.env`
    

Run it:

```bash
python manage_env.py
```

---

### `datafaker.py`

📊 **Generate fake data for Redis testing**

- Populate Redis with random keys and values for testing
    
- Supports configurable key patterns, value sizes, and data types
    
- Uses `.env` config for connection details
    

Run it:

```bash
python datafaker.py
```

Options:

- `--keys`: Number of keys to generate (default: 1000)
- `--pattern`: Key pattern (e.g., `user:{id}`)
- `--value-size`: Size of values in bytes (default: 256)
- `--data-type`: Type of data to generate (e.g., string, hash, list)

---

### `provision_elasticache.py` 🆕

🚀 **Automatically provision AWS ElastiCache Redis instances**

- Creates ElastiCache Redis clusters with proper network configuration

- Automatically configures security groups and subnet groups

- Interactive configuration builder with cost estimation

- Environment-specific presets (development, staging, production)

- Generates .env configuration for immediate use

Run it:

```bash
# Interactive mode (recommended)
python provision_elasticache.py

# Automatic mode with defaults
python provision_elasticache.py --auto

# Custom configuration
python provision_elasticache.py --auto --node-type cache.t3.small --engine-version 7.0
```

📖 **[Complete ElastiCache Guide](Help_docs/ELASTICACHE_README.md)** - Detailed documentation and troubleshooting

---

### `cleanup_elasticache.py` 🆕

🧹 **Clean up ElastiCache resources and AWS components**

- List all ElastiCache clusters

- Delete specific clusters or all migration tool resources

- Clean up associated security groups and subnet groups

- Batch cleanup operations

Run it:

```bash
# List all clusters
python cleanup_elasticache.py --list

# Delete specific cluster
python cleanup_elasticache.py --delete cluster-id

# Clean up all migration tool resources
python cleanup_elasticache.py --cleanup-all
```

---

## 📊 Output Example (CSV log from `ReadWriteOps.py`)

```csv
timestamp,redis_name,redis_host,operation,latency_ms,key_count,error_message
2025-04-03 13:00:01,AWS Redis,adar-redis...,WRITE,18.2,10,
2025-04-03 13:00:06,AWS Redis,adar-redis...,READ,12.3,10,
2025-04-03 13:01:05,AWS Redis,adar-redis...,WRITE,0,0,ConnectionError: timeout
```

---

## 📚 Documentation

### 🎯 **Getting Started**
- **[WALKTHROUGH.md](Help_docs/WALKTHROUGH.md)** - Complete step-by-step guide from deployment to migration testing
- **[migration-instance.md](Help_docs/migration-instance.md)** - Detailed CloudFormation deployment guide and manual setup

### 🔧 **Technical Documentation**
- **[ELASTICACHE_README.md](Help_docs/ELASTICACHE_README.md)** - Comprehensive ElastiCache provisioning and configuration guide
- **[CONFIGURATION_MANAGEMENT.md](Help_docs/CONFIGURATION_MANAGEMENT.md)** - Export/import configurations for quick setup and sharing
- **[OUT_OF_THE_BOX_FEATURES.md](Help_docs/OUT_OF_THE_BOX_FEATURES.md)** - Complete feature overview and capabilities
- **[TROUBLESHOOTING.md](Help_docs/TROUBLESHOOTING.md)** - Problem resolution and debugging guide

### 🔒 **Security & Organization**
- **[SECURITY.md](Help_docs/SECURITY.md)** - Security guidelines, best practices, and compliance information
- **[DOCUMENTATION_INDEX.md](Help_docs/DOCUMENTATION_INDEX.md)** - Complete documentation navigation and organization

### 🔧 **Scripts & Utilities**
- **[scripts/README.md](scripts/README.md)** - Shell scripts for troubleshooting and diagnostics
- **[scripts/diagnose_instance.sh](scripts/diagnose_instance.sh)** - Comprehensive EC2 instance diagnostics
- **[scripts/setup-s3-deployment.sh](scripts/setup-s3-deployment.sh)** - Automated S3 deployment setup for CloudFormation

### 🚀 **Deployment & Automation**
- **[GITHUB_S3_DEPLOYMENT.md](Help_docs/GITHUB_S3_DEPLOYMENT.md)** - Automatic S3 deployment setup for CloudFormation templates
- **[DEPLOYMENT_TROUBLESHOOTING.md](Help_docs/DEPLOYMENT_TROUBLESHOOTING.md)** - Deployment issue resolution guide

### 📖 **Quick Reference**
| Document | Purpose | When to Use |
|----------|---------|-------------|
| [WALKTHROUGH.md](Help_docs/WALKTHROUGH.md) | Complete setup guide | First-time users, step-by-step deployment |
| [ELASTICACHE_README.md](Help_docs/ELASTICACHE_README.md) | ElastiCache details | ElastiCache provisioning and troubleshooting |
| [GITHUB_S3_DEPLOYMENT.md](Help_docs/GITHUB_S3_DEPLOYMENT.md) | Automatic S3 deployment | Setting up GitHub Actions for CloudFormation |
| [CONFIGURATION_MANAGEMENT.md](Help_docs/CONFIGURATION_MANAGEMENT.md) | Export/import configs | Quick setup, team sharing, backups |
| [TROUBLESHOOTING.md](Help_docs/TROUBLESHOOTING.md) | Problem solving | When encountering issues or errors |
| [SECURITY.md](Help_docs/SECURITY.md) | Security practices | Before production deployment |
| [OUT_OF_THE_BOX_FEATURES.md](Help_docs/OUT_OF_THE_BOX_FEATURES.md) | Feature overview | Understanding tool capabilities |

---

## ✅ Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Required packages:

- `redis`
- `python-dotenv`
- `faker`

---

## 🚀 Future Improvements

- Graph CSV logs using matplotlib
    
- Add scheduled background syncing
    
- Slack/email alerts for errors or high latency
    
- Add support for more Redis operations (TTL, expiry tracking, streams)
    
- Enhance `datafaker` to support more complex data structures

---

## 🧠 Maintainer Notes

This project is intended for testing, validation, and internal ops — it **should not be used in production** as-is without locking down credentials and improving error handling for distributed environments.

---
