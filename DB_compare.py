#!/usr/bin/env python3
"""
Database Comparison Tool
Compares multiple Redis/Valkey databases and shows differences in keys, data types, and values.
"""

import os
import sys
import json
import redis
import time
import signal
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from input_utils import get_input, get_yes_no, get_number, print_header, print_section, pause, clear_screen

# Load environment variables
ENV_PATH = ".env"
load_dotenv(ENV_PATH)

# Timeout handler for long-running operations
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

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

def get_database_info(connection, timeout=60, show_progress=True):
    """Get comprehensive information about a database.

    Args:
        connection: Redis/Valkey connection
        timeout: Maximum time in seconds to analyze the database (default: 60)
        show_progress: Whether to show progress messages (default: True, disable for continuous mode)

    Returns:
        Dictionary with database information
    """
    info = {
        'total_keys': 0,
        'keys_by_type': defaultdict(int),
        'memory_usage': 0,
        'keys': [],
        'sample_data': {}
    }

    # Set up timeout handler (only on Unix-like systems)
    old_handler = None
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

    try:
        # Get all keys
        keys = connection.keys('*')
        info['total_keys'] = len(keys)
        info['keys'] = sorted(keys)

        # Show progress for large databases (only if show_progress is True)
        total_keys = len(keys)
        if show_progress and total_keys > 1000:
            print(f"   ⏳ Analyzing {total_keys} keys (this may take a moment)...")

        # Analyze each key
        keys_processed = 0
        for key in keys:
            try:
                # Get key type
                key_type = connection.type(key)
                info['keys_by_type'][key_type] += 1

                # Get memory usage (if available) - only for first 100 keys to avoid slowdown
                if keys_processed < 100:
                    try:
                        memory = connection.memory_usage(key)
                        if memory:
                            info['memory_usage'] += memory
                    except Exception:
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

                keys_processed += 1

                # Show progress every 1000 keys (only if show_progress is True)
                if show_progress and total_keys > 1000 and keys_processed % 1000 == 0:
                    print(f"   📊 Progress: {keys_processed}/{total_keys} keys analyzed...")

            except Exception as e:
                continue

        # Estimate total memory if we only sampled
        if total_keys > 100 and info['memory_usage'] > 0:
            # Extrapolate memory usage
            avg_memory_per_key = info['memory_usage'] / min(100, keys_processed)
            info['memory_usage'] = int(avg_memory_per_key * total_keys)
            info['memory_estimated'] = True
        else:
            info['memory_estimated'] = False

        # Cancel the alarm
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if old_handler:
                signal.signal(signal.SIGALRM, old_handler)

        return info

    except TimeoutError:
        print(f"⚠️  Analysis timed out after {timeout} seconds")
        print(f"   Partial results: {keys_processed}/{total_keys} keys analyzed")

        # Cancel the alarm
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if old_handler:
                signal.signal(signal.SIGALRM, old_handler)

        return info

    except Exception as e:
        print(f"❌ Error getting database info: {e}")
        import traceback
        traceback.print_exc()

        # Cancel the alarm
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if old_handler:
                signal.signal(signal.SIGALRM, old_handler)

        return info

def build_comparison_output(db_infos, previous_infos=None):
    """Build comparison output as a list of lines (for continuous mode).

    Args:
        db_infos: Current database information
        previous_infos: Previous comparison data for showing deltas

    Returns:
        List of output lines
    """
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("")
    lines.append("=" * 80)
    lines.append(f"📊 DATABASE COMPARISON RESULTS - {timestamp}")
    lines.append("=" * 80)

    # Summary comparison
    lines.append("")
    lines.append("📋 Summary:")
    lines.append("-" * 80)
    if previous_infos:
        lines.append(f"{'Database':<30} {'Total Keys':<15} {'Change':<12} {'Memory (bytes)':<20} {'Types'}")
    else:
        lines.append(f"{'Database':<30} {'Total Keys':<15} {'Memory (bytes)':<20} {'Types'}")
    lines.append("-" * 80)

    for db_name, info in db_infos.items():
        types_str = ", ".join([f"{k}:{v}" for k, v in info['keys_by_type'].items()])

        # Format memory with estimation indicator
        memory_str = str(info['memory_usage'])
        if info.get('memory_estimated', False):
            memory_str += " (est.)"

        # Show delta if we have previous data
        delta_str = ""
        if previous_infos and db_name in previous_infos:
            prev_count = previous_infos[db_name]['total_keys']
            curr_count = info['total_keys']
            delta = curr_count - prev_count
            if delta > 0:
                delta_str = f"🔼 +{delta}"
            elif delta < 0:
                delta_str = f"🔽 {delta}"
            else:
                delta_str = "➖ 0"

            lines.append(f"{db_name:<30} {info['total_keys']:<15} {delta_str:<12} {memory_str:<20} {types_str}")
        else:
            lines.append(f"{db_name:<30} {info['total_keys']:<15} {memory_str:<20} {types_str}")

    # Key differences
    lines.append("")
    lines.append("🔍 Key Differences:")
    lines.append("-" * 80)

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
            lines.append("")
            lines.append(f"📍 Keys only in {db_name}: {len(unique_keys)}")
            for key in sorted(list(unique_keys)[:10]):
                lines.append(f"   • {key}")
            if len(unique_keys) > 10:
                lines.append(f"   ... and {len(unique_keys) - 10} more")

    # Find common keys
    common_keys = set(db_infos[list(db_infos.keys())[0]]['keys'])
    for info in db_infos.values():
        common_keys &= set(info['keys'])

    if common_keys:
        lines.append("")
        lines.append(f"✅ Common keys across all databases: {len(common_keys)}")
        for key in sorted(list(common_keys)[:10]):
            lines.append(f"   • {key}")
        if len(common_keys) > 10:
            lines.append(f"   ... and {len(common_keys) - 10} more")
    else:
        lines.append("")
        lines.append("⚠️  No common keys found across all databases")

    return lines

def compare_databases(db_infos, show_timestamp=False, previous_infos=None):
    """Compare multiple databases and show differences.

    Args:
        db_infos: Current database information
        show_timestamp: Whether to show timestamp in header
        previous_infos: Previous comparison data for showing deltas
    """
    print("\n" + "=" * 80)
    if show_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📊 DATABASE COMPARISON RESULTS - {timestamp}")
    else:
        print("📊 DATABASE COMPARISON RESULTS")
    print("=" * 80)

    # Summary comparison
    print("\n📋 Summary:")
    print("-" * 80)
    if previous_infos:
        print(f"{'Database':<30} {'Total Keys':<15} {'Change':<12} {'Memory (bytes)':<20} {'Types'}")
    else:
        print(f"{'Database':<30} {'Total Keys':<15} {'Memory (bytes)':<20} {'Types'}")
    print("-" * 80)

    for db_name, info in db_infos.items():
        types_str = ", ".join([f"{k}:{v}" for k, v in info['keys_by_type'].items()])

        # Show delta if we have previous data
        delta_str = ""
        if previous_infos and db_name in previous_infos:
            prev_count = previous_infos[db_name]['total_keys']
            curr_count = info['total_keys']
            delta = curr_count - prev_count
            if delta > 0:
                delta_str = f"🔼 +{delta}"
            elif delta < 0:
                delta_str = f"🔽 {delta}"
            else:
                delta_str = "➖ 0"

            print(f"{db_name:<30} {info['total_keys']:<15} {delta_str:<12} {info['memory_usage']:<20} {types_str}")
        else:
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

def continuous_compare(selected_databases, cadence=5):
    """Continuously compare databases at specified interval with fixed display.

    Args:
        selected_databases: List of database configurations to compare
        cadence: Seconds between comparisons (default: 5)
    """
    import sys

    # ANSI escape codes for cursor control
    CURSOR_UP = '\033[F'
    CLEAR_LINE = '\033[K'
    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'

    print(f"\n🔄 Starting continuous comparison mode (every {cadence} seconds)")
    print("Press Ctrl+C to stop")
    print("=" * 80)

    iteration = 0
    start_time = time.time()
    previous_infos = None
    lines_printed = 0  # Track how many lines we've printed

    elapsed = 0

    # Hide cursor for cleaner display
    print(HIDE_CURSOR, end='')
    sys.stdout.flush()

    try:
        while True:
            iteration += 1
            elapsed = time.time() - start_time

            # Move cursor back to start of dynamic content (after first iteration)
            if iteration > 1 and lines_printed > 0:
                # Move cursor up by the number of lines we printed
                for _ in range(lines_printed):
                    print(CURSOR_UP, end='')
                sys.stdout.flush()

            # Capture output to count lines
            output_lines = []

            # Header (will be updated each time)
            output_lines.append("=" * 80 + CLEAR_LINE)
            output_lines.append(f"🔄 Continuous Comparison - Iteration #{iteration}" + CLEAR_LINE)
            output_lines.append(f"⏱️  Elapsed time: {int(elapsed // 60)}m {int(elapsed % 60)}s" + CLEAR_LINE)
            output_lines.append(f"🔁 Refresh rate: {cadence} seconds" + CLEAR_LINE)
            output_lines.append("=" * 80 + CLEAR_LINE)

            # Connect to databases and gather information
            db_infos = {}
            connections = {}

            for db in selected_databases:
                db_name = db['name']

                try:
                    # Reuse connection or create new one
                    conn = connect_to_database(db)
                    if not conn:
                        output_lines.append(f"❌ Failed to connect to {db_name}" + CLEAR_LINE)
                        continue

                    connections[db_name] = conn

                    # Get database info (disable progress messages for continuous mode)
                    info = get_database_info(conn, show_progress=False)
                    db_infos[db_name] = info

                except Exception as e:
                    output_lines.append(f"❌ Error analyzing {db_name}: {e}" + CLEAR_LINE)
                    continue

            # Close connections
            for conn in connections.values():
                try:
                    conn.close()
                except:
                    pass

            if len(db_infos) < 2:
                output_lines.append("" + CLEAR_LINE)
                output_lines.append("⚠️  Need at least 2 successfully connected databases" + CLEAR_LINE)
                output_lines.append(f"Retrying in {cadence} seconds..." + CLEAR_LINE)
            else:
                # Build comparison output
                comparison_output = build_comparison_output(db_infos, previous_infos)
                for line in comparison_output:
                    output_lines.append(line + CLEAR_LINE)

                # Store current info for next iteration's delta
                previous_infos = db_infos

            # Status line
            output_lines.append("" + CLEAR_LINE)
            output_lines.append(f"⏳ Next update in {cadence} seconds... (Press Ctrl+C to stop)" + CLEAR_LINE)

            # Print all lines
            for line in output_lines:
                print(line)

            lines_printed = len(output_lines)
            sys.stdout.flush()

            # Wait for next iteration
            time.sleep(cadence)

    except KeyboardInterrupt:
        # Show cursor again
        print(SHOW_CURSOR, end='')
        sys.stdout.flush()

        print("\n\n✅ Continuous comparison stopped by user")
        print(f"📊 Total iterations: {iteration}")
        print(f"⏱️  Total time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
    finally:
        # Ensure cursor is shown even if there's an error
        print(SHOW_CURSOR, end='')
        sys.stdout.flush()

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

    # Ask about comparison mode
    print("\n" + "=" * 80)
    print("📊 Comparison Mode")
    print("=" * 80)
    print("1. Single comparison (one-time)")
    print("2. Continuous comparison (monitor changes)")
    print()

    mode_choice = get_input("Select mode [1-2]", default="1")

    if mode_choice == '2':
        # Continuous mode
        print("\n🔄 Continuous Comparison Mode")
        print("=" * 80)
        cadence = get_number(
            "Refresh interval in seconds",
            min_val=1,
            max_val=3600,
            default=5
        )

        continuous_compare(selected_databases, cadence)
        return

    # Single comparison mode
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
