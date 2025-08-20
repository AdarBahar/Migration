# 🔧 Deployment Troubleshooting Guide

This guide helps resolve common issues when deploying and using the Redis Migration Tool via CloudFormation.

## 🚨 **Common Issue: activate-migration doesn't start Migration Control Center**

### **Problem Description:**
After deploying with CloudFormation and running `activate-migration`, the virtual environment is created and you're in the Migration directory, but the Migration Control Center (Start script) doesn't launch automatically.

### **Root Cause:**
The CloudFormation template was referencing the old `activate-migration` workflow instead of the new `Start` script-based Migration Control Center.

### **✅ Solution (Fixed in Latest Version):**

#### **For New Deployments:**
1. **Use the latest CloudFormation template** (`migration-instance.yaml`)
2. **After SSH to instance, run any of these commands:**
   ```bash
   # Option 1: Direct Start script
   cd /home/ubuntu/Migration && ./Start
   
   # Option 2: Convenient aliases (all do the same thing)
   migration
   start-migration
   activate-migration  # Now redirects to Start
   ```

#### **For Existing Instances (Deployed with Old Template):**
1. **Update the repository:**
   ```bash
   cd /home/ubuntu/Migration
   git pull origin main
   ```

2. **Make Start script executable:**
   ```bash
   chmod +x Start
   ```

3. **Launch Migration Control Center:**
   ```bash
   ./Start
   ```

### **🔍 Verification Steps:**

#### **Check if Start script exists and is executable:**
```bash
cd /home/ubuntu/Migration
ls -la Start
# Should show: -rwxr-xr-x ... Start
```

#### **Test Start script directly:**
```bash
cd /home/ubuntu/Migration
./Start
# Should launch Migration Control Center
```

#### **Check Python environment:**
```bash
cd /home/ubuntu/Migration
source venv/bin/activate
python3 --version
python3 -c "import redis, json; print('Dependencies OK')"
```

## 🛠️ **Other Common Issues**

### **Issue: "Start: command not found"**

**Cause:** Not in the correct directory or Start script not executable.

**Solution:**
```bash
cd /home/ubuntu/Migration
chmod +x Start
./Start
```

### **Issue: "Permission denied" when running Start**

**Cause:** Start script doesn't have execute permissions.

**Solution:**
```bash
chmod +x /home/ubuntu/Migration/Start
```

### **Issue: Python modules not found**

**Cause:** Virtual environment not activated or dependencies not installed.

**Solution:**
```bash
cd /home/ubuntu/Migration
source venv/bin/activate
pip install -r requirements.txt
./Start
```

### **Issue: Git repository is behind**

**Cause:** Instance was deployed with older version of the code.

**Solution:**
```bash
cd /home/ubuntu/Migration
git pull origin main
chmod +x Start
./Start
```

## 🔄 **Migration from Old to New Workflow**

### **Old Workflow (Deprecated):**
```bash
ssh -i key.pem ubuntu@instance-ip
source activate-migration  # Old way
# Manual script execution
```

### **New Workflow (Current):**
```bash
ssh -i key.pem ubuntu@instance-ip
./Start  # or use aliases: migration, start-migration
# Intelligent Migration Control Center launches
```

### **Transition Commands:**
```bash
# All of these now work and do the same thing:
migration           # New alias
start-migration     # New alias  
activate-migration  # Legacy redirect
cd /home/ubuntu/Migration && ./Start  # Direct method
```

## 🧪 **Testing Your Deployment**

### **Run the Test Suite:**
```bash
cd /home/ubuntu/Migration
python3 test_start_script.py
```

**Expected Output:**
```
📊 Test Results: 7/7 tests passed
✅ All tests passed! Start script is ready for deployment.
```

### **Manual Verification Checklist:**
- [ ] Start script exists and is executable
- [ ] Start script has valid bash syntax
- [ ] Python environment has required modules
- [ ] index.py exists and is valid Python
- [ ] .env.example template exists
- [ ] scripts directory contains diagnose_instance.sh
- [ ] Migration Control Center launches successfully

## 📞 **Getting Additional Help**

### **Diagnostic Script:**
```bash
cd /home/ubuntu/Migration
./scripts/diagnose_instance.sh
```

### **Check CloudFormation Logs:**
```bash
sudo cat /var/log/user-data.log
sudo cat /var/log/cloud-init-output.log
```

### **Manual Environment Setup (Last Resort):**
```bash
cd /home/ubuntu/Migration
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x Start
./Start
```

## 🎯 **Prevention for Future Deployments**

1. **Always use the latest CloudFormation template**
2. **Verify the template includes Start script references**
3. **Test the deployment with a small instance first**
4. **Check the UserData section includes Start script setup**

---

**Note:** This issue has been resolved in the latest version of the CloudFormation template. New deployments will automatically work with the Migration Control Center workflow.
