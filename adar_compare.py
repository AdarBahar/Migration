import redis
import time
import ssl
from datetime import datetime

# Configuration
REFRESH_INTERVAL = 5  # seconds
MAX_DIFF_PREVIEW = 5  # max keys to preview in output
REDIS_TIMEOUT = 5     # connection and read timeout (seconds)

def connect_to_redis(name, **kwargs):
    """Try to connect to Redis and print status."""
    print(f"⏳ Connecting to {name} Redis...")
    try:
        r = redis.Redis(
            socket_connect_timeout=REDIS_TIMEOUT,
            socket_timeout=REDIS_TIMEOUT,
            **kwargs
        )
        r.ping()
        print(f"✅ Successfully connected to {name} Redis\n")
        return r
    except Exception as e:
        print(f"❌ Failed to connect to {name} Redis: {e}\n")
        exit(1)

def scan_all_keys(redis_client):
    """Use SCAN to safely get all keys (avoids KEYS *)."""
    keys = set()
    cursor = 0
    while True:
        cursor, batch = redis_client.scan(cursor=cursor, count=1000)
        keys.update(batch)
        if cursor == 0:
            break
    return keys

def get_redis_stats(redis_client):
    """Fetch all keys using SCAN and return table info."""
    try:
        keys = scan_all_keys(redis_client)
        tables = set(key.split(":")[0] for key in keys)
        return len(tables), len(keys), keys
    except Exception as e:
        print(f"⚠️ Error fetching Redis stats: {e}")
        return 0, 0, set()

def compare_dbs(redis_db1, redis_db2):
    """Compare two Redis databases live."""
    while True:
        print("🔄 Fetching stats...", end="\r")

        # Get stats from both DBs
        tables_db1, keys_db1, key_set_db1 = get_redis_stats(redis_db1)
        tables_db2, keys_db2, key_set_db2 = get_redis_stats(redis_db2)

        # Compute key differences
        only_in_db1 = key_set_db1 - key_set_db2
        only_in_db2 = key_set_db2 - key_set_db1

        # Timestamp
        last_refreshed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Clear screen
        print("\033[H\033[J", end="")

        # Output comparison
        print("\n📌 Live Redis Database Comparison")
        print("-" * 50)
        print(f"🔹 Source (AWS OSS Redis, serverless) - Tables: {tables_db1}, Keys: {keys_db1}")
        print(f"🔹      Destination (Redis Cloud Pro) - Tables: {tables_db2}, Keys: {keys_db2}")

        if tables_db1 == tables_db2 and keys_db1 == keys_db2 and not only_in_db1 and not only_in_db2:
            print("\n✅ Source and Destination are identical.")
        else:
            print("\n⚠️ Differences found:")

            if tables_db1 != tables_db2:
                print(f"   - Table count differs: source: {tables_db1} vs destination: {tables_db2}")

            if keys_db1 != keys_db2:
                print(f"   - Key count differs: source: {keys_db1} vs destination: {keys_db2}")

            if only_in_db1:
                preview = list(only_in_db1)[:MAX_DIFF_PREVIEW]
                print(f"   - Keys only in Source ({len(only_in_db1)}): {preview}{'...' if len(only_in_db1) > MAX_DIFF_PREVIEW else ''}")

            if only_in_db2:
                preview = list(only_in_db2)[:MAX_DIFF_PREVIEW]
                print(f"   - Keys only in Destination ({len(only_in_db2)}): {preview}{'...' if len(only_in_db2) > MAX_DIFF_PREVIEW else ''}")

        print(f"\n🕒 Last Refreshed: {last_refreshed}")
        print(f"🔄 Refreshing in {REFRESH_INTERVAL} seconds...\n")
        time.sleep(REFRESH_INTERVAL)

# --- Connect to Redis databases ---

print("🚀 Starting Redis Database Comparison Tool...\n")

# Connect to AWS Redis OSS (Source) with SSL
redis_db1 = connect_to_redis(
    "Source (AWS OSS)",
    host='adar-redis-nkwtpc.serverless.eun1.cache.amazonaws.com',
    port=6379,
    password='',
    ssl=True,
    ssl_cert_reqs=ssl.CERT_NONE,
    decode_responses=True
)

# Connect to Redis Cloud (Destination)
redis_db2 = connect_to_redis(
    "Destination (Redis Cloud)",
    host='redis-17687.c37722.us-east-1-mz.ec2.cloud.rlrcp.com',
    port=17687,
    password='dlXk5YvIUXydm6Cit9SkeY90jD2aZauC',
    decode_responses=True
)

# Run the comparison
compare_dbs(redis_db1, redis_db2)
