#!/bin/bash
# 🔐 Create IAM User for GitHub Actions S3 Deployment
#
# This script creates a dedicated IAM user with minimal permissions
# for GitHub Actions to deploy CloudFormation templates to S3.
#
# Usage: ./scripts/create-github-iam-user.sh <bucket-name>
# Example: ./scripts/create-github-iam-user.sh adar-testing
#
# Author: Migration Project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_header() { echo -e "${PURPLE}🔐 $1${NC}"; }

# Check if bucket name is provided
if [[ $# -eq 0 ]]; then
    print_error "Bucket name is required"
    echo "Usage: $0 <bucket-name>"
    echo "Example: $0 adar-testing"
    exit 1
fi

BUCKET_NAME="$1"
IAM_USER="github-actions-s3-deploy-$(date +%Y%m%d)"
POLICY_NAME="GitHubS3DeployPolicy-$(date +%Y%m%d)"

print_header "Creating IAM User for GitHub Actions S3 Deployment"
echo "Bucket: $BUCKET_NAME"
echo "IAM User: $IAM_USER"
echo "=" * 60
echo ""

# Check AWS CLI
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured"
    print_info "Please run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_info "AWS Account: $ACCOUNT_ID"

# Create IAM user
print_info "Creating IAM user: $IAM_USER"
aws iam create-user --user-name "$IAM_USER" --tags Key=Purpose,Value=GitHubActions Key=Project,Value=Migration
print_status "IAM user created"

# Create IAM policy
print_info "Creating IAM policy: $POLICY_NAME"
cat > iam-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3BucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::$BUCKET_NAME",
        "arn:aws:s3:::$BUCKET_NAME/*"
      ]
    },
    {
      "Sid": "CloudFormationValidation",
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate"
      ],
      "Resource": "*"
    }
  ]
}
EOF

POLICY_ARN=$(aws iam create-policy --policy-name "$POLICY_NAME" --policy-document file://iam-policy.json --query 'Policy.Arn' --output text)
print_status "IAM policy created: $POLICY_ARN"

# Attach policy to user
print_info "Attaching policy to user..."
aws iam attach-user-policy --user-name "$IAM_USER" --policy-arn "$POLICY_ARN"
print_status "Policy attached to user"

# Create access keys
print_info "Creating access keys..."
ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name "$IAM_USER")
ACCESS_KEY_ID=$(echo "$ACCESS_KEY_OUTPUT" | jq -r '.AccessKey.AccessKeyId')
SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_OUTPUT" | jq -r '.AccessKey.SecretAccessKey')

# Clean up
rm iam-policy.json

print_status "IAM user setup complete!"
echo ""

print_header "GitHub Secrets Configuration"
echo ""
print_info "Add these secrets to your GitHub repository:"
print_info "Go to: https://github.com/AdarBahar/Migration/settings/secrets/actions"
echo ""

echo "🔐 Secret 1: AWS_ACCESS_KEY_ID"
echo "   Name: AWS_ACCESS_KEY_ID"
echo "   Value: $ACCESS_KEY_ID"
echo ""

echo "🔐 Secret 2: AWS_SECRET_ACCESS_KEY"
echo "   Name: AWS_SECRET_ACCESS_KEY"
echo "   Value: $SECRET_ACCESS_KEY"
echo ""

echo "🔐 Secret 3: S3_BUCKET_NAME"
echo "   Name: S3_BUCKET_NAME"
echo "   Value: $BUCKET_NAME"
echo ""

echo "🔐 Secret 4: AWS_REGION"
echo "   Name: AWS_REGION"
echo "   Value: $(aws configure get region || echo 'us-east-1')"
echo ""

print_warning "IMPORTANT SECURITY NOTES:"
print_info "• Save these credentials securely - they won't be shown again"
print_info "• The secret access key is only displayed once"
print_info "• These credentials have minimal permissions (only S3 and CloudFormation validation)"
print_info "• You can delete this IAM user anytime to revoke access"
echo ""

print_header "Next Steps:"
print_info "1. Copy the values above to GitHub Secrets"
print_info "2. Run: ./scripts/fix-s3-bucket-policy.sh $BUCKET_NAME"
print_info "3. Test by updating migration-instance.yaml and pushing to GitHub"
echo ""

print_status "Setup complete! Your GitHub Actions can now deploy to S3 securely."
