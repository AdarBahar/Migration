#!/bin/bash
# 🔍 Instance Diagnostic Script
# Run this on your EC2 instance to diagnose UserData execution issues

echo "🔍 EC2 Instance Diagnostic Report"
echo "=================================="
echo "Generated at: $(date)"
echo ""

# Basic system info
echo "📋 System Information:"
echo "  OS: $(lsb_release -d | cut -f2)"
echo "  Kernel: $(uname -r)"
echo "  Uptime: $(uptime -p)"
echo "  User: $(whoami)"
echo "  Home: $HOME"
echo ""

# Check cloud-init status
echo "☁️  Cloud-Init Status:"
if command -v cloud-init >/dev/null 2>&1; then
    echo "  Cloud-init installed: ✅"
    sudo cloud-init status --long 2>/dev/null || echo "  Status check failed"
else
    echo "  Cloud-init installed: ❌"
fi
echo ""

# Check UserData
echo "📄 UserData Information:"
if [ -f /var/lib/cloud/instance/user-data.txt ]; then
    echo "  UserData file exists: ✅"
    echo "  UserData size: $(wc -c < /var/lib/cloud/instance/user-data.txt) bytes"
    echo "  UserData first line: $(head -1 /var/lib/cloud/instance/user-data.txt)"
else
    echo "  UserData file exists: ❌"
fi
echo ""

# Check cloud-init logs
echo "📝 Cloud-Init Logs:"
if [ -f /var/log/cloud-init.log ]; then
    echo "  Main log exists: ✅"
    echo "  Main log size: $(wc -l < /var/log/cloud-init.log) lines"
    echo "  Last 3 lines:"
    tail -3 /var/log/cloud-init.log | sed 's/^/    /'
else
    echo "  Main log exists: ❌"
fi

if [ -f /var/log/cloud-init-output.log ]; then
    echo "  Output log exists: ✅"
    echo "  Output log size: $(wc -l < /var/log/cloud-init-output.log) lines"
    echo "  Last 5 lines:"
    tail -5 /var/log/cloud-init-output.log | sed 's/^/    /'
else
    echo "  Output log exists: ❌"
fi
echo ""

# Check for errors
echo "🚨 Error Analysis:"
if [ -f /var/log/cloud-init-output.log ]; then
    ERROR_COUNT=$(grep -i "error\|failed\|exception" /var/log/cloud-init-output.log | wc -l)
    echo "  Errors in output log: $ERROR_COUNT"
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "  Recent errors:"
        grep -i "error\|failed\|exception" /var/log/cloud-init-output.log | tail -3 | sed 's/^/    /'
    fi
else
    echo "  Cannot check errors: output log missing"
fi
echo ""

# Check network connectivity
echo "🌐 Network Connectivity:"
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "  Internet connectivity: ✅"
else
    echo "  Internet connectivity: ❌"
fi

if ping -c 1 github.com >/dev/null 2>&1; then
    echo "  GitHub connectivity: ✅"
else
    echo "  GitHub connectivity: ❌"
fi
echo ""

# Check installed packages
echo "📦 Package Status:"
for pkg in python3 python3-pip python3-venv git curl wget; do
    if dpkg -l | grep -q "^ii  $pkg "; then
        echo "  $pkg: ✅ installed"
    else
        echo "  $pkg: ❌ not installed"
    fi
done
echo ""

# Check Migration directory
echo "📁 Migration Directory:"
if [ -d /home/ubuntu/Migration ]; then
    echo "  Migration directory exists: ✅"
    echo "  Directory contents:"
    ls -la /home/ubuntu/Migration | sed 's/^/    /'
    
    if [ -f /home/ubuntu/Migration/requirements.txt ]; then
        echo "  requirements.txt exists: ✅"
    else
        echo "  requirements.txt exists: ❌"
    fi
    
    if [ -d /home/ubuntu/Migration/venv ]; then
        echo "  Virtual environment exists: ✅"
    else
        echo "  Virtual environment exists: ❌"
    fi
else
    echo "  Migration directory exists: ❌"
fi
echo ""

# Check scripts
echo "🔧 Helper Scripts:"
for script in start-migration.sh activate-migration migration; do
    if [ -f /home/ubuntu/$script ]; then
        echo "  $script: ✅ exists"
        if [ -x /home/ubuntu/$script ]; then
            echo "    Executable: ✅"
        else
            echo "    Executable: ❌"
        fi
    else
        echo "  $script: ❌ missing"
    fi
done
echo ""

# Check AWS CLI and cfn-signal
echo "🔧 AWS Tools:"
if command -v aws >/dev/null 2>&1; then
    echo "  AWS CLI: ✅ installed"
    echo "    Version: $(aws --version 2>&1 | head -1)"
else
    echo "  AWS CLI: ❌ not installed"
fi

if command -v cfn-signal >/dev/null 2>&1; then
    echo "  cfn-signal: ✅ available"
    echo "    Location: $(which cfn-signal)"
else
    echo "  cfn-signal: ❌ not available"
fi
echo ""

# Check CloudFormation signaling
echo "📡 CloudFormation Signaling:"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "unknown")
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || echo "unknown")
echo "  Instance ID: $INSTANCE_ID"
echo "  Region: $REGION"

if [ "$INSTANCE_ID" != "unknown" ] && [ "$REGION" != "unknown" ]; then
    echo "  Metadata access: ✅"
    if command -v aws >/dev/null 2>&1; then
        STACK_NAME=$(aws ec2 describe-tags --region $REGION --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=aws:cloudformation:stack-name" --query 'Tags[0].Value' --output text 2>/dev/null || echo "unknown")
        echo "  Stack name: $STACK_NAME"
    fi
else
    echo "  Metadata access: ❌"
fi
echo ""

# Recommendations
echo "💡 Recommendations:"
if [ ! -d /home/ubuntu/Migration ]; then
    echo "  • Migration directory missing - UserData script likely failed"
    echo "  • Check cloud-init logs for errors"
    echo "  • Consider manual installation"
fi

if ! command -v git >/dev/null 2>&1; then
    echo "  • Git not installed - package installation failed"
    echo "  • Check internet connectivity and package repositories"
fi

if [ -f /var/log/cloud-init-output.log ]; then
    if grep -q "✅ All installation completed successfully" /var/log/cloud-init-output.log; then
        echo "  • Installation appears to have completed successfully"
    else
        echo "  • Installation did not complete - check output log for details"
    fi
fi

echo ""
echo "🔍 For detailed analysis, check:"
echo "  • sudo cat /var/log/cloud-init-output.log"
echo "  • sudo journalctl -u cloud-init-final"
echo "  • sudo cloud-init status --long"
echo ""
echo "📞 If issues persist, share this report for further assistance."
