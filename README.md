# 🔁 Redis Sync & Load Testing Toolkit

![Python](https://img.shields.io/badge/python-3.7%2B-blue?logo=python)
![Redis](https://img.shields.io/badge/redis-tested-green?logo=redis)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)

A collection of Python tools to manage, test, and verify synchronization between two Redis databases.

---

## 🚀 Quick AWS Setup with CloudFormation

Want to quickly set up an AWS EC2 instance with everything pre-configured? Use our CloudFormation template:

👉 **[Launch Stack](https://console.aws.amazon.com/cloudformation/home?#/stacks/create/review?templateURL=https://adar-testing.s3.eu-north-1.amazonaws.com/migration-instance.yaml)**

📖 **[Detailed Setup Guide](migration-instance.md)** - Complete walkthrough including manual setup steps

The CloudFormation template automatically:
- Creates an Ubuntu EC2 instance
- Installs Python, Git, and dependencies
- Clones this repository
- Sets up the virtual environment
- Configures security groups for SSH access

After deployment, simply SSH to your instance and start using the migration tools!

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
