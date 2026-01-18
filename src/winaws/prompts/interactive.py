"""Interactive prompts for user input."""

import questionary
from typing import Optional, Dict, Any

from winaws.utils.aws import get_available_regions, get_current_region
from winaws.core.ec2 import get_windows_amis, get_instance_types, get_current_public_ip


def prompt_region() -> Optional[str]:
    """Prompt user to select AWS region."""
    regions = get_available_regions()
    current = get_current_region()

    # Highlight current region if set
    default = current if current in regions else None

    region = questionary.select(
        "Select AWS region:",
        choices=regions,
        default=default,
    ).ask()

    return region


def prompt_windows_ami(region: str) -> Optional[Dict[str, str]]:
    """Prompt user to select Windows AMI."""
    print("Fetching available Windows AMIs...")
    amis = get_windows_amis(region, limit=15)

    if not amis:
        return None

    # Format choices with name
    choices = []
    for ami in amis:
        # Extract version from name (e.g., Windows_Server-2022-English-Full-Base-2024.01.10)
        name = ami['name']
        display = name.replace('Windows_Server-', 'Windows Server ').replace('-English-Full-Base-', ' ')
        choices.append(questionary.Choice(title=display, value=ami))

    ami = questionary.select(
        "Select Windows version:",
        choices=choices,
    ).ask()

    return ami


def prompt_instance_type(region: str) -> Optional[str]:
    """Prompt user to select instance type."""
    print("Fetching instance types...")
    types = get_instance_types(region)

    if not types:
        return None

    # Format choices with specs
    choices = []
    for t in types:
        display = f"{t['type']:15} - {t['vcpu']:2} vCPU, {t['memory_gb']:5.1f} GB RAM - {t['network']}"
        choices.append(questionary.Choice(title=display, value=t['type']))

    instance_type = questionary.select(
        "Select instance type:",
        choices=choices,
    ).ask()

    return instance_type


def prompt_instance_name() -> Optional[str]:
    """Prompt user for instance name."""
    name = questionary.text(
        "Enter instance name:",
        validate=lambda text: len(text) > 0 or "Name cannot be empty",
    ).ask()

    return name


def prompt_volume_size() -> Optional[int]:
    """Prompt user for root volume size."""
    size = questionary.text(
        "Enter root volume size (GB):",
        default="50",
        validate=lambda text: text.isdigit() and 30 <= int(text) <= 16384 or "Must be between 30 and 16384",
    ).ask()

    return int(size) if size else None


def prompt_rdp_access() -> Optional[str]:
    """Prompt user for RDP access restriction."""
    current_ip = get_current_public_ip()

    choices = []

    if current_ip:
        choices.append(
            questionary.Choice(
                title=f"My IP only ({current_ip}/32)",
                value=f"{current_ip}/32"
            )
        )

    choices.extend([
        questionary.Choice(title="Anywhere (0.0.0.0/0) - Not recommended", value="0.0.0.0/0"),
        questionary.Choice(title="Custom CIDR", value="custom"),
    ])

    selection = questionary.select(
        "RDP access restriction:",
        choices=choices,
    ).ask()

    if selection == "custom":
        cidr = questionary.text(
            "Enter CIDR block (e.g., 203.0.113.0/24):",
            validate=lambda text: validate_cidr(text) or "Invalid CIDR format",
        ).ask()
        return cidr

    return selection


def validate_cidr(cidr: str) -> bool:
    """Validate CIDR notation."""
    import re
    pattern = r'^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$'
    if not re.match(pattern, cidr):
        return False

    # Validate IP octets and prefix
    parts = cidr.split('/')
    ip_parts = parts[0].split('.')

    if not all(0 <= int(p) <= 255 for p in ip_parts):
        return False

    if not 0 <= int(parts[1]) <= 32:
        return False

    return True


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for yes/no confirmation."""
    result = questionary.confirm(message, default=default).ask()
    return result if result is not None else False


def prompt_create_configuration(region: str) -> Optional[Dict[str, Any]]:
    """
    Gather all configuration for creating a Windows instance.

    Returns:
        Dictionary with configuration, or None if cancelled
    """
    # Select region if not provided
    if not region:
        region = prompt_region()
        if not region:
            return None

    # Select Windows AMI
    ami = prompt_windows_ami(region)
    if not ami:
        return None

    # Select instance type
    instance_type = prompt_instance_type(region)
    if not instance_type:
        return None

    # Get instance name
    instance_name = prompt_instance_name()
    if not instance_name:
        return None

    # Get volume size
    volume_size = prompt_volume_size()
    if not volume_size:
        return None

    # Get RDP access restriction
    rdp_cidr = prompt_rdp_access()
    if not rdp_cidr:
        return None

    # Confirm configuration
    print("\nConfiguration Summary:")
    print(f"  Region:         {region}")
    print(f"  Windows:        {ami['name']}")
    print(f"  Instance Type:  {instance_type}")
    print(f"  Name:           {instance_name}")
    print(f"  Volume Size:    {volume_size} GB")
    print(f"  RDP Access:     {rdp_cidr}")
    print()

    if not confirm_action("Create instance with this configuration?", default=True):
        return None

    return {
        'region': region,
        'ami_id': ami['id'],
        'ami_name': ami['name'],
        'instance_type': instance_type,
        'instance_name': instance_name,
        'volume_size': volume_size,
        'rdp_cidr': rdp_cidr,
    }


def select_instance(instances: list[Dict[str, Any]]) -> Optional[str]:
    """
    Prompt user to select an instance from a list.

    Args:
        instances: List of instance dictionaries

    Returns:
        Selected instance ID, or None if cancelled
    """
    if not instances:
        return None

    choices = []
    for inst in instances:
        name = inst.get('name', 'N/A')
        instance_id = inst['instance_id']
        state = inst['state']
        instance_type = inst['instance_type']
        public_ip = inst.get('public_ip', 'N/A')

        display = f"{name:20} | {instance_id:19} | {state:10} | {instance_type:12} | {public_ip}"
        choices.append(questionary.Choice(title=display, value=instance_id))

    instance_id = questionary.select(
        "Select instance:",
        choices=choices,
    ).ask()

    return instance_id
