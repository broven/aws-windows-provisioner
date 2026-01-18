"""Create Windows instance command."""

import typer
from typing import Optional

from winaws.utils.aws import validate_aws_credentials
from winaws.utils.console import (
    print_error,
    print_success,
    print_header,
    print_instance_info,
)
from winaws.prompts.interactive import prompt_create_configuration
from winaws.core.keypair import create_key_pair, get_key_path
from winaws.core.cloudformation import create_stack, get_stack_outputs
from winaws.core.password import get_instance_password


app = typer.Typer()


@app.command()
def create(
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
    instance_type: Optional[str] = typer.Option(None, "--type", "-t", help="Instance type"),
    instance_name: Optional[str] = typer.Option(None, "--name", "-n", help="Instance name"),
    ami_id: Optional[str] = typer.Option(None, "--ami", help="Windows AMI ID"),
    volume_size: Optional[int] = typer.Option(50, "--volume-size", "-s", help="Root volume size in GB"),
    rdp_cidr: Optional[str] = typer.Option(None, "--rdp-cidr", help="CIDR for RDP access"),
    skip_password: bool = typer.Option(False, "--skip-password", help="Skip password retrieval"),
):
    """
    Create a new Windows EC2 instance with VPC infrastructure.

    If no options are provided, enters interactive mode.
    """
    print_header("WinAWS - Create Windows Instance")

    # Validate AWS credentials
    if not validate_aws_credentials():
        print_error("AWS credentials not configured. Please run 'aws configure' first.")
        raise typer.Exit(1)

    # Interactive mode if no arguments provided
    if not all([region, instance_type, instance_name, ami_id]):
        config = prompt_create_configuration(region)
        if not config:
            print_error("Creation cancelled")
            raise typer.Exit(1)

        region = config['region']
        instance_type = config['instance_type']
        instance_name = config['instance_name']
        ami_id = config['ami_id']
        volume_size = config['volume_size']
        rdp_cidr = config['rdp_cidr']

    # Validate required parameters
    if not all([region, instance_type, instance_name, ami_id]):
        print_error("Missing required parameters. Run in interactive mode or provide all options.")
        raise typer.Exit(1)

    # Generate stack and key names
    stack_name = f"winaws-{instance_name}"
    key_name = f"winaws-{instance_name}"

    # Create key pair
    print_header("Creating Key Pair")
    key_path = create_key_pair(region, key_name)
    if not key_path:
        print_error("Failed to create key pair")
        raise typer.Exit(1)

    # Create CloudFormation stack
    print_header("Creating CloudFormation Stack")

    parameters = {
        'InstanceType': instance_type,
        'WindowsAMI': ami_id,
        'InstanceName': instance_name,
        'VolumeSize': str(volume_size),
        'KeyPairName': key_name,
        'RDPSourceCIDR': rdp_cidr or '0.0.0.0/0',
    }

    stack_id = create_stack(
        region=region,
        stack_name=stack_name,
        parameters=parameters,
        wait=True,
    )

    if not stack_id:
        print_error("Failed to create stack")
        raise typer.Exit(1)

    # Get stack outputs
    outputs = get_stack_outputs(region, stack_name)
    instance_id = outputs.get('InstanceId')
    public_ip = outputs.get('PublicIP')

    if not instance_id or not public_ip:
        print_error("Failed to get instance information from stack outputs")
        raise typer.Exit(1)

    print_success(f"Instance created successfully!")

    # Get password
    password = None
    if not skip_password:
        print_header("Retrieving Administrator Password")
        password = get_instance_password(
            region=region,
            instance_id=instance_id,
            private_key_path=key_path,
            max_wait=300,
        )

    # Display connection information
    print_header("Instance Ready")
    print_instance_info(
        instance_id=instance_id,
        public_ip=public_ip,
        instance_type=instance_type,
        name=instance_name,
        region=region,
        password=password,
    )

    if not password:
        print_error("Password not available yet. Retrieve it later with:")
        print(f"  winaws password {instance_id} --region {region}")


if __name__ == "__main__":
    app()
