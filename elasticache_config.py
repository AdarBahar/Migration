#!/usr/bin/env python3
"""
🔧 ElastiCache Configuration Options

This module contains configuration options and utilities for ElastiCache provisioning.
"""

# ElastiCache Node Types and their specifications
ELASTICACHE_NODE_TYPES = {
    # Burstable Performance (T3/T4g)
    'cache.t3.micro': {
        'memory': '0.5 GB',
        'vcpu': '2',
        'network': 'Up to 5 Gbps',
        'cost': 'Lowest',
        'use_case': 'Development, testing, light workloads'
    },
    'cache.t3.small': {
        'memory': '1.37 GB',
        'vcpu': '2',
        'network': 'Up to 5 Gbps',
        'cost': 'Low',
        'use_case': 'Small production workloads'
    },
    'cache.t3.medium': {
        'memory': '3.09 GB',
        'vcpu': '2',
        'network': 'Up to 5 Gbps',
        'cost': 'Low',
        'use_case': 'Medium production workloads'
    },
    'cache.t4g.micro': {
        'memory': '0.5 GB',
        'vcpu': '2',
        'network': 'Up to 5 Gbps',
        'cost': 'Lowest (ARM)',
        'use_case': 'Development, testing (ARM-based)'
    },
    
    # Memory Optimized (R6g/R7g)
    'cache.r6g.large': {
        'memory': '12.32 GB',
        'vcpu': '2',
        'network': 'Up to 10 Gbps',
        'cost': 'Medium',
        'use_case': 'Memory-intensive applications'
    },
    'cache.r6g.xlarge': {
        'memory': '25.05 GB',
        'vcpu': '4',
        'network': 'Up to 10 Gbps',
        'cost': 'Medium-High',
        'use_case': 'Large memory-intensive applications'
    },
    
    # General Purpose (M6g/M7g)
    'cache.m6g.large': {
        'memory': '6.38 GB',
        'vcpu': '2',
        'network': 'Up to 10 Gbps',
        'cost': 'Medium',
        'use_case': 'Balanced compute and memory'
    }
}

# Redis Engine Versions
REDIS_ENGINE_VERSIONS = {
    '7.1': {
        'features': ['Redis Functions', 'ACLs', 'Streams', 'JSON support'],
        'recommended': True,
        'description': 'Latest stable version with all features'
    },
    '7.0': {
        'features': ['Redis Functions', 'ACLs', 'Streams', 'JSON support'],
        'recommended': False,
        'description': 'Stable version with all features'
    },
    '6.2': {
        'features': ['ACLs', 'Streams', 'Modules support'],
        'recommended': False,
        'description': 'Previous stable version'
    },
    '5.0.6': {
        'features': ['Streams', 'Basic functionality'],
        'recommended': False,
        'description': 'Older version for compatibility'
    }
}

# Valkey Engine Versions (Valkey uses different version numbers)
VALKEY_ENGINE_VERSIONS = {
    '7.2.5': {
        'features': ['Valkey Functions', 'ACLs', 'Streams', 'JSON support'],
        'recommended': True,
        'description': 'Latest Valkey version with enhanced features'
    },
    '7.2.4': {
        'features': ['Valkey Functions', 'ACLs', 'Streams', 'JSON support'],
        'recommended': False,
        'description': 'Stable Valkey version'
    },
    '7.0.5': {
        'features': ['ACLs', 'Streams', 'Enhanced performance'],
        'recommended': False,
        'description': 'Older stable Valkey version'
    }
}

# Default configuration
DEFAULT_CONFIG = {
    'node_type': 'cache.t3.micro',
    'engine_version': '7.1',  # Updated to latest Redis version
    'port': 6379,
    'num_cache_nodes': 1,
    'parameter_group_family': 'redis7.x',
    'maintenance_window': 'sun:05:00-sun:06:00',
    'snapshot_retention_limit': 1,
    'snapshot_window': '03:00-04:00'
}

# Valkey-specific default configuration
VALKEY_DEFAULT_CONFIG = {
    'node_type': 'cache.t3.micro',
    'engine_version': '7.2.5',  # Latest supported Valkey version
    'port': 6379,
    'num_cache_nodes': 1,
    'parameter_group_family': 'valkey7.x',
    'maintenance_window': 'sun:05:00-sun:06:00',
    'snapshot_retention_limit': 1,
    'snapshot_window': '03:00-04:00'
}

# Security best practices
SECURITY_RECOMMENDATIONS = {
    'encryption_at_rest': True,
    'encryption_in_transit': False,  # Set to True for production
    'auth_token': False,  # Set to True for production
    'automatic_failover': False,  # Set to True for production clusters
    'multi_az': False  # Set to True for production
}

def get_recommended_config(environment='development', engine='redis'):
    """Get recommended configuration based on environment and engine."""
    base_config = VALKEY_DEFAULT_CONFIG if engine == 'valkey' else DEFAULT_CONFIG

    if environment.lower() == 'production':
        return {
            **base_config,
            'node_type': 'cache.r6g.large',
            'num_cache_nodes': 2,
            'automatic_failover': True,
            'multi_az': True,
            'encryption_at_rest': True,
            'encryption_in_transit': True,
            'auth_token': True,
            'snapshot_retention_limit': 7
        }
    elif environment.lower() == 'staging':
        return {
            **base_config,
            'node_type': 'cache.t3.small',
            'encryption_at_rest': True,
            'snapshot_retention_limit': 3
        }
    else:  # development
        return base_config

def display_node_type_options():
    """Display available node type options."""
    print("\n📊 Available ElastiCache Node Types:")
    print("=" * 80)
    
    for node_type, specs in ELASTICACHE_NODE_TYPES.items():
        print(f"\n🔧 {node_type}")
        print(f"   Memory: {specs['memory']}")
        print(f"   vCPU: {specs['vcpu']}")
        print(f"   Network: {specs['network']}")
        print(f"   Cost: {specs['cost']}")
        print(f"   Use Case: {specs['use_case']}")

def display_engine_versions():
    """Display available Redis engine versions."""
    print("\n🔧 Available Redis Engine Versions:")
    print("=" * 50)
    
    for version, info in REDIS_ENGINE_VERSIONS.items():
        recommended = " (RECOMMENDED)" if info['recommended'] else ""
        print(f"\n📦 Redis {version}{recommended}")
        print(f"   Description: {info['description']}")
        print(f"   Features: {', '.join(info['features'])}")

def validate_node_type(node_type):
    """Validate if the node type is supported."""
    return node_type in ELASTICACHE_NODE_TYPES

def validate_engine_version(version, engine='redis'):
    """Validate if the engine version is supported."""
    if engine == 'valkey':
        return version in VALKEY_ENGINE_VERSIONS
    else:
        return version in REDIS_ENGINE_VERSIONS

def get_cost_estimate(node_type, hours_per_month=730):
    """Get rough cost estimate for a node type (placeholder - actual costs vary by region)."""
    # These are approximate costs and vary by region
    cost_per_hour = {
        'cache.t3.micro': 0.017,
        'cache.t3.small': 0.034,
        'cache.t3.medium': 0.068,
        'cache.t4g.micro': 0.016,
        'cache.r6g.large': 0.151,
        'cache.r6g.xlarge': 0.302,
        'cache.m6g.large': 0.077
    }
    
    if node_type in cost_per_hour:
        monthly_cost = cost_per_hour[node_type] * hours_per_month
        return {
            'hourly': cost_per_hour[node_type],
            'monthly': monthly_cost,
            'currency': 'USD',
            'note': 'Approximate cost - varies by region and usage'
        }
    
    return None

def interactive_config_builder():
    """Interactive configuration builder for ElastiCache."""
    print("\n🔧 ElastiCache Configuration Builder")
    print("=" * 40)
    
    # Environment selection
    print("\n1. Select Environment:")
    print("   1) Development (default)")
    print("   2) Staging")
    print("   3) Production")
    
    env_choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
    environment_map = {"1": "development", "2": "staging", "3": "production"}
    environment = environment_map.get(env_choice, "development")
    
    config = get_recommended_config(environment)
    print(f"\n✅ Selected environment: {environment.title()}")
    
    # Node type selection
    print("\n2. Node Type Selection:")
    display_node_type_options()
    
    node_type = input(f"\nEnter node type [{config['node_type']}]: ").strip() or config['node_type']
    
    if validate_node_type(node_type):
        config['node_type'] = node_type
        
        # Show cost estimate
        cost_info = get_cost_estimate(node_type)
        if cost_info:
            print(f"\n💰 Estimated cost for {node_type}:")
            print(f"   Hourly: ${cost_info['hourly']:.3f}")
            print(f"   Monthly: ${cost_info['monthly']:.2f}")
            print(f"   Note: {cost_info['note']}")
    else:
        print(f"⚠️  Invalid node type, using default: {config['node_type']}")
    
    # Engine version selection
    print("\n3. Redis Engine Version:")
    display_engine_versions()
    
    engine_version = input(f"\nEnter engine version [{config['engine_version']}]: ").strip() or config['engine_version']
    
    if validate_engine_version(engine_version):
        config['engine_version'] = engine_version
    else:
        print(f"⚠️  Invalid engine version, using default: {config['engine_version']}")
    
    print(f"\n✅ Configuration complete!")
    print(f"📋 Final configuration:")
    print(f"   Environment: {environment}")
    print(f"   Node Type: {config['node_type']}")
    print(f"   Engine Version: {config['engine_version']}")
    print(f"   Port: {config['port']}")
    
    return config

if __name__ == "__main__":
    # Demo the configuration builder
    config = interactive_config_builder()
    print(f"\n📄 Generated configuration: {config}")
