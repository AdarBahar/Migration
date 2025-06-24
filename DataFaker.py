import os
import redis
import ssl
import random
from faker import Faker
from dotenv import load_dotenv
from datetime import datetime

# Load .env
load_dotenv(".env")

fake = Faker()

STATUSES = ['active', 'inactive', 'pending']

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
        return client
    except Exception as e:
        print(f"❌ Failed to connect to {conf['name']}: {e}")
        exit(1)

def generate_record():
    return {
        "user_id": fake.uuid4(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone": fake.phone_number(),
        "address": fake.address().replace("\n", ", "),
        "status": random.choice(STATUSES),
        "created_at": datetime.now().isoformat(),
        "nickname": fake.user_name()
    }

def create_fake_data(client, key_prefix, count):
    for i in range(count):
        record = generate_record()
        redis_key = f"{key_prefix}:{record['user_id']}"
        client.hset(redis_key, mapping=record)
    print(f"\n✅ Inserted {count} fake user records.")

if __name__ == "__main__":
    print("🛠️ Redis Fake Data Generator")

    # Load configs
    source_conf = get_redis_config("REDIS_SOURCE")
    dest_conf = get_redis_config("REDIS_DEST")

    # Select target
    print("\nSelect Redis target:")
    print(f"1. {source_conf['name']}")
    print(f"2. {dest_conf['name']}")
    choice = input("Enter choice [1/2]: ").strip()

    if choice == "1":
        client = connect_to_redis(source_conf)
        prefix = "source:user"
    elif choice == "2":
        client = connect_to_redis(dest_conf)
        prefix = "dest:user"
    else:
        print("❌ Invalid selection.")
        exit(1)

    # Number of records
    try:
        count = int(input("How many fake user records to create? ").strip())
    except ValueError:
        print("❌ Please enter a valid number.")
        exit(1)

    create_fake_data(client, prefix, count)

