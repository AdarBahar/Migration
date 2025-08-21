#!/bin/bash
# 🚀 Setup S3 Deployment for CloudFormation Templates
#
# This script helps set up the S3 bucket and IAM user for automatic
# GitHub Actions deployment of CloudFormation templates.
#
# Usage: ./scripts/setup-s3-deployment.sh
# Author: Migration Project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        print_info "Please install AWS CLI: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Check if AWS is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured"
        print_info "Please run: aws configure"
        exit 1
    fi
    
    print_status "AWS CLI is installed and configured"
}

# Get user input for configuration
get_configuration() {
    print_header "S3 Deployment Configuration"
    echo ""
    
    # Get bucket name
    read -p "Enter S3 bucket name for CloudFormation templates: " BUCKET_NAME
    if [[ -z "$BUCKET_NAME" ]]; then
        print_error "Bucket name cannot be empty"
        exit 1
    fi
    
    # Get AWS region
    read -p "Enter AWS region [us-east-1]: " AWS_REGION
    AWS_REGION=${AWS_REGION:-us-east-1}
    
    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    print_info "Configuration:"
    print_info "  Bucket: $BUCKET_NAME"
    print_info "  Region: $AWS_REGION"
    print_info "  Account: $ACCOUNT_ID"
    echo ""
}

# Create S3 bucket
create_s3_bucket() {
    print_step "Step 1: Creating S3 bucket..."
    
    # Check if bucket already exists
    if aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
        print_warning "Bucket $BUCKET_NAME already exists"
    else
        # Create bucket
        if [[ "$AWS_REGION" == "us-east-1" ]]; then
            aws s3 mb "s3://$BUCKET_NAME"
        else
            aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION"
        fi
        print_status "S3 bucket created: $BUCKET_NAME"
    fi
    
    # Configure bucket for public read
    print_info "Configuring bucket for public read access..."

    # First, disable block public access settings
    print_info "Disabling block public access settings..."
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

    # Wait a moment for the setting to take effect
    sleep 5

    cat > bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

    aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://bucket-policy.json
    rm bucket-policy.json

    print_status "Bucket configured for public read access"
}

# Create IAM user and policy
create_iam_user() {
    print_step "Step 2: Creating IAM user for GitHub Actions..."
    
    IAM_USER="github-actions-s3-deploy"
    POLICY_NAME="GitHubS3DeployPolicy"
    
    # Check if user already exists
    if aws iam get-user --user-name "$IAM_USER" &> /dev/null; then
        print_warning "IAM user $IAM_USER already exists"
    else
        aws iam create-user --user-name "$IAM_USER"
        print_status "IAM user created: $IAM_USER"
    fi
    
    # Create IAM policy
    cat > iam-policy.json << EOF
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
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::$BUCKET_NAME"
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
EOF
    
    # Create policy (delete if exists)
    POLICY_ARN="arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"
    if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
        print_warning "Policy $POLICY_NAME already exists, updating..."
        aws iam create-policy-version --policy-arn "$POLICY_ARN" --policy-document file://iam-policy.json --set-as-default
    else
        aws iam create-policy --policy-name "$POLICY_NAME" --policy-document file://iam-policy.json
        print_status "IAM policy created: $POLICY_NAME"
    fi
    
    # Attach policy to user
    aws iam attach-user-policy --user-name "$IAM_USER" --policy-arn "$POLICY_ARN"
    print_status "Policy attached to user"
    
    rm iam-policy.json
}

# Create access keys
create_access_keys() {
    print_step "Step 3: Creating access keys..."
    
    IAM_USER="github-actions-s3-deploy"
    
    # Delete existing access keys
    EXISTING_KEYS=$(aws iam list-access-keys --user-name "$IAM_USER" --query 'AccessKeyMetadata[].AccessKeyId' --output text)
    for key in $EXISTING_KEYS; do
        print_warning "Deleting existing access key: $key"
        aws iam delete-access-key --user-name "$IAM_USER" --access-key-id "$key"
    done
    
    # Create new access key
    ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name "$IAM_USER")
    ACCESS_KEY_ID=$(echo "$ACCESS_KEY_OUTPUT" | jq -r '.AccessKey.AccessKeyId')
    SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_OUTPUT" | jq -r '.AccessKey.SecretAccessKey')
    
    print_status "Access keys created successfully"
}

# Display GitHub Secrets configuration
display_github_secrets() {
    print_step "Step 4: GitHub Secrets Configuration"
    echo ""
    print_header "Add these secrets to your GitHub repository:"
    print_header "Settings → Secrets and variables → Actions → New repository secret"
    echo ""
    
    echo "🔐 AWS_ACCESS_KEY_ID"
    echo "   Value: $ACCESS_KEY_ID"
    echo ""
    
    echo "🔐 AWS_SECRET_ACCESS_KEY"
    echo "   Value: $SECRET_ACCESS_KEY"
    echo ""
    
    echo "🔐 S3_BUCKET_NAME"
    echo "   Value: $BUCKET_NAME"
    echo ""
    
    echo "🔐 AWS_REGION"
    echo "   Value: $AWS_REGION"
    echo ""
}

# Test the setup
test_setup() {
    print_step "Step 5: Testing the setup..."
    
    # Test S3 upload
    echo "Test file for GitHub Actions deployment" > test-file.txt
    aws s3 cp test-file.txt "s3://$BUCKET_NAME/test-file.txt"
    aws s3 rm "s3://$BUCKET_NAME/test-file.txt"
    rm test-file.txt
    
    print_status "S3 upload test successful"
    
    # Test CloudFormation validation
    if [[ -f "migration-instance.yaml" ]]; then
        aws cloudformation validate-template --template-body file://migration-instance.yaml > /dev/null
        print_status "CloudFormation template validation successful"
    else
        print_warning "migration-instance.yaml not found, skipping validation test"
    fi
}

# Display final URLs
display_urls() {
    print_header "Deployment URLs"
    echo ""
    
    print_info "Public S3 URL:"
    echo "   https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/migration-instance.yaml"
    echo ""
    
    print_info "One-Click Deploy URL:"
    TEMPLATE_URL="https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/migration-instance.yaml"
    ENCODED_URL=$(echo "$TEMPLATE_URL" | sed 's/:/%3A/g; s/\//%2F/g')
    echo "   https://console.aws.amazon.com/cloudformation/home?region=$AWS_REGION#/stacks/create/review?templateURL=$ENCODED_URL&stackName=Redis-Migration-Stack"
    echo ""
}

# Main function
main() {
    print_header "S3 Deployment Setup for CloudFormation Templates"
    echo "=" * 60
    echo ""
    
    check_aws_cli
    get_configuration
    create_s3_bucket
    create_iam_user
    create_access_keys
    display_github_secrets
    test_setup
    display_urls
    
    print_header "Setup Complete!"
    print_status "Your S3 deployment is ready for GitHub Actions"
    print_info "Next steps:"
    print_info "1. Add the GitHub Secrets shown above"
    print_info "2. Commit and push changes to migration-instance.yaml"
    print_info "3. Watch the GitHub Actions workflow deploy automatically"
}

# Run main function
main "$@"
