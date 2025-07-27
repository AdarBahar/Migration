# 🔧 CloudFormation Troubleshooting Guide

## 🚨 "Failed to receive resource signal" Error

If your CloudFormation stack fails with "Failed to receive 1 resource signal(s) within the specified duration", here's how to troubleshoot:

### 📋 Quick Checklist

1. **✅ Check subnet configuration**: Must be a PUBLIC subnet with auto-assign public IP enabled
2. **✅ Check security groups**: SSH access (port 22) must be allowed from your IP
3. **✅ Check key pair**: Must exist and be accessible for SSH
4. **✅ Check IAM permissions**: Stack creates IAM role automatically
5. **✅ Check region**: AMI `ami-042b4708b1d05f512` is for us-east-1

### 🔍 Debugging Steps

#### Step 1: Check Instance Status
1. Go to **EC2 Console** → **Instances**
2. Find your instance (tagged with stack name)
3. Check **Instance State** (should be "running")
4. Check **Status Checks** (should be 2/2 checks passed)

#### Step 2: Check Instance Logs
1. Select your instance → **Actions** → **Monitor and troubleshoot** → **Get system log**
2. Look for errors in the boot process
3. Check for network connectivity issues

#### Step 3: SSH to Instance (if accessible)
```bash
# Use the SSH command from CloudFormation Outputs
ssh -i /path/to/your-key.pem ubuntu@<public-ip>

# Check cloud-init logs
sudo tail -f /var/log/cloud-init-output.log

# Check if cfn-signal is available
which cfn-signal

# Check if installation completed
ls -la /home/ubuntu/Migration/
```

#### Step 4: Check CloudFormation Events
1. Go to **CloudFormation Console** → Your stack
2. Click **Events** tab
3. Look for detailed error messages
4. Check timestamps to see where it got stuck

### 🛠️ Common Issues and Solutions

#### Issue 1: Subnet Not Public
**Error**: Instance has no public IP
**Solution**: 
1. Go to **VPC Console** → **Subnets**
2. Select your subnet → **Actions** → **Modify auto-assign IP settings**
3. Enable **"Auto-assign public IPv4 address"**
4. Redeploy stack

#### Issue 2: Security Group Issues
**Error**: Can't SSH to instance
**Solution**:
1. Check your current IP: https://checkip.amazonaws.com
2. Update **MyIP** parameter with correct IP/32
3. Ensure security group allows SSH (port 22)

#### Issue 3: Wrong Region
**Error**: AMI not found
**Solution**:
1. Deploy in **us-east-1** region, OR
2. Find Ubuntu 22.04 LTS AMI ID for your region
3. Update **AmiId** parameter

#### Issue 4: Installation Timeout
**Error**: Signal timeout after 15 minutes
**Solution**:
1. Check internet connectivity from instance
2. Verify package repositories are accessible
3. Check if GitHub is accessible for git clone

### 📊 Monitoring Installation Progress

The updated template includes detailed logging. You can monitor progress by:

1. **SSH to instance** (if accessible)
2. **Check installation log**:
   ```bash
   sudo tail -f /var/log/cloud-init-output.log
   ```

3. **Look for these progress indicators**:
   ```
   ✅ All installation completed successfully!
   🎉 Migration environment is ready for use!
   🔄 Starting CloudFormation signaling process...
   📍 Getting instance metadata...
   📍 Instance ID: i-1234567890abcdef0
   📍 Region: us-east-1
   ✅ cfn-signal found
   🔍 Looking for stack name in instance tags...
   📍 Stack name: Redis-Migration-Tool
   🚀 Sending CloudFormation signal...
   ✅ CloudFormation signal sent successfully!
   ```

### 🚀 Alternative: Deploy Without Signaling

If signaling continues to fail, you can temporarily disable it:

1. **Remove CreationPolicy** from the template:
   ```yaml
   MigrationInstance:
     Type: AWS::EC2::Instance
     # Remove these lines:
     # CreationPolicy:
     #   ResourceSignal:
     #     Count: 1
     #     Timeout: PT15M
   ```

2. **Deploy stack** - it will complete immediately
3. **SSH to instance** after 10-15 minutes to verify installation
4. **Re-enable signaling** once issues are resolved

### 📞 Getting Help

If issues persist:

1. **Check AWS CloudTrail** for API call errors
2. **Review VPC Flow Logs** for network issues
3. **Contact AWS Support** for infrastructure issues
4. **Check GitHub Issues** for template-specific problems

### 💡 Prevention Tips

1. **Test in us-east-1** first (default AMI region)
2. **Use default VPC** for initial testing
3. **Verify internet connectivity** before deployment
4. **Keep CloudFormation timeout** reasonable (15 minutes is good)
5. **Monitor AWS service health** during deployment
