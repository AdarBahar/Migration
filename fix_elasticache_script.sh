#!/bin/bash
# 🔧 Fix ElastiCache Script on Current Instance
# This script updates the ElastiCache provisioning script with the latest fixes

echo "🔧 Fixing ElastiCache Script"
echo "============================"

cd /home/ubuntu/Migration

# Pull latest changes
echo "📥 Pulling latest updates..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Repository updated successfully"
else
    echo "⚠️  Git pull failed, trying reset..."
    git fetch origin
    git reset --hard origin/main
    
    if [ $? -eq 0 ]; then
        echo "✅ Repository reset to latest version"
    else
        echo "❌ Could not update repository"
        exit 1
    fi
fi

# Test the updated script
echo ""
echo "🧪 Testing updated ElastiCache script..."
python3 -c "
try:
    from provision_elasticache import ElastiCacheProvisioner
    provisioner = ElastiCacheProvisioner()
    print('✅ ElastiCache provisioner loaded successfully')
    print(f'🌍 Region: {provisioner.region}')
except Exception as e:
    print(f'❌ ElastiCache test failed: {e}')
"

echo ""
echo "🎯 Fix completed!"
echo "💡 You can now run: python provision_elasticache.py"
echo ""
echo "📋 What was fixed:"
echo "  • Cache type detection logic"
echo "  • Serverless vs cluster fallback handling"
echo "  • Status checking for correct cache type"
echo "  • Variable name consistency"
