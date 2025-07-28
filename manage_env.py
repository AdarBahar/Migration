import os
import redis
import ssl
from dotenv import load_dotenv, set_key
from getpass import getpass

ENV_PATH = ".env"
load_dotenv(ENV_PATH)

def reload_env():
    """Reload updated .env values into the environment."""
    load_dotenv(ENV_PATH, override=True)

def prompt_env(key, label, secret=False, default=None, max_length=None, allow_empty=False):
    """Prompt user for a value and set it in the .env file."""
    current = os.getenv(key, default or "")

    # For passwords, show a more helpful prompt
    if secret and current and current not in ["", "your-source-password", "your-destination-password"]:
        prompt = f"{label} [***hidden***] (press Enter to keep current, or type new): "
    elif secret:
        prompt = f"{label} (press Enter for no password): "
    else:
        prompt = f"{label} [{current}]: "

    while True:
        new_value = getpass(prompt) if secret else input(prompt).strip()

        # Handle empty input
        if not new_value:
            if secret and allow_empty:
                # For passwords, empty input means no password
                new_value = ""
            elif secret and current not in ["", "your-source-password", "your-destination-password"]:
                # Keep existing password if it's not a placeholder
                new_value = current
            elif not secret:
                # For non-secrets, keep current value if not empty
                new_value = current if current else ""
            else:
                # For passwords with placeholder values, set to empty
                new_value = ""

        if max_length and len(new_value) > max_length:
            print(f"⚠️ Value too long. Max {max_length} characters allowed.")
            continue
        break

    set_key(ENV_PATH, key, new_value)
    reload_env()

def setup_connection(label_prefix):
    """Prompt user for Redis connection config."""
    print(f"\n🔧 Configuring {label_prefix.capitalize()} Redis")
    prompt_env(f"{label_prefix.upper()}_NAME", "Name (friendly label)", max_length=50)
    prompt_env(f"{label_prefix.upper()}_HOST", "Host")
    prompt_env(f"{label_prefix.upper()}_PORT", "Port")
    prompt_env(f"{label_prefix.upper()}_PASSWORD", "Password (hidden)", secret=True, allow_empty=True)
    tls = input("Use TLS/SSL? (y/n): ").strip().lower()
    tls_value = "true" if tls == "y" else "false"
    set_key(ENV_PATH, f"{label_prefix.upper()}_TLS", tls_value)
    reload_env()

def show_current_config():
    print("\n📄 Current Redis Configuration:")
    keys_to_show = [
        ("REDIS_SOURCE_NAME", "Source Name"),
        ("REDIS_SOURCE_HOST", "Source Host"),
        ("REDIS_SOURCE_PORT", "Source Port"),
        ("REDIS_SOURCE_TLS",  "Source TLS"),

        ("REDIS_DEST_NAME",   "Destination Name"),
        ("REDIS_DEST_HOST",   "Destination Host"),
        ("REDIS_DEST_PORT",   "Destination Port"),
        ("REDIS_DEST_TLS",    "Destination TLS"),
    ]
    for key, label in keys_to_show:
        value = os.getenv(key, "(not set)")
        print(f"{label}: {value}")
    print("Passwords are hidden for security.\n")

def test_redis_connection(prefix):
    """Test Redis connectivity using .env settings."""
    name = os.getenv(f"{prefix}_NAME", prefix)
    host = os.getenv(f"{prefix}_HOST")
    port = int(os.getenv(f"{prefix}_PORT", 6379))
    password = os.getenv(f"{prefix}_PASSWORD")
    use_tls = os.getenv(f"{prefix}_TLS", "false").lower() == "true"

    print(f"\n🔌 Testing connection to {name} ({host}:{port})...")

    try:
        conn_args = {
            "host": host,
            "port": port,
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5
        }
        if password and password.strip().lower() != "none":
            conn_args["password"] = password
        if use_tls:
            conn_args["ssl"] = True
            conn_args["ssl_cert_reqs"] = ssl.CERT_NONE

        client = redis.Redis(**conn_args)
        client.ping()
        print(f"✅ Connection to {name} successful.\n")
    except Exception as e:
        print(f"❌ Connection to {name} failed: {e}\n")

def main():
    print("🔐 Redis Environment Configuration Tool")

    while True:
        show_current_config()
        print("Choose an option:")
        print("1. Edit Source Redis")
        print("2. Edit Destination Redis")
        print("3. Test Source Redis")
        print("4. Test Destination Redis")
        print("5. Exit")
        choice = input("Enter choice [1-5]: ").strip()

        if choice == "1":
            setup_connection("REDIS_SOURCE")
        elif choice == "2":
            setup_connection("REDIS_DEST")
        elif choice == "3":
            test_redis_connection("REDIS_SOURCE")
        elif choice == "4":
            test_redis_connection("REDIS_DEST")
        elif choice == "5":
            print("✅ Exiting config tool.")
            break
        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()
