import os
import redis
import ssl
from dotenv import load_dotenv

# Load .env config
load_dotenv(".env")

def get_redis_config(prefix):
    return {
        "name": os.getenv(f"{prefix}_NAME", prefix.title()),
        "host": os.getenv(f"{prefix}_HOST"),
        "port": int(os.getenv(f"{prefix}_PORT", 6379)),
        "password": os.getenv(f"{prefix}_PASSWORD") or None,
        "use_tls": os.getenv(f"{prefix}_TLS", "false").lower() == "true"
    }

def connect_to_redis(conf):
    connection_kwargs = {
        "host": conf["host"],
        "port": conf["port"],
        "password": conf["password"],
        "decode_responses": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 5
    }

    if conf["use_tls"]:
        connection_kwargs["ssl"] = True
        connection_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE

    try:
        client = redis.Redis(**connection_kwargs)
        client.ping()
        return client
    except Exception as e:
        print(f"❌ Failed to connect to {conf['name']} ({conf['host']}): {e}")
        return None

def flush_db(redis_client, name):
    try:
        redis_client.flushall()
        print(f"✅ {name} database flushed successfully.")
    except Exception as e:
        print(f"❌ Error flushing {name}: {e}")

# Load configs
source_conf = get_redis_config("REDIS_SOURCE")
dest_conf = get_redis_config("REDIS_DEST")

# Choose DBs to flush
print("\n📦 Select Redis database to flush:")
print(f"1. {source_conf['name']}")
print(f"2. {dest_conf['name']}")
print("3. Both")
choice = input("Enter choice [1/2/3]: ").strip()

if choice == "1":
    client = connect_to_redis(source_conf)
    if client:
        flush_db(client, source_conf["name"])
elif choice == "2":
    client = connect_to_redis(dest_conf)
    if client:
        flush_db(client, dest_conf["name"])
elif choice == "3":
    client1 = connect_to_redis(source_conf)
    client2 = connect_to_redis(dest_conf)
    if client1:
        flush_db(client1, source_conf["name"])
    if client2:
        flush_db(client2, dest_conf["name"])
else:
    print("❌ Invalid choice.")

