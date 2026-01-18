"""EC2 key pair management."""

import os
from pathlib import Path
from typing import Optional

from winaws.utils.aws import get_ec2_client
from winaws.utils.console import print_success, print_error, print_info


def get_keys_directory() -> Path:
    """Get or create the directory for storing key pairs."""
    keys_dir = Path.home() / ".winaws" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    return keys_dir


def get_key_path(key_name: str) -> Path:
    """Get the path for a key pair file."""
    return get_keys_directory() / f"{key_name}.pem"


def create_key_pair(region: str, key_name: str) -> Optional[str]:
    """
    Create an EC2 key pair and save the private key locally.

    Args:
        region: AWS region
        key_name: Name for the key pair

    Returns:
        Path to the private key file, or None if failed
    """
    ec2 = get_ec2_client(region)
    key_path = get_key_path(key_name)

    try:
        # Check if key already exists locally
        if key_path.exists():
            print_info(f"Key pair file already exists: {key_path}")
            # Check if it exists in AWS
            try:
                ec2.describe_key_pairs(KeyNames=[key_name])
                print_info(f"Key pair '{key_name}' exists in AWS")
                return str(key_path)
            except ec2.exceptions.ClientError:
                # Exists locally but not in AWS, delete local and recreate
                print_info("Key pair not found in AWS, recreating...")
                key_path.unlink()

        # Delete existing key pair in AWS if it exists
        try:
            ec2.delete_key_pair(KeyName=key_name)
            print_info(f"Deleted existing key pair '{key_name}' from AWS")
        except ec2.exceptions.ClientError:
            pass

        # Create new key pair
        response = ec2.create_key_pair(KeyName=key_name)
        private_key = response['KeyMaterial']

        # Save private key to file
        key_path.write_text(private_key)
        key_path.chmod(0o600)  # Set restrictive permissions

        print_success(f"Created key pair: {key_name}")
        print_info(f"Private key saved to: {key_path}")

        return str(key_path)

    except Exception as e:
        print_error(f"Failed to create key pair: {e}")
        return None


def delete_key_pair(region: str, key_name: str) -> bool:
    """
    Delete an EC2 key pair from AWS and local file.

    Args:
        region: AWS region
        key_name: Name of the key pair

    Returns:
        True if successful, False otherwise
    """
    ec2 = get_ec2_client(region)
    success = True

    try:
        # Delete from AWS
        ec2.delete_key_pair(KeyName=key_name)
        print_success(f"Deleted key pair '{key_name}' from AWS")
    except Exception as e:
        print_error(f"Failed to delete key pair from AWS: {e}")
        success = False

    # Delete local file
    key_path = get_key_path(key_name)
    if key_path.exists():
        try:
            key_path.unlink()
            print_success(f"Deleted local key file: {key_path}")
        except Exception as e:
            print_error(f"Failed to delete local key file: {e}")
            success = False

    return success


def key_exists(region: str, key_name: str) -> bool:
    """
    Check if a key pair exists in AWS.

    Args:
        region: AWS region
        key_name: Name of the key pair

    Returns:
        True if exists, False otherwise
    """
    ec2 = get_ec2_client(region)
    try:
        ec2.describe_key_pairs(KeyNames=[key_name])
        return True
    except ec2.exceptions.ClientError:
        return False


def list_key_pairs(region: str) -> list[dict]:
    """
    List all key pairs in the region.

    Args:
        region: AWS region

    Returns:
        List of key pair dictionaries
    """
    ec2 = get_ec2_client(region)
    try:
        response = ec2.describe_key_pairs()
        return response.get('KeyPairs', [])
    except Exception as e:
        print_error(f"Failed to list key pairs: {e}")
        return []
