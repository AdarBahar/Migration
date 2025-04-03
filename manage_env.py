import os
from dotenv import load_dotenv, set_key
from getpass import getpass

ENV_PATH = ".env"
load_dotenv(ENV_PATH)

def reload_env():
    """Reload updated .env values into the environment."""
    load_dotenv(ENV_PATH, override=True)

def prompt_env(key, label, secret=False, default=None, max_length=None):
    """Prompt user for a value and set it in the .env file."""
    current = os.getenv(key, default or "")
    prompt = f"{label} [{current}]: "
    while True:
        new_value = getpass(prompt) if secret else input(prompt).strip()
        if not new_value:
            new_value = current
        if max_length and len(new_value) > max_length:
            print(f"⚠️ Value too long. Max {max_length} characters allowed.")
            continue
        break
    set_key(ENV_PATH, key, new_value)
    reload_env()  # Reload environment after setting new value

def setup_connection(label_prefix):
    """Prompt user for Redis connection config."""
    print(f"\n🔧 Configuring {label_prefix.capitalize()} Redis")
    prompt_env(f"{label_prefix.upper()}_NAME", "Name (friendly label)", max_length=50)
    prompt_env(f"{label_prefix.upper()}_HOST", "Host")
    prompt_env(f"{label_prefix.upper()}_PORT", "Port")
    prompt_env(f"{label_prefix.upper()}_PASSWORD", "Password (hidden)", secret=True)
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

def main():
    print("🔐 Redis Environment Configuration Tool")

    while True:
        show_current_config()
        print("Choose an option:")
        print("1. Edit Source Redis")
        print("2. Edit Destination Redis")
        print("3. Exit")
        choice = input("Enter choice [1-3]: ").strip()

        if choice == "1":
            setup_connection("REDIS_SOURCE")
        elif choice == "2":
            setup_connection("REDIS_DEST")
        elif choice == "3":
            print("✅ Exiting config tool.")
            break
        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()
