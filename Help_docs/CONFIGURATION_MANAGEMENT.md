# 📋 Configuration Management Guide

This guide covers the enhanced configuration management features in the Redis Migration Tool, including export/import functionality for quick setup and sharing.

## 🎯 **Overview**

The `manage_env.py` tool now includes powerful export/import capabilities that allow you to:
- **Export** current Redis configurations to JSON files
- **Import** configurations from JSON files for quick setup
- **Share** configurations between environments and team members
- **Backup** configurations for disaster recovery

## 🔧 **Using the Configuration Manager**

### **Starting the Tool**
```bash
python manage_env.py
```

### **Menu Options**
```
🔐 Redis Environment Configuration Tool

Choose an option:
1. Edit Source Redis
2. Edit Destination Redis
3. Test Source Redis
4. Test Destination Redis
5. Export Configuration      # 🆕 NEW
6. Import Configuration      # 🆕 NEW
7. Exit
```

## 📤 **Export Configuration**

### **How to Export**
1. Run `python manage_env.py`
2. Select option `5. Export Configuration`
3. Choose a filename (or use the auto-generated timestamp name)
4. Configuration is saved as JSON file

### **Export Example**
```bash
📤 Export Redis Configuration
========================================
Export filename [redis_config_20250820_105459.json]: my_config
✅ Configuration exported to: my_config.json
📁 File size: 514 bytes

📋 Exported configuration includes:
   🔗 Source: Development Redis (dev-redis.example.com)
   🔗 Destination: Production Redis (prod-redis.example.com)
   ⚠️  Note: Passwords are NOT exported for security reasons
```

### **What Gets Exported**
- ✅ **Connection Details**: Host, port, TLS settings, database numbers
- ✅ **Friendly Names**: Source and destination labels
- ✅ **Settings**: Timeout and log level configurations
- ✅ **Metadata**: Export timestamp and version information
- ❌ **Passwords**: NOT exported for security reasons

## 📥 **Import Configuration**

### **How to Import**
1. Run `python manage_env.py`
2. Select option `6. Import Configuration`
3. Choose from available files or enter filename
4. Review the configuration to be imported
5. Confirm the import (this overwrites current settings)

### **Import Example**
```bash
📥 Import Redis Configuration
========================================
📁 Available configuration files:
   1. redis_config_example.json (570 bytes, modified: 2025-08-20 10:54)
   2. my_config.json (514 bytes, modified: 2025-08-20 11:30)

Import filename (or press Enter to browse): 1
✅ Configuration loaded from: redis_config_example.json

📋 Configuration to import:
   📅 Exported: 2024-01-15T10:30:00.000000
   🔗 Source: Development Redis (dev-redis.example.com:6379)
   🔗 Destination: Staging Redis (staging-redis.example.com:6379)

⚠️  This will overwrite your current configuration!
Continue with import? (y/N): y
✅ Configuration imported successfully!
⚠️  Remember to set passwords manually for security reasons.
```

## 📁 **Configuration File Format**

### **JSON Structure**
```json
{
  "metadata": {
    "exported_at": "2025-08-20T10:54:59.208483",
    "exported_by": "Redis Migration Tool",
    "version": "1.0"
  },
  "source": {
    "name": "Development Redis",
    "host": "dev-redis.example.com",
    "port": "6379",
    "tls": "false",
    "db": "0"
  },
  "destination": {
    "name": "Production Redis",
    "host": "prod-redis.example.com",
    "port": "6379",
    "tls": "true",
    "db": "0"
  },
  "settings": {
    "timeout": "5",
    "log_level": "INFO"
  }
}
```

### **File Naming Convention**
- **Auto-generated**: `redis_config_YYYYMMDD_HHMMSS.json`
- **Custom names**: Any name you choose (`.json` extension added automatically)
- **Example files**: `redis_config_example.json` (provided as template)

## 🔒 **Security Considerations**

### **Password Handling**
- ✅ **Passwords are NEVER exported** to configuration files
- ✅ **Manual password entry required** after import
- ✅ **Configuration files are safe to share** (no sensitive data)
- ✅ **Files are gitignored** by default (`redis_config_*.json`)

### **Best Practices**
1. **Always set passwords manually** after importing configurations
2. **Review imported configurations** before confirming
3. **Use descriptive filenames** for easy identification
4. **Store configuration files securely** if they contain environment details
5. **Test connections** after importing to verify settings

## 🚀 **Use Cases**

### **1. Environment Setup**
```bash
# Developer onboarding
python manage_env.py
# Select 6. Import Configuration
# Choose: dev_environment.json
# Set passwords manually
# Ready to work!
```

### **2. Configuration Backup**
```bash
# Before making changes
python manage_env.py
# Select 5. Export Configuration
# Save as: backup_before_changes.json
```

### **3. Team Sharing**
```bash
# Team lead exports standard config
python manage_env.py
# Select 5. Export Configuration
# Save as: team_standard_config.json
# Share file with team (passwords not included)
```

### **4. Multi-Environment Management**
```bash
# Save different environment configs
dev_config.json      # Development environment
staging_config.json  # Staging environment
prod_config.json     # Production environment
```

## 🔄 **Integration with Migration Control Center**

The export/import functionality integrates seamlessly with the Migration Control Center:

1. **Use Migration Control Center** (`./Start` → `python index.py`)
2. **Select option 2**: "Manage Environment"
3. **Access export/import** through the enhanced menu
4. **Return to main menu** when configuration is complete

## 📚 **Advanced Tips**

### **Batch Configuration**
```bash
# Create multiple environment configs
python manage_env.py
# Export current as: base_config.json
# Modify for different environments
# Import base_config.json as starting point
# Adjust settings for each environment
# Export as environment-specific files
```

### **Configuration Validation**
- Import validates JSON structure
- Checks for required fields
- Shows preview before applying changes
- Provides clear error messages for invalid files

### **File Management**
```bash
# List all configuration files
ls redis_config_*.json

# Clean up old exports
rm redis_config_2024*.json

# Organize by environment
mkdir configs
mv *_config.json configs/
```

## 🆘 **Troubleshooting**

### **Common Issues**

**Import fails with "Invalid JSON"**
- Check file format with `cat filename.json`
- Ensure proper JSON syntax
- Use provided example as template

**Configuration not applied**
- Verify import completed successfully
- Check .env file was updated
- Restart any running applications

**Missing configuration files**
- Check current directory
- Ensure files have .json extension
- Verify file permissions

### **Getting Help**
- Use the diagnostic script: `./scripts/diagnose_instance.sh`
- Check the troubleshooting guide: `Help_docs/TROUBLESHOOTING.md`
- Review security guidelines: `Help_docs/SECURITY.md`

---

This enhanced configuration management makes Redis migration setup faster, more reliable, and easier to share across teams and environments! 🚀
