# 🔐 Database Configuration Management Guide

## Overview

The enhanced `manage_env.py` tool provides a comprehensive interface for managing multiple Redis and Valkey database configurations for migration projects.

## 🚀 Quick Start

```bash
python3 manage_env.py
```

## 📋 Main Menu Structure

```
🔐 Redis/Valkey Migration Configuration Tool
============================================================

📊 Quick Overview:
   🔹 Sources: 2 configured (1 tested ✅, 1 untested ⏳)
   🔸 Targets: 1 configured (1 tested ✅)

Main Menu:
1. Source Databases (2 configured)
2. Target Databases (1 configured)
3. Export/Import Configuration
4. View All Configurations
5. Exit
```

## 🔹 Managing Source Databases

### Add New Source Database

**Menu Path:** Main Menu → 1 → 1

**Supported Engine Types:**
1. **Redis (AWS ElastiCache Redis)**
   - Paste AWS CLI command from ElastiCache console
   - Format: `redis6-cli --tls -h host.amazonaws.com -p 6379`
   - Auto-detects TLS, host, and port

2. **Valkey (AWS ElastiCache Valkey)**
   - Paste Valkey CLI command or endpoint
   - Format: `valkey-cli --tls -h host.amazonaws.com -p 6379`
   - Or: `host.amazonaws.com:6379`
   - Supports both node-based and serverless Valkey

3. **Redis Cloud**
   - Paste Redis Cloud connection URL
   - Format: `rediss://user:password@host.redis-cloud.com:12345`
   - Or: `redis-cli -u rediss://user:password@host:12345`
   - Auto-extracts credentials and TLS settings

4. **Manual Redis/Valkey Configuration**
   - Enter details manually
   - Choose engine type (Redis or Valkey)
   - Specify host, port, password, TLS

**Auto-Test Feature:**
After adding a database, the tool automatically tests the connection and displays:
- ✅ Connection successful
- Version information (if available)
- Connection details

### Edit Existing Source Database

**Menu Path:** Main Menu → 1 → 2

- Select database from list
- Modify any field (name, host, port, password, TLS)
- Press Enter to keep current value
- Option to test connection after editing

### Test Source Database Connection

**Menu Path:** Main Menu → 1 → 3

**Options:**
- **0. Test All** - Tests all configured source databases
- **1-N. Individual Database** - Test specific database
- Shows real-time connection status
- Detects and displays engine version
- Saves test results with timestamp

**Test Results:**
- ✅ Successfully tested (shows timestamp)
- ❌ Test failed (shows error)
- ⏳ Never tested

### Delete Source Database

**Menu Path:** Main Menu → 1 → 4

- Select database to delete
- Type 'DELETE' to confirm
- Removes database from configuration

## 🔸 Managing Target Databases

Same functionality as Source Databases:
- Add new target database
- Edit existing target database
- Test target database connection
- Delete target database

**Menu Path:** Main Menu → 2

## 📦 Export/Import Configuration

### Export Configuration

**Menu Path:** Main Menu → 3 → 1

**Features:**
- Exports all source and target databases to JSON file
- Default filename: `migration_config_YYYYMMDD_HHMMSS.json`
- **Security:** Passwords are NOT exported
- Includes metadata (export date, version)

**Export Format:**
```json
{
  "metadata": {
    "exported_at": "2024-01-15T14:30:00",
    "exported_by": "Redis/Valkey Migration Tool",
    "version": "2.0"
  },
  "sources": [
    {
      "name": "AWS ElastiCache Prod",
      "engine": "redis",
      "engine_version": "7.1.0",
      "host": "my-cache.amazonaws.com",
      "port": "6379",
      "password": "",
      "tls": true,
      "db": "0",
      "source": "AWS ElastiCache"
    }
  ],
  "targets": [...]
}
```

### Import Configuration

**Menu Path:** Main Menu → 3 → 2

**Features:**
- Lists available configuration files
- Browse and select file
- Two import modes:
  1. **Replace All** - Clear existing and import
  2. **Merge** - Add to existing configurations

**Security Note:** Remember to set passwords manually after import

## 📊 View All Configurations

**Menu Path:** Main Menu → 4

Displays comprehensive overview of all databases:
- Source databases with status
- Target databases with status
- Engine type and version
- Host and port
- TLS status
- Configuration source

## 🎯 Database Configuration Details

Each database stores:
- **name**: Friendly label for identification
- **engine**: 'redis' or 'valkey'
- **engine_version**: Detected version (e.g., '7.1.0', '8.1')
- **host**: Database hostname
- **port**: Database port (default: 6379)
- **password**: Securely stored (hidden in displays)
- **tls**: Boolean for TLS/SSL encryption
- **db**: Database number (default: 0)
- **source**: Configuration source (ElastiCache/Redis Cloud/Manual)

## 🔍 Connection Testing

### Test Status Indicators

- **✅ Success** - Connection successful, version detected
- **❌ Failed** - Connection failed, error displayed
- **⏳ Untested** - Never tested or test pending

### Test Results Storage

Test results are saved in `.env` file:
```json
{
  "redis_host.amazonaws.com_6379": {
    "status": "success",
    "timestamp": "2024-01-15T14:30:00",
    "version": "7.1.0"
  }
}
```

## 💾 Data Storage

All configurations are stored in `.env` file:

```bash
# Source databases (JSON array)
MIGRATION_SOURCES='[{"name":"AWS Redis","engine":"redis",...}]'

# Target databases (JSON array)
MIGRATION_TARGETS='[{"name":"Redis Cloud","engine":"redis",...}]'

# Test results (JSON object)
MIGRATION_TEST_RESULTS='{"redis_host_6379":{"status":"success",...}}'
```

## 🔧 Advanced Features

### Valkey Support

**Valkey CLI Parsing:**
```bash
valkey-cli --tls -h my-valkey.amazonaws.com -p 6379
```

**Endpoint Parsing:**
```bash
my-valkey.amazonaws.com:6379
```

**Features:**
- Auto-detects TLS from CLI command
- Supports both node-based and serverless Valkey
- Version detection during testing
- Compatible with Valkey 7.2, 8.0, 8.1

### Multiple Database Support

**Use Cases:**
- Migrate from multiple sources to one target
- Migrate from one source to multiple targets
- Test different database configurations
- Compare performance across databases

### Connection Status Tracking

**Benefits:**
- Know which databases are tested and working
- See when databases were last tested
- Identify failed connections quickly
- Track engine versions across databases

## 🎨 User Experience Features

### Visual Feedback
- Status icons (✅/❌/⏳)
- Color-coded sections (🔹 sources, 🔸 targets)
- Progress indicators
- Confirmation prompts

### Navigation
- Clear menu hierarchy
- Breadcrumb-style navigation
- Consistent option numbering
- "Press Enter to continue" prompts

### Error Handling
- Invalid input validation
- File not found handling
- Connection error reporting
- Graceful failure recovery

## 📝 Example Workflow

### Setting Up Migration

1. **Add Source Database**
   ```
   Main Menu → 1 → 1 → Select Engine Type
   Paste AWS CLI command or URL
   Auto-test connection ✅
   ```

2. **Add Target Database**
   ```
   Main Menu → 2 → 1 → Select Engine Type
   Paste Redis Cloud URL
   Auto-test connection ✅
   ```

3. **Verify Configuration**
   ```
   Main Menu → 4 (View All Configurations)
   Check all databases are configured correctly
   ```

4. **Export Configuration**
   ```
   Main Menu → 3 → 1
   Save as migration_config_20240115.json
   ```

5. **Test All Connections**
   ```
   Main Menu → 1 → 3 → 0 (Test All)
   Main Menu → 2 → 3 → 0 (Test All)
   ```

## 🔒 Security Best Practices

1. **Passwords**
   - Never exported to JSON files
   - Hidden in all displays (shown as ***)
   - Stored securely in .env file
   - Must be re-entered after import

2. **.env File**
   - Add to .gitignore
   - Never commit to version control
   - Keep backups securely
   - Restrict file permissions

3. **Configuration Files**
   - Review before sharing
   - Remove sensitive data
   - Use secure transfer methods
   - Delete after use if temporary

## 🆘 Troubleshooting

### Connection Test Fails

**Check:**
- Host and port are correct
- TLS setting matches database
- Password is correct (if required)
- Network connectivity
- Firewall rules
- Security group settings

### Import Fails

**Check:**
- JSON file format is valid
- File exists and is readable
- Configuration version compatibility
- Sufficient permissions

### Database Not Showing

**Check:**
- .env file exists
- MIGRATION_SOURCES/TARGETS keys present
- JSON format is valid
- Reload environment (restart tool)

## 📚 Additional Resources

- AWS ElastiCache Documentation
- Redis Cloud Documentation
- Valkey Documentation
- Migration best practices

## 🎉 Summary

The enhanced database configuration tool provides:
- ✅ Multi-database support (sources and targets)
- ✅ Full Valkey support
- ✅ Intuitive UX with visual feedback
- ✅ Comprehensive testing capabilities
- ✅ Flexible export/import
- ✅ Connection status tracking
- ✅ Secure password handling
- ✅ Easy database management (add/edit/delete)

Perfect for managing complex Redis and Valkey migration projects!

