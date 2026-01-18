"""EC2 instance operations."""

from typing import Optional, List, Dict, Any

from winaws.utils.aws import get_ec2_client
from winaws.utils.console import print_success, print_error, print_info


def get_windows_amis(region: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get available Windows AMIs in the region.

    Args:
        region: AWS region
        limit: Maximum number of AMIs to return

    Returns:
        List of AMI dictionaries with 'id', 'name', 'description'
    """
    ec2 = get_ec2_client(region)

    try:
        # Search for Windows Server AMIs from Amazon
        response = ec2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['Windows_Server-*-English-Full-Base-*']},
                {'Name': 'state', 'Values': ['available']},
                {'Name': 'architecture', 'Values': ['x86_64']},
            ]
        )

        # Sort by creation date (newest first)
        amis = sorted(
            response['Images'],
            key=lambda x: x.get('CreationDate', ''),
            reverse=True
        )

        # Format results
        results = []
        for ami in amis[:limit]:
            results.append({
                'id': ami['ImageId'],
                'name': ami.get('Name', 'Unknown'),
                'description': ami.get('Description', ''),
                'creation_date': ami.get('CreationDate', '')
            })

        return results

    except Exception as e:
        print_error(f"Failed to retrieve Windows AMIs: {e}")
        return []


def get_instance_types(region: str) -> List[Dict[str, Any]]:
    """
    Get common instance types with their specifications.

    Returns a curated list of commonly used instance types.
    """
    # Common instance types for Windows
    common_types = [
        't3.medium', 't3.large', 't3.xlarge', 't3.2xlarge',
        't3a.medium', 't3a.large', 't3a.xlarge',
        'm5.large', 'm5.xlarge', 'm5.2xlarge',
        'c5.large', 'c5.xlarge', 'c5.2xlarge',
        'r5.large', 'r5.xlarge',
    ]

    ec2 = get_ec2_client(region)

    try:
        response = ec2.describe_instance_types(InstanceTypes=common_types)

        results = []
        for itype in response['InstanceTypes']:
            results.append({
                'type': itype['InstanceType'],
                'vcpu': itype['VCpuInfo']['DefaultVCpus'],
                'memory_gb': itype['MemoryInfo']['SizeInMiB'] / 1024,
                'network': itype.get('NetworkInfo', {}).get('NetworkPerformance', 'Unknown'),
            })

        # Sort by vcpu and memory
        results.sort(key=lambda x: (x['vcpu'], x['memory_gb']))
        return results

    except Exception as e:
        print_error(f"Failed to retrieve instance types: {e}")
        # Return basic fallback list
        return [
            {'type': 't3.medium', 'vcpu': 2, 'memory_gb': 4, 'network': 'Up to 5 Gigabit'},
            {'type': 't3.large', 'vcpu': 2, 'memory_gb': 8, 'network': 'Up to 5 Gigabit'},
            {'type': 't3.xlarge', 'vcpu': 4, 'memory_gb': 16, 'network': 'Up to 5 Gigabit'},
        ]


def get_instance_info(region: str, instance_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about an EC2 instance.

    Args:
        region: AWS region
        instance_id: EC2 instance ID

    Returns:
        Dictionary with instance information, or None if not found
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])

        if not response['Reservations']:
            return None

        instance = response['Reservations'][0]['Instances'][0]

        # Extract tags
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

        return {
            'instance_id': instance['InstanceId'],
            'instance_type': instance['InstanceType'],
            'state': instance['State']['Name'],
            'public_ip': instance.get('PublicIpAddress', 'N/A'),
            'private_ip': instance.get('PrivateIpAddress', 'N/A'),
            'launch_time': instance['LaunchTime'],
            'availability_zone': instance['Placement']['AvailabilityZone'],
            'vpc_id': instance.get('VpcId', 'N/A'),
            'subnet_id': instance.get('SubnetId', 'N/A'),
            'key_name': instance.get('KeyName', 'N/A'),
            'name': tags.get('Name', 'N/A'),
            'managed_by': tags.get('ManagedBy', 'N/A'),
            'tags': tags,
        }

    except Exception as e:
        print_error(f"Failed to get instance info: {e}")
        return None


def list_managed_instances(region: str) -> List[Dict[str, Any]]:
    """
    List all instances managed by winaws.

    Args:
        region: AWS region

    Returns:
        List of instance dictionaries
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:ManagedBy', 'Values': ['winaws']},
                {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']},
            ]
        )

        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

                instances.append({
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'public_ip': instance.get('PublicIpAddress', 'N/A'),
                    'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                    'launch_time': instance.get('LaunchTime'),
                    'name': tags.get('Name', 'N/A'),
                })

        return instances

    except Exception as e:
        print_error(f"Failed to list instances: {e}")
        return []


def start_instance(region: str, instance_id: str) -> bool:
    """
    Start a stopped EC2 instance.

    Args:
        region: AWS region
        instance_id: EC2 instance ID

    Returns:
        True if successful, False otherwise
    """
    ec2 = get_ec2_client(region)

    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print_success(f"Starting instance {instance_id}")
        return True
    except Exception as e:
        print_error(f"Failed to start instance: {e}")
        return False


def stop_instance(region: str, instance_id: str) -> bool:
    """
    Stop a running EC2 instance.

    Args:
        region: AWS region
        instance_id: EC2 instance ID

    Returns:
        True if successful, False otherwise
    """
    ec2 = get_ec2_client(region)

    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print_success(f"Stopping instance {instance_id}")
        return True
    except Exception as e:
        print_error(f"Failed to stop instance: {e}")
        return False


def terminate_instance(region: str, instance_id: str) -> bool:
    """
    Terminate an EC2 instance.

    Args:
        region: AWS region
        instance_id: EC2 instance ID

    Returns:
        True if successful, False otherwise
    """
    ec2 = get_ec2_client(region)

    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print_success(f"Terminating instance {instance_id}")
        return True
    except Exception as e:
        print_error(f"Failed to terminate instance: {e}")
        return False


def get_current_public_ip() -> Optional[str]:
    """
    Get the current public IP address of this machine.

    Returns:
        Public IP address, or None if unable to determine
    """
    import urllib.request

    try:
        response = urllib.request.urlopen('https://api.ipify.org', timeout=5)
        return response.read().decode('utf-8')
    except Exception:
        return None
