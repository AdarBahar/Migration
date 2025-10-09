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

# Database configuration storage
SOURCES_KEY = "MIGRATION_SOURCES"
TARGETS_KEY = "MIGRATION_TARGETS"
TEST_RESULTS_KEY = "MIGRATION_TEST_RESULTS"

def reload_env():
    """Reload updated .env values into the environment."""
    load_dotenv(ENV_PATH, override=True)

def load_databases(db_type):
    """Load source or target databases from .env file.

    Args:
        db_type: 'sources' or 'targets'

    Returns:
        List of database configurations
    """
    key = SOURCES_KEY if db_type == 'sources' else TARGETS_KEY
    data = os.getenv(key, '[]')
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return []

def save_databases(db_type, databases):
    """Save source or target databases to .env file.

    Args:
        db_type: 'sources' or 'targets'
        databases: List of database configurations
    """
    key = SOURCES_KEY if db_type == 'sources' else TARGETS_KEY
    set_key(ENV_PATH, key, json.dumps(databases))
    reload_env()

def load_test_results():
    """Load test results from .env file."""
    data = os.getenv(TEST_RESULTS_KEY, '{}')
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}

def save_test_results(results):
    """Save test results to .env file."""
    set_key(ENV_PATH, TEST_RESULTS_KEY, json.dumps(results))
    reload_env()

def get_db_id(db_config):
    """Generate unique ID for database configuration."""
    return f"{db_config['engine']}_{db_config['host']}_{db_config['port']}"

# Legacy functions removed - now using new database management system

def add_database(db_type):
    """Add a new source or target database with engine selection.

    Args:
        db_type: 'sources' or 'targets'
    """
    label = "Source" if db_type == 'sources' else "Target"
    print(f"\n🔧 Add New {label} Database")
    print("=" * 60)

    # Select engine type
    print("\n📦 Select Database Engine:")
    print("1. Redis (AWS ElastiCache Redis)")
    print("2. Valkey (AWS ElastiCache Valkey)")
    print("3. Redis Cloud")
    print("4. Manual Redis/Valkey Configuration")
    print("5. Cancel")

    engine_choice = input(f"\nSelect engine type [1-5]: ").strip()

    if engine_choice == '1':
        db_config = setup_elasticache_redis()
    elif engine_choice == '2':
        db_config = setup_elasticache_valkey()
    elif engine_choice == '3':
        db_config = setup_redis_cloud()
    elif engine_choice == '4':
        db_config = setup_manual_database()
    elif engine_choice == '5':
        print("❌ Cancelled.")
        return
    else:
        print("❌ Invalid choice.")
        return

    if not db_config:
        print("❌ Database configuration failed.")
        return

    # Add to database list
    databases = load_databases(db_type)
    databases.append(db_config)
    save_databases(db_type, databases)

    print(f"\n✅ {label} database added successfully!")

    # Auto-test connection
    print(f"\n🔌 Testing connection to {db_config['name']}...")
    test_single_database(db_config, db_type)

    input("\nPress Enter to continue...")

def setup_elasticache_redis():
    """Setup AWS ElastiCache Redis connection."""
    print(f"\n🔧 Configuring AWS ElastiCache Redis")
    print("=" * 50)

    # Get friendly name
    name = input("Database name (friendly label): ").strip()
    if not name:
        print("❌ Name cannot be empty.")
        return None

    # Instructions for getting AWS CLI command
    print("\n📋 AWS ElastiCache Redis Connection Instructions:")
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

    # Ask for password (ElastiCache might not need one, but allow setting)
    print("\n🔒 Password Configuration:")
    print("💡 Many AWS ElastiCache instances don't require a password")
    print("💡 Press Enter to skip password, or enter one if your instance requires it")
    password = getpass("Password (optional, press Enter to skip): ").strip()

    return {
        'name': name,
        'engine': 'redis',
        'engine_version': 'Unknown',
        'host': parsed['host'],
        'port': parsed['port'],
        'password': password,
        'tls': parsed['tls'],
        'db': '0',
        'source': 'AWS ElastiCache'
    }

def setup_elasticache_valkey():
    """Setup AWS ElastiCache Valkey connection."""
    print(f"\n🔧 Configuring AWS ElastiCache Valkey")
    print("=" * 50)

    # Get friendly name
    name = input("Database name (friendly label): ").strip()
    if not name:
        print("❌ Name cannot be empty.")
        return None

    # Instructions for getting Valkey CLI command
    print("\n📋 AWS ElastiCache Valkey Connection Instructions:")
    print("1. Go to AWS Console > ElastiCache > Valkey caches")
    print("2. Click on your cache cluster or replication group")
    print("3. Go to 'Connecting to your cache' tab")
    print("4. Copy the primary endpoint or CLI command")
    print()
    print("💡 Expected formats:")
    print("   valkey-cli --tls -h your-valkey.amazonaws.com -p 6379")
    print("   valkey-cli -h your-valkey.amazonaws.com -p 6379")
    print("   Or just the endpoint: your-valkey.amazonaws.com:6379")
    print()

    while True:
        cli_input = input("🔗 Valkey endpoint or CLI command: ").strip()

        if not cli_input:
            print("❌ Input cannot be empty.")
            continue

        # Try parsing as CLI command first
        parsed = parse_valkey_cli(cli_input)

        # If not a CLI command, try parsing as endpoint
        if not parsed:
            parsed = parse_endpoint(cli_input)

        if not parsed:
            print("❌ Invalid format.")
            print("💡 Expected: valkey-cli --tls -h host.amazonaws.com -p 6379")
            print("💡 Or: host.amazonaws.com:6379")
            continue

        # Show parsed information for confirmation
        print(f"\n✅ Successfully parsed Valkey connection:")
        print(f"   🏠 Host: {parsed['host']}")
        print(f"   🔌 Port: {parsed['port']}")
        print(f"   🔐 TLS: {'Enabled' if parsed['tls'] else 'Disabled'}")
        print()

        confirm = input("Is this information correct? (y/n): ").strip().lower()
        if confirm == 'y':
            break
        else:
            print("Please enter the information again.")

    # Ask for password
    print("\n🔒 Password Configuration:")
    print("💡 Many AWS ElastiCache Valkey instances don't require a password")
    print("💡 Press Enter to skip password, or enter one if your instance requires it")
    password = getpass("Password (optional, press Enter to skip): ").strip()

    return {
        'name': name,
        'engine': 'valkey',
        'engine_version': 'Unknown',
        'host': parsed['host'],
        'port': parsed['port'],
        'password': password,
        'tls': parsed['tls'],
        'db': '0',
        'source': 'AWS ElastiCache Valkey'
    }

# Legacy setup_connection function removed

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

def parse_valkey_cli(cli_command):
    """Parse Valkey CLI command and extract connection parameters.

    Supports formats:
    - valkey-cli --tls -h host.amazonaws.com -p 6379
    - valkey-cli -h host.amazonaws.com -p 6379
    - valkey-cli -h host.amazonaws.com -p 6379 --tls

    Returns dict with parsed parameters or None if invalid.
    """
    if not cli_command or not cli_command.strip():
        return None

    command = cli_command.strip()

    # Check if it's a valkey-cli command
    if not command.startswith('valkey-cli'):
        return None

    # Initialize defaults
    host = None
    port = "6379"
    tls = False

    # Split command into parts
    parts = command.split()

    # Parse arguments
    i = 1  # Skip the valkey-cli part
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
        "tls": tls
    }

def parse_endpoint(endpoint):
    """Parse endpoint in format host:port or just host.

    Returns dict with parsed parameters or None if invalid.
    """
    if not endpoint or not endpoint.strip():
        return None

    endpoint = endpoint.strip()

    # Check for host:port format
    if ':' in endpoint:
        parts = endpoint.split(':')
        if len(parts) == 2:
            host = parts[0]
            try:
                port = str(int(parts[1]))  # Validate port is numeric
                return {
                    "host": host,
                    "port": port,
                    "tls": False  # Default to no TLS for plain endpoint
                }
            except ValueError:
                return None
    else:
        # Just host, use default port
        return {
            "host": endpoint,
            "port": "6379",
            "tls": False
        }

    return None

def setup_redis_cloud():
    """Setup Redis Cloud connection."""
    print(f"\n🔧 Configuring Redis Cloud")
    print("=" * 50)

    # Get friendly name
    name = input("Database name (friendly label): ").strip()
    if not name:
        print("❌ Name cannot be empty.")
        return None

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

    return {
        'name': name,
        'engine': 'redis',
        'engine_version': 'Unknown',
        'host': parsed['host'],
        'port': parsed['port'],
        'password': parsed['password'],
        'tls': parsed['tls'],
        'db': '0',
        'source': 'Redis Cloud'
    }

def setup_manual_database():
    """Setup database connection manually."""
    print(f"\n🔧 Manual Database Configuration")
    print("=" * 50)

    # Get friendly name
    name = input("Database name (friendly label): ").strip()
    if not name:
        print("❌ Name cannot be empty.")
        return None

    # Select engine
    print("\n📦 Select Engine:")
    print("1. Redis")
    print("2. Valkey")
    engine_choice = input("Select engine [1-2]: ").strip()

    if engine_choice == '1':
        engine = 'redis'
    elif engine_choice == '2':
        engine = 'valkey'
    else:
        print("❌ Invalid choice.")
        return None

    # Get connection details
    host = input("Host: ").strip()
    if not host:
        print("❌ Host cannot be empty.")
        return None

    port = input("Port [6379]: ").strip() or "6379"

    password = getpass("Password (press Enter for no password): ").strip()

    tls_input = input("Use TLS/SSL? (y/n) [n]: ").strip().lower()
    tls = tls_input == 'y'

    db = input("Database number [0]: ").strip() or "0"

    return {
        'name': name,
        'engine': engine,
        'engine_version': 'Unknown',
        'host': host,
        'port': port,
        'password': password,
        'tls': tls,
        'db': db,
        'source': 'Manual Configuration'
    }

def manage_databases_menu(db_type):
    """Show menu to manage source or target databases.

    Args:
        db_type: 'sources' or 'targets'
    """
    label = "Source" if db_type == 'sources' else "Target"

    while True:
        databases = load_databases(db_type)
        test_results = load_test_results()

        print(f"\n📦 {label} Databases Management")
        print("=" * 60)

        if databases:
            print(f"\n📍 Configured {label} Databases:")
            for i, db in enumerate(databases, 1):
                db_id = get_db_id(db)
                test_result = test_results.get(db_id, {})

                status_icon = "⏳"
                status_text = "Never tested"
                if test_result.get('status') == 'success':
                    status_icon = "✅"
                    timestamp = test_result.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            status_text = f"Tested: {dt.strftime('%Y-%m-%d %H:%M')}"
                        except:
                            status_text = "Tested: Recently"
                elif test_result.get('status') == 'failed':
                    status_icon = "❌"
                    status_text = "Test failed"

                engine_display = db['engine'].title()
                if db.get('engine_version') and db['engine_version'] != 'Unknown':
                    engine_display += f" {db['engine_version']}"

                print(f"   {i}. {db['name']} ({engine_display}) - {status_icon} {status_text}")
                print(f"      {db['host']}:{db['port']} | TLS: {'Yes' if db.get('tls') else 'No'}")
        else:
            print(f"\n⚠️  No {label.lower()} databases configured yet.")

        print(f"\nOptions:")
        print(f"1. Add New {label} Database")
        print(f"2. Edit Existing {label} Database")
        print(f"3. Test {label} Database Connection")
        print(f"4. Delete {label} Database")
        print(f"5. Back to Main Menu")

        choice = input(f"\nSelect option [1-5]: ").strip()

        if choice == '1':
            add_database(db_type)
        elif choice == '2':
            edit_database(db_type)
        elif choice == '3':
            test_databases_menu(db_type)
        elif choice == '4':
            delete_database(db_type)
        elif choice == '5':
            break
        else:
            print("❌ Invalid choice.")

def edit_database(db_type):
    """Edit an existing database configuration.

    Args:
        db_type: 'sources' or 'targets'
    """
    label = "Source" if db_type == 'sources' else "Target"
    databases = load_databases(db_type)

    if not databases:
        print(f"\n⚠️  No {label.lower()} databases configured.")
        input("Press Enter to continue...")
        return

    print(f"\n✏️  Edit {label} Database")
    print("=" * 60)
    print(f"\n📍 Select database to edit:")

    for i, db in enumerate(databases, 1):
        print(f"{i}. {db['name']} ({db['engine'].title()}) - {db['host']}:{db['port']}")
    print(f"{len(databases) + 1}. Cancel")

    choice = input(f"\nSelect database [1-{len(databases) + 1}]: ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(databases) + 1):
        print("❌ Invalid choice.")
        return

    if int(choice) == len(databases) + 1:
        return

    db_index = int(choice) - 1
    db = databases[db_index]

    print(f"\n✏️  Editing: {db['name']}")
    print("=" * 60)
    print("Press Enter to keep current value")
    print()

    # Edit fields
    new_name = input(f"Name [{db['name']}]: ").strip()
    if new_name:
        db['name'] = new_name

    new_host = input(f"Host [{db['host']}]: ").strip()
    if new_host:
        db['host'] = new_host

    new_port = input(f"Port [{db['port']}]: ").strip()
    if new_port:
        db['port'] = new_port

    print(f"Password: {'***set***' if db.get('password') else '(not set)'}")
    change_password = input("Change password? (y/n) [n]: ").strip().lower()
    if change_password == 'y':
        new_password = getpass("New password (press Enter for no password): ").strip()
        db['password'] = new_password

    new_tls = input(f"Use TLS? (y/n) [{'y' if db.get('tls') else 'n'}]: ").strip().lower()
    if new_tls:
        db['tls'] = new_tls == 'y'

    # Save changes
    databases[db_index] = db
    save_databases(db_type, databases)

    print(f"\n✅ {label} database updated successfully!")

    # Ask to test
    test_now = input("\nTest connection now? (y/n) [y]: ").strip().lower()
    if test_now != 'n':
        print()
        test_single_database(db, db_type)

    input("\nPress Enter to continue...")

def delete_database(db_type):
    """Delete a database configuration.

    Args:
        db_type: 'sources' or 'targets'
    """
    label = "Source" if db_type == 'sources' else "Target"
    databases = load_databases(db_type)

    if not databases:
        print(f"\n⚠️  No {label.lower()} databases configured.")
        input("Press Enter to continue...")
        return

    print(f"\n🗑️  Delete {label} Database")
    print("=" * 60)
    print(f"\n📍 Select database to delete:")

    for i, db in enumerate(databases, 1):
        print(f"{i}. {db['name']} ({db['engine'].title()}) - {db['host']}:{db['port']}")
    print(f"{len(databases) + 1}. Cancel")

    choice = input(f"\nSelect database [1-{len(databases) + 1}]: ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(databases) + 1):
        print("❌ Invalid choice.")
        return

    if int(choice) == len(databases) + 1:
        return

    db_index = int(choice) - 1
    db = databases[db_index]

    # Confirm deletion
    print(f"\n⚠️  Are you sure you want to delete:")
    print(f"   Name: {db['name']}")
    print(f"   Engine: {db['engine'].title()}")
    print(f"   Host: {db['host']}:{db['port']}")

    confirm = input("\nType 'DELETE' to confirm: ").strip()

    if confirm == 'DELETE':
        databases.pop(db_index)
        save_databases(db_type, databases)
        print(f"\n✅ {label} database deleted successfully!")
    else:
        print("\n❌ Deletion cancelled.")

    input("\nPress Enter to continue...")

def view_all_configurations():
    """Display all configured databases."""
    sources = load_databases('sources')
    targets = load_databases('targets')
    test_results = load_test_results()

    print("\n📊 All Configured Databases")
    print("=" * 60)

    if sources:
        print("\n🔹 Source Databases:")
        for i, db in enumerate(sources, 1):
            db_id = get_db_id(db)
            test_result = test_results.get(db_id, {})
            status_icon = "⏳" if not test_result else ("✅" if test_result.get('status') == 'success' else "❌")

            engine_display = db['engine'].title()
            if db.get('engine_version') and db['engine_version'] != 'Unknown':
                engine_display += f" {db['engine_version']}"

            print(f"   {i}. {db['name']} ({engine_display}) - {status_icon}")
            print(f"      Host: {db['host']}:{db['port']}")
            print(f"      TLS: {'Enabled' if db.get('tls') else 'Disabled'}")
            print(f"      Source: {db.get('source', 'Unknown')}")
            print()
    else:
        print("\n🔹 Source Databases: None configured")

    if targets:
        print("\n🔸 Target Databases:")
        for i, db in enumerate(targets, 1):
            db_id = get_db_id(db)
            test_result = test_results.get(db_id, {})
            status_icon = "⏳" if not test_result else ("✅" if test_result.get('status') == 'success' else "❌")

            engine_display = db['engine'].title()
            if db.get('engine_version') and db['engine_version'] != 'Unknown':
                engine_display += f" {db['engine_version']}"

            print(f"   {i}. {db['name']} ({engine_display}) - {status_icon}")
            print(f"      Host: {db['host']}:{db['port']}")
            print(f"      TLS: {'Enabled' if db.get('tls') else 'Disabled'}")
            print(f"      Source: {db.get('source', 'Unknown')}")
            print()
    else:
        print("\n🔸 Target Databases: None configured")

    input("\nPress Enter to continue...")

def test_single_database(db_config, db_type):
    """Test connection to a single database.

    Args:
        db_config: Database configuration dict
        db_type: 'sources' or 'targets'

    Returns:
        True if connection successful, False otherwise
    """
    name = db_config['name']
    host = db_config['host']
    port = int(db_config['port'])
    password = db_config.get('password', '')
    use_tls = db_config.get('tls', False)

    print(f"🔌 Testing connection to {name} ({host}:{port})...")

    try:
        conn_args = {
            "host": host,
            "port": port,
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5
        }
        if password and password.strip():
            conn_args["password"] = password
        if use_tls:
            conn_args["ssl"] = True
            conn_args["ssl_cert_reqs"] = ssl.CERT_NONE

        client = redis.Redis(**conn_args)
        client.ping()

        # Try to get server info
        try:
            info = client.info('server')
            version = info.get('redis_version', 'Unknown')
            db_config['engine_version'] = version
        except:
            pass

        print(f"✅ Connection to {name} successful!")
        if db_config.get('engine_version') != 'Unknown':
            print(f"   Version: {db_config['engine_version']}")

        # Save test result
        test_results = load_test_results()
        db_id = get_db_id(db_config)
        test_results[db_id] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'version': db_config.get('engine_version', 'Unknown')
        }
        save_test_results(test_results)

        return True

    except Exception as e:
        print(f"❌ Connection to {name} failed: {e}")

        # Save test result
        test_results = load_test_results()
        db_id = get_db_id(db_config)
        test_results[db_id] = {
            'status': 'failed',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }
        save_test_results(test_results)

        return False

def test_databases_menu(db_type):
    """Show menu to test database connections.

    Args:
        db_type: 'sources' or 'targets'
    """
    label = "Source" if db_type == 'sources' else "Target"
    databases = load_databases(db_type)

    if not databases:
        print(f"\n⚠️  No {label.lower()} databases configured.")
        input("Press Enter to continue...")
        return

    while True:
        print(f"\n🔌 Test {label} Database Connection")
        print("=" * 60)
        print(f"\n📍 Configured {label} Databases:")
        print("0. Test All")

        for i, db in enumerate(databases, 1):
            test_results = load_test_results()
            db_id = get_db_id(db)
            test_result = test_results.get(db_id, {})

            status_icon = "⏳"
            if test_result.get('status') == 'success':
                status_icon = "✅"
            elif test_result.get('status') == 'failed':
                status_icon = "❌"

            print(f"{i}. {db['name']} ({db['engine'].title()}) - {status_icon}")

        print(f"{len(databases) + 1}. Back")

        choice = input(f"\nSelect database to test [0-{len(databases) + 1}]: ").strip()

        if choice == '0':
            # Test all
            print(f"\n🔌 Testing all {label.lower()} databases...")
            print("=" * 60)
            success_count = 0
            for db in databases:
                if test_single_database(db, db_type):
                    success_count += 1
                print()

            print(f"📊 Results: {success_count}/{len(databases)} successful")
            input("\nPress Enter to continue...")

        elif choice.isdigit() and 1 <= int(choice) <= len(databases):
            # Test specific database
            db = databases[int(choice) - 1]
            print()
            test_single_database(db, db_type)
            input("\nPress Enter to continue...")

        elif choice == str(len(databases) + 1):
            break
        else:
            print("❌ Invalid choice.")

def export_configuration():
    """Export current database configurations to a JSON file."""
    print("\n📤 Export Configuration")
    print("=" * 60)

    sources = load_databases('sources')
    targets = load_databases('targets')

    # Check if there's any configuration to export
    if not sources and not targets:
        print("⚠️  No database configurations found to export.")
        print("   Please configure at least one database first.")
        input("\nPress Enter to continue...")
        return

    # Prepare configuration (without passwords for security)
    config = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "exported_by": "Redis/Valkey Migration Tool",
            "version": "2.0"
        },
        "sources": [],
        "targets": []
    }

    # Export sources (without passwords)
    for db in sources:
        db_export = db.copy()
        db_export['password'] = ''  # Don't export passwords
        config['sources'].append(db_export)

    # Export targets (without passwords)
    for db in targets:
        db_export = db.copy()
        db_export['password'] = ''  # Don't export passwords
        config['targets'].append(db_export)

    # Generate default filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"migration_config_{timestamp}.json"

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

        print(f"\n✅ Configuration exported to: {filename}")
        print(f"📁 File size: {os.path.getsize(filename)} bytes")
        print()
        print("📋 Exported configuration includes:")
        print(f"   🔹 Source databases: {len(sources)}")
        print(f"   🔸 Target databases: {len(targets)}")
        print("   ⚠️  Note: Passwords are NOT exported for security reasons")
        print()

    except Exception as e:
        print(f"❌ Failed to export configuration: {e}")

    input("\nPress Enter to continue...")

def import_configuration():
    """Import database configurations from a JSON file."""
    print("\n📥 Import Configuration")
    print("=" * 60)

    # List available JSON files
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and
                  (f.startswith('migration_config') or f.startswith('redis_config'))]

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
                    input("\nPress Enter to continue...")
                    return
            except:
                print("❌ Invalid selection.")
                input("\nPress Enter to continue...")
                return
        else:
            print("❌ No configuration files found.")
            input("\nPress Enter to continue...")
            return

    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'

    # Check if file exists
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        input("\nPress Enter to continue...")
        return

    try:
        # Read configuration from file
        with open(filename, 'r') as f:
            config = json.load(f)

        print(f"✅ Configuration loaded from: {filename}")

        # Show what will be imported
        print("\n📋 Configuration to import:")
        if config.get('metadata', {}).get('exported_at'):
            print(f"   📅 Exported: {config['metadata']['exported_at']}")

        sources = config.get('sources', [])
        targets = config.get('targets', [])

        print(f"   🔹 Source databases: {len(sources)}")
        for db in sources:
            print(f"      - {db.get('name', 'Unnamed')} ({db.get('engine', 'unknown').title()})")

        print(f"   🔸 Target databases: {len(targets)}")
        for db in targets:
            print(f"      - {db.get('name', 'Unnamed')} ({db.get('engine', 'unknown').title()})")

        # Confirm import
        print("\n⚠️  Import options:")
        print("1. Replace all (clear existing and import)")
        print("2. Merge (add to existing)")
        print("3. Cancel")

        import_choice = input("\nSelect option [1-3]: ").strip()

        if import_choice == '3':
            print("❌ Import cancelled.")
            input("\nPress Enter to continue...")
            return
        elif import_choice == '1':
            # Replace all
            save_databases('sources', sources)
            save_databases('targets', targets)
            print("\n✅ Configuration replaced successfully!")
        elif import_choice == '2':
            # Merge
            existing_sources = load_databases('sources')
            existing_targets = load_databases('targets')

            existing_sources.extend(sources)
            existing_targets.extend(targets)

            save_databases('sources', existing_sources)
            save_databases('targets', existing_targets)
            print("\n✅ Configuration merged successfully!")
        else:
            print("❌ Invalid choice.")
            input("\nPress Enter to continue...")
            return

        print("⚠️  Remember to set passwords manually for security reasons.")

    except json.JSONDecodeError:
        print("❌ Invalid JSON file format.")
    except Exception as e:
        print(f"❌ Failed to import configuration: {e}")

    input("\nPress Enter to continue...")

def main():
    """Main menu for database configuration tool."""
    while True:
        sources = load_databases('sources')
        targets = load_databases('targets')
        test_results = load_test_results()

        # Count tested databases
        sources_tested = sum(1 for db in sources if test_results.get(get_db_id(db), {}).get('status') == 'success')
        targets_tested = sum(1 for db in targets if test_results.get(get_db_id(db), {}).get('status') == 'success')

        print("\n" + "=" * 60)
        print("🔐 Redis/Valkey Migration Configuration Tool")
        print("=" * 60)

        print("\n📊 Quick Overview:")
        if sources:
            print(f"   🔹 Sources: {len(sources)} configured ({sources_tested} tested ✅, {len(sources) - sources_tested} untested ⏳)")
        else:
            print(f"   🔹 Sources: None configured")

        if targets:
            print(f"   🔸 Targets: {len(targets)} configured ({targets_tested} tested ✅, {len(targets) - targets_tested} untested ⏳)")
        else:
            print(f"   🔸 Targets: None configured")

        print("\nMain Menu:")
        print(f"1. Source Databases ({len(sources)} configured)")
        print(f"2. Target Databases ({len(targets)} configured)")
        print(f"3. Export/Import Configuration")
        print(f"4. View All Configurations")
        print(f"5. Exit")

        choice = input("\nSelect option [1-5]: ").strip()

        if choice == "1":
            manage_databases_menu('sources')
        elif choice == "2":
            manage_databases_menu('targets')
        elif choice == "3":
            export_import_menu()
        elif choice == "4":
            view_all_configurations()
        elif choice == "5":
            print("\n✅ Exiting configuration tool.")
            print("💡 Your configurations are saved in .env file")
            break
        else:
            print("❌ Invalid choice, try again.")

def export_import_menu():
    """Menu for export/import operations."""
    while True:
        print("\n📦 Export/Import Configuration")
        print("=" * 60)
        print("\nOptions:")
        print("1. Export Configuration to File")
        print("2. Import Configuration from File")
        print("3. Back to Main Menu")

        choice = input("\nSelect option [1-3]: ").strip()

        if choice == "1":
            export_configuration()
        elif choice == "2":
            import_configuration()
        elif choice == "3":
            break
        else:
            print("❌ Invalid choice.")

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
