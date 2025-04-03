import redis

# Connect to destination Redis Cloud
redis_db2 = redis.Redis(
    host='redis-17687.c37722.us-east-1-mz.ec2.cloud.rlrcp.com',
    port=17687,
    password='dlXk5YvIUXydm6Cit9SkeY90jD2aZauC',
    decode_responses=True
)

try:
    redis_db2.flushall()  # or use flushdb() if you want to clear just the current DB
    print("✅ Destination database flushed successfully.")
except Exception as e:
    print(f"❌ Error flushing destination database: {e}")
