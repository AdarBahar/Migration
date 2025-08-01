# 🔁 Redis Sync & Load Testing Toolkit

![Python](https://img.shields.io/badge/python-3.7%2B-blue?logo=python)
![Redis](https://img.shields.io/badge/redis-tested-green?logo=redis)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)

A collection of Python tools to manage, test, and verify synchronization between two Redis databases.

---

## 📖 **NEW: Complete Walkthrough Guide**

🎯 **[WALKTHROUGH.md](WALKTHROUGH.md)** - **Complete step-by-step guide** from deployment to migration testing!

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

📖 **[Detailed Setup Guide](migration-instance.md)** - Complete walkthrough including manual setup steps

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
2. **Activate environment**: `cd Migration && source venv/bin/activate`
3. **Follow the walkthrough**: See [WALKTHROUGH.md](WALKTHROUGH.md) for complete step-by-step instructions
4. **Start using tools**: `python manage_env.py`

### ⚡ Quick Start Commands:
```bash
# After SSH to instance
cd /home/ubuntu/Migration && source venv/bin/activate

# 1. Provision ElastiCache (auto-detects region and VPC)
python provision_elasticache.py

# 2. Configure connections
python manage_env.py

# 3. Generate test data
python DataFaker.py

# 4. Compare databases
python DB_compare.py

# 5. Run performance tests
python ReadWriteOps.py
``` to configure Redis connections

### 💡 Quick Environment Activation:
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

📖 **[Complete ElastiCache Guide](ELASTICACHE_README.md)** - Detailed documentation and troubleshooting

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
