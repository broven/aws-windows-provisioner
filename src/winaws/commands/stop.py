"""Stop instance command."""

import typer
from typing import Optional

from winaws.utils.console import print_error, print_success, print_header, print_warning
from winaws.core.ec2 import stop_instance, get_instance_info, list_managed_instances
from winaws.prompts.interactive import select_instance


app = typer.Typer()


@app.command()
def stop(
    instance_id: Optional[str] = typer.Argument(None, help="Instance ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
):
    """
    Stop a running Windows instance.

    The instance will be shut down but not terminated.
    You can start it again later with 'winaws start'.
    """
    print_header("WinAWS - Stop Instance")

    # If no instance ID provided, let user select from list
    if not instance_id:
        if not region:
            print_error("Region required when selecting from list")
            raise typer.Exit(1)

        instances = list_managed_instances(region)
        if not instances:
            print_error(f"No managed instances found in region {region}")
            raise typer.Exit(1)

        # Filter for running instances
        running_instances = [i for i in instances if i['state'] in ['running', 'pending']]
        if not running_instances:
            print_error("No running instances found")
            raise typer.Exit(1)

        instance_id = select_instance(running_instances)
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
    if current_state == 'stopped':
        print_success(f"Instance {instance_id} is already stopped")
        return

    if current_state not in ['running', 'pending']:
        print_error(f"Cannot stop instance in state: {current_state}")
        raise typer.Exit(1)

    # Stop instance
    print_warning("Stopping instance will shut down Windows gracefully")
    success = stop_instance(region, instance_id)
    if success:
        print_success(f"Instance {info['name']} is stopping")
        print(f"Check status with: winaws status {instance_id} --region {region}")
    else:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
