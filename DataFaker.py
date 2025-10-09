#!/usr/bin/env python3
"""
Fake Data Generator for Redis/Valkey
Generates realistic test data for migration testing.
"""

import os
import sys
import json
import redis
import ssl
import random
from faker import Faker
from dotenv import load_dotenv
from datetime import datetime
from input_utils import get_input, get_number, get_yes_no, print_header

# Load .env
ENV_PATH = ".env"
load_dotenv(ENV_PATH)

fake = Faker()

STATUSES = ['active', 'inactive', 'pending']

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
        engine = db_config.get('engine', 'redis')

        # Create connection
        connection_kwargs = {
            "host": host,
            "port": port,
            "db": db_num,
            "decode_responses": True,
            "socket_timeout": 10,
            "socket_connect_timeout": 10
        }

        if password and str(password).strip():
            connection_kwargs["password"] = password

        if tls:
            connection_kwargs["ssl"] = True
            connection_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE

        client = redis.Redis(**connection_kwargs)
        client.ping()

        engine_label = engine.title()
        print(f"✅ Connected to {engine_label}: {db_config['name']} ({host}:{port})")
        return client

    except redis.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def generate_record():
    """Generate a fake user record."""
    return {
        "user_id": fake.uuid4(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address().replace("\n", ", "),
        "city": fake.city(),
        "country": fake.country(),
        "status": random.choice(STATUSES),
        "created_at": datetime.now().isoformat(),
        "nickname": fake.user_name(),
        "company": fake.company(),
        "job_title": fake.job()
    }

def generate_session():
    """Generate a fake session record."""
    return {
        "session_id": fake.uuid4(),
        "user_id": fake.uuid4(),
        "ip_address": fake.ipv4(),
        "user_agent": fake.user_agent(),
        "created_at": datetime.now().isoformat(),
        "expires_at": fake.future_datetime().isoformat(),
        "active": random.choice(['true', 'false'])
    }

def generate_product():
    """Generate a fake product record."""
    return {
        "product_id": fake.uuid4(),
        "name": fake.catch_phrase(),
        "description": fake.text(max_nb_chars=200),
        "price": f"{random.uniform(10, 1000):.2f}",
        "category": random.choice(['Electronics', 'Clothing', 'Food', 'Books', 'Toys']),
        "stock": str(random.randint(0, 1000)),
        "created_at": datetime.now().isoformat()
    }

def create_fake_data(client, data_type, count, key_prefix="test"):
    """Create fake data in the database.

    Args:
        client: Redis/Valkey client
        data_type: Type of data to generate (users, sessions, products, mixed)
        count: Number of records to create
        key_prefix: Prefix for keys
    """
    print(f"\n🔄 Generating {count} {data_type} records...")

    created = 0
    errors = 0

    for i in range(count):
        try:
            if data_type == 'users':
                record = generate_record()
                redis_key = f"{key_prefix}:user:{record['user_id']}"
                client.hset(redis_key, mapping=record)

            elif data_type == 'sessions':
                record = generate_session()
                redis_key = f"{key_prefix}:session:{record['session_id']}"
                client.hset(redis_key, mapping=record)

            elif data_type == 'products':
                record = generate_product()
                redis_key = f"{key_prefix}:product:{record['product_id']}"
                client.hset(redis_key, mapping=record)

            elif data_type == 'mixed':
                # Mix of different data types
                choice = random.choice(['user', 'session', 'product'])
                if choice == 'user':
                    record = generate_record()
                    redis_key = f"{key_prefix}:user:{record['user_id']}"
                elif choice == 'session':
                    record = generate_session()
                    redis_key = f"{key_prefix}:session:{record['session_id']}"
                else:
                    record = generate_product()
                    redis_key = f"{key_prefix}:product:{record['product_id']}"

                client.hset(redis_key, mapping=record)

            created += 1

            # Show progress every 100 records
            if (i + 1) % 100 == 0:
                print(f"   📊 Progress: {i + 1}/{count} records created...")

        except Exception as e:
            errors += 1
            if errors <= 5:  # Only show first 5 errors
                print(f"   ⚠️  Error creating record {i + 1}: {e}")

    print(f"\n✅ Successfully created {created} records")
    if errors > 0:
        print(f"⚠️  {errors} errors occurred")

def select_database(all_databases):
    """Interactive database selection."""
    if not all_databases:
        print("❌ No databases configured!")
        print("💡 Use 'python3 manage_env.py' to configure databases")
        return None

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

    while True:
        try:
            choice = get_input("Select database number")

            if not choice:
                print("❌ Please enter a database number")
                continue

            index = int(choice)

            if index < 1 or index > len(all_databases):
                print(f"❌ Invalid selection. Please enter a number between 1 and {len(all_databases)}")
                continue

            selected = all_databases[index - 1]

            # Confirm selection
            print(f"\n✅ Selected: {selected['name']} ({selected.get('engine', 'unknown').title()})")

            if get_yes_no("Proceed with this database?", default=True):
                return selected
            else:
                print("Selection cancelled. Please select again.")
                continue

        except ValueError:
            print("❌ Invalid input. Please enter a number")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            return None

def main():
    """Main function for fake data generation."""
    print_header("🛠️  Redis/Valkey Fake Data Generator")

    # Load databases from .env
    all_databases = load_databases()

    if not all_databases:
        print("\n❌ No databases configured in .env file")
        print("💡 Use 'python3 manage_env.py' to configure databases")
        return

    print(f"\n📊 Found {len(all_databases)} configured database(s)")

    # Select database
    selected_db = select_database(all_databases)

    if not selected_db:
        print("\n❌ No database selected")
        return

    # Connect to database
    print(f"\n🔌 Connecting to {selected_db['name']}...")
    client = connect_to_database(selected_db)

    if not client:
        print("❌ Failed to connect to database")
        return

    # Select data type
    print("\n" + "=" * 80)
    print("📋 Data Type Selection")
    print("=" * 80)
    print("1. Users (user profiles with contact info)")
    print("2. Sessions (user sessions with IP and user agent)")
    print("3. Products (product catalog with prices)")
    print("4. Mixed (random mix of all types)")
    print()

    data_type_choice = get_input("Select data type [1-4]", default="1")

    data_type_map = {
        '1': 'users',
        '2': 'sessions',
        '3': 'products',
        '4': 'mixed'
    }

    data_type = data_type_map.get(data_type_choice, 'users')

    # Get number of records
    count = get_number(
        "\nHow many records to create?",
        min_val=1,
        max_val=1000000,
        default=100
    )

    # Get key prefix
    default_prefix = f"{selected_db.get('engine', 'test')}:fake"
    key_prefix = get_input(f"\nKey prefix", default=default_prefix)

    # Confirm before creating
    print("\n" + "=" * 80)
    print("📋 Summary")
    print("=" * 80)
    print(f"Database: {selected_db['name']} ({selected_db.get('engine', 'unknown').title()})")
    print(f"Data Type: {data_type}")
    print(f"Records: {count}")
    print(f"Key Prefix: {key_prefix}")
    print("=" * 80)

    if not get_yes_no("\nProceed with data generation?", default=True):
        print("❌ Cancelled by user")
        return

    # Create fake data
    try:
        create_fake_data(client, data_type, count, key_prefix)

        # Show final stats
        print("\n" + "=" * 80)
        print("📊 Final Statistics")
        print("=" * 80)

        try:
            total_keys = client.dbsize()
            print(f"Total keys in database: {total_keys}")

            # Sample some keys
            sample_keys = client.keys(f"{key_prefix}:*")[:5]
            if sample_keys:
                print(f"\nSample keys created:")
                for key in sample_keys:
                    print(f"   • {key}")
        except Exception as e:
            print(f"⚠️  Could not get database stats: {e}")

        print("\n✅ Data generation complete!")

    except Exception as e:
        print(f"\n❌ Error during data generation: {e}")

    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

