"""Windows password decryption utilities."""

import base64
import time
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from winaws.utils.aws import get_ec2_client
from winaws.utils.console import print_info, print_error, print_warning, create_progress


def decrypt_password(encrypted_password: str, private_key_path: str) -> Optional[str]:
    """
    Decrypt Windows Administrator password using RSA private key.

    Args:
        encrypted_password: Base64 encoded encrypted password
        private_key_path: Path to the private key file

    Returns:
        Decrypted password, or None if failed
    """
    try:
        # Load private key
        private_key_pem = Path(private_key_path).read_bytes()
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )

        # Decode and decrypt
        encrypted_bytes = base64.b64decode(encrypted_password)
        decrypted_bytes = private_key.decrypt(
            encrypted_bytes,
            padding.PKCS1v15()
        )

        # Decode password
        password = decrypted_bytes.decode('utf-8')
        return password

    except Exception as e:
        print_error(f"Failed to decrypt password: {e}")
        return None


def get_instance_password(
    region: str,
    instance_id: str,
    private_key_path: str,
    max_wait: int = 300,
    poll_interval: int = 10
) -> Optional[str]:
    """
    Get and decrypt Windows instance password.

    Waits for password data to become available (usually takes 4-5 minutes).

    Args:
        region: AWS region
        instance_id: EC2 instance ID
        private_key_path: Path to the private key file
        max_wait: Maximum time to wait in seconds (default: 300)
        poll_interval: Time between polls in seconds (default: 10)

    Returns:
        Decrypted password, or None if failed
    """
    ec2 = get_ec2_client(region)
    start_time = time.time()

    print_info("Waiting for password data to become available...")
    print_warning("This usually takes 4-5 minutes after instance launch")

    with create_progress() as progress:
        task = progress.add_task("Retrieving password...", total=None)

        while time.time() - start_time < max_wait:
            try:
                response = ec2.get_password_data(InstanceId=instance_id)
                password_data = response.get('PasswordData', '')

                if password_data:
                    print_info("Password data retrieved, decrypting...")
                    password = decrypt_password(password_data, private_key_path)

                    if password:
                        return password
                    else:
                        print_error("Failed to decrypt password")
                        return None

                # Wait before next poll
                time.sleep(poll_interval)
                elapsed = int(time.time() - start_time)
                progress.update(task, description=f"Waiting for password... ({elapsed}s elapsed)")

            except Exception as e:
                print_error(f"Error retrieving password: {e}")
                return None

    print_error(f"Timeout waiting for password data after {max_wait} seconds")
    print_info("You can try running 'winaws password <instance-id>' again later")
    return None


def password_available(region: str, instance_id: str) -> bool:
    """
    Check if password data is available for an instance.

    Args:
        region: AWS region
        instance_id: EC2 instance ID

    Returns:
        True if password data is available, False otherwise
    """
    ec2 = get_ec2_client(region)
    try:
        response = ec2.get_password_data(InstanceId=instance_id)
        return bool(response.get('PasswordData', ''))
    except Exception:
        return False
