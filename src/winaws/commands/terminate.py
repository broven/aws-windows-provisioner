"""Terminate instance command."""

import typer
from typing import Optional

from winaws.utils.console import print_error, print_success, print_header, print_warning
from winaws.core.ec2 import get_instance_info, list_managed_instances
from winaws.core.cloudformation import delete_stack, stack_exists
from winaws.core.keypair import delete_key_pair
from winaws.prompts.interactive import select_instance, confirm_action


app = typer.Typer()


@app.command()
def terminate(
    instance_id: Optional[str] = typer.Argument(None, help="Instance ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """
    Terminate a Windows instance and cleanup all resources.

    This will delete:
    - The EC2 instance
    - VPC and networking resources
    - CloudFormation stack
    - EC2 key pair
    """
    print_header("WinAWS - Terminate Instance")

    # If no instance ID provided, let user select from list
    if not instance_id:
        if not region:
            print_error("Region required when selecting from list")
            raise typer.Exit(1)

        instances = list_managed_instances(region)
        if not instances:
            print_error(f"No managed instances found in region {region}")
            raise typer.Exit(1)

        instance_id = select_instance(instances)
        if not instance_id:
            print_error("No instance selected")
            raise typer.Exit(1)

    # Get instance info to find region if not provided
    if not region:
        # Try common regions
        for test_region in ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']:
            info = get_instance_info(test_region, instance_id)
            if info:
                region = test_region
                break

        if not region:
            print_error("Could not determine instance region. Please specify with --region")
            raise typer.Exit(1)

    # Get instance info
    info = get_instance_info(region, instance_id)
    if not info:
        print_error(f"Instance {instance_id} not found in region {region}")
        raise typer.Exit(1)

    instance_name = info['name']
    stack_name = f"winaws-{instance_name}"
    key_name = f"winaws-{instance_name}"

    # Confirm termination
    if not yes:
        print_warning(f"This will permanently delete:")
        print(f"  - Instance: {instance_name} ({instance_id})")
        print(f"  - Stack: {stack_name}")
        print(f"  - Key pair: {key_name}")
        print(f"  - All associated VPC resources")
        print()

        if not confirm_action("Are you sure you want to terminate this instance?", default=False):
            print_error("Termination cancelled")
            raise typer.Exit(1)

    # Delete CloudFormation stack (this will delete the instance and all resources)
    print_header("Deleting CloudFormation Stack")

    if stack_exists(region, stack_name):
        success = delete_stack(region, stack_name, wait=True)
        if not success:
            print_error("Failed to delete CloudFormation stack")
            print_warning("You may need to manually cleanup resources in the AWS console")
            raise typer.Exit(1)
    else:
        print_warning(f"Stack {stack_name} not found, may have been deleted already")

    # Delete key pair
    print_header("Deleting Key Pair")
    delete_key_pair(region, key_name)

    print_success(f"Instance {instance_name} terminated successfully!")


if __name__ == "__main__":
    app()
