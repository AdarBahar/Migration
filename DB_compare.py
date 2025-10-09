#!/usr/bin/env python3
"""
Database Comparison Tool
Compares multiple Redis/Valkey databases and shows differences in keys, data types, and values.
"""

import os
import sys
import json
import redis
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from input_utils import get_input, get_yes_no, print_header, print_section, pause

# Load environment variables
ENV_PATH = ".env"
load_dotenv(ENV_PATH)

def load_databases():
    """Load all configured databases from .env file."""
    sources_json = os.getenv('MIGRATION_SOURCES', '[]')
    targets_json = os.getenv('MIGRATION_TARGETS', '[]')

    try:
        sources = json.loads(sources_json)
        targets = json.loads(targets_json)
    except json.JSONDecodeError:
        sources = []
        targets = []

    all_databases = []

    # Add sources with label
    for db in sources:
        db_copy = db.copy()
        db_copy['db_type'] = 'Source'
        all_databases.append(db_copy)

    # Add targets with label
    for db in targets:
        db_copy = db.copy()
        db_copy['db_type'] = 'Target'
        all_databases.append(db_copy)

    return all_databases

def connect_to_database(db_config):
    """Connect to a Redis/Valkey database."""
    try:
        host = db_config['host']
        port = int(db_config['port'])
        password = db_config.get('password', '')
        tls = db_config.get('tls', False)
        db_num = int(db_config.get('db', 0))

        # Create connection
        if tls:
            r = redis.Redis(
                host=host,
                port=port,
                password=password if password else None,
                db=db_num,
                ssl=True,
                ssl_cert_reqs=None,
                decode_responses=True,
                socket_connect_timeout=10
            )
        else:
            r = redis.Redis(
                host=host,
                port=port,
                password=password if password else None,
                db=db_num,
                decode_responses=True,
                socket_connect_timeout=10
            )

        # Test connection
        r.ping()
        return r

    except redis.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_database_info(connection):
    """Get comprehensive information about a database."""
    info = {
        'total_keys': 0,
        'keys_by_type': defaultdict(int),
        'memory_usage': 0,
        'keys': [],
        'sample_data': {}
    }

    try:
        # Get all keys
        keys = connection.keys('*')
        info['total_keys'] = len(keys)
        info['keys'] = sorted(keys)

        # Analyze each key
        for key in keys:
            try:
                # Get key type
                key_type = connection.type(key)
                info['keys_by_type'][key_type] += 1

                # Get memory usage (if available)
                try:
                    memory = connection.memory_usage(key)
                    if memory:
                        info['memory_usage'] += memory
                except:
                    pass

                # Sample first 10 keys for detailed info
                if len(info['sample_data']) < 10:
                    info['sample_data'][key] = {
                        'type': key_type,
                        'ttl': connection.ttl(key)
                    }

                    # Get value based on type
                    if key_type == 'string':
                        value = connection.get(key)
                        info['sample_data'][key]['value'] = value[:100] if len(str(value)) > 100 else value
                    elif key_type == 'list':
                        info['sample_data'][key]['length'] = connection.llen(key)
                    elif key_type == 'set':
                        info['sample_data'][key]['size'] = connection.scard(key)
                    elif key_type == 'zset':
                        info['sample_data'][key]['size'] = connection.zcard(key)
                    elif key_type == 'hash':
                        info['sample_data'][key]['fields'] = connection.hlen(key)

            except Exception as e:
                continue

        return info

    except Exception as e:
        print(f"❌ Error getting database info: {e}")
        return info

def compare_databases(db_infos):
    """Compare multiple databases and show differences."""
    print("\n" + "=" * 80)
    print("📊 DATABASE COMPARISON RESULTS")
    print("=" * 80)

    # Summary comparison
    print("\n📋 Summary:")
    print("-" * 80)
    print(f"{'Database':<30} {'Total Keys':<15} {'Memory (bytes)':<20} {'Types'}")
    print("-" * 80)

    for db_name, info in db_infos.items():
        types_str = ", ".join([f"{k}:{v}" for k, v in info['keys_by_type'].items()])
        print(f"{db_name:<30} {info['total_keys']:<15} {info['memory_usage']:<20} {types_str}")

    # Key differences
    print("\n🔍 Key Differences:")
    print("-" * 80)

    all_keys = set()
    for info in db_infos.values():
        all_keys.update(info['keys'])

    # Find keys unique to each database
    for db_name, info in db_infos.items():
        db_keys = set(info['keys'])
        unique_keys = db_keys - set().union(*[set(other_info['keys'])
                                               for other_name, other_info in db_infos.items()
                                               if other_name != db_name])

        if unique_keys:
            print(f"\n📍 Keys only in {db_name}: {len(unique_keys)}")
            for key in sorted(list(unique_keys)[:10]):
                print(f"   • {key}")
            if len(unique_keys) > 10:
                print(f"   ... and {len(unique_keys) - 10} more")

    # Find common keys
    common_keys = set(db_infos[list(db_infos.keys())[0]]['keys'])
    for info in db_infos.values():
        common_keys &= set(info['keys'])

    if common_keys:
        print(f"\n✅ Common keys across all databases: {len(common_keys)}")
        for key in sorted(list(common_keys)[:10]):
            print(f"   • {key}")
        if len(common_keys) > 10:
            print(f"   ... and {len(common_keys) - 10} more")
    else:
        print("\n⚠️  No common keys found across all databases")

def select_databases_to_compare(all_databases):
    """Interactive selection of databases to compare."""
    if not all_databases:
        print("❌ No databases configured!")
        print("💡 Use 'python3 manage_env.py' to configure databases")
        return []

    print("\n📦 Available Databases:")
    print("=" * 80)

    for i, db in enumerate(all_databases, 1):
        db_type_label = db.get('db_type', 'Unknown')
        engine = db.get('engine', 'unknown').title()
        version = db.get('engine_version', '')
        name = db.get('name', 'Unnamed')
        host = db.get('host', '')
        port = db.get('port', '')

        version_str = f" {version}" if version else ""
        print(f"{i}. [{db_type_label}] {name} ({engine}{version_str})")
        print(f"   {host}:{port}")

    print("\n" + "=" * 80)
    print("Select databases to compare (minimum 2)")
    print("Enter numbers separated by commas (e.g., 1,2,3)")
    print("Or enter 'all' to compare all databases")
    print("=" * 80)

    while True:
        try:
            choice = get_input("\nYour selection: ").strip()

            if choice.lower() == 'all':
                return all_databases

            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in choice.split(',')]

            # Validate indices
            if len(indices) < 2:
                print("❌ Please select at least 2 databases to compare")
                continue

            if any(i < 1 or i > len(all_databases) for i in indices):
                print(f"❌ Invalid selection. Please enter numbers between 1 and {len(all_databases)}")
                continue

            # Get selected databases
            selected = [all_databases[i-1] for i in indices]

            # Confirm selection
            print("\n✅ Selected databases:")
            for db in selected:
                print(f"   • {db['name']} ({db.get('engine', 'unknown').title()})")

            if get_yes_no("\nProceed with comparison?", default=True):
                return selected
            else:
                print("Selection cancelled. Please select again.")
                continue

        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            return []

def main():
    """Main function for database comparison."""
    print("=" * 80)
    print("🔍 Redis/Valkey Database Comparison Tool")
    print("=" * 80)

    # Load databases from .env
    all_databases = load_databases()

    if not all_databases:
        print("\n❌ No databases configured in .env file")
        print("💡 Use 'python3 manage_env.py' to configure databases")
        return

    print(f"\n📊 Found {len(all_databases)} configured database(s)")

    # Select databases to compare
    selected_databases = select_databases_to_compare(all_databases)

    if not selected_databases:
        print("\n❌ No databases selected for comparison")
        return

    # Connect to databases and gather information
    print("\n🔌 Connecting to databases...")
    db_infos = {}
    connections = {}

    for db in selected_databases:
        db_name = db['name']
        print(f"\n📍 Connecting to {db_name}...")

        conn = connect_to_database(db)
        if not conn:
            print(f"❌ Failed to connect to {db_name}")
            continue

        print(f"✅ Connected to {db_name}")
        connections[db_name] = conn

        print(f"📊 Analyzing {db_name}...")
        info = get_database_info(conn)
        db_infos[db_name] = info
        print(f"✅ Found {info['total_keys']} keys")

    # Close connections
    for conn in connections.values():
        try:
            conn.close()
        except:
            pass

    if len(db_infos) < 2:
        print("\n❌ Need at least 2 successfully connected databases to compare")
        return

    # Compare databases
    compare_databases(db_infos)

    # Export option
    print("\n" + "=" * 80)

    if get_yes_no("Export comparison results to file?", default=False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_comparison_{timestamp}.txt"

        try:
            # Redirect output to file
            from contextlib import redirect_stdout

            with open(filename, 'w') as f:
                with redirect_stdout(f):
                    compare_databases(db_infos)

            print(f"✅ Results exported to: {filename}")
        except Exception as e:
            print(f"❌ Failed to export results: {e}")

    print("\n✅ Comparison complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
