# 🚀 ElastiCache Provisioning Tool

This tool automatically provisions AWS ElastiCache Redis instances with proper configuration to allow your EC2 instance to connect to them.

## ✨ Features

- **Automatic Network Configuration**: Creates security groups and subnet groups
- **EC2 Integration**: Automatically detects your EC2 instance's VPC and security groups
- **Multiple Configuration Options**: Interactive, command-line, or preset configurations
- **Cost Estimation**: Shows estimated monthly costs before provisioning
- **Environment-Specific Presets**: Development, staging, and production configurations
- **Cleanup Tools**: Easy removal of created resources

## 📋 Prerequisites

1. **AWS Credentials**: Configure AWS credentials on your EC2 instance
2. **IAM Permissions**: Your instance needs permissions for ElastiCache, EC2, and VPC operations
3. **Python Dependencies**: boto3 and botocore (included in requirements.txt)

### Required IAM Permissions

Your EC2 instance role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticache:CreateCacheCluster",
                "elasticache:CreateCacheSubnetGroup",
                "elasticache:DescribeCacheClusters",
                "elasticache:DescribeCacheSubnetGroups",
                "elasticache:DeleteCacheCluster",
                "elasticache:DeleteCacheSubnetGroup",
                "ec2:CreateSecurityGroup",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeInstances",
                "ec2:DescribeVpcs",
                "ec2:CreateTags",
                "ec2:DeleteSecurityGroup",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🚀 Quick Start

### Interactive Mode (Recommended)

```bash
# Activate virtual environment
cd /home/ubuntu/Migration
source venv/bin/activate

# Run interactive provisioning
python provision_elasticache.py
```

### Automatic Mode

```bash
# Use defaults for development
python provision_elasticache.py --auto

# Specify configuration
python provision_elasticache.py --auto --node-type cache.t3.small --engine-version 7.0

# Use production preset
python provision_elasticache.py --auto --environment production
```

## 📊 Configuration Options

### Node Types

| Node Type | Memory | vCPU | Use Case | Est. Monthly Cost |
|-----------|--------|------|----------|-------------------|
| cache.t3.micro | 0.5 GB | 2 | Development, testing | ~$12 |
| cache.t3.small | 1.37 GB | 2 | Small production | ~$25 |
| cache.t3.medium | 3.09 GB | 2 | Medium production | ~$50 |
| cache.r6g.large | 12.32 GB | 2 | Memory-intensive | ~$110 |

### Engine Versions

- **Redis 7.0** (Recommended): Latest features, Redis Functions, ACLs
- **Redis 6.2**: Previous stable, good compatibility
- **Redis 5.0.6**: Older version for legacy compatibility

### Environment Presets

**Development** (Default):
- Node Type: cache.t3.micro
- Single node
- No encryption
- Basic configuration

**Staging**:
- Node Type: cache.t3.small
- Encryption at rest
- Extended snapshots

**Production**:
- Node Type: cache.r6g.large
- Multi-AZ deployment
- Encryption at rest and in transit
- Authentication token
- Extended backup retention

## 📁 Generated Files

After successful provisioning, you'll get:

1. **`elasticache_<cluster-id>.env`**: Environment configuration for .env file
2. **`elasticache_cluster_<cluster-id>.json`**: Cluster information and metadata

### Example .env Configuration

```bash
# ElastiCache Redis Configuration - Generated 2024-01-15 10:30:00
# Cluster ID: redis-migration-1705312200

# ElastiCache Redis (Destination)
REDIS_DEST_NAME=ElastiCache-redis-migration-1705312200
REDIS_DEST_HOST=redis-migration-1705312200.abc123.cache.amazonaws.com
REDIS_DEST_PORT=6379
REDIS_DEST_PASSWORD=
REDIS_DEST_TLS=false
REDIS_DEST_DB=0

# Connection timeout
REDIS_TIMEOUT=5
```

## 🔧 Usage Examples

### 1. Basic Development Setup

```bash
# Interactive mode - choose development settings
python provision_elasticache.py

# Follow prompts to configure your cluster
```

### 2. Quick Production Setup

```bash
# Automatic production setup
python provision_elasticache.py --auto --environment production --node-type cache.r6g.large
```

### 3. Custom Configuration

```bash
# Specific node type and engine version
python provision_elasticache.py --auto --node-type cache.t3.medium --engine-version 7.0
```

## 🧹 Cleanup

### List Resources

```bash
# List all ElastiCache clusters
python cleanup_elasticache.py --list
```

### Delete Specific Cluster

```bash
# Delete a specific cluster
python cleanup_elasticache.py --delete redis-migration-1705312200
```

### Clean Up All Migration Resources

```bash
# Remove all resources created by the migration tool
python cleanup_elasticache.py --cleanup-all
```

## 🔍 Troubleshooting

### Common Issues

**1. AWS Credentials Not Found**
```bash
# Configure AWS credentials (if not using IAM role)
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**2. Insufficient Permissions**
- Ensure your EC2 instance has the required IAM role
- Check that the role includes all necessary ElastiCache and EC2 permissions

**3. VPC/Subnet Issues**
- Ensure you're running on an EC2 instance in a VPC
- Verify that your VPC has multiple subnets in different availability zones

**4. Security Group Issues**
- The tool automatically creates security groups
- Ensure your EC2 security groups allow outbound traffic on port 6379

### Debug Mode

```bash
# Enable verbose AWS SDK logging
export BOTO_DEBUG=1
python provision_elasticache.py --auto
```

## 💡 Best Practices

1. **Use IAM Roles**: Attach IAM roles to EC2 instances instead of hardcoding credentials
2. **Environment Separation**: Use different clusters for dev/staging/production
3. **Cost Monitoring**: Monitor costs in AWS Cost Explorer
4. **Security**: Enable encryption and authentication for production workloads
5. **Backup Strategy**: Configure appropriate snapshot retention for production
6. **Monitoring**: Set up CloudWatch alarms for your ElastiCache clusters

## 🔗 Integration with Migration Tools

After provisioning ElastiCache:

1. **Copy configuration** from the generated .env file to your main .env
2. **Use manage_env.py** to configure source Redis if needed
3. **Test connection** with DB_compare.py
4. **Run performance tests** with ReadWriteOps.py
5. **Generate test data** with DataFaker.py

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudFormation events in the AWS Console
3. Check CloudWatch logs for detailed error messages
4. Ensure all prerequisites are met
