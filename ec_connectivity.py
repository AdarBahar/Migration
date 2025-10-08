#!/usr/bin/env python3
"""
ElastiCache Connectivity Doctor

Interactive tool to troubleshoot connectivity between THIS EC2 instance and an AWS ElastiCache for Redis endpoint.
- Prompts for ElastiCache URI/connection details interactively
- Discovers EC2 networking (VPC, subnet, SGs, routes, NACLs)
- Finds the target ElastiCache replication group / cluster
- Checks DNS, TCP, TLS reachability
- Compares SG rules and suggests or applies minimal fixes

Supports various input formats:
- redis-cli commands: redis6-cli --tls -h host.cache.amazonaws.com -p 6379 -c
- Redis URLs: redis://host:port or rediss://host:port (TLS)
- Host:port format: host.cache.amazonaws.com:6379
- Host only: host.cache.amazonaws.com (defaults to port 6379)
"""

import ipaddress
import json
import re
import socket
import ssl
import sys
import time
from typing import Dict, List, Optional, Tuple

import boto3
import botocore
import requests

IMDS_BASE = "http://169.254.169.254"
IMDS_TOKEN_TTL = "21600"

# Best-effort mapping from ElastiCache DNS shard code to region name.
# Fallbacks: instance region, then --region flag if provided.
REGION_HINTS = {
    "use1": "us-east-1",
    "use2": "us-east-2",
    "usw1": "us-west-1",
    "usw2": "us-west-2",
    "cac1": "ca-central-1",
    "euw1": "eu-west-1",
    "euw2": "eu-west-2",
    "euw3": "eu-west-3",
    "euc1": "eu-central-1",
    "eun1": "eu-north-1",
    "eus1": "eu-south-1",
    "eus2": "eu-south-2",
    "mes1": "me-south-1",
    "afc1": "af-south-1",
    "apse1": "ap-southeast-1",
    "apse2": "ap-southeast-2",
    "apse3": "ap-southeast-3",
    "aps1": "ap-south-1",
    "aps2": "ap-south-2",
    "apne1": "ap-northeast-1",
    "apne2": "ap-northeast-2",
    "apne3": "ap-northeast-3",
    "sae1": "sa-east-1",
}

def print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def get_user_input():
    """Interactive function to get ElastiCache connection details from user."""
    print("🚀 ElastiCache Connectivity Doctor")
    print("=" * 50)
    print("\nThis tool will help diagnose connectivity issues between this EC2 instance")
    print("and your ElastiCache Redis endpoint.\n")

    print("📝 Enter your ElastiCache connection details:")
    print("   You can provide:")
    print("   • Redis CLI command: redis6-cli --tls -h host.cache.amazonaws.com -p 6379")
    print("   • Redis URL: redis://host:port or rediss://host:port")
    print("   • Host:port: host.cache.amazonaws.com:6379")
    print("   • Host only: host.cache.amazonaws.com (defaults to port 6379)")
    print()

    while True:
        try:
            # Get URI/connection string
            uri_input = input("🔗 Enter ElastiCache URI/connection string: ").strip()
            if not uri_input:
                print("❌ Please enter a valid URI or connection string.")
                continue

            # Parse the input
            try:
                host, port, tls = parse_uri_or_command(uri_input)
                print(f"✅ Parsed connection: {host}:{port} {'(TLS enabled)' if tls else '(TLS disabled)'}")
                break
            except ValueError as e:
                print(f"❌ Could not parse input: {e}")
                print("   Please try a different format.")
                continue

        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            sys.exit(0)

    # Get additional options
    print("\n⚙️ Additional Options:")

    # TLS override
    if not tls:
        tls_input = input("🔒 Force TLS connection? (y/N): ").strip().lower()
        if tls_input in ('y', 'yes'):
            tls = True
            print("✅ TLS enabled")

    # Port override
    port_input = input(f"🔌 Override port (current: {port}): ").strip()
    if port_input:
        try:
            new_port = int(port_input)
            if 1 <= new_port <= 65535:
                port = new_port
                print(f"✅ Port set to {port}")
            else:
                print("⚠️ Invalid port range, keeping current port")
        except ValueError:
            print("⚠️ Invalid port number, keeping current port")

    # Region override
    region_input = input("🌍 AWS region override (leave empty for auto-detection): ").strip()
    region = region_input if region_input else None

    # Apply fixes option
    apply_fixes_input = input("🔧 Apply security group fixes automatically? (y/N): ").strip().lower()
    apply_fixes = apply_fixes_input in ('y', 'yes')

    # Timeout
    timeout_input = input("⏱️ Connection timeout in seconds (default: 3): ").strip()
    try:
        timeout = int(timeout_input) if timeout_input else 3
        if timeout < 1:
            timeout = 3
    except ValueError:
        timeout = 3

    print(f"\n📋 Configuration Summary:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   TLS: {'Enabled' if tls else 'Disabled'}")
    print(f"   Region: {region or 'Auto-detect'}")
    print(f"   Apply fixes: {'Yes' if apply_fixes else 'No'}")
    print(f"   Timeout: {timeout}s")

    confirm = input("\n✅ Proceed with these settings? (Y/n): ").strip().lower()
    if confirm in ('n', 'no'):
        print("👋 Exiting...")
        sys.exit(0)

    return {
        'host': host,
        'port': port,
        'tls': tls,
        'region': region,
        'apply_fixes': apply_fixes,
        'timeout': timeout
    }

def get_imds_token() -> Optional[str]:
    """Get IMDS v2 token for secure metadata access."""
    try:
        r = requests.put(
            IMDS_BASE + "/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": IMDS_TOKEN_TTL},
            timeout=2,
        )
        if r.status_code == 200:
            return r.text
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        # Network issues, timeouts, or connection errors
        print(f"DEBUG: IMDS token retrieval failed: {e}")
    except Exception as e:
        # Other unexpected errors
        print(f"DEBUG: Unexpected error getting IMDS token: {e}")
    return None

def imds_get(path: str, token: Optional[str]) -> str:
    headers = {"X-aws-ec2-metadata-token": token} if token else {}
    url = IMDS_BASE + "/latest/meta-data/" + path.lstrip("/")
    r = requests.get(url, headers=headers, timeout=2)
    r.raise_for_status()
    return r.text

def get_instance_identity_doc() -> Dict:
    try:
        r = requests.get(IMDS_BASE + "/latest/dynamic/instance-identity/document", timeout=2)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def parse_uri_or_command(s: str) -> Tuple[str, int, bool]:
    """
    Accepts:
      - redis/redis6-cli ... -h host -p 6379 [--tls|-tls|-ssl]
      - rediss://host:port
      - redis://host:port
      - plain host:port
      - plain host (defaults to 6379)
    Returns: (host, port, tls)
    """
    s = s.strip()

    # URL forms
    m = re.match(r'^(rediss?)://([^:/\s]+)(?::(\d+))?', s, re.IGNORECASE)
    if m:
        scheme = m.group(1).lower()
        host = m.group(2)
        port = int(m.group(3)) if m.group(3) else 6379
        return host, port, scheme == "rediss"

    # redis-cli style
    if "redis" in s and (" -h " in s or " -p " in s):
        host = None
        port = 6379
        tls = False
        tokens = re.split(r"\s+", s)
        for i, t in enumerate(tokens):
            if t in ("-h", "--host") and i + 1 < len(tokens):
                host = tokens[i + 1]
            if t in ("-p", "--port") and i + 1 < len(tokens):
                try:
                    port = int(tokens[i + 1])
                except ValueError:
                    pass
            if t in ("--tls", "-tls", "--ssl"):
                tls = True
        if host:
            return host, port, tls

    # host:port
    if ":" in s and " " not in s:
        host, p = s.split(":", 1)
        try:
            return host, int(p), False
        except ValueError:
            pass

    # bare host
    if " " not in s and "." in s:
        return s, 6379, False

    raise ValueError("Could not parse URI/command/host from input.")

def infer_region_from_host(host: str) -> Optional[str]:
    # ...something.like.this.<shard>.cache.amazonaws.com
    parts = host.split(".")
    # Find a token that looks like a shard code (3-4 chars alnum)
    for p in parts:
        if len(p) in (3, 4) and p.lower() in REGION_HINTS:
            return REGION_HINTS[p.lower()]
    return None

def resolve_dns(host: str) -> List[str]:
    try:
        infos = socket.getaddrinfo(host, None)
        addrs = sorted({ai[4][0] for ai in infos})
        return addrs
    except socket.gaierror:
        return []

def tcp_check(host: str, port: int, tls: bool, timeout=3) -> Tuple[bool, Optional[str]]:
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            if tls:
                context = ssl.create_default_context()
                # SNI
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    # simple TLS handshake done if no exception
                    return True, None
            else:
                return True, None
    except Exception as e:
        return False, str(e)

def get_boto3_clients(region: str) -> Tuple[boto3.client, boto3.client]:
    """Get EC2 and ElastiCache boto3 clients for the specified region."""
    return (
        boto3.client("ec2", region_name=region),
        boto3.client("elasticache", region_name=region),
    )

def find_self_instance(ec2) -> Dict:
    """
    Find the current EC2 instance details using IMDS or private IP lookup.

    Returns:
        Dict: EC2 instance description dict containing InstanceId, NetworkInterfaces, etc.

    Raises:
        RuntimeError: If instance cannot be identified via IMDS or private IP lookup.
    """
    # Try IMDS
    token = get_imds_token()
    try:
        instance_id = imds_get("instance-id", token)
    except Exception:
        instance_id = None

    if not instance_id:
        # As a fallback, use Instance Identity Doc region and try to deduce by private IP
        iid = get_instance_identity_doc()
        my_private_ip = iid.get("privateIp", None)
        region = iid.get("region", None)
        if not my_private_ip or not region:
            raise RuntimeError("Unable to determine instance identity via IMDS.")
        # Search by private IP
        resp = ec2.describe_instances(
            Filters=[{"Name": "private-ip-address", "Values": [my_private_ip]}]
        )
        for r in resp["Reservations"]:
            for inst in r["Instances"]:
                return inst
        raise RuntimeError("Could not find instance by private IP.")
    # Normal path: instance-id known
    resp = ec2.describe_instances(InstanceIds=[instance_id])
    return resp["Reservations"][0]["Instances"][0]

def sg_ids_to_rules(ec2, sg_ids: List[str]) -> Dict[str, Dict]:
    if not sg_ids:
        return {}
    resp = ec2.describe_security_groups(GroupIds=sg_ids)
    out = {}
    for sg in resp["SecurityGroups"]:
        out[sg["GroupId"]] = sg
    return out

def get_route_tables_for_subnet(ec2, subnet_id: str) -> List[Dict]:
    # main or explicit association
    rts = ec2.describe_route_tables(
        Filters=[{"Name": "association.subnet-id", "Values": [subnet_id]}]
    )["RouteTables"]
    if rts:
        return rts
    # Otherwise fetch VPC main
    subnet = ec2.describe_subnets(SubnetIds=[subnet_id])["Subnets"][0]
    vpc_id = subnet["VpcId"]
    rts = ec2.describe_route_tables(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["RouteTables"]
    main = [rt for rt in rts for assoc in rt.get("Associations", []) if assoc.get("Main")]
    return main or rts

def get_nacls_for_subnet(ec2, subnet_id: str) -> List[Dict]:
    resp = ec2.describe_network_acls(
        Filters=[{"Name": "association.subnet-id", "Values": [subnet_id]}]
    )
    return resp["NetworkAcls"]

def find_elasticache_target(ecc, host: str, port: int) -> Dict:
    """
    Try to match host to a replication group config endpoint or cluster node endpoint.
    Returns a dict with keys: type ('replication-group'|'cluster'|'unknown'), and details.
    """
    # Try replication groups
    try:
        paginator = ecc.get_paginator("describe_replication_groups")
        for page in paginator.paginate():
            for rg in page.get("ReplicationGroups", []):
                cep = rg.get("ConfigurationEndpoint")
                if cep and cep.get("Address") == host:
                    # Only check port if it's explicitly provided in the endpoint
                    endpoint_port = cep.get("Port")
                    if endpoint_port is not None and int(endpoint_port) == port:
                        return {"type": "replication-group", "object": rg}

                # Check member clusters for endpoints
                for member_id in rg.get("MemberClusters", []):
                    try:
                        member_resp = ecc.describe_cache_clusters(
                            CacheClusterId=member_id,
                            ShowCacheNodeInfo=True
                        )
                        member_cluster = member_resp["CacheClusters"][0]

                        # Check member cluster endpoints
                        member_endpoints = []
                        if member_cluster.get("ConfigurationEndpoint"):
                            member_endpoints.append(member_cluster["ConfigurationEndpoint"])
                        for node in member_cluster.get("CacheNodes", []):
                            if node.get("Endpoint"):
                                member_endpoints.append(node["Endpoint"])

                        for ep in member_endpoints:
                            if ep.get("Address") == host:
                                endpoint_port = ep.get("Port")
                                if endpoint_port is not None and int(endpoint_port) == port:
                                    return {"type": "replication-group", "object": rg}
                    except Exception:
                        # Skip member clusters that can't be described
                        continue
    except ecc.exceptions.ReplicationGroupNotFoundFault:
        pass
    # Try clusters
    paginator = ecc.get_paginator("describe_cache_clusters")
    for page in paginator.paginate(ShowCacheNodeInfo=True):
        for cc in page.get("CacheClusters", []):
            # Primary endpoint (for non-cluster-mode)
            p = cc.get("ConfigurationEndpoint") or cc.get("CacheNodes", [{}])[0].get("Endpoint")
            endpoints = []
            if p:
                endpoints.append(p)
            for node in cc.get("CacheNodes", []):
                if node.get("Endpoint"):
                    endpoints.append(node["Endpoint"])
            for ep in endpoints:
                if ep.get("Address") == host:
                    # Only check port if it's explicitly provided in the endpoint
                    endpoint_port = ep.get("Port")
                    if endpoint_port is not None and int(endpoint_port) == port:
                        return {"type": "cluster", "object": cc}
    return {"type": "unknown", "object": None}

def _extract_cluster_port(cc: Dict) -> Optional[int]:
    """
    Extract port from cluster configuration, checking both ConfigurationEndpoint and CacheNodes.
    Returns None if no port can be determined reliably.
    """
    # Try ConfigurationEndpoint first
    config_endpoint = cc.get("ConfigurationEndpoint")
    if config_endpoint and "Port" in config_endpoint:
        return config_endpoint["Port"]

    # Try first cache node endpoint
    cache_nodes = cc.get("CacheNodes", [])
    if cache_nodes:
        first_node = cache_nodes[0]
        endpoint = first_node.get("Endpoint")
        if endpoint and "Port" in endpoint:
            return endpoint["Port"]

    # Return None if no port found (caller should handle this)
    return None

def collect_elasticache_networking(ecc, ec2, target: Dict) -> Dict:
    """
    Returns: {
      'vpc_id', 'subnet_group', 'subnet_ids', 'sg_ids'
    }
    """
    if target["type"] == "replication-group":
        rg = target["object"]
        # Need to fetch a representative member cluster to read SGs/subnet group
        member = (rg.get("MemberClusters") or [None])[0]
        if not member:
            return {}
        cc = ecc.describe_cache_clusters(CacheClusterId=member, ShowCacheNodeInfo=True)["CacheClusters"][0]
    elif target["type"] == "cluster":
        cc = target["object"]
    else:
        return {}

    # Subnet group
    sng = ecc.describe_cache_subnet_groups(
        CacheSubnetGroupName=cc["CacheSubnetGroupName"]
    )["CacheSubnetGroups"][0]
    subnet_ids = [sn["SubnetIdentifier"] for sn in sng["Subnets"]]

    # VPC ID via any subnet
    subnet = ec2.describe_subnets(SubnetIds=[subnet_ids[0]])["Subnets"][0]
    vpc_id = subnet["VpcId"]

    # Security groups (ElastiCache exposes VPCSecurityGroups)
    sg_ids = [sg["SecurityGroupId"] for sg in cc.get("SecurityGroups", [])]
    return {
        "vpc_id": vpc_id,
        "subnet_group": sng["CacheSubnetGroupName"],
        "subnet_ids": subnet_ids,
        "sg_ids": sg_ids,
        "engine": cc.get("Engine"),
        "engine_version": cc.get("EngineVersion"),
        "port": _extract_cluster_port(cc),
        "cluster_id": cc.get("CacheClusterId"),
    }

def cidr_contains(ip: str, cidr: str) -> bool:
    """Check if an IP address is contained within a CIDR block."""
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        return False

def sg_allows_ingress_from_instance(sg: Dict, inst_sg_ids: List[str], inst_ip: str, port: int) -> bool:
    for rule in sg.get("IpPermissions", []):
        ip_ok = False
        # Port check
        from_p = rule.get("FromPort")
        to_p = rule.get("ToPort")
        ip_proto = rule.get("IpProtocol")
        if ip_proto not in ("tcp", "-1"):
            continue
        if ip_proto == "tcp":
            if from_p is None or to_p is None:
                continue
            if not (from_p <= port <= to_p):
                continue
        # Sources
        for pair in rule.get("UserIdGroupPairs", []):
            if pair.get("GroupId") in inst_sg_ids:
                ip_ok = True
        for rng in rule.get("IpRanges", []):
            cidr = rng.get("CidrIp")
            if cidr and cidr_contains(inst_ip, cidr):
                ip_ok = True
        for rng6 in rule.get("Ipv6Ranges", []):
            cidr6 = rng6.get("CidrIpv6")
            if cidr6 and cidr_contains(inst_ip, cidr6):
                ip_ok = True
        if ip_ok:
            return True
    return False

def sg_allows_egress_to_cache(inst_sg: Dict, cache_ips: List[str], port: int) -> bool:
    """
    Check if instance security group allows egress to cache IPs on the specified port.
    Returns True if egress is allowed, False otherwise.
    """
    if not cache_ips:
        # If no cache IPs provided, cannot determine egress allowance
        return False

    for rule in inst_sg.get("IpPermissionsEgress", []):
        ip_proto = rule.get("IpProtocol")
        from_p = rule.get("FromPort")
        to_p = rule.get("ToPort")

        # -1 means all protocols/ports
        if ip_proto == "-1":
            return True

        if ip_proto != "tcp":
            continue

        if from_p is None or to_p is None:
            continue

        if not (from_p <= port <= to_p):
            continue

        # Check if any cache IP is covered by the rule's CIDR ranges
        for ip_range in rule.get("IpRanges", []):
            cidr = ip_range.get("CidrIp")
            if cidr:
                for cache_ip in cache_ips:
                    if cidr_contains(cache_ip, cidr):
                        return True

        for ipv6_range in rule.get("Ipv6Ranges", []):
            cidr6 = ipv6_range.get("CidrIpv6")
            if cidr6:
                for cache_ip in cache_ips:
                    if cidr_contains(cache_ip, cidr6):
                        return True

    return False

def add_ingress_to_cache_sg(ec2, cache_sg_id: str, inst_sg_id: str, port: int) -> Tuple[bool, str]:
    try:
        ec2.authorize_security_group_ingress(
            GroupId=cache_sg_id,
            IpPermissions=[{
                "IpProtocol": "tcp",
                "FromPort": port,
                "ToPort": port,
                "UserIdGroupPairs": [{"GroupId": inst_sg_id}],
            }],
        )
        return True, f"Added ingress tcp/{port} from SG {inst_sg_id} to {cache_sg_id}"
    except botocore.exceptions.ClientError as e:
        msg = str(e)
        if "InvalidPermission.Duplicate" in msg:
            return True, f"Ingress already present on {cache_sg_id}"
        return False, msg

def add_egress_on_instance_sg(ec2, inst_sg_id: str, port: int) -> Tuple[bool, str]:
    """
    Add egress rule to instance security group for the specified port.

    SECURITY WARNING: This adds a permissive egress rule allowing outbound traffic
    to 0.0.0.0/0 on the specified port. For tighter security, consider restricting
    egress to specific CIDR ranges (e.g., ElastiCache subnet ranges) instead.

    Args:
        ec2: EC2 client
        inst_sg_id: Instance security group ID
        port: Port to allow egress on

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        ec2.authorize_security_group_egress(
            GroupId=inst_sg_id,
            IpPermissions=[{
                "IpProtocol": "tcp",
                "FromPort": port,
                "ToPort": port,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }],
        )
        return True, f"Added egress tcp/{port} to 0.0.0.0/0 on {inst_sg_id}"
    except botocore.exceptions.ClientError as e:
        msg = str(e)
        if "InvalidPermission.Duplicate" in msg:
            return True, f"Egress already present on {inst_sg_id}"
        return False, msg

def main():
    print("\n" + "🔧" * 25 + " ElastiCache Connectivity Doctor " + "🔧" * 25)
    print("Interactive tool to diagnose EC2 ↔ ElastiCache connectivity issues")
    print("=" * 80)

    # Get user input interactively
    config = get_user_input()

    host = config['host']
    port = config['port']
    tls = config['tls']
    region_override = config['region']
    apply_fixes = config['apply_fixes']
    timeout = config['timeout']

    print_header("Target")
    print(json.dumps({"host": host, "port": port, "tls": tls}, indent=2))

    # Resolve DNS early
    ips = resolve_dns(host)
    print_header("DNS Resolution")
    if ips:
        print(f"{host} resolves to: {', '.join(ips)}")
    else:
        print(f"DNS resolution FAILED for {host}. Check VPC DNS settings / resolvers.")
        # We can continue with API checks, but TCP will fail.
    # TCP/TLS probe
    print_header("Network Probe (from this instance)")
    ok, err = tcp_check(host, port, tls, timeout=timeout)
    if ok:
        print(f"SUCCESS: TCP{'/TLS' if tls else ''} connect to {host}:{port}")
    else:
        print(f"FAIL: Could not connect to {host}:{port} ({'TLS' if tls else 'plain TCP'})")
        if err:
            print(f"Error: {err}")

    # Determine region
    iidoc = get_instance_identity_doc()
    instance_region = iidoc.get("region")
    inferred = infer_region_from_host(host)
    region = region_override or inferred or instance_region
    if not region:
        print("\nWARN: Could not infer AWS region; defaulting to instance region if available.", file=sys.stderr)
        region = instance_region
    print_header("Region Selection")
    print(json.dumps({"instance_region": instance_region, "host_hint_region": inferred, "used_region": region}, indent=2))

    ec2, ecc = get_boto3_clients(region)

    # Find self instance and networking
    print_header("EC2 Instance Networking")
    try:
        inst = find_self_instance(ec2)
    except Exception as e:
        print(f"ERROR: Could not identify this instance: {e}")
        sys.exit(1)

    network_interfaces = inst.get("NetworkInterfaces", [])
    if not network_interfaces:
        print("ERROR: Instance has no network interfaces")
        sys.exit(1)

    primary_eni = sorted(network_interfaces, key=lambda x: x.get("Attachment", {}).get("DeviceIndex", 0))[0]
    inst_info = {
        "InstanceId": inst["InstanceId"],
        "PrivateIp": primary_eni["PrivateIpAddress"],
        "SubnetId": primary_eni["SubnetId"],
        "VpcId": primary_eni["VpcId"],
        "SecurityGroupIds": [sg["GroupId"] for sg in primary_eni.get("Groups", [])],
        "Az": inst.get("Placement", {}).get("AvailabilityZone"),
    }
    print(json.dumps(inst_info, indent=2))

    # Route tables & NACLs
    rts = get_route_tables_for_subnet(ec2, inst_info["SubnetId"])
    nacls = get_nacls_for_subnet(ec2, inst_info["SubnetId"])
    print("\nRouteTables (instance subnet):")
    print(json.dumps([{"RouteTableId": rt["RouteTableId"], "Associations": rt.get("Associations", []), "Routes": rt.get("Routes", [])} for rt in rts], indent=2))
    print("\nNetworkACLs (instance subnet):")
    print(json.dumps([{"NetworkAclId": n["NetworkAclId"], "Entries": n.get("Entries", [])} for n in nacls], indent=2))

    # Find ElastiCache object
    print_header("ElastiCache Discovery")
    target = find_elasticache_target(ecc, host, port)
    if target["type"] == "unknown":
        print("WARN: Could not match endpoint to a replication group or cluster in this region.")
        cache_net = {}
    else:
        print(f"Matched ElastiCache type: {target['type']}")
        cache_net = collect_elasticache_networking(ecc, ec2, target)
        print(json.dumps(cache_net, indent=2))

    # Compare VPCs
    print_header("VPC / Subnet Comparison")
    if cache_net:
        same_vpc = (inst_info["VpcId"] == cache_net["vpc_id"])
        print(json.dumps({"instance_vpc": inst_info["VpcId"], "cache_vpc": cache_net["vpc_id"], "same_vpc": same_vpc}, indent=2))
        if not same_vpc:
            print("ERROR: Instance and ElastiCache are in DIFFERENT VPCs. You need VPC peering / TGW + routes + SG/NACL updates.")
    else:
        print("No cache networking info available; cannot compare VPCs.")

    # SG analysis
    print_header("Security Group Analysis")
    try:
        inst_sgs = sg_ids_to_rules(ec2, inst_info["SecurityGroupIds"])
        if cache_net and cache_net["sg_ids"]:
            cache_sgs = sg_ids_to_rules(ec2, cache_net["sg_ids"])
        else:
            cache_sgs = {}
        # Ingress on cache SGs
        if cache_sgs:
            ingress_ok = any(
                sg_allows_ingress_from_instance(cache_sgs[sgid], inst_info["SecurityGroupIds"], inst_info["PrivateIp"], port)
                for sgid in cache_sgs
            )
            print(f"Ingress on cache SGs allows instance? {'YES' if ingress_ok else 'NO'}")
        else:
            ingress_ok = False
            print("No cache SGs found (or not discoverable).")
        # Egress on instance SGs
        if ips:
            # Check if ANY instance SG permits egress to the actual cache IPs
            egress_ok = any(
                sg_allows_egress_to_cache(inst_sgs[sgid], ips, port) for sgid in inst_sgs
            )
            print(f"Egress on instance SGs allows port {port} to cache IPs? {'YES' if egress_ok else 'NO'}")
        else:
            egress_ok = False
            print(f"Egress check skipped - DNS resolution failed for {host}")

        # Suggest/apply fixes
        if not ingress_ok and cache_sgs and apply_fixes:
            # Add an ingress rule on each cache SG, referencing the FIRST instance SG (least privilege)
            first_inst_sg = inst_info["SecurityGroupIds"][0]
            for sgid in cache_sgs:
                ok, msg = add_ingress_to_cache_sg(ec2, sgid, first_inst_sg, port)
                print(("OK: " if ok else "ERR: ") + msg)

        if not egress_ok and apply_fixes:
            # Add egress on first instance SG
            first_inst_sg = inst_info["SecurityGroupIds"][0]
            ok, msg = add_egress_on_instance_sg(ec2, first_inst_sg, port)
            print(("OK: " if ok else "ERR: ") + msg)

    except botocore.exceptions.ClientError as e:
        print(f"ERROR reading or modifying SGs: {e}")

    # NACL / Route sanity notes (cannot auto-fix safely)
    print_header("NACL / Route Sanity Checks")
    if cache_net:
        print("- Ensure subnet NACLs in BOTH directions allow ephemeral >1024 and tcp/%d as needed." % port)
        print("- Ensure routes allow instance-subnet → cache-subnet (same VPC) or via peering/TGW (cross-VPC).")
    else:
        print("- Skipping detailed checks (cache subnet unknown).")

    # Final recap & hints
    print_header("Result Recap")
    print(json.dumps({
        "dns_resolves": bool(ips),
        "tcp_tls_connect_ok": ok,
        "same_vpc": (bool(cache_net) and inst_info["VpcId"] == cache_net["vpc_id"]) if cache_net else None,
        "cache_sg_ingress_allows_instance": ingress_ok if cache_net else None,
        "instance_sg_egress_allows_port": egress_ok,
        "auto_fixes_applied": bool(apply_fixes),
    }, indent=2))

    print("\nHints:")
    if tls:
        print("• Target requires TLS: connect with redis-cli --tls (or rediss://).")
    else:
        print("• If the cluster enforces in-transit encryption, you MUST use --tls / rediss://.")
    print("• If AUTH is enabled, reachability can succeed but AUTH will still fail — this script checks connectivity only.")
    print("• Cross-VPC setups require peering/TGW + routes + SG/NACL. This script won’t auto-create those.")

if __name__ == "__main__":
    main()
