#!/bin/bash
# 🔧 Fix Current Instance Issues
# Run this script on your current EC2 instance to fix the ls command and update ElastiCache script

echo "🔧 Fixing Current Instance Issues"
echo "================================="
echo "Generated at: $(date)"
echo ""

# Fix 1: Check and fix ls command issue
echo "🔍 Issue 1: Checking ls command availability..."

if command -v ls >/dev/null 2>&1; then
    echo "✅ ls command is available"
else
    echo "❌ ls command not found"
    echo "📍 Current PATH: $PATH"
    echo "🔧 Fixing PATH..."
    
    # Add standard paths to current session
    export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
    
    # Add to .bashrc for future sessions
    echo 'export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"' >> ~/.bashrc
    
    if command -v ls >/dev/null 2>&1; then
        echo "✅ ls command fixed!"
    else
        echo "❌ Could not fix ls command. Please check system installation."
    fi
fi

echo ""

# Fix 2: Update ElastiCache script with latest version
echo "🔍 Issue 2: Updating ElastiCache provisioning script..."

if [ -d "/home/ubuntu/Migration" ]; then
    echo "✅ Migration directory found"
    cd /home/ubuntu/Migration
    
    # Pull latest changes
    echo "📥 Pulling latest updates from GitHub..."
    git pull origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Repository updated successfully"
    else
        echo "⚠️  Git pull failed, trying to reset..."
        git fetch origin
        git reset --hard origin/main
        
        if [ $? -eq 0 ]; then
            echo "✅ Repository reset to latest version"
        else
            echo "❌ Could not update repository"
        fi
    fi
    
    # Check if the updated script exists
    if [ -f "provision_elasticache.py" ]; then
        echo "✅ ElastiCache script found"
        
        # Test the region detection
        echo "🌍 Testing region detection..."
        python3 -c "
import urllib.request
try:
    region = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/placement/region', timeout=5).read().decode()
    print(f'✅ Detected region: {region}')
except Exception as e:
    print(f'⚠️  Could not detect region: {e}')
"
    else
        echo "❌ ElastiCache script not found"
    fi
    
else
    echo "❌ Migration directory not found"
    echo "🔧 Cloning repository..."
    
    cd /home/ubuntu
    git clone https://github.com/AdarBahar/Migration.git
    
    if [ $? -eq 0 ]; then
        echo "✅ Repository cloned successfully"
        cd Migration
    else
        echo "❌ Could not clone repository"
        exit 1
    fi
fi

echo ""

# Fix 3: Ensure virtual environment is working
echo "🔍 Issue 3: Checking Python virtual environment..."

if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    
    # Test activation
    source venv/bin/activate
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment activation: OK"
        echo "🐍 Python version: $(python --version)"
        echo "🐍 Pip version: $(pip --version)"
        
        # Test if requirements are installed
        echo "📦 Checking installed packages..."
        pip list | grep -E "(boto3|redis|python-dotenv)" || echo "⚠️  Some packages might be missing"
        
    else
        echo "❌ Virtual environment activation failed"
        echo "🔧 Recreating virtual environment..."
        
        rm -rf venv
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        
        if [ $? -eq 0 ]; then
            echo "✅ Virtual environment recreated successfully"
        else
            echo "❌ Could not recreate virtual environment"
        fi
    fi
else
    echo "❌ Virtual environment not found"
    echo "🔧 Creating virtual environment..."
    
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully"
    else
        echo "❌ Could not create virtual environment"
    fi
fi

echo ""

# Fix 4: Test ElastiCache provisioning
echo "🔍 Issue 4: Testing ElastiCache provisioning..."

if [ -f "provision_elasticache.py" ]; then
    echo "🧪 Running ElastiCache script test (dry run)..."
    
    # Test the script without actually provisioning
    python3 -c "
import sys
sys.path.append('.')
try:
    from provision_elasticache import ElastiCacheProvisioner
    provisioner = ElastiCacheProvisioner()
    print('✅ ElastiCache provisioner initialized successfully')
    print(f'🌍 Region: {provisioner.region}')
    
    # Test instance info detection
    instance_info = provisioner.get_current_instance_info()
    if instance_info:
        print('✅ Instance info detected successfully')
        print(f'📍 VPC: {instance_info[\"vpc_id\"]}')
    else:
        print('⚠️  Instance info detection failed (manual config will be available)')
        
except Exception as e:
    print(f'❌ ElastiCache test failed: {e}')
"
else
    echo "❌ ElastiCache script not found"
fi

echo ""

# Summary
echo "📋 Fix Summary:"
echo "==============="

# Test ls again
if command -v ls >/dev/null 2>&1; then
    echo "✅ ls command: Working"
else
    echo "❌ ls command: Still not working"
fi

# Test Migration directory
if [ -d "/home/ubuntu/Migration" ]; then
    echo "✅ Migration directory: Present"
else
    echo "❌ Migration directory: Missing"
fi

# Test virtual environment
if [ -f "/home/ubuntu/Migration/venv/bin/activate" ]; then
    echo "✅ Virtual environment: Present"
else
    echo "❌ Virtual environment: Missing"
fi

# Test ElastiCache script
if [ -f "/home/ubuntu/Migration/provision_elasticache.py" ]; then
    echo "✅ ElastiCache script: Present"
else
    echo "❌ ElastiCache script: Missing"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. If ls command is working, try: ls -la"
echo "2. To activate virtual environment: cd /home/ubuntu/Migration && source venv/bin/activate"
echo "3. To test ElastiCache: python provision_elasticache.py"
echo "4. The script will now auto-detect your region (eu-north-1) and offer manual VPC config if needed"
echo ""
echo "✅ Fix script completed!"
