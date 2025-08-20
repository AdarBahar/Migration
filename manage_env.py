import os
import redis
import ssl
import json
from datetime import datetime
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

def export_configuration():
    """Export current Redis configuration to a JSON file."""
    print("\n📤 Export Redis Configuration")
    print("=" * 40)

    # Get current configuration
    config = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "exported_by": "Redis Migration Tool",
            "version": "1.0"
        },
        "source": {
            "name": os.getenv("REDIS_SOURCE_NAME", ""),
            "host": os.getenv("REDIS_SOURCE_HOST", ""),
            "port": os.getenv("REDIS_SOURCE_PORT", "6379"),
            "tls": os.getenv("REDIS_SOURCE_TLS", "false"),
            "db": os.getenv("REDIS_SOURCE_DB", "0")
        },
        "destination": {
            "name": os.getenv("REDIS_DEST_NAME", ""),
            "host": os.getenv("REDIS_DEST_HOST", ""),
            "port": os.getenv("REDIS_DEST_PORT", "6379"),
            "tls": os.getenv("REDIS_DEST_TLS", "false"),
            "db": os.getenv("REDIS_DEST_DB", "0")
        },
        "settings": {
            "timeout": os.getenv("REDIS_TIMEOUT", "5"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }
    }

    # Check if there's any configuration to export
    if not config["source"]["host"] and not config["destination"]["host"]:
        print("⚠️  No Redis configuration found to export.")
        print("   Please configure at least one Redis connection first.")
        return

    # Generate default filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"redis_config_{timestamp}.json"

    # Get filename from user
    filename = input(f"Export filename [{default_filename}]: ").strip()
    if not filename:
        filename = default_filename

    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'

    try:
        # Write configuration to file
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Configuration exported to: {filename}")
        print(f"📁 File size: {os.path.getsize(filename)} bytes")
        print()
        print("📋 Exported configuration includes:")
        if config["source"]["host"]:
            print(f"   🔗 Source: {config['source']['name']} ({config['source']['host']})")
        if config["destination"]["host"]:
            print(f"   🔗 Destination: {config['destination']['name']} ({config['destination']['host']})")
        print("   ⚠️  Note: Passwords are NOT exported for security reasons")
        print()

    except Exception as e:
        print(f"❌ Failed to export configuration: {e}")

def import_configuration():
    """Import Redis configuration from a JSON file."""
    print("\n📥 Import Redis Configuration")
    print("=" * 40)

    # List available JSON files
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('redis_config')]

    if json_files:
        print("📁 Available configuration files:")
        for i, file in enumerate(json_files, 1):
            try:
                stat = os.stat(file)
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"   {i}. {file} ({size} bytes, modified: {mtime})")
            except:
                print(f"   {i}. {file}")
        print()

    # Get filename from user
    filename = input("Import filename (or press Enter to browse): ").strip()

    if not filename:
        if json_files:
            try:
                choice = input(f"Select file [1-{len(json_files)}]: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(json_files):
                    filename = json_files[int(choice) - 1]
                else:
                    print("❌ Invalid selection.")
                    return
            except:
                print("❌ Invalid selection.")
                return
        else:
            print("❌ No configuration files found.")
            return

    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'

    # Check if file exists
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return

    try:
        # Read configuration from file
        with open(filename, 'r') as f:
            config = json.load(f)

        # Validate configuration structure
        if not isinstance(config, dict) or 'source' not in config or 'destination' not in config:
            print("❌ Invalid configuration file format.")
            return

        print(f"✅ Configuration loaded from: {filename}")

        # Show what will be imported
        print("\n📋 Configuration to import:")
        if config.get('metadata', {}).get('exported_at'):
            print(f"   📅 Exported: {config['metadata']['exported_at']}")

        source = config.get('source', {})
        dest = config.get('destination', {})

        if source.get('host'):
            print(f"   🔗 Source: {source.get('name', 'Unnamed')} ({source.get('host')}:{source.get('port', '6379')})")
        if dest.get('host'):
            print(f"   🔗 Destination: {dest.get('name', 'Unnamed')} ({dest.get('host')}:{dest.get('port', '6379')})")

        # Confirm import
        print("\n⚠️  This will overwrite your current configuration!")
        confirm = input("Continue with import? (y/N): ").strip().lower()

        if confirm != 'y':
            print("❌ Import cancelled.")
            return

        # Import source configuration
        if source.get('host'):
            set_key(ENV_PATH, "REDIS_SOURCE_NAME", source.get('name', ''))
            set_key(ENV_PATH, "REDIS_SOURCE_HOST", source.get('host', ''))
            set_key(ENV_PATH, "REDIS_SOURCE_PORT", source.get('port', '6379'))
            set_key(ENV_PATH, "REDIS_SOURCE_TLS", source.get('tls', 'false'))
            set_key(ENV_PATH, "REDIS_SOURCE_DB", source.get('db', '0'))

        # Import destination configuration
        if dest.get('host'):
            set_key(ENV_PATH, "REDIS_DEST_NAME", dest.get('name', ''))
            set_key(ENV_PATH, "REDIS_DEST_HOST", dest.get('host', ''))
            set_key(ENV_PATH, "REDIS_DEST_PORT", dest.get('port', '6379'))
            set_key(ENV_PATH, "REDIS_DEST_TLS", dest.get('tls', 'false'))
            set_key(ENV_PATH, "REDIS_DEST_DB", dest.get('db', '0'))

        # Import settings
        settings = config.get('settings', {})
        if settings.get('timeout'):
            set_key(ENV_PATH, "REDIS_TIMEOUT", settings.get('timeout', '5'))
        if settings.get('log_level'):
            set_key(ENV_PATH, "LOG_LEVEL", settings.get('log_level', 'INFO'))

        # Reload environment
        reload_env()

        print("✅ Configuration imported successfully!")
        print("⚠️  Remember to set passwords manually for security reasons.")
        print()

    except json.JSONDecodeError:
        print("❌ Invalid JSON file format.")
    except Exception as e:
        print(f"❌ Failed to import configuration: {e}")

def main():
    print("🔐 Redis Environment Configuration Tool")

    while True:
        show_current_config()
        print("Choose an option:")
        print("1. Edit Source Redis")
        print("2. Edit Destination Redis")
        print("3. Test Source Redis")
        print("4. Test Destination Redis")
        print("5. Export Configuration")
        print("6. Import Configuration")
        print("7. Exit")
        choice = input("Enter choice [1-7]: ").strip()

        if choice == "1":
            setup_connection("REDIS_SOURCE")
        elif choice == "2":
            setup_connection("REDIS_DEST")
        elif choice == "3":
            test_redis_connection("REDIS_SOURCE")
        elif choice == "4":
            test_redis_connection("REDIS_DEST")
        elif choice == "5":
            export_configuration()
        elif choice == "6":
            import_configuration()
        elif choice == "7":
            print("✅ Exiting config tool.")
            break
        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()
