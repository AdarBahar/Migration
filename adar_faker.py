# CREATE FAKE DATA ON ADAR-REDIS INSTANCE ON AWS (OSS CACHE REDIS)
import redis
import random
import time
import ssl
from faker import Faker

# Initialize Faker
fake = Faker()

# Configuration: Set the destination Redis database number
db_number = 0  # Change this to any number between 0-15

# Connect to Redis with TLS
redis_client = redis.StrictRedis(
    host="adar-redis-nkwtpc.serverless.eun1.cache.amazonaws.com",
    port=6379,
    ssl=True,  # Enable TLS
    ssl_cert_reqs=ssl.CERT_NONE,  # Bypass certificate validation (change if needed)
    decode_responses=True
)

# Validate DB number (AWS Redis OSS does not support multiple DBs)
if db_number != 0:
    raise ValueError("AWS Redis OSS supports only DB 0. Change db_number to 0.")

print(f"✅ Writing data to Redis DB {db_number}")

# Generate 200 users
for i in range(1, 201):
    user_id = f"user{i}"
    
    # User information
    user_data = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone": fake.phone_number(),
        "address": fake.address()
    }
    
    # User status information
    user_status_data = {
        "status": random.choice(["active", "inactive", "pending"]),
        "created_at": str(int(time.time())),  # Store timestamp
        "nickname": fake.user_name()
    }
    
    # Store in Redis
    redis_client.hset(f"user:{user_id}", mapping=user_data)
    redis_client.hset(f"user_status:{user_id}", mapping=user_status_data)

print(f"✅ 200 users and their statuses have been added to Redis DB {db_number}.")
