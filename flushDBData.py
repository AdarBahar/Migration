#!/usr/bin/env python3
"""
Flush Database Tool
Flushes Redis/Valkey databases configured in .env file.
"""

import os
import json
import redis
from dotenv import load_dotenv

# Load .env config
load_dotenv(".env")

def load_databases():
    """Load all configured databases from .env file."""
    sources_json = os.getenv('MIGRATION_SOURCES', '[]')
    targets_json = os.getenv('MIGRATION_TARGETS', '[]')

    try:
        sources = json.loads(sources_json)
        targets = json.loads(targets_json)
    except json.JSONDecodeError:
        print("⚠️  Warning: Could not parse MIGRATION_SOURCES or MIGRATION_TARGETS from .env")
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

def connect_to_redis(db_config):
    """Connect to a Redis/Valkey database."""
    try:
        host = db_config['host']
        port = int(db_config['port'])
        password = db_config.get('password')
        db_num = int(db_config.get('db', 0))
        tls = db_config.get('tls', 'false').lower() == 'true'

        connection_kwargs = {
            "host": host,
            "port": port,
            "decode_responses": True,
            "socket_connect_timeout": 10,
            "socket_timeout": 10,
            "db": db_num
        }

        if password and str(password).strip().lower() not in ['none', '']:
            connection_kwargs["password"] = password

        if tls:
            connection_kwargs["ssl"] = True
            connection_kwargs["ssl_cert_reqs"] = None

        client = redis.Redis(**connection_kwargs)
        client.ping()
        return client
    except Exception as e:
        print(f"❌ Failed to connect to {db_config['name']} ({host}:{port}): {e}")
        return None

def flush_db(redis_client, db_name):
    """Flush all data from a database."""
    try:
        # Ask for confirmation
        print(f"\n⚠️  WARNING: This will delete ALL data from {db_name}!")
        confirm = input(f"Type '{db_name}' to confirm: ").strip()

        if confirm != db_name:
            print(f"❌ Confirmation failed. Database {db_name} was NOT flushed.")
            return False

        redis_client.flushall()
        print(f"✅ {db_name} database flushed successfully.")
        return True
    except Exception as e:
        print(f"❌ Error flushing {db_name}: {e}")
        return False

def main():
    """Main function for flushing databases."""
    print("=" * 80)
    print("🗑️  Redis/Valkey Database Flush Tool")
    print("=" * 80)

    # Load databases from .env
    all_databases = load_databases()

    if not all_databases:
        print("\n❌ No databases found in .env file!")
        print("Please configure MIGRATION_SOURCES and/or MIGRATION_TARGETS in .env")
        return

    # Display available databases
    print("\n📦 Available Databases:")
    for idx, db in enumerate(all_databases, 1):
        db_type_label = f"[{db['db_type']}]"
        print(f"{idx}. {db_type_label:<10} {db['name']} ({db['host']}:{db['port']})")

    print(f"{len(all_databases) + 1}. Flush ALL databases")
    print("0. Cancel")

    # Get user choice
    try:
        choice = input(f"\nEnter choice [0-{len(all_databases) + 1}]: ").strip()
        choice_num = int(choice)
    except ValueError:
        print("❌ Invalid choice.")
        return

    if choice_num == 0:
        print("✅ Operation cancelled.")
        return

    # Flush all databases
    if choice_num == len(all_databases) + 1:
        print(f"\n⚠️  WARNING: This will flush ALL {len(all_databases)} databases!")
        confirm = input("Type 'FLUSH ALL' to confirm: ").strip()

        if confirm != "FLUSH ALL":
            print("❌ Confirmation failed. No databases were flushed.")
            return

        success_count = 0
        for db in all_databases:
            print(f"\n🔌 Connecting to {db['name']}...")
            client = connect_to_redis(db)
            if client:
                try:
                    client.flushall()
                    print(f"✅ {db['name']} flushed successfully.")
                    success_count += 1
                except Exception as e:
                    print(f"❌ Error flushing {db['name']}: {e}")

        print(f"\n📊 Summary: {success_count}/{len(all_databases)} databases flushed successfully.")
        return

    # Flush single database
    if 1 <= choice_num <= len(all_databases):
        selected_db = all_databases[choice_num - 1]
        print(f"\n🔌 Connecting to {selected_db['name']}...")
        client = connect_to_redis(selected_db)
        if client:
            flush_db(client, selected_db['name'])
    else:
        print("❌ Invalid choice.")

if __name__ == "__main__":
    main()

