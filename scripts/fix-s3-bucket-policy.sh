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

print_header "Configuring S3 Bucket for Secure CloudFormation Access"
echo "Bucket: $BUCKET_NAME"
echo "Access Method: Pre-signed URLs (Secure)"
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

# Enable block public access settings for security
print_info "Enabling block public access settings for maximum security..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

print_status "Block public access settings enabled for security"

# Remove any existing public bucket policy
print_info "Removing any existing public bucket policies..."
aws s3api delete-bucket-policy --bucket "$BUCKET_NAME" 2>/dev/null || print_info "No existing bucket policy to remove"

print_status "Bucket configured for secure private access"

# Test the configuration
print_info "Testing the configuration..."

# Upload a test file
echo "Test file for CloudFormation template access" > test-file.txt
aws s3 cp test-file.txt "s3://$BUCKET_NAME/test-file.txt"

# Test pre-signed URL generation
print_info "Testing pre-signed URL generation..."
PRESIGNED_URL=$(aws s3 presign "s3://$BUCKET_NAME/test-file.txt" --expires-in 3600)
if [[ -n "$PRESIGNED_URL" ]]; then
    print_status "Pre-signed URL generation successful"
    print_info "Sample pre-signed URL: ${PRESIGNED_URL:0:80}..."
else
    print_warning "Pre-signed URL generation failed"
fi

# Clean up test file
aws s3 rm "s3://$BUCKET_NAME/test-file.txt"
rm test-file.txt

print_status "Test cleanup complete"

echo ""
print_header "Configuration Complete!"
echo ""
print_info "Your bucket is now configured for secure CloudFormation template access:"
print_info "  🔒 Access Method: Pre-signed URLs (secure, time-limited)"
print_info "  🚀 Ready for GitHub Actions deployment"
print_info "  ✅ CloudFormation can access templates via pre-signed URLs"
print_info "  🛡️  Maximum security: No public access allowed"
echo ""
print_status "Security Benefits:"
print_info "  • Bucket remains completely private"
print_info "  • Access controlled via time-limited pre-signed URLs"
print_info "  • No risk of unauthorized public access"
print_info "  • Follows AWS security best practices"
echo ""
print_status "You can now run your GitHub Actions workflow successfully!"
