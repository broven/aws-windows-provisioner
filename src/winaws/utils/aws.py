"""AWS client factory and utilities."""

import boto3
from typing import Optional


def get_ec2_client(region: str):
    """Create an EC2 client for the specified region."""
    return boto3.client('ec2', region_name=region)


def get_cloudformation_client(region: str):
    """Create a CloudFormation client for the specified region."""
    return boto3.client('cloudformation', region_name=region)


def get_pricing_client(region: str = 'us-east-1'):
    """Create a Pricing client. Pricing API is only available in us-east-1."""
    return boto3.client('pricing', region_name='us-east-1')


def get_available_regions() -> list[str]:
    """Get list of available AWS regions for EC2."""
    ec2 = boto3.client('ec2', region_name='us-east-1')
    response = ec2.describe_regions(AllRegions=False)
    regions = [region['RegionName'] for region in response['Regions']]
    return sorted(regions)


def validate_aws_credentials() -> bool:
    """Validate that AWS credentials are configured."""
    try:
        sts = boto3.client('sts')
        sts.get_caller_identity()
        return True
    except Exception:
        return False


def get_current_region() -> Optional[str]:
    """Get the current AWS region from session."""
    session = boto3.session.Session()
    return session.region_name
