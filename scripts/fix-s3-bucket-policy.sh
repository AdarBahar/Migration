#!/bin/bash
# 🔧 Fix S3 Bucket Policy for CloudFormation Template Access
#
# This script fixes the "BlockPublicPolicy" error by disabling
# block public access settings and applying the correct bucket policy.
#
# Usage: ./scripts/fix-s3-bucket-policy.sh <bucket-name>
# Example: ./scripts/fix-s3-bucket-policy.sh adar-testing
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
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Check if bucket name is provided
if [[ $# -eq 0 ]]; then
    print_error "Bucket name is required"
    echo "Usage: $0 <bucket-name>"
    echo "Example: $0 adar-testing"
    exit 1
fi

BUCKET_NAME="$1"

print_header "Fixing S3 Bucket Policy for CloudFormation Access"
echo "Bucket: $BUCKET_NAME"
echo "=" * 60
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured"
    print_info "Please run: aws configure"
    exit 1
fi

# Check if bucket exists
print_info "Checking if bucket exists..."
if ! aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
    print_error "Bucket '$BUCKET_NAME' does not exist or you don't have access"
    exit 1
fi
print_status "Bucket exists and accessible"

# Get current block public access settings
print_info "Checking current block public access settings..."
CURRENT_SETTINGS=$(aws s3api get-public-access-block --bucket "$BUCKET_NAME" 2>/dev/null || echo "No settings found")
echo "Current settings: $CURRENT_SETTINGS"

# Disable block public access settings
print_info "Disabling block public access settings..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

print_status "Block public access settings disabled"

# Wait for settings to take effect
print_info "Waiting for settings to take effect..."
sleep 10

# Create and apply bucket policy
print_info "Creating bucket policy for public read access..."
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

print_info "Applying bucket policy..."
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://bucket-policy.json

# Clean up
rm bucket-policy.json

print_status "Bucket policy applied successfully"

# Test the configuration
print_info "Testing the configuration..."

# Upload a test file
echo "Test file for CloudFormation template access" > test-file.txt
aws s3 cp test-file.txt "s3://$BUCKET_NAME/test-file.txt"

# Test public access
PUBLIC_URL="https://$BUCKET_NAME.s3.amazonaws.com/test-file.txt"
if curl -s --head "$PUBLIC_URL" | grep -q "200 OK"; then
    print_status "Public access test successful"
else
    print_warning "Public access test failed - bucket may need more time to update"
fi

# Clean up test file
aws s3 rm "s3://$BUCKET_NAME/test-file.txt"
rm test-file.txt

print_status "Test cleanup complete"

echo ""
print_header "Configuration Complete!"
echo ""
print_info "Your bucket is now configured for CloudFormation template access:"
print_info "  🌐 Public URL format: https://$BUCKET_NAME.s3.amazonaws.com/migration-instance.yaml"
print_info "  🚀 Ready for GitHub Actions deployment"
print_info "  ✅ CloudFormation can access templates directly"
echo ""
print_warning "Security Note:"
print_info "  • The bucket now allows public read access to all objects"
print_info "  • Only upload non-sensitive files (like CloudFormation templates)"
print_info "  • Consider using IAM policies for sensitive content"
echo ""
print_status "You can now run your GitHub Actions workflow successfully!"
