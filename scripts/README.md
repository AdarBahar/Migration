# 🔧 Scripts Directory

This directory contains shell scripts for troubleshooting and maintenance tasks.

## 📋 **Current Scripts**

### ✅ **Active Scripts**

#### **`diagnose_instance.sh`**
- **Purpose**: Comprehensive EC2 instance diagnostics
- **Usage**: `./scripts/diagnose_instance.sh`
- **When to use**: When troubleshooting deployment or environment issues
- **Features**:
  - System information and status
  - Cloud-init status and logs
  - UserData execution verification
  - Python environment checks
  - Network connectivity tests
  - File permissions and ownership
  - Service status checks

### ⚠️ **Legacy Scripts (Consider for Removal)**

#### **`fix_activation.sh`** 
- **Status**: 🔴 **OBSOLETE**
- **Reason**: Replaced by the new `Start` script
- **Original Purpose**: Fixed virtual environment activation issues
- **Migration Path**: Use `./Start` instead

#### **`fix_elasticache_script.sh`**
- **Status**: 🔴 **OBSOLETE** 
- **Reason**: Simple git pull functionality, not needed with current workflow
- **Original Purpose**: Updated ElastiCache script from repository
- **Migration Path**: Use `git pull` directly or redeploy with CloudFormation

#### **`fix_current_instance.sh`**
- **Status**: 🟡 **MOSTLY OBSOLETE**
- **Reason**: Issues addressed by proper CloudFormation deployment
- **Original Purpose**: Fixed PATH issues and updated scripts on existing instances
- **Migration Path**: Redeploy with updated CloudFormation template

## 🚀 **Recommended Actions**

### **Immediate Actions:**
1. **Keep**: `diagnose_instance.sh` - Still valuable for troubleshooting
2. **Remove**: `fix_activation.sh` - Completely replaced by `Start` script
3. **Remove**: `fix_elasticache_script.sh` - Simple functionality, not needed
4. **Consider Removing**: `fix_current_instance.sh` - Mostly obsolete

### **Usage Guidelines:**

#### **For New Deployments:**
- Use the main `Start` script for initialization
- Use Migration Control Center (`index.py`) for all operations
- Only use `diagnose_instance.sh` if troubleshooting is needed

#### **For Existing Instances:**
- Run `./Start` to update to new workflow
- Use `scripts/diagnose_instance.sh` for troubleshooting
- Avoid using legacy fix scripts

## 📚 **Script Documentation**

### **`diagnose_instance.sh` Features:**

```bash
# Run comprehensive diagnostics
./scripts/diagnose_instance.sh

# Output includes:
# - System information (OS, kernel, uptime)
# - Cloud-init status and logs
# - UserData execution status
# - Python environment verification
# - Network connectivity tests
# - File permissions and ownership
# - Service status checks
# - Migration tool status
```

### **Migration from Legacy Scripts:**

```bash
# OLD WAY (don't use):
./fix_activation.sh
./fix_elasticache_script.sh
./fix_current_instance.sh

# NEW WAY (recommended):
./Start                              # Initialize everything
python index.py                      # Use Migration Control Center
./scripts/diagnose_instance.sh       # Only for troubleshooting
```

## 🧹 **Cleanup Recommendations**

To clean up obsolete scripts:

```bash
# Remove obsolete scripts
rm scripts/fix_activation.sh
rm scripts/fix_elasticache_script.sh
rm scripts/fix_current_instance.sh

# Keep only the useful diagnostic script
# scripts/diagnose_instance.sh (keep this one)
```

## 🔄 **Future Considerations**

- **Integration**: Consider integrating `diagnose_instance.sh` functionality into the Migration Control Center
- **Modernization**: Convert remaining useful scripts to Python for better integration
- **Automation**: Add diagnostic capabilities to the main toolset

---

**Note**: This directory represents the evolution of the project from individual fix scripts to a comprehensive, integrated migration management system. Most functionality has been consolidated into the main Python tools and the `Start` script.
