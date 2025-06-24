import os
import redis
import time
import random
import string
import csv
from threading import Thread, Lock
import ssl
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv(".env")

# =========================
# 🔧 SETTINGS
# =========================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"redis_perf_log_{timestamp}.csv"

CONFIG = {
    "write_interval": 5,
    "write_batch_size": 10,
    "read_interval": 5,
    "read_batch_size": 10,
    "key_prefix": "testload",
    "value_size": 100,
    "log_file": log_filename
}

log_lock = Lock()

# =========================
# 📦 Load Redis Config
# =========================
def get_redis_config(prefix):
    return {
        "name": os.getenv(f"{prefix}_NAME", prefix.title()),
        "host": os.getenv(f"{prefix}_HOST"),
        "port": int(os.getenv(f"{prefix}_PORT", 6379)),
        "password": os.getenv(f"{prefix}_PASSWORD") or None,
        "use_tls": os.getenv(f"{prefix}_TLS", "false").lower() == "true"
    }

source_config = get_redis_config("REDIS_SOURCE")
dest_config = get_redis_config("REDIS_DEST")

# =========================
# 🔌 Redis Connector
# =========================
def connect_to_redis(conf):
    connection_kwargs = {
        "host": conf["host"],
        "port": conf["port"],
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5
    }
    if conf["password"] and str(conf["password"]).strip().lower() != "none":
        connection_kwargs["password"] = conf["password"]
    if conf["use_tls"]:
        connection_kwargs["ssl"] = True
        connection_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE

    try:
        client = redis.Redis(**connection_kwargs)
        client.ping()
        print(f"✅ Connected to Redis: {conf['name']} ({conf['host']}:{conf['port']})")
        return {"client": client, "name": conf["name"], "host": conf["host"]}
    except Exception as e:
        print(f"❌ Failed to connect to {conf['name']}: {e}")
        log_to_file(conf["name"], conf["host"], "CONNECT", 0, 0, str(e))
        exit(1)

# =========================
# 📊 Logging
# =========================
def log_to_file(redis_name, redis_host, operation, latency_ms, key_count, error_message=""):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, redis_name, redis_host, operation, latency_ms, key_count, error_message]
    with log_lock:
        new_file = not os.path.exists(CONFIG["log_file"])
        with open(CONFIG["log_file"], "a", newline="") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow([
                    "timestamp", "redis_name", "redis_host",
                    "operation", "latency_ms", "key_count", "error_message"
                ])
            writer.writerow(row)

# =========================
# 🧠 Prompt for DB Selection
# =========================
print("\n📘 Choose which Redis to use:")
print(f"1. {source_config['name']}")
print(f"2. {dest_config['name']}")
print(f"3. Both")
choice = input("Enter choice [1/2/3]: ").strip()

selected_instances = []
if choice == "1":
    selected_instances = [connect_to_redis(source_config)]
elif choice == "2":
    selected_instances = [connect_to_redis(dest_config)]
elif choice == "3":
    selected_instances = [connect_to_redis(source_config), connect_to_redis(dest_config)]
else:
    print("❌ Invalid selection.")
    exit(1)

# =========================
# 🔄 Write Keys
# =========================
def write_keys():
    while True:
        for instance in selected_instances:
            try:
                start = time.time()
                for _ in range(CONFIG["write_batch_size"]):
                    key = f"{CONFIG['key_prefix']}:key:{random.randint(1, 1000000)}"
                    value = ''.join(random.choices(string.ascii_letters + string.digits, k=CONFIG["value_size"]))
                    instance["client"].set(key, value)
                duration = (time.time() - start) * 1000
                print(f"✅ Wrote {CONFIG['write_batch_size']} keys to {instance['name']} in {duration:.2f} ms")
                log_to_file(instance["name"], instance["host"], "WRITE", round(duration, 2), CONFIG["write_batch_size"])
            except Exception as e:
                print(f"❌ WRITE error on {instance['name']}: {e}")
                log_to_file(instance["name"], instance["host"], "WRITE", 0, 0, str(e))
        time.sleep(CONFIG["write_interval"])

# =========================
# 🔄 Read Keys
# =========================
def read_keys():
    while True:
        for instance in selected_instances:
            try:
                cursor = 0
                all_keys = []
                client = instance["client"]
                while True:
                    cursor, keys = client.scan(cursor=cursor, match=f"{CONFIG['key_prefix']}:key:*", count=100)
                    all_keys.extend(keys)
                    if cursor == 0 or len(all_keys) > CONFIG["read_batch_size"] * 2:
                        break

                sample_keys = random.sample(all_keys, min(CONFIG["read_batch_size"], len(all_keys)))

                start = time.time()
                for key in sample_keys:
                    _ = client.get(key)
                duration = (time.time() - start) * 1000
                print(f"📖 Read {len(sample_keys)} keys from {instance['name']} in {duration:.2f} ms")
                log_to_file(instance["name"], instance["host"], "READ", round(duration, 2), len(sample_keys))
            except Exception as e:
                print(f"❌ READ error on {instance['name']}: {e}")
                log_to_file(instance["name"], instance["host"], "READ", 0, 0, str(e))
        time.sleep(CONFIG["read_interval"])

# =========================
# ▶️ Start Threads
# =========================
Thread(target=write_keys, daemon=True).start()
Thread(target=read_keys, daemon=True).start()

print(f"\n📁 Logging to: {CONFIG['log_file']}\n")

while True:
    time.sleep(60)

