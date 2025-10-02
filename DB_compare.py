import os
import redis
import time
import ssl
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(".env")

# Configuration
REFRESH_INTERVAL = 5  # seconds (default, can be overridden by user input)
MAX_DIFF_PREVIEW = 5  # number of keys to preview
REDIS_TIMEOUT = 5     # connection and read timeout (seconds)

def connect_to_redis(name, host, port, password, use_tls):
    """Connect to Redis using provided parameters."""
    print(f"\n⏳ Connecting to {name} Redis at {host}:{port} ...")
    try:
        connection_kwargs = {
            "host": host,
            "port": int(port),
            "decode_responses": True,
            "socket_connect_timeout": REDIS_TIMEOUT,
            "socket_timeout": REDIS_TIMEOUT,
            "ssl": True if use_tls else False,
            "ssl_cert_reqs": ssl.CERT_NONE if use_tls else None
        }
        if password and str(password).strip().lower() != "none":
            connection_kwargs["password"] = password
        connection = redis.Redis(**connection_kwargs)
        connection.ping()
        print(f"✅ Connected to {name} Redis\n")
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to {name} Redis: {e}")
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

def get_user_interval():
    """Prompt user for comparison interval with default of 5 seconds."""
    print("\n⚙️ Configuration Setup")
    print("-" * 30)

    while True:
        try:
            user_input = input("🕒 Enter comparison interval in seconds (default: 5): ").strip()

            # Use default if empty input
            if not user_input:
                interval = 5
                print(f"✅ Using default interval: {interval} seconds")
                return interval

            # Parse user input
            interval = float(user_input)

            # Validate range
            if interval < 0.5:
                print("⚠️ Interval too short. Minimum is 0.5 seconds.")
                continue
            elif interval > 300:
                print("⚠️ Interval too long. Maximum is 300 seconds (5 minutes).")
                continue

            print(f"✅ Using interval: {interval} seconds")
            return interval

        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            exit(0)

def get_redis_stats(redis_client):
    """Fetch all keys using SCAN and return table info."""
    try:
        keys = scan_all_keys(redis_client)
        tables = set(key.split(":")[0] for key in keys)
        return len(tables), len(keys), keys
    except Exception as e:
        print(f"⚠️ Error fetching Redis stats: {e}")
        return 0, 0, set()

def compare_dbs(source, dest, name1, name2, interval=5.0):
    """Live comparison loop between two Redis databases."""
    while True:
        print("🔄 Fetching stats...", end="\r")

        # Fetch stats
        tables1, keys1, set1 = get_redis_stats(source)
        tables2, keys2, set2 = get_redis_stats(dest)

        # Diffs
        only_in_1 = set1 - set2
        only_in_2 = set2 - set1

        # Timestamp
        last_refreshed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Clear screen
        print("\033[H\033[J", end="")

        # Output
        print("\n📌 Live Redis Database Comparison")
        print("-" * 50)
        print(f"🔹 Source: {name1} - Tables: {tables1}, Keys: {keys1}")
        print(f"🔹 Destination: {name2} - Tables: {tables2}, Keys: {keys2}")

        if tables1 == tables2 and keys1 == keys2 and not only_in_1 and not only_in_2:
            print("\n✅ Both databases are identical.")
        else:
            print("\n⚠️ Differences found:")

            if tables1 != tables2:
                print(f"   - Table count differs: {tables1} vs {tables2}")
            if keys1 != keys2:
                print(f"   - Key count differs: {keys1} vs {keys2}")
            if only_in_1:
                preview = list(only_in_1)[:MAX_DIFF_PREVIEW]
                print(f"   - Keys only in {name1} ({len(only_in_1)}): {preview}{'...' if len(only_in_1) > MAX_DIFF_PREVIEW else ''}")
            if only_in_2:
                preview = list(only_in_2)[:MAX_DIFF_PREVIEW]
                print(f"   - Keys only in {name2} ({len(only_in_2)}): {preview}{'...' if len(only_in_2) > MAX_DIFF_PREVIEW else ''}")

        print(f"\n🕒 Last Refreshed: {last_refreshed}")
        print(f"🔄 Refreshing in {interval} seconds...\n")
        time.sleep(interval)

# ---- Main Execution ----
if __name__ == "__main__":
    print("🚀 Starting Redis Comparison Tool with Environment Configuration")

    # Get user-defined comparison interval
    comparison_interval = get_user_interval()

    # Source Redis config from .env
    source_name = os.getenv("REDIS_SOURCE_NAME") or "Source"
    source_host = os.getenv("REDIS_SOURCE_HOST")
    source_port = os.getenv("REDIS_SOURCE_PORT")
    source_password = os.getenv("REDIS_SOURCE_PASSWORD")
    source_tls = os.getenv("REDIS_SOURCE_TLS", "false").lower() == "true"

    # Destination Redis config from .env
    dest_name = os.getenv("REDIS_DEST_NAME") or "Destination"
    dest_host = os.getenv("REDIS_DEST_HOST")
    dest_port = os.getenv("REDIS_DEST_PORT")
    dest_password = os.getenv("REDIS_DEST_PASSWORD")
    dest_tls = os.getenv("REDIS_DEST_TLS", "false").lower() == "true"

    # Validate required fields
    required = [("REDIS_SOURCE_HOST", source_host), ("REDIS_SOURCE_PORT", source_port),
                ("REDIS_DEST_HOST", dest_host), ("REDIS_DEST_PORT", dest_port)]
    for var, val in required:
        if not val:
            print(f"❌ Missing required environment variable: {var}")
            exit(1)

    # Connect and run comparison
    redis1 = connect_to_redis(source_name, source_host, source_port, source_password, source_tls)
    redis2 = connect_to_redis(dest_name, dest_host, dest_port, dest_password, dest_tls)
    compare_dbs(redis1, redis2, source_name, dest_name, comparison_interval)
