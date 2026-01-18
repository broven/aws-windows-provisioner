"""Start instance command."""

import typer
from typing import Optional

from winaws.utils.console import print_error, print_success, print_header
from winaws.core.ec2 import start_instance, get_instance_info, list_managed_instances
from winaws.prompts.interactive import select_instance


app = typer.Typer()


@app.command()
def start(
    instance_id: Optional[str] = typer.Argument(None, help="Instance ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
):
    """
    Start a stopped Windows instance.

    The instance will boot up and be accessible via RDP once running.
    """
    print_header("WinAWS - Start Instance")

    # If no instance ID provided, let user select from list
    if not instance_id:
        if not region:
            print_error("Region required when selecting from list")
            raise typer.Exit(1)

        instances = list_managed_instances(region)
        if not instances:
            print_error(f"No managed instances found in region {region}")
            raise typer.Exit(1)

        # Filter for stopped instances
        stopped_instances = [i for i in instances if i['state'] in ['stopped', 'stopping']]
        if not stopped_instances:
            print_error("No stopped instances found")
            raise typer.Exit(1)

        instance_id = select_instance(stopped_instances)
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

    # Verify instance exists
    info = get_instance_info(region, instance_id)
    if not info:
        print_error(f"Instance {instance_id} not found in region {region}")
        raise typer.Exit(1)

    # Check current state
    current_state = info['state']
    if current_state == 'running':
        print_success(f"Instance {instance_id} is already running")
        return

    if current_state not in ['stopped', 'stopping']:
        print_error(f"Cannot start instance in state: {current_state}")
        raise typer.Exit(1)

    # Start instance
    success = start_instance(region, instance_id)
    if success:
        print_success(f"Instance {info['name']} will be running shortly")
        print(f"Check status with: winaws status {instance_id} --region {region}")
    else:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
