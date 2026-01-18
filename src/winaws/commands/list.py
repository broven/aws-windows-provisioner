"""List instances command."""

import typer
from typing import Optional

from winaws.utils.console import print_error, print_header, create_table, console
from winaws.core.ec2 import list_managed_instances
from winaws.utils.aws import get_available_regions


app = typer.Typer()


@app.command()
def list_instances(
    region: Optional[str] = typer.Option(None, "--region", "-r", help="AWS region"),
    all_regions: bool = typer.Option(False, "--all", "-a", help="List instances in all regions"),
):
    """
    List all Windows instances managed by winaws.

    By default, lists instances in the specified region.
    Use --all to search all regions.
    """
    print_header("WinAWS - List Instances")

    if all_regions:
        regions = get_available_regions()
    elif region:
        regions = [region]
    else:
        print_error("Please specify --region or use --all to search all regions")
        raise typer.Exit(1)

    all_instances = []

    for reg in regions:
        instances = list_managed_instances(reg)
        for inst in instances:
            inst['region'] = reg
            all_instances.append(inst)

    if not all_instances:
        console.print("[yellow]No managed instances found[/yellow]")
        return

    # Create table
    table = create_table(
        f"Found {len(all_instances)} instance(s)",
        ["Name", "Instance ID", "Type", "State", "Public IP", "Region"]
    )

    for inst in all_instances:
        state_color = {
            'running': 'green',
            'stopped': 'yellow',
            'stopping': 'yellow',
            'pending': 'blue',
            'terminated': 'red',
            'terminating': 'red',
        }.get(inst['state'], 'white')

        table.add_row(
            inst.get('name', 'N/A'),
            inst['instance_id'],
            inst['instance_type'],
            f"[{state_color}]{inst['state']}[/{state_color}]",
            inst.get('public_ip', 'N/A'),
            inst['region'],
        )

    console.print(table)


if __name__ == "__main__":
    app()
