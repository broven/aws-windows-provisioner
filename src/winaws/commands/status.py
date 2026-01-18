"""Get instance status command."""

import typer
from typing import Optional
from datetime import datetime

from winaws.utils.console import print_error, print_header, console, print_summary
from winaws.core.ec2 import get_instance_info, list_managed_instances
from winaws.prompts.interactive import select_instance


app = typer.Typer()


@app.command()
def status(
    instance_id: Optional[str] = typer.Argument(None, help="Instance ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
):
    """
    Show detailed status of a Windows instance.

    Displays instance configuration, network settings, and current state.
    """
    print_header("WinAWS - Instance Status")

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

    # Format state with color
    state = info['state']
    state_color = {
        'running': 'green',
        'stopped': 'yellow',
        'stopping': 'yellow',
        'pending': 'blue',
        'terminated': 'red',
        'terminating': 'red',
    }.get(state, 'white')

    # Format launch time
    launch_time = info.get('launch_time')
    if launch_time:
        if isinstance(launch_time, datetime):
            launch_time_str = launch_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            launch_time_str = str(launch_time)
    else:
        launch_time_str = 'N/A'

    # Display summary
    console.print()
    print_summary({
        "Name": info.get('name', 'N/A'),
        "Instance ID": info['instance_id'],
        "Instance Type": info['instance_type'],
        "State": f"[{state_color}]{state}[/{state_color}]",
        "Region": region,
        "Availability Zone": info['availability_zone'],
    })

    console.print("\n[bold cyan]Network:[/bold cyan]")
    print_summary({
        "Public IP": info.get('public_ip', 'N/A'),
        "Private IP": info.get('private_ip', 'N/A'),
        "VPC ID": info.get('vpc_id', 'N/A'),
        "Subnet ID": info.get('subnet_id', 'N/A'),
    })

    console.print("\n[bold cyan]Configuration:[/bold cyan]")
    print_summary({
        "Key Name": info.get('key_name', 'N/A'),
        "Launch Time": launch_time_str,
        "Managed By": info.get('managed_by', 'N/A'),
    })

    # Display tags if any
    tags = info.get('tags', {})
    if tags:
        console.print("\n[bold cyan]Tags:[/bold cyan]")
        tag_summary = {k: v for k, v in tags.items() if k not in ['Name', 'ManagedBy']}
        if tag_summary:
            print_summary(tag_summary)

    # Display RDP connection info if running
    if state == 'running' and info.get('public_ip') != 'N/A':
        console.print("\n[bold green]RDP Connection:[/bold green]")
        console.print(f"  mstsc /v:{info['public_ip']}:3389")
        console.print(f"\n[dim]Get password with: winaws password {instance_id} --region {region}[/dim]")

    console.print()


if __name__ == "__main__":
    app()
