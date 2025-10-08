# 🔔 Keyspace Notifications for RIOT-X Live Migration

## 📋 Overview

Redis keyspace notifications enable real-time monitoring of key changes, which RIOT-X uses for live migration with minimal downtime. This guide shows you how to enable them on your ElastiCache cluster.

## 🎯 What Are Keyspace Notifications?

Keyspace notifications allow clients to subscribe to Pub/Sub channels to receive events affecting the Redis data set:

- **All commands affecting a given key** (e.g., SET, DEL, EXPIRE)
- **All keys receiving specific operations** (e.g., all LPUSH operations)
- **All keys expiring** in the database

### **Live Migration Benefits:**
- ✅ **Real-time synchronization** during migration
- ✅ **Minimal downtime** (seconds instead of minutes)
- ✅ **Continuous data capture** while migration runs
- ✅ **Zero data loss** during migration process

## 🚀 Quick Setup (3 Options)

### **Option 1: Enable on Your Existing Cluster (Recommended)**

```bash
# Using the automated script
python3 enable_keyspace_notifications.py

# Or specify your cluster directly
python3 enable_keyspace_notifications.py --cluster-id redis-elasticache-1759926962

# Or use direct host connection
python3 enable_keyspace_notifications.py --host redis-elasticache-1759926962.nkwtpc.0001.eun1.cache.amazonaws.com
```

### **Option 2: Manual Redis CLI Setup**

```bash
# Connect to your ElastiCache cluster
redis-cli -h redis-elasticache-1759926962.nkwtpc.0001.eun1.cache.amazonaws.com -p 6379

# Enable keyspace notifications for live migration
CONFIG SET notify-keyspace-events KEA

# Verify the setting
CONFIG GET notify-keyspace-events

# Should return: "KEA"
exit
```

### **Option 3: During New ElastiCache Provisioning**

```bash
# Run the enhanced provisioning script
python3 provision_elasticache.py

# When prompted:
# "Enable keyspace notifications for live migration? (Y/n):"
# Answer: Y

# The script will automatically configure keyspace notifications
```

## 🔧 Configuration Details

### **Recommended Setting: `KEA`**

- **K** = Keyspace events (published with `__keyspace@<db>__` prefix)
- **E** = Keyevent events (published with `__keyevent@<db>__` prefix)  
- **A** = All events (alias for `g$lshztdxe`)

### **What Events Are Captured:**

- **g** = Generic commands (DEL, EXPIRE, RENAME)
- **$** = String commands (SET, GET, INCR)
- **l** = List commands (LPUSH, RPOP, LREM)
- **s** = Set commands (SADD, SREM, SPOP)
- **h** = Hash commands (HSET, HDEL, HINCRBY)
- **z** = Sorted set commands (ZADD, ZREM, ZINCRBY)
- **t** = Stream commands (XADD, XDEL, XTRIM)
- **x** = Expired events (when keys expire)
- **e** = Evicted events (when keys are evicted)

## 📊 Verification

### **Check Current Configuration:**

```bash
# Using Redis CLI
redis-cli -h YOUR_CLUSTER_HOST -p 6379 CONFIG GET notify-keyspace-events

# Using Python script
python3 enable_keyspace_notifications.py --host YOUR_CLUSTER_HOST
```

### **Test Keyspace Notifications:**

```bash
# Terminal 1: Subscribe to keyspace events
redis-cli -h YOUR_CLUSTER_HOST -p 6379 --csv psubscribe '__key*__:*'

# Terminal 2: Perform some operations
redis-cli -h YOUR_CLUSTER_HOST -p 6379
SET test_key "hello"
DEL test_key
EXPIRE another_key 60

# Terminal 1 should show events like:
# "pmessage","__key*__:*","__keyspace@0__:test_key","set"
# "pmessage","__key*__:*","__keyevent@0__:set","test_key"
```

## 🎯 RIOT-X Live Migration Usage

Once keyspace notifications are enabled, you can use RIOT-X live migration:

### **Deploy RIOT-X with Live Migration:**

```bash
aws cloudformation create-stack \
  --stack-name riotx-live-migration \
  --template-url https://riot-x.s3.amazonaws.com/ec-sync.yaml \
  --parameters \
    ParameterKey=SourceElastiCacheClusterId,ParameterValue=redis-elasticache-1759926962 \
    ParameterKey=TargetRedisURI,ParameterValue=redis://:PASSWORD@redis-cloud.com:12850 \
    ParameterKey=SyncMode,ParameterValue=LIVE \
    ParameterKey=EnableLiveSync,ParameterValue=true \
  --capabilities CAPABILITY_IAM \
  --region eu-north-1
```

### **Live Migration Process:**

1. **Initial Sync**: RIOT-X performs full data sync
2. **Live Sync**: Captures ongoing changes via keyspace notifications
3. **Cutover**: Brief pause to sync final changes
4. **Complete**: Switch traffic to target with minimal downtime

## ⚠️ Important Notes

### **Performance Impact:**
- Keyspace notifications use some CPU power
- Impact is minimal for most workloads
- Monitor your ElastiCache metrics after enabling

### **Persistence:**
- Configuration persists across ElastiCache restarts
- Setting is cluster-wide (affects all databases)
- No additional storage overhead

### **Security:**
- Keyspace notifications are internal to Redis
- No external network traffic generated
- Events are only visible to connected clients

## 🔍 Troubleshooting

### **"Connection Failed" Error:**

```bash
# Check security groups allow access
aws ec2 describe-security-groups --group-ids sg-YOUR-SG-ID

# Verify ElastiCache is running
aws elasticache describe-cache-clusters --cache-cluster-id redis-elasticache-1759926962

# Test basic connectivity
telnet redis-elasticache-1759926962.nkwtpc.0001.eun1.cache.amazonaws.com 6379
```

### **"Permission Denied" Error:**

```bash
# ElastiCache doesn't support AUTH by default
# Ensure you're not passing a password parameter
redis-cli -h YOUR_CLUSTER_HOST -p 6379 # No -a password
```

### **"Setting Not Persisting" Error:**

```bash
# Verify the setting was applied
redis-cli -h YOUR_CLUSTER_HOST -p 6379 CONFIG GET notify-keyspace-events

# If empty, try setting again
redis-cli -h YOUR_CLUSTER_HOST -p 6379 CONFIG SET notify-keyspace-events KEA
```

## 📚 Additional Resources

- **Redis Documentation**: [Keyspace Notifications](https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/)
- **RIOT-X Documentation**: Live migration features
- **AWS ElastiCache**: Configuration management

## 🎉 Success Indicators

You'll know keyspace notifications are working when:

1. ✅ `CONFIG GET notify-keyspace-events` returns `"KEA"`
2. ✅ Test subscription shows key events in real-time
3. ✅ RIOT-X live migration runs without errors
4. ✅ Migration completes with minimal downtime

Your ElastiCache cluster is now ready for RIOT-X live migration with minimal downtime! 🚀✨
