import redis
import time
import random
import string
from threading import Thread
import ssl

# =========================
# 🔧 SETTINGS
# =========================
CONFIG = {
    "redis_host": "adar-redis-nkwtpc.serverless.eun1.cache.amazonaws.com",
    "redis_port": 6379,
    "redis_password": None,  # Add password if needed
    "use_tls": True,

    "write_interval": 5,       # Seconds between write operations
    "write_batch_size": 10,    # How many keys to write each time

    "read_interval": 5,        # Seconds between read operations
    "read_batch_size": 10,     # How many keys to read each time

    "key_prefix": "testload",  # All keys will be prefixed with this
    "value_size": 100          # Number of characters per value
}

# =========================
# 🔌 Connect to Redis
# =========================
def connect_to_redis():
    connection_kwargs = {
        "host": CONFIG["redis_host"],
        "port": CONFIG["redis_port"],
        "password": CONFIG["redis_password"],
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5
    }

    if CONFIG["use_tls"]:
        connection_kwargs["ssl"] = True
        connection_kwargs["ssl_cert_reqs"] = None

    return redis.Redis(**connection_kwargs)

r = connect_to_redis()

# =========================
# 🔄 Write Keys
# =========================
def write_keys():
    while True:
        for i in range(CONFIG["write_batch_size"]):
            key = f"{CONFIG['key_prefix']}:key:{random.randint(1, 1000000)}"
            value = ''.join(random.choices(string.ascii_letters + string.digits, k=CONFIG["value_size"]))
            r.set(key, value)
        print(f"✅ Wrote {CONFIG['write_batch_size']} keys.")
        time.sleep(CONFIG["write_interval"])

# =========================
# 🔄 Read Keys
# =========================
def read_keys():
    while True:
        # Scan for matching keys
        cursor = 0
        all_keys = []
        while True:
            cursor, keys = r.scan(cursor=cursor, match=f"{CONFIG['key_prefix']}:key:*", count=100)
            all_keys.extend(keys)
            if cursor == 0 or len(all_keys) > CONFIG["read_batch_size"] * 2:
                break

        sample_keys = random.sample(all_keys, min(CONFIG["read_batch_size"], len(all_keys)))
        for key in sample_keys:
            _ = r.get(key)
        print(f"📖 Read {len(sample_keys)} keys.")
        time.sleep(CONFIG["read_interval"])

# =========================
# ▶️ Run in Threads
# =========================
Thread(target=write_keys, daemon=True).start()
Thread(target=read_keys, daemon=True).start()

# Keep main thread alive
while True:
    time.sleep(60)
