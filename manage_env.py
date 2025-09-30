import os
import redis
import ssl
import json
import re
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

def setup_source_connection():
    """Setup source Redis connection using AWS ElastiCache CLI command."""
    print(f"\n🔧 Configuring Source Redis (AWS ElastiCache)")
    print("=" * 50)

    # Get friendly name
    prompt_env("REDIS_SOURCE_NAME", "Name (friendly label)", max_length=50)

    # Instructions for getting AWS CLI command
    print("\n📋 AWS ElastiCache Connection Instructions:")
    print("1. Go to AWS Console > ElastiCache > Redis OSS caches")
    print("2. Click on your cache cluster")
    print("3. Go to 'Connecting to your cache' tab")
    print("4. Select 'AWS CloudShell / CLI' tab")
    print("5. Copy the entire redis-cli command")
    print()
    print("💡 Expected format:")
    print("   redis6-cli --tls -h your-cache.amazonaws.com -p 6379")
    print("   redis-cli -h your-cache.amazonaws.com -p 6379")
    print()

    while True:
        cli_command = input("🔗 AWS redis-cli command: ").strip()

        if not cli_command:
            print("❌ Command cannot be empty. Please enter a valid redis-cli command.")
            continue

        # Parse the CLI command
        parsed = parse_aws_redis_cli(cli_command)

        if not parsed:
            print("❌ Invalid redis-cli command format.")
            print("💡 Expected format: redis6-cli --tls -h host.amazonaws.com -p 6379")
            print("💡 Or: redis-cli -h host.amazonaws.com -p 6379")
            continue

        # Show parsed information for confirmation
        print(f"\n✅ Successfully parsed AWS redis-cli command:")
        print(f"   🏠 Host: {parsed['host']}")
        print(f"   🔌 Port: {parsed['port']}")
        print(f"   🔐 TLS: {'Enabled' if parsed['tls'] else 'Disabled'}")
        print()

        confirm = input("Is this information correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Please enter the command again.")

    # Set the parsed values in environment
    set_key(ENV_PATH, "REDIS_SOURCE_HOST", parsed['host'])
    set_key(ENV_PATH, "REDIS_SOURCE_PORT", parsed['port'])
    set_key(ENV_PATH, "REDIS_SOURCE_TLS", "true" if parsed['tls'] else "false")

    # Set default database if not already set
    if not os.getenv("REDIS_SOURCE_DB"):
        set_key(ENV_PATH, "REDIS_SOURCE_DB", "0")

    # Ask for password (ElastiCache might not need one, but allow setting)
    print("\n🔒 Password Configuration:")
    print("💡 Many AWS ElastiCache instances don't require a password")
    print("💡 Press Enter to skip password, or enter one if your instance requires it")
    prompt_env("REDIS_SOURCE_PASSWORD", "Password (optional)", secret=True, allow_empty=True)

    reload_env()

    print("✅ Source Redis configuration updated successfully!")
    print("💡 You can test the connection using option 3 from the main menu.")

def setup_connection(label_prefix):
    """Legacy function - prompt user for Redis connection config manually."""
    print(f"\n🔧 Configuring {label_prefix.capitalize()} Redis (Manual)")
    prompt_env(f"{label_prefix.upper()}_NAME", "Name (friendly label)", max_length=50)
    prompt_env(f"{label_prefix.upper()}_HOST", "Host")
    prompt_env(f"{label_prefix.upper()}_PORT", "Port")
    prompt_env(f"{label_prefix.upper()}_PASSWORD", "Password (hidden)", secret=True, allow_empty=True)
    tls = input("Use TLS/SSL? (y/n): ").strip().lower()
    tls_value = "true" if tls == "y" else "false"
    set_key(ENV_PATH, f"{label_prefix.upper()}_TLS", tls_value)
    reload_env()

def parse_redis_url(redis_url):
    """Parse Redis URL and extract connection parameters.

    Supports formats:
    - redis://[user]:[password]@[host]:[port]
    - rediss://[user]:[password]@[host]:[port] (TLS enabled)

    Returns dict with parsed parameters or None if invalid.
    """
    # Redis URL pattern
    pattern = r'^(redis|rediss)://(?:([^:]+):([^@]+)@)?([^:]+):(\d+)/?$'

    match = re.match(pattern, redis_url.strip())
    if not match:
        return None

    scheme, user, password, host, port = match.groups()

    # Determine TLS based on scheme
    tls = scheme == "rediss"

    # Default user if not specified
    if user is None:
        user = "default"

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password or "",
        "tls": tls
    }

def parse_aws_redis_cli(cli_command):
    """Parse AWS ElastiCache redis-cli command and extract connection parameters.

    Supports formats:
    - redis6-cli --tls -h host.amazonaws.com -p 6379
    - redis-cli -h host.amazonaws.com -p 6379
    - redis6-cli -h host.amazonaws.com -p 6379 --tls

    Returns dict with parsed parameters or None if invalid.
    """
    if not cli_command or not cli_command.strip():
        return None

    command = cli_command.strip()

    # Check if it's a redis-cli command
    if not (command.startswith('redis-cli') or command.startswith('redis6-cli')):
        return None

    # Initialize defaults
    host = None
    port = "6379"
    tls = False

    # Split command into parts
    parts = command.split()

    # Parse arguments
    i = 1  # Skip the redis-cli/redis6-cli part
    while i < len(parts):
        arg = parts[i]

        if arg == '--tls':
            tls = True
            i += 1
        elif arg == '-h' and i + 1 < len(parts):
            host = parts[i + 1]
            i += 2
        elif arg == '-p' and i + 1 < len(parts):
            port = parts[i + 1]
            i += 2
        else:
            i += 1

    # Validate that we got a host
    if not host:
        return None

    return {
        "host": host,
        "port": port,
        "tls": tls,
        "user": "default",
        "password": ""
    }

def setup_destination_connection():
    """Simplified destination Redis setup using Redis Cloud URL."""
    print(f"\n🔧 Configuring Destination Redis (Redis Cloud)")
    print("=" * 50)

    # Get friendly name
    prompt_env("REDIS_DEST_NAME", "Name (friendly label)", max_length=50)

    # Instructions for getting Redis Cloud URL
    print("\n📋 Redis Cloud Connection Instructions:")
    print("1. Go to Redis Cloud > Your database")
    print("2. Click 'Connect to database'")
    print("3. Select 'Redis CLI' tab")
    print("4. Click 'Unmask the password'")
    print("5. Copy the entire connection string")
    print()
    print("💡 Expected format:")
    print("   redis-cli -u redis://<username>:<password>@redis-xxxxx.c123.region-1.ec2.redns.redis-cloud.com:12345")
    print("   redis-cli -u rediss://<username>:<password>@redis-xxxxx.c123.region-1.ec2.redns.redis-cloud.com:12345")
    print("   Or just the URL part:")
    print("   redis://default:<password>@redis-xxxxx.c123.region-1.ec2.redns.redis-cloud.com:12345")
    print("   rediss://default:<password>@redis-xxxxx.c123.region-1.ec2.redns.redis-cloud.com:12345")
    print()

    while True:
        redis_input = input("🔗 Redis Cloud Connection (URL or redis-cli command): ").strip()

        if not redis_input:
            print("❌ Input cannot be empty. Please enter a valid Redis connection string.")
            continue

        # Check if it's a redis-cli command with -u flag
        if redis_input.startswith('redis-cli -u '):
            # Extract URL from redis-cli -u command
            redis_url = redis_input.replace('redis-cli -u ', '').strip()
        else:
            # Assume it's a direct URL
            redis_url = redis_input

        # Parse the URL
        parsed = parse_redis_url(redis_url)

        if not parsed:
            print("❌ Invalid Redis connection format.")
            print("💡 Expected formats:")
            print("   redis-cli -u redis://[user]:[password]@[host]:[port]")
            print("   redis://[user]:[password]@[host]:[port]")
            print("   rediss://[user]:[password]@[host]:[port] (with TLS)")
            continue

        # Show parsed information for confirmation
        print(f"\n✅ Successfully parsed Redis URL:")
        print(f"   🏠 Host: {parsed['host']}")
        print(f"   🔌 Port: {parsed['port']}")
        print(f"   👤 User: {parsed['user']}")
        print(f"   🔒 Password: {'***' + parsed['password'][-4:] if len(parsed['password']) > 4 else '***'}")
        print(f"   🔐 TLS: {'Enabled' if parsed['tls'] else 'Disabled'}")
        print()

        confirm = input("Is this information correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Please enter the URL again.")

    # Set the parsed values in environment
    set_key(ENV_PATH, "REDIS_DEST_HOST", parsed['host'])
    set_key(ENV_PATH, "REDIS_DEST_PORT", parsed['port'])
    set_key(ENV_PATH, "REDIS_DEST_PASSWORD", parsed['password'])
    set_key(ENV_PATH, "REDIS_DEST_TLS", "true" if parsed['tls'] else "false")

    # Set default database if not already set
    if not os.getenv("REDIS_DEST_DB"):
        set_key(ENV_PATH, "REDIS_DEST_DB", "0")

    reload_env()

    print("✅ Destination Redis configuration updated successfully!")
    print("💡 You can test the connection using option 4 from the main menu.")

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
        print("1. Configure Source Redis (AWS ElastiCache)")
        print("2. Configure Destination Redis (Redis Cloud)")
        print("3. Manual Source Redis Setup")
        print("4. Test Source Redis")
        print("5. Test Destination Redis")
        print("6. Export Configuration")
        print("7. Import Configuration")
        print("8. Exit")
        choice = input("Enter choice [1-8]: ").strip()

        if choice == "1":
            setup_source_connection()
        elif choice == "2":
            setup_destination_connection()
        elif choice == "3":
            setup_connection("REDIS_SOURCE")
        elif choice == "4":
            test_redis_connection("REDIS_SOURCE")
        elif choice == "5":
            test_redis_connection("REDIS_DEST")
        elif choice == "6":
            export_configuration()
        elif choice == "7":
            import_configuration()
        elif choice == "8":
            print("✅ Exiting config tool.")
            break
        else:
            print("❌ Invalid choice, try again.")

def test_parsers():
    """Test the parsing functions with sample inputs."""
    print("🧪 Testing Connection String Parsers")
    print("=" * 40)

    # Test AWS CLI parsing
    aws_samples = [
        "redis6-cli --tls -h adar-elasticache-redis-oss-nkwtpc.serverless.eun1.cache.amazonaws.com -p 6379",
        "redis-cli -h my-cache.amazonaws.com -p 6379",
        "redis6-cli -h test.cache.amazonaws.com -p 6380 --tls"
    ]

    print("\n🔧 AWS ElastiCache CLI Command Tests:")
    for i, cmd in enumerate(aws_samples, 1):
        print(f"\n{i}. Input: {cmd}")
        result = parse_aws_redis_cli(cmd)
        if result:
            print(f"   ✅ Host: {result['host']}")
            print(f"   ✅ Port: {result['port']}")
            print(f"   ✅ TLS: {result['tls']}")
        else:
            print("   ❌ Failed to parse")

    # Test Redis URL parsing
    redis_samples = [
        "redis://default:mypassword@redis-xxxxx.c123.region-1.ec2.redns.redis-cloud.com:12345",
        "rediss://user:pass123@redis-yyyyy.c456.region-2.ec2.redns.redis-cloud.com:15000",
        "redis-cli -u redis://default:secret@redis-zzzzz.c789.region-3.ec2.redns.redis-cloud.com:16000"
    ]

    print("\n🔗 Redis Cloud URL Tests:")
    for i, url in enumerate(redis_samples, 1):
        print(f"\n{i}. Input: {url}")
        # Handle redis-cli -u format
        test_url = url.replace('redis-cli -u ', '') if url.startswith('redis-cli -u ') else url
        result = parse_redis_url(test_url)
        if result:
            print(f"   ✅ Host: {result['host']}")
            print(f"   ✅ Port: {result['port']}")
            print(f"   ✅ User: {result['user']}")
            print(f"   ✅ Password: {'***' + result['password'][-4:] if len(result['password']) > 4 else '***'}")
            print(f"   ✅ TLS: {result['tls']}")
        else:
            print("   ❌ Failed to parse")

    print("\n✅ Parser testing complete!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_parsers()
    else:
        main()
