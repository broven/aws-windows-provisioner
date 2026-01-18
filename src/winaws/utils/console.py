"""Console output utilities using rich."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from typing import Optional

console = Console()


def print_success(message: str):
    """Print success message in green."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print error message in red."""
    console.print(f"[red]✗[/red] {message}", style="red")


def print_warning(message: str):
    """Print warning message in yellow."""
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


def print_info(message: str):
    """Print info message in blue."""
    console.print(f"[blue]ℹ[/blue] {message}", style="blue")


def print_header(title: str):
    """Print a header panel."""
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))


def create_table(title: str, columns: list[str]) -> Table:
    """Create a formatted table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column)
    return table


def print_key_value(key: str, value: str, key_style: str = "cyan"):
    """Print key-value pair."""
    console.print(f"[{key_style}]{key}:[/{key_style}] {value}")


def create_progress():
    """Create a progress spinner."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def print_instance_info(
    instance_id: str,
    public_ip: str,
    instance_type: str,
    name: str,
    region: str,
    password: Optional[str] = None,
):
    """Print instance connection information in a formatted panel."""
    info_text = Text()
    info_text.append("Instance Details\n\n", style="bold cyan")
    info_text.append(f"Instance ID:   {instance_id}\n", style="white")
    info_text.append(f"Name:          {name}\n", style="white")
    info_text.append(f"Type:          {instance_type}\n", style="white")
    info_text.append(f"Region:        {region}\n", style="white")
    info_text.append(f"Public IP:     {public_ip}\n", style="green")
    info_text.append(f"RDP Port:      3389\n", style="white")
    info_text.append(f"Username:      Administrator\n", style="yellow")

    if password:
        info_text.append(f"Password:      {password}\n", style="red")
    else:
        info_text.append("Password:      (retrieving...)\n", style="dim")

    info_text.append(f"\nRDP Command:\n", style="bold cyan")
    info_text.append(f"  mstsc /v:{public_ip}:3389\n", style="green")

    console.print(Panel(info_text, title="[bold]Connection Info[/bold]", border_style="green"))


def print_summary(items: dict[str, str]):
    """Print a summary of key-value pairs."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    for key, value in items.items():
        table.add_row(key, value)

    console.print(table)
