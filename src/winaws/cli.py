"""WinAWS CLI - AWS Windows Provisioner."""

import typer
from typing import Optional

from winaws.commands.create import create
from winaws.commands.list import list_instances
from winaws.commands.status import status
from winaws.commands.start import start
from winaws.commands.stop import stop
from winaws.commands.terminate import terminate
from winaws.commands.password import password

app = typer.Typer(
    name="winaws",
    help="AWS Windows Provisioner CLI - Quickly create and manage Windows instances on AWS",
    add_completion=False,
)


# Register commands
app.command(name="create", help="Create a new Windows EC2 instance")(create)
app.command(name="list", help="List all managed Windows instances")(list_instances)
app.command(name="status", help="Show detailed instance status")(status)
app.command(name="start", help="Start a stopped instance")(start)
app.command(name="stop", help="Stop a running instance")(stop)
app.command(name="terminate", help="Terminate instance and cleanup resources")(terminate)
app.command(name="password", help="Get Administrator password")(password)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
):
    """
    WinAWS - AWS Windows Provisioner CLI

    A command-line tool to quickly create and manage Windows EC2 instances on AWS.

    Common workflows:

      1. Create a Windows instance:
         $ winaws create

      2. List all instances:
         $ winaws list --all

      3. Get Administrator password:
         $ winaws password <instance-id> --region us-east-1

      4. Stop an instance:
         $ winaws stop <instance-id> --region us-east-1

      5. Terminate an instance:
         $ winaws terminate <instance-id> --region us-east-1

    For more information on a specific command:
      $ winaws <command> --help
    """
    if version:
        typer.echo("winaws version 0.1.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
