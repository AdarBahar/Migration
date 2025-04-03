# 🔁 Redis Sync & Load Testing Toolkit

![Python](https://img.shields.io/badge/python-3.7%2B-blue?logo=python)
![Redis](https://img.shields.io/badge/redis-tested-green?logo=redis)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)

A collection of Python tools to manage, test, and verify synchronization between two Redis databases.

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
    

---

## 📦 Project Objectives

- Validate sync between **source** and **destination** Redis instances
    
- Perform **stress tests** via randomized key read/write batches
    
- Measure **latency per Redis** instance and **log performance**
    
- Enable secure and reusable connection handling using `.env` files
    

---

## 🗂 Project Structure

|File|Description|
|---|---|
|`DB_compare.py`|Live compare keys/tables between source and destination Redis|
|`ReadWriteOps.py`|Run multi-threaded read/write tests on one or both Redis databases, logs latency per op|
|`flushDBData.py`|Interactively flush one or both databases|
|`manage_env.py`|CLI tool to manage Redis connection strings and friendly names in a `.env` file|
|`.env`|Environment file used by all scripts for Redis configuration (auto-generated/edited)|

---

## 🔧 Configuration

All scripts use a common `.env` file to manage connection details. You can create or update this file by running:

bash

CopyEdit

`python manage_env.py`

This lets you define:

- `REDIS_SOURCE_NAME`, `REDIS_DEST_NAME`
    
- `REDIS_SOURCE_HOST`, `REDIS_DEST_HOST`
    
- `REDIS_SOURCE_PORT`, `REDIS_DEST_PORT`
    
- `REDIS_SOURCE_PASSWORD`, `REDIS_DEST_PASSWORD`
    
- `REDIS_SOURCE_TLS`, `REDIS_DEST_TLS`
    

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

bash

CopyEdit

`python DB_compare.py`

---

### `ReadWriteOps.py`

⚙️ **Multi-threaded read/write stress test and performance logger**

- Write and read random keys to/from selected DB(s)
    
- Track latency and operation count
    
- Logs all activity to a timestamped CSV (e.g., `redis_perf_log_20250403_120000.csv`)
    
- Handles exceptions and logs failures too
    

Run it:

bash

CopyEdit

`python ReadWriteOps.py`

---

### `flushDBData.py`

🧹 **Flush one or both Redis databases**

- Interactive selection: flush source, destination, or both
    
- Uses `flushall()` on selected targets
    
- Uses `.env` config for connection
    

Run it:

bash

CopyEdit

`python flushDBData.py`

---

### `manage_env.py`

🛠 **CLI tool to manage your `.env` config**

- Set or update source/destination Redis connections
    
- Friendly name, host, port, password, TLS support
    
- Saves everything to `.env`
    

Run it:

bash

CopyEdit

`python manage_env.py`

---

## 📊 Output Example (CSV log from `ReadWriteOps.py`)

csv

CopyEdit

`timestamp,redis_name,redis_host,operation,latency_ms,key_count,error_message 2025-04-03 13:00:01,AWS Redis,adar-redis...,WRITE,18.2,10, 2025-04-03 13:00:06,AWS Redis,adar-redis...,READ,12.3,10, 2025-04-03 13:01:05,AWS Redis,adar-redis...,WRITE,0,0,ConnectionError: timeout`

---

## ✅ Requirements

Install dependencies:

bash

CopyEdit

`pip install -r requirements.txt`

Required packages:

- `redis`
    
- `python-dotenv`
    

---

## 🚀 Future Improvements

- Graph CSV logs using matplotlib
    
- Add scheduled background syncing
    
- Slack/email alerts for errors or high latency
    
- Add support for more Redis operations (TTL, expiry tracking, streams)
    

---

## 🧠 Maintainer Notes

This project is intended for testing, validation, and internal ops — it **should not be used in production** as-is without locking down credentials and improving error handling for distributed environments.

---
