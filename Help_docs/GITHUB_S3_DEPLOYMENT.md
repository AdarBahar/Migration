# 🚀 GitHub to S3 Automatic Deployment Setup

This guide explains how to set up automatic deployment of the CloudFormation template to S3 whenever `migration-instance.yaml` is updated on GitHub.

## 🎯 **Overview**

The GitHub Actions workflow automatically:
- ✅ **Validates** the CloudFormation template
- ✅ **Uploads** to S3 bucket when `migration-instance.yaml` changes
- ✅ **Generates** public URLs for easy deployment
- ✅ **Creates** deployment logs for tracking
- ✅ **Provides** one-click deploy links

## 🔧 **Setup Requirements**

### **1. AWS S3 Bucket**
You need an S3 bucket to store the CloudFormation template.

#### **Create S3 Bucket:**
```bash
# Replace 'your-bucket-name' with your desired bucket name
aws s3 mb s3://your-cloudformation-templates --region us-east-1
```

#### **Configure Bucket for Public Read (Optional):**
```bash
# Make the bucket publicly readable for CloudFormation
aws s3api put-bucket-policy --bucket your-cloudformation-templates --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-cloudformation-templates/*"
    }
  ]
}'
```

### **2. AWS IAM User for GitHub Actions**

#### **Create IAM User:**
```bash
aws iam create-user --user-name github-actions-s3-deploy
```

#### **Create IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-cloudformation-templates/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::your-cloudformation-templates"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **Attach Policy and Create Access Keys:**
```bash
# Save the policy to a file
cat > github-s3-policy.json << 'EOF'
[paste the JSON policy above]
EOF

# Create and attach the policy
aws iam create-policy --policy-name GitHubS3DeployPolicy --policy-document file://github-s3-policy.json
aws iam attach-user-policy --user-name github-actions-s3-deploy --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/GitHubS3DeployPolicy

# Create access keys
aws iam create-access-key --user-name github-actions-s3-deploy
```

## 🔐 **GitHub Secrets Configuration**

### **Required Secrets:**
Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

#### **1. AWS_ACCESS_KEY_ID**
- **Value**: Access Key ID from the IAM user created above
- **Description**: AWS Access Key for S3 deployment

#### **2. AWS_SECRET_ACCESS_KEY**
- **Value**: Secret Access Key from the IAM user created above
- **Description**: AWS Secret Key for S3 deployment

#### **3. S3_BUCKET_NAME**
- **Value**: Your S3 bucket name (e.g., `your-cloudformation-templates`)
- **Description**: S3 bucket where CloudFormation template will be stored

#### **4. AWS_REGION (Optional)**
- **Value**: AWS region (e.g., `us-east-1`)
- **Description**: AWS region for S3 bucket (defaults to us-east-1 if not set)

### **Setting Up Secrets:**

1. **Go to GitHub Repository**
2. **Click Settings** (top menu)
3. **Click Secrets and variables** → **Actions** (left sidebar)
4. **Click "New repository secret"**
5. **Add each secret** with the name and value above

## 🚀 **How It Works**

### **Trigger Conditions:**
The workflow runs when:
- ✅ **Push to main branch** with changes to `migration-instance.yaml`
- ✅ **Pull request to main** with changes to `migration-instance.yaml`

### **Workflow Steps:**
1. **📥 Checkout** - Downloads repository code
2. **🔧 Configure AWS** - Sets up AWS credentials from secrets
3. **✅ Validate Template** - Validates CloudFormation syntax
4. **📊 Template Info** - Shows file details and target location
5. **📤 Upload to S3** - Uploads template with metadata
6. **🔗 Generate URLs** - Creates public and one-click deploy URLs
7. **📝 Deployment Log** - Creates timestamped deployment record
8. **🎉 Summary** - Shows completion status and next steps

### **Generated URLs:**

#### **Public S3 URL:**
```
https://your-bucket-name.s3.us-east-1.amazonaws.com/migration-instance.yaml
```

#### **One-Click Deploy URL:**
```
https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?templateURL=https%3A//your-bucket-name.s3.us-east-1.amazonaws.com/migration-instance.yaml&stackName=Redis-Migration-Stack
```

## 📋 **Usage Examples**

### **After Setup:**
1. **Edit** `migration-instance.yaml` in your repository
2. **Commit and push** to main branch
3. **GitHub Actions** automatically runs
4. **Template is uploaded** to S3
5. **Use the generated URLs** for deployment

### **Deployment Logs:**
Deployment logs are stored in S3 at:
```
s3://your-bucket-name/deployment-logs/YYYYMMDD-HHMMSS-commit-sha.json
```

Each log contains:
- Timestamp and commit information
- Template size and S3 location
- Public URLs for deployment
- Actor and branch information

## 🔍 **Monitoring and Troubleshooting**

### **Check Workflow Status:**
1. Go to your GitHub repository
2. Click **Actions** tab
3. View **Deploy CloudFormation Template to S3** workflows

### **Common Issues:**

#### **❌ AWS Credentials Error**
- **Cause**: Missing or incorrect AWS secrets
- **Fix**: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in GitHub secrets

#### **❌ S3 Bucket Not Found**
- **Cause**: Bucket doesn't exist or wrong name
- **Fix**: Create bucket or update S3_BUCKET_NAME secret

#### **❌ Permission Denied**
- **Cause**: IAM user lacks S3 permissions
- **Fix**: Attach proper IAM policy to the user

#### **❌ Template Validation Failed**
- **Cause**: Invalid CloudFormation syntax
- **Fix**: Validate template locally before committing

### **Manual Validation:**
```bash
# Test locally before committing
aws cloudformation validate-template --template-body file://migration-instance.yaml
```

## 🎯 **Benefits**

### **✅ Automation:**
- No manual S3 uploads needed
- Automatic validation prevents broken templates
- Consistent deployment process

### **✅ Tracking:**
- Deployment logs for audit trail
- Version tracking with commit SHA
- Timestamped deployments

### **✅ Convenience:**
- One-click deploy URLs generated automatically
- Public URLs for easy sharing
- Integration with existing GitHub workflow

### **✅ Reliability:**
- Template validation before upload
- Error handling and notifications
- Rollback capability through version history

---

**Note**: This setup ensures your CloudFormation template is always available in S3 and ready for deployment whenever you make changes to the repository!
