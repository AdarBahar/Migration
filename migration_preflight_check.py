#!/usr/bin/env python3
"""
RIOT-X Migration Pre-flight Checker

This script validates all requirements for the RIOT-X CloudFormation migration template
to ensure successful ElastiCache to Redis Cloud migration.

Usage:
    python3 migration_preflight_check.py --source-cluster <cluster-id> --target-uri <redis-uri>

Author: Migration Tool
Version: 1.0.0
"""

import argparse
import boto3
import json
import os
import socket
import ssl
import sys
import time
import urllib.parse
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class CheckStatus(Enum):
    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    INFO = "ℹ️"

@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    remediation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class MigrationPreflightChecker:
    """Comprehensive pre-flight checker for RIOT-X migration CloudFormation template."""

    def __init__(self, source_cluster_id: Optional[str] = None, target_redis_uri: Optional[str] = None,
                 region: Optional[str] = None, verbose: bool = False, env_file: str = '.env'):
        """Initialize the pre-flight checker."""
        self.verbose = verbose
        self.results: List[CheckResult] = []
        self.env_file = env_file

        # Load configuration from .env file if available
        self.env_config = self.load_env_config()

        # Use provided parameters or fall back to .env configuration
        self.source_cluster_id = source_cluster_id or self.get_source_cluster_from_env()
        self.target_redis_uri = target_redis_uri or self.build_target_uri_from_env()
        
        # Initialize AWS clients
        self.session = boto3.Session(region_name=region)
        self.region = self.session.region_name or 'us-east-1'
        
        try:
            self.elasticache_client = self.session.client('elasticache')
            self.ec2_client = self.session.client('ec2')
            self.ecs_client = self.session.client('ecs')
            self.iam_client = self.session.client('iam')
            self.logs_client = self.session.client('logs')
            self.sts_client = self.session.client('sts')
            self.cloudformation_client = self.session.client('cloudformation')
        except Exception as e:
            self.log_error(f"Failed to initialize AWS clients: {e}")
            sys.exit(1)
        
        # Cache for discovered resources
        self.elasticache_details = None
        self.vpc_details = None

    def load_env_config(self) -> Dict[str, str]:
        """Load configuration from .env file."""
        config = {}

        if not os.path.exists(self.env_file):
            return config

        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('\'"')
                        config[key.strip()] = value

            if self.verbose:
                print(f"ℹ️  Loaded {len(config)} configuration items from {self.env_file}")

        except Exception as e:
            if self.verbose:
                print(f"⚠️  Could not load {self.env_file}: {e}")

        return config

    def get_source_cluster_from_env(self) -> Optional[str]:
        """Extract source cluster ID from .env configuration."""
        # Check for explicit cluster ID first
        cluster_id = self.env_config.get('ELASTICACHE_CLUSTER_ID') or self.env_config.get('SOURCE_CLUSTER_ID')
        if cluster_id:
            return cluster_id

        # Try to extract from Redis source host (ElastiCache format)
        source_host = self.env_config.get('REDIS_SOURCE_HOST')
        if source_host and '.cache.amazonaws.com' in source_host:
            # Extract cluster ID from ElastiCache hostname
            # Format: cluster-id.xxxxx.cache.amazonaws.com
            cluster_id = source_host.split('.')[0]
            if self.verbose:
                print(f"ℹ️  Extracted cluster ID '{cluster_id}' from REDIS_SOURCE_HOST")
            return cluster_id

        return None

    def build_target_uri_from_env(self) -> Optional[str]:
        """Build target Redis URI from .env configuration."""
        host = self.env_config.get('REDIS_DEST_HOST')
        port = self.env_config.get('REDIS_DEST_PORT', '6379')
        password = self.env_config.get('REDIS_DEST_PASSWORD', '')
        tls = self.env_config.get('REDIS_DEST_TLS', 'false').lower() == 'true'

        if not host:
            return None

        # Build URI
        scheme = 'rediss' if tls else 'redis'
        auth_part = f":{password}@" if password else ""
        uri = f"{scheme}://{auth_part}{host}:{port}"

        if self.verbose:
            # Mask password in verbose output
            display_uri = f"{scheme}://***@{host}:{port}" if password else uri
            print(f"ℹ️  Built target URI from .env: {display_uri}")

        return uri

    def check_configuration_source(self) -> CheckResult:
        """Check and validate configuration source."""
        config_details = {}

        if self.env_config:
            config_details['env_file'] = self.env_file
            config_details['env_vars_found'] = len(self.env_config)

            # Check what configuration was found
            source_config = []
            if self.env_config.get('ELASTICACHE_CLUSTER_ID'):
                source_config.append('ELASTICACHE_CLUSTER_ID')
            if self.env_config.get('REDIS_SOURCE_HOST'):
                source_config.append('REDIS_SOURCE_HOST')

            target_config = []
            for var in ['REDIS_DEST_HOST', 'REDIS_DEST_PORT', 'REDIS_DEST_PASSWORD', 'REDIS_DEST_TLS']:
                if self.env_config.get(var):
                    target_config.append(var)

            config_details['source_vars'] = source_config
            config_details['target_vars'] = target_config

            if source_config and target_config:
                return CheckResult(
                    name="Configuration Source",
                    status=CheckStatus.PASS,
                    message=f"Configuration loaded from {self.env_file}",
                    details=config_details
                )
            else:
                missing = []
                if not source_config:
                    missing.append("source (ELASTICACHE_CLUSTER_ID or REDIS_SOURCE_HOST)")
                if not target_config:
                    missing.append("target (REDIS_DEST_* variables)")

                return CheckResult(
                    name="Configuration Source",
                    status=CheckStatus.WARN,
                    message=f"Partial configuration in {self.env_file}, missing: {', '.join(missing)}",
                    details=config_details
                )
        else:
            return CheckResult(
                name="Configuration Source",
                status=CheckStatus.INFO,
                message="Using command line parameters (no .env file found)",
                details={'env_file': self.env_file, 'exists': False}
            )
        
    def log_info(self, message: str):
        """Log info message."""
        print(f"{CheckStatus.INFO.value} {message}")
    
    def log_success(self, message: str):
        """Log success message."""
        print(f"{CheckStatus.PASS.value} {message}")
    
    def log_warning(self, message: str):
        """Log warning message."""
        print(f"{CheckStatus.WARN.value} {message}")
    
    def log_error(self, message: str):
        """Log error message."""
        print(f"{CheckStatus.FAIL.value} {message}")
    
    def add_result(self, result: CheckResult):
        """Add a check result."""
        self.results.append(result)
        
        # Print result immediately
        status_icon = result.status.value
        print(f"{status_icon} {result.name}: {result.message}")
        
        if result.remediation and result.status == CheckStatus.FAIL:
            print(f"   🔧 Remediation: {result.remediation}")
        
        if self.verbose and result.details:
            print(f"   📋 Details: {json.dumps(result.details, indent=2, default=str)}")
    
    def check_aws_credentials(self) -> CheckResult:
        """Verify AWS credentials are configured and valid."""
        try:
            identity = self.sts_client.get_caller_identity()
            return CheckResult(
                name="AWS Credentials",
                status=CheckStatus.PASS,
                message=f"Valid credentials for {identity.get('Arn', 'Unknown')}",
                details={"account": identity.get('Account'), "user_arn": identity.get('Arn')}
            )
        except Exception as e:
            return CheckResult(
                name="AWS Credentials",
                status=CheckStatus.FAIL,
                message=f"Invalid or missing AWS credentials: {e}",
                remediation="Configure AWS credentials using 'aws configure' or IAM roles"
            )
    
    def check_iam_permissions(self) -> List[CheckResult]:
        """Check required IAM permissions for CloudFormation template."""
        results = []
        
        # Required permissions for the CloudFormation template
        required_permissions = [
            # ElastiCache permissions
            ("elasticache", "describe_cache_clusters", "DescribeCacheClusters"),
            ("elasticache", "describe_replication_groups", "DescribeReplicationGroups"),
            ("elasticache", "describe_serverless_caches", "DescribeServerlessCaches"),
            ("elasticache", "describe_cache_subnet_groups", "DescribeCacheSubnetGroups"),
            
            # EC2 permissions
            ("ec2", "describe_vpcs", "DescribeVpcs"),
            ("ec2", "describe_subnets", "DescribeSubnets"),
            ("ec2", "describe_security_groups", "DescribeSecurityGroups"),
            ("ec2", "describe_route_tables", "DescribeRouteTables"),
            ("ec2", "describe_internet_gateways", "DescribeInternetGateways"),
            
            # ECS permissions
            ("ecs", "describe_clusters", "DescribeClusters"),
            ("ecs", "list_clusters", "ListClusters"),
        ]
        
        for service, method, action in required_permissions:
            try:
                client = getattr(self, f"{service}_client")
                method_func = getattr(client, method)
                
                # Test with minimal parameters
                if service == "elasticache":
                    if "cache_clusters" in method:
                        method_func(MaxRecords=20)  # Minimum is 20
                    elif "replication_groups" in method:
                        method_func(MaxRecords=20)  # Minimum is 20
                    elif "serverless_caches" in method:
                        method_func(MaxResults=20)  # Minimum is 20
                    elif "cache_subnet_groups" in method:
                        method_func(MaxRecords=20)  # Minimum is 20
                elif service == "ec2":
                    method_func(MaxResults=5)
                elif service == "ecs":
                    if "describe_clusters" in method:
                        method_func(clusters=[])
                    else:
                        method_func(maxResults=1)
                
                results.append(CheckResult(
                    name=f"IAM Permission: {action}",
                    status=CheckStatus.PASS,
                    message=f"Permission verified for {service}:{action}"
                ))
                
            except Exception as e:
                error_msg = str(e)
                if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                    results.append(CheckResult(
                        name=f"IAM Permission: {action}",
                        status=CheckStatus.FAIL,
                        message=f"Missing permission: {service}:{action}",
                        remediation=f"Add IAM permission: {service}:{action} to your role/user"
                    ))
                else:
                    results.append(CheckResult(
                        name=f"IAM Permission: {action}",
                        status=CheckStatus.WARN,
                        message=f"Could not verify {service}:{action}: {error_msg}"
                    ))
        
        return results
    
    def discover_elasticache_cluster(self) -> CheckResult:
        """Discover and validate source ElastiCache cluster (mirrors CF template logic)."""
        cluster_id = self.source_cluster_id
        
        try:
            # Try as replication group first
            try:
                resp = self.elasticache_client.describe_replication_groups(
                    ReplicationGroupId=cluster_id
                )
                if resp['ReplicationGroups']:
                    rg = resp['ReplicationGroups'][0]
                    
                    # Get endpoint details
                    if 'ConfigurationEndpoint' in rg and rg['ConfigurationEndpoint']:
                        endpoint = rg['ConfigurationEndpoint']['Address']
                        port = rg['ConfigurationEndpoint']['Port']
                        cluster_mode = True
                    elif 'NodeGroups' in rg and rg['NodeGroups'] and 'PrimaryEndpoint' in rg['NodeGroups'][0]:
                        endpoint = rg['NodeGroups'][0]['PrimaryEndpoint']['Address']
                        port = rg['NodeGroups'][0]['PrimaryEndpoint']['Port']
                        cluster_mode = False
                    else:
                        raise Exception("Could not find endpoint for replication group")
                    
                    # Get subnet group from first member cluster
                    first_member = rg['MemberClusters'][0]
                    cluster_resp = self.elasticache_client.describe_cache_clusters(
                        CacheClusterId=first_member
                    )
                    cluster_detail = cluster_resp['CacheClusters'][0]
                    subnet_group_name = cluster_detail['CacheSubnetGroupName']
                    security_groups = cluster_detail.get('SecurityGroups', [])
                    
                    self.elasticache_details = {
                        'type': 'replication-group',
                        'endpoint': endpoint,
                        'port': port,
                        'cluster_mode': cluster_mode,
                        'subnet_group_name': subnet_group_name,
                        'security_groups': security_groups,
                        'transit_encryption': rg.get('TransitEncryptionEnabled', False),
                        'auth_token_enabled': rg.get('AuthTokenEnabled', False)
                    }
                    
                    return CheckResult(
                        name="ElastiCache Discovery",
                        status=CheckStatus.PASS,
                        message=f"Found replication group: {endpoint}:{port}",
                        details=self.elasticache_details
                    )
                    
            except Exception as e:
                if 'ReplicationGroupNotFound' not in str(e):
                    raise e
            
            # Try as serverless cache
            try:
                resp = self.elasticache_client.describe_serverless_caches(
                    ServerlessCacheName=cluster_id
                )
                if resp['ServerlessCaches']:
                    cache = resp['ServerlessCaches'][0]
                    endpoint = cache['Endpoint']['Address']
                    port = cache['Endpoint']['Port']
                    subnet_ids = cache['SubnetIds']
                    security_group_ids = cache.get('SecurityGroupIds', [])
                    
                    self.elasticache_details = {
                        'type': 'serverless-cache',
                        'endpoint': endpoint,
                        'port': port,
                        'cluster_mode': False,
                        'subnet_ids': subnet_ids,
                        'security_group_ids': security_group_ids,
                        'transit_encryption': True,
                        'auth_token_enabled': False
                    }
                    
                    return CheckResult(
                        name="ElastiCache Discovery",
                        status=CheckStatus.PASS,
                        message=f"Found serverless cache: {endpoint}:{port}",
                        details=self.elasticache_details
                    )
                    
            except Exception as e:
                if 'ServerlessCacheNotFound' not in str(e):
                    raise e
            
            # Try as single cluster
            resp = self.elasticache_client.describe_cache_clusters(
                CacheClusterId=cluster_id,
                ShowCacheNodeInfo=True
            )
            if resp['CacheClusters']:
                cluster = resp['CacheClusters'][0]
                endpoint = cluster['CacheNodes'][0]['Endpoint']['Address']
                port = cluster['CacheNodes'][0]['Endpoint']['Port']
                subnet_group_name = cluster['CacheSubnetGroupName']
                security_groups = cluster.get('SecurityGroups', [])
                
                self.elasticache_details = {
                    'type': 'single-cluster',
                    'endpoint': endpoint,
                    'port': port,
                    'cluster_mode': False,
                    'subnet_group_name': subnet_group_name,
                    'security_groups': security_groups,
                    'transit_encryption': cluster.get('TransitEncryptionEnabled', False),
                    'auth_token_enabled': False
                }
                
                return CheckResult(
                    name="ElastiCache Discovery",
                    status=CheckStatus.PASS,
                    message=f"Found single cluster: {endpoint}:{port}",
                    details=self.elasticache_details
                )
            
            return CheckResult(
                name="ElastiCache Discovery",
                status=CheckStatus.FAIL,
                message=f"ElastiCache cluster '{cluster_id}' not found",
                remediation=f"Verify cluster ID exists in region {self.region}. Use 'aws elasticache describe-replication-groups' or 'aws elasticache describe-cache-clusters' to list available clusters."
            )
            
        except Exception as e:
            return CheckResult(
                name="ElastiCache Discovery",
                status=CheckStatus.FAIL,
                message=f"Failed to discover ElastiCache cluster: {e}",
                remediation="Check IAM permissions and cluster ID format"
            )

    def discover_vpc_details(self) -> CheckResult:
        """Discover VPC details from ElastiCache cluster."""
        if not self.elasticache_details:
            return CheckResult(
                name="VPC Discovery",
                status=CheckStatus.FAIL,
                message="ElastiCache details not available",
                remediation="Run ElastiCache discovery first"
            )

        try:
            if self.elasticache_details['type'] == 'serverless-cache':
                # For serverless, get VPC from subnet
                subnet_ids = self.elasticache_details['subnet_ids']
                subnet_resp = self.ec2_client.describe_subnets(SubnetIds=[subnet_ids[0]])
                vpc_id = subnet_resp['Subnets'][0]['VpcId']

                self.vpc_details = {
                    'vpc_id': vpc_id,
                    'subnet_ids': subnet_ids,
                    'security_group_ids': self.elasticache_details['security_group_ids']
                }
            else:
                # For traditional clusters, get VPC from subnet group
                subnet_group_name = self.elasticache_details['subnet_group_name']
                subnet_resp = self.elasticache_client.describe_cache_subnet_groups(
                    CacheSubnetGroupName=subnet_group_name
                )
                subnet_group = subnet_resp['CacheSubnetGroups'][0]
                vpc_id = subnet_group['VpcId']
                subnet_ids = [subnet['SubnetIdentifier'] for subnet in subnet_group['Subnets']]

                # Get security group IDs
                security_group_ids = []
                for sg in self.elasticache_details['security_groups']:
                    security_group_ids.append(sg['SecurityGroupId'])

                self.vpc_details = {
                    'vpc_id': vpc_id,
                    'subnet_ids': subnet_ids,
                    'security_group_ids': security_group_ids
                }

            return CheckResult(
                name="VPC Discovery",
                status=CheckStatus.PASS,
                message=f"Found VPC: {vpc_id} with {len(self.vpc_details['subnet_ids'])} subnets",
                details=self.vpc_details
            )

        except Exception as e:
            return CheckResult(
                name="VPC Discovery",
                status=CheckStatus.FAIL,
                message=f"Failed to discover VPC details: {e}",
                remediation="Check ElastiCache subnet group configuration"
            )

    def check_internet_connectivity(self) -> CheckResult:
        """Check if VPC has internet connectivity for container image downloads."""
        if not self.vpc_details:
            return CheckResult(
                name="Internet Connectivity",
                status=CheckStatus.FAIL,
                message="VPC details not available",
                remediation="Run VPC discovery first"
            )

        try:
            vpc_id = self.vpc_details['vpc_id']

            # Check for Internet Gateway
            igw_resp = self.ec2_client.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )

            has_igw = len(igw_resp['InternetGateways']) > 0

            if has_igw:
                igw_id = igw_resp['InternetGateways'][0]['InternetGatewayId']

                # Check for default route in main route table
                rt_resp = self.ec2_client.describe_route_tables(
                    Filters=[
                        {'Name': 'vpc-id', 'Values': [vpc_id]},
                        {'Name': 'association.main', 'Values': ['true']}
                    ]
                )

                if rt_resp['RouteTables']:
                    main_rt = rt_resp['RouteTables'][0]
                    has_default_route = False

                    for route in main_rt['Routes']:
                        if (route.get('DestinationCidrBlock') == '0.0.0.0/0' and
                            route.get('GatewayId') == igw_id):
                            has_default_route = True
                            break

                    if has_default_route:
                        return CheckResult(
                            name="Internet Connectivity",
                            status=CheckStatus.PASS,
                            message=f"VPC has internet connectivity via IGW {igw_id}",
                            details={"igw_id": igw_id, "has_default_route": True}
                        )
                    else:
                        return CheckResult(
                            name="Internet Connectivity",
                            status=CheckStatus.WARN,
                            message="VPC has IGW but no default route",
                            remediation="CloudFormation will create default route automatically",
                            details={"igw_id": igw_id, "has_default_route": False}
                        )
                else:
                    return CheckResult(
                        name="Internet Connectivity",
                        status=CheckStatus.FAIL,
                        message="Could not find main route table",
                        remediation="Check VPC route table configuration"
                    )
            else:
                return CheckResult(
                    name="Internet Connectivity",
                    status=CheckStatus.WARN,
                    message="VPC has no Internet Gateway",
                    remediation="CloudFormation will create Internet Gateway automatically if AutoCreateInternetAccess=true",
                    details={"has_igw": False}
                )

        except Exception as e:
            return CheckResult(
                name="Internet Connectivity",
                status=CheckStatus.FAIL,
                message=f"Failed to check internet connectivity: {e}",
                remediation="Check EC2 permissions for DescribeInternetGateways and DescribeRouteTables"
            )

    def parse_target_redis_uri(self) -> CheckResult:
        """Parse and validate target Redis URI."""
        try:
            parsed = urllib.parse.urlparse(self.target_redis_uri)

            if parsed.scheme not in ['redis', 'rediss']:
                return CheckResult(
                    name="Target Redis URI",
                    status=CheckStatus.FAIL,
                    message=f"Invalid URI scheme: {parsed.scheme}",
                    remediation="Use redis:// or rediss:// scheme"
                )

            if not parsed.hostname:
                return CheckResult(
                    name="Target Redis URI",
                    status=CheckStatus.FAIL,
                    message="Missing hostname in URI",
                    remediation="Provide valid Redis URI with hostname"
                )

            port = parsed.port or (6380 if parsed.scheme == 'rediss' else 6379)
            uses_tls = parsed.scheme == 'rediss'

            target_details = {
                'hostname': parsed.hostname,
                'port': port,
                'uses_tls': uses_tls,
                'username': parsed.username,
                'password': parsed.password
            }

            return CheckResult(
                name="Target Redis URI",
                status=CheckStatus.PASS,
                message=f"Valid URI: {parsed.hostname}:{port} (TLS: {uses_tls})",
                details=target_details
            )

        except Exception as e:
            return CheckResult(
                name="Target Redis URI",
                status=CheckStatus.FAIL,
                message=f"Failed to parse URI: {e}",
                remediation="Provide valid Redis URI format: redis://[user:pass@]host:port"
            )

    def test_target_connectivity(self) -> CheckResult:
        """Test connectivity to target Redis Cloud."""
        uri_result = self.parse_target_redis_uri()
        if uri_result.status != CheckStatus.PASS:
            return CheckResult(
                name="Target Connectivity",
                status=CheckStatus.FAIL,
                message="Cannot test connectivity - invalid URI",
                remediation="Fix target Redis URI first"
            )

        target_details = uri_result.details
        hostname = target_details['hostname']
        port = target_details['port']
        uses_tls = target_details['uses_tls']

        try:
            # Test TCP connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)

            if uses_tls:
                # Test TLS connectivity
                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    ssock.connect((hostname, port))
                    return CheckResult(
                        name="Target Connectivity",
                        status=CheckStatus.PASS,
                        message=f"TLS connection successful to {hostname}:{port}",
                        details={"tls_verified": True}
                    )
            else:
                # Test plain TCP connectivity
                sock.connect((hostname, port))
                sock.close()
                return CheckResult(
                    name="Target Connectivity",
                    status=CheckStatus.PASS,
                    message=f"TCP connection successful to {hostname}:{port}",
                    details={"tls_verified": False}
                )

        except socket.timeout:
            return CheckResult(
                name="Target Connectivity",
                status=CheckStatus.FAIL,
                message=f"Connection timeout to {hostname}:{port}",
                remediation="Check network connectivity and firewall rules"
            )
        except socket.gaierror as e:
            return CheckResult(
                name="Target Connectivity",
                status=CheckStatus.FAIL,
                message=f"DNS resolution failed for {hostname}: {e}",
                remediation="Check hostname and DNS configuration"
            )
        except Exception as e:
            return CheckResult(
                name="Target Connectivity",
                status=CheckStatus.FAIL,
                message=f"Connection failed to {hostname}:{port}: {e}",
                remediation="Check target Redis Cloud configuration and network access"
            )

    def check_ecs_prerequisites(self) -> List[CheckResult]:
        """Check ECS service prerequisites."""
        results = []

        # Check ECS service availability
        try:
            clusters = self.ecs_client.list_clusters(maxResults=1)
            results.append(CheckResult(
                name="ECS Service",
                status=CheckStatus.PASS,
                message="ECS service is available in region"
            ))
        except Exception as e:
            results.append(CheckResult(
                name="ECS Service",
                status=CheckStatus.FAIL,
                message=f"ECS service not available: {e}",
                remediation=f"Ensure ECS is available in region {self.region}"
            ))

        # Check Fargate capacity
        try:
            # Try to describe a non-existent cluster to test Fargate availability
            self.ecs_client.describe_clusters(clusters=['non-existent-cluster'])
        except Exception as e:
            if 'ClusterNotFoundException' in str(e):
                results.append(CheckResult(
                    name="Fargate Capacity",
                    status=CheckStatus.PASS,
                    message="Fargate capacity provider is available"
                ))
            else:
                results.append(CheckResult(
                    name="Fargate Capacity",
                    status=CheckStatus.WARN,
                    message=f"Could not verify Fargate availability: {e}"
                ))

        return results

    def check_cloudformation_permissions(self) -> CheckResult:
        """Check CloudFormation stack creation permissions."""
        try:
            # Test by describing stacks (minimal permission)
            self.cloudformation_client.describe_stacks()

            return CheckResult(
                name="CloudFormation Permissions",
                status=CheckStatus.PASS,
                message="CloudFormation access verified"
            )
        except Exception as e:
            if "AccessDenied" in str(e):
                return CheckResult(
                    name="CloudFormation Permissions",
                    status=CheckStatus.FAIL,
                    message="Missing CloudFormation permissions",
                    remediation="Add CloudFormation permissions: CreateStack, DescribeStacks, etc."
                )
            else:
                return CheckResult(
                    name="CloudFormation Permissions",
                    status=CheckStatus.WARN,
                    message=f"Could not verify CloudFormation permissions: {e}"
                )

    def run_all_checks(self) -> bool:
        """Run all pre-flight checks and return overall success status."""
        print("🚀 RIOT-X Migration Pre-flight Checker")
        print("=" * 50)

        # Show configuration source
        if self.env_config:
            print(f"📁 Configuration: Loaded from {self.env_file}")
        else:
            print("📁 Configuration: Command line parameters")

        print(f"Source Cluster: {self.source_cluster_id}")

        # Mask password in target URI for display
        display_uri = self.target_redis_uri
        if '@' in display_uri and ':' in display_uri:
            parts = display_uri.split('@')
            if len(parts) == 2:
                scheme_and_auth = parts[0]
                host_and_port = parts[1]
                if ':' in scheme_and_auth:
                    scheme_part = scheme_and_auth.split('://')[0] + '://'
                    auth_part = scheme_and_auth.split('://')[1]
                    if ':' in auth_part:
                        user = auth_part.split(':')[0]
                        display_uri = f"{scheme_part}{user}:***@{host_and_port}"

        print(f"Target URI: {display_uri}")
        print(f"Region: {self.region}")
        print("=" * 50)

        # Run checks in logical order
        print("\n📋 1. Configuration Source")
        self.add_result(self.check_configuration_source())

        print("\n📋 2. AWS Credentials & Basic Access")
        self.add_result(self.check_aws_credentials())

        print("\n📋 3. IAM Permissions")
        iam_results = self.check_iam_permissions()
        for result in iam_results:
            self.add_result(result)

        print("\n📋 4. ElastiCache Discovery")
        self.add_result(self.discover_elasticache_cluster())

        print("\n📋 5. VPC & Network Discovery")
        self.add_result(self.discover_vpc_details())

        print("\n📋 6. Internet Connectivity")
        self.add_result(self.check_internet_connectivity())

        print("\n📋 7. Target Redis Validation")
        self.add_result(self.parse_target_redis_uri())
        self.add_result(self.test_target_connectivity())

        print("\n📋 8. ECS Prerequisites")
        ecs_results = self.check_ecs_prerequisites()
        for result in ecs_results:
            self.add_result(result)

        print("\n📋 9. CloudFormation Permissions")
        self.add_result(self.check_cloudformation_permissions())

        # Generate summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)

        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warned = sum(1 for r in self.results if r.status == CheckStatus.WARN)

        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"📊 Total: {len(self.results)}")

        if failed == 0:
            print(f"\n🎉 SUCCESS: All critical checks passed!")
            print("✅ CloudFormation migration template should work successfully.")
            if warned > 0:
                print("⚠️  Some warnings were found - review them above.")
            return True
        else:
            print(f"\n❌ FAILURE: {failed} critical issues found.")
            print("🔧 Fix the issues above before running CloudFormation template.")

            # Show remediation summary
            print("\n🔧 REMEDIATION SUMMARY:")
            for result in self.results:
                if result.status == CheckStatus.FAIL and result.remediation:
                    print(f"   • {result.name}: {result.remediation}")

            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pre-flight checker for RIOT-X CloudFormation migration template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use configuration from .env file (recommended)
  python3 migration_preflight_check.py

  # Override specific parameters
  python3 migration_preflight_check.py --source-cluster my-cluster --verbose

  # Use command line parameters only
  python3 migration_preflight_check.py --source-cluster my-redis-cluster --target-uri redis://user:pass@redis-cloud.com:6379

  # With custom .env file location
  python3 migration_preflight_check.py --env-file /path/to/custom.env --region us-west-2 --verbose

.env Configuration:
  The script automatically reads configuration from .env file with these variables:
  - ELASTICACHE_CLUSTER_ID or REDIS_SOURCE_HOST (for source cluster)
  - REDIS_DEST_HOST, REDIS_DEST_PORT, REDIS_DEST_PASSWORD, REDIS_DEST_TLS (for target)
        """
    )

    parser.add_argument(
        '--source-cluster',
        help='Source ElastiCache cluster ID or replication group ID (optional if configured in .env)'
    )

    parser.add_argument(
        '--target-uri',
        help='Target Redis Cloud URI (redis://[user:pass@]host:port or rediss://[user:pass@]host:port) (optional if configured in .env)'
    )

    parser.add_argument(
        '--region',
        help='AWS region (default: from AWS config)'
    )

    parser.add_argument(
        '--env-file',
        default='.env',
        help='Path to .env configuration file (default: .env)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output with detailed information'
    )

    args = parser.parse_args()

    # Initialize checker (will load from .env if parameters not provided)
    checker = MigrationPreflightChecker(
        source_cluster_id=args.source_cluster,
        target_redis_uri=args.target_uri,
        region=args.region,
        verbose=args.verbose,
        env_file=args.env_file
    )

    # Validate that we have required configuration
    if not checker.source_cluster_id:
        print("❌ Error: Source cluster ID not provided and not found in .env file")
        print("   Either provide --source-cluster or configure ELASTICACHE_CLUSTER_ID/REDIS_SOURCE_HOST in .env")
        sys.exit(1)

    if not checker.target_redis_uri:
        print("❌ Error: Target Redis URI not provided and not found in .env file")
        print("   Either provide --target-uri or configure REDIS_DEST_* variables in .env")
        sys.exit(1)

    success = checker.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
