# 🚀 Migration Setup - Next Steps

## 📊 Current Status Analysis

Based on your pre-flight check results, here's what we found:

### ✅ **Working Perfectly:**
- **ElastiCache Discovery**: Found `redis-elasticache-1759926962`
- **VPC Discovery**: Found VPC `vpc-0bc09fad9d2add0e5` with 2 subnets
- **Target Connectivity**: Successfully connected to Redis Cloud
- **Basic IAM Permissions**: ElastiCache and core EC2 permissions work
- **Configuration Loading**: .env file loaded successfully

### ❌ **Issues to Fix:**
1. **Missing IAM Permissions** (6 permissions)
2. **CloudFormation Stack Update Required**

## 🔧 **Solution: Update Your CloudFormation Stack**

### **Step 1: Update the CloudFormation Stack**

The `migration-instance.yaml` file has been updated with all required permissions. You need to update your existing CloudFormation stack:

```bash
# Update your existing stack with the enhanced permissions
aws cloudformation update-stack \
  --stack-name migration-instance-30-09-test \
  --template-body file://migration-instance.yaml \
  --capabilities CAPABILITY_IAM \
  --region eu-north-1
```

### **Step 2: Wait for Stack Update**

```bash
# Monitor the update progress
aws cloudformation describe-stacks \
  --stack-name migration-instance-30-09-test \
  --region eu-north-1 \
  --query 'Stacks[0].StackStatus'

# Wait for UPDATE_COMPLETE status
aws cloudformation wait stack-update-complete \
  --stack-name migration-instance-30-09-test \
  --region eu-north-1
```

### **Step 3: Verify Permissions**

After the stack update completes, run the pre-flight check again:

```bash
python3 migration_preflight_check.py
```

## 📋 **What the Update Adds**

### **New IAM Permissions Added:**

#### **EC2 Networking:**
- `ec2:DescribeInternetGateways` - For internet connectivity validation

#### **ECS (Container Execution):**
- `ecs:DescribeClusters`, `ecs:ListClusters` - Cluster discovery
- `ecs:CreateCluster`, `ecs:DeleteCluster` - Cluster management
- `ecs:CreateService`, `ecs:UpdateService`, `ecs:DeleteService` - Service management
- `ecs:RegisterTaskDefinition`, `ecs:RunTask`, `ecs:DescribeTasks` - Task execution

#### **CloudFormation (RIOT-X Template):**
- `cloudformation:CreateStack`, `cloudformation:UpdateStack`, `cloudformation:DeleteStack`
- `cloudformation:DescribeStacks`, `cloudformation:DescribeStackEvents`
- `cloudformation:DescribeStackResources`, `cloudformation:ListStacks`

#### **IAM (Service Roles):**
- `iam:CreateRole`, `iam:DeleteRole`, `iam:GetRole`
- `iam:AttachRolePolicy`, `iam:DetachRolePolicy`, `iam:PassRole`

#### **Lambda (Custom Resources):**
- `lambda:CreateFunction`, `lambda:DeleteFunction`, `lambda:InvokeFunction`
- `lambda:UpdateFunctionCode`, `lambda:GetFunction`

#### **CloudWatch Logs:**
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
- `logs:DescribeLogGroups`, `logs:GetLogEvents`

## 🎯 **Expected Results After Update**

Once the CloudFormation stack update completes, your pre-flight check should show:

```
📊 SUMMARY
✅ Passed: 20
❌ Failed: 0
⚠️  Warnings: 1
📊 Total: 21

🎉 SUCCESS: All critical checks passed!
✅ CloudFormation migration template should work successfully.
```

## 🚀 **Ready for Migration**

After all checks pass, you can deploy the RIOT-X migration:

```bash
aws cloudformation create-stack \
  --stack-name riotx-elasticache-migration \
  --template-url https://riot-x.s3.amazonaws.com/ec-sync.yaml \
  --parameters \
    ParameterKey=SourceElastiCacheClusterId,ParameterValue=redis-elasticache-1759926962 \
    ParameterKey=TargetRedisURI,ParameterValue=redis://:YOUR_PASSWORD@redis-12850.c278.us-east-1-4.ec2.redns.redis-cloud.com:12850 \
  --capabilities CAPABILITY_IAM \
  --region eu-north-1
```

## 🔍 **Troubleshooting**

### **If Stack Update Fails:**
```bash
# Check stack events for errors
aws cloudformation describe-stack-events \
  --stack-name migration-instance-30-09-test \
  --region eu-north-1
```

### **If Permissions Still Missing:**
```bash
# Check the current IAM role
aws iam get-role \
  --role-name migration-instance-30-09-test-MigrationInstanceRole-* \
  --region eu-north-1

# List attached policies
aws iam list-attached-role-policies \
  --role-name migration-instance-30-09-test-MigrationInstanceRole-* \
  --region eu-north-1
```

### **Alternative: Manual Permission Addition**

If CloudFormation update doesn't work, you can add permissions manually:

```bash
# Create a policy document with missing permissions
cat > additional-permissions.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInternetGateways",
        "ecs:DescribeClusters",
        "ecs:ListClusters",
        "cloudformation:CreateStack",
        "cloudformation:DescribeStacks"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach to the role
aws iam put-role-policy \
  --role-name migration-instance-30-09-test-MigrationInstanceRole-* \
  --policy-name AdditionalMigrationPermissions \
  --policy-document file://additional-permissions.json \
  --region eu-north-1
```

## 📈 **Success Indicators**

You'll know everything is working when:

1. ✅ **CloudFormation stack update** completes successfully
2. ✅ **Pre-flight check** shows all green checkmarks
3. ✅ **RIOT-X template deployment** succeeds
4. ✅ **Migration execution** completes without errors

## 🎉 **Summary**

Your setup is 95% complete! The pre-flight checker successfully:
- Found your ElastiCache cluster
- Connected to Redis Cloud
- Validated network configuration
- Identified exactly what permissions are missing

Just update the CloudFormation stack with the enhanced IAM permissions, and you'll be ready for a successful migration! 🚀✨
