#!/usr/bin/env python3
"""
🎯 Redis Migration Control Center

This is the main interface for managing Redis migration operations.
It provides intelligent suggestions based on current environment state
and allows easy access to all migration tools.

Author: Migration Project
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime


class MigrationControlCenter:
    def __init__(self):
        """Initialize the Migration Control Center."""
        self.scripts = {
            '1': {
                'name': 'Provision ElastiCache',
                'script': 'provision_elasticache.py',
                'description': 'Create AWS ElastiCache Redis instance',
                'category': 'setup'
            },
            '2': {
                'name': 'Manage Environment',
                'script': 'manage_env.py',
                'description': 'Configure Redis connection settings',
                'category': 'setup'
            },
            '3': {
                'name': 'Generate Test Data',
                'script': 'DataFaker.py',
                'description': 'Create sample data for migration testing',
                'category': 'data'
            },
            '4': {
                'name': 'Compare Databases',
                'script': 'DB_compare.py',
                'description': 'Compare source and destination Redis instances',
                'category': 'migration'
            },
            '5': {
                'name': 'Migration Operations',
                'script': 'ReadWriteOps.py',
                'description': 'Perform read/write operations and migration',
                'category': 'migration'
            },
            '6': {
                'name': 'Flush Database',
                'script': 'flushDBData.py',
                'description': 'Clear all data from Redis database',
                'category': 'maintenance'
            },
            '7': {
                'name': 'Cleanup ElastiCache',
                'script': 'cleanup_elasticache.py',
                'description': 'Remove ElastiCache instances and resources',
                'category': 'maintenance'
            },
            '8': {
                'name': 'Network Troubleshooting',
                'script': 'network_troubleshoot.py',
                'description': 'Diagnose network connectivity issues',
                'category': 'troubleshooting'
            },
            '9': {
                'name': 'Test Security Config',
                'script': 'test_security_config.py',
                'description': 'Test ElastiCache security configuration',
                'category': 'troubleshooting'
            }
        }
        
        self.categories = {
            'setup': '🚀 Setup & Configuration',
            'data': '📊 Data Management',
            'migration': '🔄 Migration Operations',
            'maintenance': '🧹 Maintenance',
            'troubleshooting': '🔧 Troubleshooting'
        }

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print the main header."""
        print("=" * 80)
        print("🎯 Redis Migration Control Center")
        print("=" * 80)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Show environment status
        env_status = "✅ Configured" if self.check_env_file() else "❌ Not configured"
        elasticache_status = "✅ Available" if self.check_elasticache_instance() else "❌ Not found"

        print(f"🔧 Environment: {env_status} | ☁️  ElastiCache: {elasticache_status}")
        print()

    def check_environment_status(self):
        """Check the current environment status and provide suggestions."""
        suggestions = []
        
        # Check if .env file exists and has content
        env_configured = self.check_env_file()
        if not env_configured:
            suggestions.append({
                'priority': 'high',
                'message': 'Environment not configured',
                'action': 'Run option 2 (Manage Environment) to configure Redis connections',
                'script': '2'
            })
        
        # Check if ElastiCache instance exists
        elasticache_exists = self.check_elasticache_instance()
        if not elasticache_exists:
            suggestions.append({
                'priority': 'high',
                'message': 'No ElastiCache instance found',
                'action': 'Run option 1 (Provision ElastiCache) to create Redis instance',
                'script': '1'
            })
        
        # Check if source Redis has data
        if env_configured and elasticache_exists:
            has_data = self.check_redis_data()
            if not has_data:
                suggestions.append({
                    'priority': 'medium',
                    'message': 'No test data found in source Redis',
                    'action': 'Run option 3 (Generate Test Data) to create sample data',
                    'script': '3'
                })
        
        return suggestions

    def check_env_file(self):
        """Check if .env file is properly configured."""
        if not os.path.exists('.env'):
            return False

        try:
            with open('.env', 'r') as f:
                lines = f.readlines()

            # Parse environment variables
            env_vars = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

            # Check if essential variables are set and not empty
            required_vars = ['REDIS_SOURCE_HOST', 'REDIS_DEST_HOST']
            for var in required_vars:
                if var not in env_vars or not env_vars[var]:
                    return False

            return True
        except Exception:
            return False

    def check_elasticache_instance(self):
        """Check if ElastiCache instance exists."""
        try:
            # Look for ElastiCache info files
            elasticache_files = [f for f in os.listdir('.') if f.startswith('elasticache_') and f.endswith('.json')]
            if elasticache_files:
                # Check the most recent file for valid configuration
                latest_file = max(elasticache_files, key=os.path.getmtime)
                with open(latest_file, 'r') as f:
                    config = json.load(f)
                    # Check if it has required fields
                    if 'endpoint' in config and 'port' in config:
                        return True
            return False
        except Exception:
            return False

    def check_redis_data(self):
        """Check if Redis instance has data."""
        try:
            # This is a simplified check - could be enhanced with actual Redis connection
            # For now, assume if env is configured, we can check data
            return False  # Default to suggesting data generation
        except Exception:
            return False

    def display_suggestions(self, suggestions):
        """Display intelligent suggestions based on environment state."""
        if not suggestions:
            print("✅ Environment looks good! All systems ready.")
            print()
            return
        
        print("💡 Intelligent Suggestions:")
        print("-" * 40)
        
        for i, suggestion in enumerate(suggestions, 1):
            priority_icon = "🔴" if suggestion['priority'] == 'high' else "🟡"
            print(f"{priority_icon} {suggestion['message']}")
            print(f"   👉 {suggestion['action']}")
            print()

    def display_menu(self):
        """Display the main menu organized by categories."""
        print("📋 Available Operations:")
        print("-" * 40)
        
        for category_key, category_name in self.categories.items():
            print(f"\n{category_name}")
            for script_key, script_info in self.scripts.items():
                if script_info['category'] == category_key:
                    print(f"  {script_key}. {script_info['name']}")
                    print(f"     {script_info['description']}")
        
        print(f"\n🚪 Other Options:")
        print(f"  h. Help & Documentation")
        print(f"  q. Quit")
        print()

    def run_script(self, script_path):
        """Run a Python script and return to the menu."""
        if not os.path.exists(script_path):
            print(f"❌ Script not found: {script_path}")
            input("Press Enter to continue...")
            return
        
        print(f"🚀 Launching {script_path}...")
        print("=" * 60)
        
        try:
            # Run the script and wait for completion
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=False, 
                                  text=True)
            
            print("=" * 60)
            if result.returncode == 0:
                print(f"✅ {script_path} completed successfully")
            else:
                print(f"⚠️  {script_path} completed with exit code {result.returncode}")
                
        except KeyboardInterrupt:
            print(f"\n⚠️  {script_path} interrupted by user")
        except Exception as e:
            print(f"❌ Error running {script_path}: {e}")
        
        print()
        input("Press Enter to return to the main menu...")

    def show_help(self):
        """Show help and documentation links."""
        self.clear_screen()
        print("📚 Help & Documentation")
        print("=" * 40)
        print()
        print("📖 Available Documentation:")
        print("  • README.md - Project overview and quick start")
        print("  • Help_docs/WALKTHROUGH.md - Complete step-by-step guide")
        print("  • Help_docs/TROUBLESHOOTING.md - Problem resolution")
        print("  • Help_docs/ELASTICACHE_README.md - ElastiCache details")
        print()
        print("🔗 Quick Links:")
        print("  • GitHub Repository: https://github.com/AdarBahar/Migration")
        print("  • AWS ElastiCache Documentation")
        print("  • Redis Documentation")
        print()
        print("💡 Getting Started:")
        print("  1. If this is your first time, start with option 1 (Provision ElastiCache)")
        print("  2. Configure your environment with option 2 (Manage Environment)")
        print("  3. Generate test data with option 3 (Generate Test Data)")
        print("  4. Test your setup with option 4 (Compare Databases)")
        print()
        input("Press Enter to return to the main menu...")

    def main_loop(self):
        """Main application loop."""
        while True:
            self.clear_screen()
            self.print_header()
            
            # Check environment and show suggestions
            suggestions = self.check_environment_status()
            self.display_suggestions(suggestions)
            
            # Show menu
            self.display_menu()
            
            # Get user choice
            choice = input("Enter your choice: ").strip().lower()
            
            if choice == 'q':
                print("\n👋 Thank you for using Redis Migration Tool!")
                print("🚀 Happy migrating!")
                break
            elif choice == 'h':
                self.show_help()
            elif choice in self.scripts:
                script_info = self.scripts[choice]
                self.run_script(script_info['script'])
            else:
                print(f"\n❌ Invalid choice: {choice}")
                print("Please select a valid option from the menu.")
                input("Press Enter to continue...")


def main():
    """Main function."""
    try:
        control_center = MigrationControlCenter()
        control_center.main_loop()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the logs and try again.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
