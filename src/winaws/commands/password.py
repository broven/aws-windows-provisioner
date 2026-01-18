"""Get instance password command."""

import typer
from typing import Optional

from winaws.utils.console import print_error, print_success, print_header, console
from winaws.core.ec2 import get_instance_info, list_managed_instances
from winaws.core.password import get_instance_password
from winaws.core.keypair import get_key_path
from winaws.prompts.interactive import select_instance


app = typer.Typer()


@app.command()
def password(
    instance_id: Optional[str] = typer.Argument(None, help="Instance ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
):
    """
    Get the Administrator password for a Windows instance.

    Decrypts the password using the stored private key.
    """
    print_header("WinAWS - Get Instance Password")

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
    key_name = info['key_name']

    # Get key path
    key_path = get_key_path(f"winaws-{instance_name}")
    if not key_path.exists():
        # Try with the key name from instance
        key_path = get_key_path(key_name)
        if not key_path.exists():
            print_error(f"Private key not found for instance {instance_id}")
            print_error(f"Expected key file: {key_path}")
            raise typer.Exit(1)

    # Get and decrypt password
    password = get_instance_password(
        region=region,
        instance_id=instance_id,
        private_key_path=str(key_path),
        max_wait=300,
    )

    if password:
        print_success("Password retrieved successfully!")
        console.print()
        console.print(f"[bold]Instance:[/bold] {instance_name} ({instance_id})")
        console.print(f"[bold]Public IP:[/bold] {info['public_ip']}")
        console.print(f"[bold]Username:[/bold] Administrator")
        console.print(f"[bold red]Password:[/bold red] {password}")
        console.print()
        console.print(f"[bold]RDP Command:[/bold]")
        console.print(f"  mstsc /v:{info['public_ip']}:3389")
    else:
        print_error("Failed to retrieve password")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
