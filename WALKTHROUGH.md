# 🚀 Redis Migration Tool - Complete Walkthrough

This guide walks you through the entire process of deploying and using the Redis Migration Tool, from CloudFormation deployment to running migration tests.

## 📋 Prerequisites

- **AWS Account** with appropriate permissions
- **EC2 Key Pair** for SSH access
- **VPC and Subnet** (public subnet with auto-assign public IP)
- **Your IP address** for security group access

## 🎯 Step 1: Deploy CloudFormation Stack

### **Get Your IP Address**
```bash
curl https://checkip.amazonaws.com
# Note this IP for the MyIP parameter
```

### **Deploy the Stack**
```bash
aws cloudformation create-stack \
  --stack-name Redis-Migration-Tool \
  --template-body file://migration-instance.yaml \
  --parameters \
    ParameterKey=KeyName,ParameterValue=your-key-name \
    ParameterKey=VpcId,ParameterValue=vpc-xxxxxxxx \
    ParameterKey=SubnetId,ParameterValue=subnet-xxxxxxxx \
    ParameterKey=MyIP,ParameterValue=YOUR.IP.ADDRESS/32 \
  --capabilities CAPABILITY_IAM \
  --region your-preferred-region
```

### **Monitor Deployment**
```bash
# Watch stack progress (15-20 minutes)
aws cloudformation describe-stacks \
  --stack-name Redis-Migration-Tool \
  --query 'Stacks[0].StackStatus'

# Get SSH command when complete
aws cloudformation describe-stacks \
  --stack-name Redis-Migration-Tool \
  --query 'Stacks[0].Outputs[?OutputKey==`SSHCommand`].OutputValue' \
  --output text
```

**⏱️ Expected Time**: 15-20 minutes for complete installation

## 🔗 Step 2: Connect to Your Instance

### **SSH to Instance**
```bash
# Use the SSH command from CloudFormation outputs
ssh -i /path/to/your-key.pem ubuntu@<public-ip>
```

### **Verify Installation**
```bash
# Navigate to Migration directory
cd /home/ubuntu/Migration

# Run verification script
./verify_setup.sh

# Expected output:
# ✅ Region detected: eu-north-1 (or your region)
# ✅ Virtual environment activated
# ✅ AWS CLI available
# ✅ ElastiCache provisioner ready
```

### **Activate Environment**
```bash
# Activate virtual environment
source venv/bin/activate

# Verify Python environment
python --version  # Should show Python 3.x
pip list | grep -E "(redis|boto3|faker)"  # Should show installed packages
```

## 🚀 Step 3: Provision ElastiCache

### **Run ElastiCache Provisioning**
```bash
# Provision your first ElastiCache instance
python provision_elasticache.py
```

### **Follow the Prompts**
1. **Cache Name**: `Source-ElastiCache` (or your preferred name)
2. **Environment**: `development`
3. **Node Type**: `cache.t3.micro` (free tier eligible)
4. **Engine Version**: `7.0` (latest)

### **Expected Output**
```
🌍 Detected region from EC2 metadata (IMDSv2): eu-north-1
✅ Current EC2 instance detected: i-1234567890abcdef0
📍 VPC: vpc-12345678
📍 Subnet: subnet-12345678
🚀 Creating ElastiCache Redis cluster: Source-ElastiCache
⏳ Waiting for cluster to become available...
✅ Cluster is available!
🎉 ElastiCache Redis Cluster provisioned successfully!
```

**⏱️ Expected Time**: 10-15 minutes for ElastiCache provisioning

## ⚙️ Step 4: Configure Environment

### **Run Environment Configuration**
```bash
python manage_env.py
```

### **Configure Source Redis (ElastiCache)**
The script will auto-detect your ElastiCache instance:
- **Name**: `AWS_RedisOSS`
- **Host**: `source-elasticache.xxxxx.cache.amazonaws.com`
- **Port**: `6379`
- **Password**: Press **Enter** (no password)
- **TLS/SSL**: `n` (no encryption)

### **Configure Destination Redis**
Choose one option:

#### **Option A: Same ElastiCache (Different DB)**
- **Name**: `AWS_RedisOSS_Dest`
- **Host**: Same as source
- **Port**: `6379`
- **Password**: Press **Enter** (no password)
- **TLS/SSL**: `n`
- **Database**: `1` (different from source DB 0)

#### **Option B: Local Redis**
```bash
# Install local Redis first
sudo apt update && sudo apt install -y redis-server
sudo systemctl start redis-server

# Then configure:
# Name: Local_Redis
# Host: localhost
# Port: 6379
# Password: [Enter] (no password)
# TLS/SSL: n
```

### **Test Connections**
The script will automatically test both connections:
```
Testing connection to AWS_RedisOSS...
✅ Connection to AWS_RedisOSS successful!
Testing connection to AWS_RedisOSS_Dest...
✅ Connection to AWS_RedisOSS_Dest successful!
```

## 📊 Step 5: Generate Test Data

### **Create Sample Data**
```bash
python DataFaker.py
```

### **Follow the Prompts**
1. **Select source database**: Choose your source Redis
2. **Number of records**: `1000` (or your preferred amount)
3. **Data types**: Select what to generate (users, products, sessions, etc.)

### **Expected Output**
```
🎲 Generating fake data for Redis database...
📊 Connected to: AWS_RedisOSS (source-elasticache.xxxxx.cache.amazonaws.com:6379)
✅ Generated 1000 user records
✅ Generated 500 product records
✅ Generated 200 session records
🎉 Data generation complete!
```

## 🔍 Step 6: Compare Databases

### **Run Database Comparison**
```bash
python DB_compare.py
```

### **Expected Output**
```
🔍 Comparing Redis databases...
📊 Source: AWS_RedisOSS (1700 keys)
📊 Destination: AWS_RedisOSS_Dest (0 keys)

📋 Comparison Results:
  • Keys only in source: 1700
  • Keys only in destination: 0
  • Keys in both: 0
  • Value mismatches: 0

💡 Databases are different - migration needed!
```

## ⚡ Step 7: Performance Testing

### **Run Performance Benchmarks**
```bash
python ReadWriteOps.py
```

### **Test Options**
1. **Read Performance**: Test read operations per second
2. **Write Performance**: Test write operations per second
3. **Mixed Workload**: Test combined read/write operations
4. **Latency Testing**: Measure response times

### **Expected Output**
```
🚀 Redis Performance Testing
📊 Testing AWS_RedisOSS (source-elasticache.xxxxx.cache.amazonaws.com:6379)

📈 Write Performance: 2,500 ops/sec
📈 Read Performance: 5,000 ops/sec
📈 Average Latency: 2.5ms
✅ Performance test complete!
```

## 🧹 Step 8: Cleanup (Optional)

### **Clean Test Data**
```bash
python flushDBData.py
```

### **Remove ElastiCache Resources**
```bash
python cleanup_elasticache.py
```

### **Delete CloudFormation Stack**
```bash
aws cloudformation delete-stack --stack-name Redis-Migration-Tool
```

## 🎯 Advanced Usage

### **Multiple ElastiCache Instances**
```bash
# Provision second instance for real migration testing
python provision_elasticache.py
# Choose different name: "Destination-ElastiCache"
```

### **Custom Configuration**
```bash
# Edit .env file directly
nano .env

# Or use environment-specific configs
python elasticache_config.py
```

### **Monitoring and Logs**
```bash
# Check CloudFormation deployment logs
sudo cat /var/log/cloud-init-output.log

# Monitor ElastiCache metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name CPUUtilization \
  --dimensions Name=CacheClusterId,Value=source-elasticache \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Average
```

## 🔧 Troubleshooting

### **Connection Issues**
```bash
# Test direct Redis connection
python3 -c "
import redis
r = redis.Redis(host='your-elasticache-endpoint', port=6379, ssl=False)
print(r.ping())
"

# Check security groups
aws ec2 describe-security-groups --filters "Name=group-name,Values=*elasticache*"
```

### **Permission Issues**
```bash
# Check IAM role permissions
aws sts get-caller-identity
aws iam list-attached-role-policies --role-name YourRoleName
```

### **ElastiCache Issues**
```bash
# Check cluster status
aws elasticache describe-cache-clusters --show-cache-node-info

# Check subnet groups
aws elasticache describe-cache-subnet-groups
```

## 📚 Additional Resources

- **CloudFormation Template**: `migration-instance.yaml`
- **Troubleshooting Guide**: `TROUBLESHOOTING.md`
- **Out-of-the-Box Features**: `OUT_OF_THE_BOX_FEATURES.md`
- **Instance Documentation**: `migration-instance.md`

## 🎉 Success Criteria

You've successfully completed the walkthrough when:
- ✅ CloudFormation stack deploys successfully
- ✅ Instance verification script passes all checks
- ✅ ElastiCache instance provisions without errors
- ✅ Environment configuration connects to both databases
- ✅ Test data generates successfully
- ✅ Database comparison shows expected results
- ✅ Performance tests complete successfully

**🎊 Congratulations! Your Redis Migration Tool is ready for production use!**

---

## 📖 Detailed Command Reference

### **Quick Commands Cheat Sheet**

```bash
# Environment Setup
cd /home/ubuntu/Migration
source venv/bin/activate

# Core Tools
python provision_elasticache.py    # Provision ElastiCache
python manage_env.py               # Configure connections
python DataFaker.py                # Generate test data
python DB_compare.py               # Compare databases
python ReadWriteOps.py             # Performance testing
python flushDBData.py              # Clean databases
python cleanup_elasticache.py      # Remove ElastiCache

# Verification
./verify_setup.sh                  # Check installation
aws elasticache describe-cache-clusters --region your-region
```

### **Environment Variables Reference**

Your `.env` file should contain:
```bash
# Source Redis (ElastiCache)
REDIS_SOURCE_HOST=source-elasticache.xxxxx.cache.amazonaws.com
REDIS_SOURCE_PORT=6379
REDIS_SOURCE_PASSWORD=
REDIS_SOURCE_TLS=false
REDIS_SOURCE_DB=0

# Destination Redis
REDIS_DEST_HOST=destination-host
REDIS_DEST_PORT=6379
REDIS_DEST_PASSWORD=
REDIS_DEST_TLS=false
REDIS_DEST_DB=0
```

### **Common Use Cases**

#### **Scenario 1: Development Testing**
- Single ElastiCache instance
- Different databases (0 and 1)
- Local development workflow

#### **Scenario 2: Migration Testing**
- Two ElastiCache instances
- Production-like environment
- Performance benchmarking

#### **Scenario 3: Hybrid Setup**
- ElastiCache as source
- Local Redis as destination
- Cost-effective testing

### **Best Practices**

1. **Security**
   - Always use specific IP ranges in security groups
   - Enable encryption in transit for production
   - Use IAM roles instead of access keys

2. **Performance**
   - Choose appropriate instance types
   - Monitor CloudWatch metrics
   - Test with realistic data volumes

3. **Cost Management**
   - Use t3.micro for development
   - Clean up resources when done
   - Monitor AWS billing

4. **Monitoring**
   - Check ElastiCache metrics
   - Monitor connection counts
   - Track performance trends

---

## 🚨 Important Notes

- **Free Tier**: t3.micro ElastiCache instances are free tier eligible
- **Regions**: Template works in any AWS region with automatic detection
- **Networking**: Requires public subnet with auto-assign public IP
- **Security**: SSH access restricted to your IP only
- **Cleanup**: Remember to delete resources to avoid charges

---

## 📞 Support and Troubleshooting

If you encounter issues:

1. **Check the verification script**: `./verify_setup.sh`
2. **Review installation logs**: `sudo cat /var/log/cloud-init-output.log`
3. **Consult troubleshooting guide**: `TROUBLESHOOTING.md`
4. **Check AWS service health**: AWS Status page
5. **Verify permissions**: IAM role and security groups

---

**Happy Redis Migration! 🎉**
