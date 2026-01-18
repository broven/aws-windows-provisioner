"""CloudFormation stack operations."""

import time
from pathlib import Path
from typing import Optional, Dict, Any

from winaws.utils.aws import get_cloudformation_client
from winaws.utils.console import (
    print_success,
    print_error,
    print_info,
    print_warning,
    create_progress,
)


def get_template_path() -> Path:
    """Get the path to the CloudFormation template."""
    return Path(__file__).parent.parent / "templates" / "vpc_windows.yaml"


def load_template() -> str:
    """Load the CloudFormation template."""
    template_path = get_template_path()
    return template_path.read_text()


def create_stack(
    region: str,
    stack_name: str,
    parameters: Dict[str, str],
    wait: bool = True,
) -> Optional[str]:
    """
    Create a CloudFormation stack.

    Args:
        region: AWS region
        stack_name: Name for the stack
        parameters: CloudFormation parameters
        wait: Whether to wait for stack creation to complete

    Returns:
        Stack ID if successful, None otherwise
    """
    cfn = get_cloudformation_client(region)
    template = load_template()

    # Convert parameters to CloudFormation format
    cfn_parameters = [
        {'ParameterKey': key, 'ParameterValue': value}
        for key, value in parameters.items()
    ]

    try:
        response = cfn.create_stack(
            StackName=stack_name,
            TemplateBody=template,
            Parameters=cfn_parameters,
            Capabilities=['CAPABILITY_IAM'],
            Tags=[
                {'Key': 'ManagedBy', 'Value': 'winaws'},
                {'Key': 'Name', 'Value': stack_name},
            ],
        )

        stack_id = response['StackId']
        print_success(f"Created CloudFormation stack: {stack_name}")
        print_info(f"Stack ID: {stack_id}")

        if wait:
            wait_for_stack_creation(region, stack_name)

        return stack_id

    except Exception as e:
        print_error(f"Failed to create stack: {e}")
        return None


def wait_for_stack_creation(region: str, stack_name: str, timeout: int = 600) -> bool:
    """
    Wait for CloudFormation stack creation to complete.

    Args:
        region: AWS region
        stack_name: Name of the stack
        timeout: Maximum time to wait in seconds

    Returns:
        True if successful, False otherwise
    """
    cfn = get_cloudformation_client(region)
    start_time = time.time()

    print_info("Waiting for stack creation to complete...")
    print_warning("This typically takes 3-5 minutes")

    with create_progress() as progress:
        task = progress.add_task("Creating stack...", total=None)

        while time.time() - start_time < timeout:
            try:
                response = cfn.describe_stacks(StackName=stack_name)
                stack = response['Stacks'][0]
                status = stack['StackStatus']

                elapsed = int(time.time() - start_time)
                progress.update(task, description=f"Stack status: {status} ({elapsed}s)")

                if status == 'CREATE_COMPLETE':
                    print_success("Stack created successfully!")
                    return True

                elif status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED']:
                    print_error(f"Stack creation failed with status: {status}")
                    print_stack_events(region, stack_name, limit=10)
                    return False

                time.sleep(10)

            except Exception as e:
                print_error(f"Error checking stack status: {e}")
                return False

    print_error(f"Timeout waiting for stack creation after {timeout} seconds")
    return False


def delete_stack(region: str, stack_name: str, wait: bool = True) -> bool:
    """
    Delete a CloudFormation stack.

    Args:
        region: AWS region
        stack_name: Name of the stack
        wait: Whether to wait for deletion to complete

    Returns:
        True if successful, False otherwise
    """
    cfn = get_cloudformation_client(region)

    try:
        cfn.delete_stack(StackName=stack_name)
        print_success(f"Deleting CloudFormation stack: {stack_name}")

        if wait:
            wait_for_stack_deletion(region, stack_name)

        return True

    except Exception as e:
        print_error(f"Failed to delete stack: {e}")
        return False


def wait_for_stack_deletion(region: str, stack_name: str, timeout: int = 600) -> bool:
    """
    Wait for CloudFormation stack deletion to complete.

    Args:
        region: AWS region
        stack_name: Name of the stack
        timeout: Maximum time to wait in seconds

    Returns:
        True if successful, False otherwise
    """
    cfn = get_cloudformation_client(region)
    start_time = time.time()

    print_info("Waiting for stack deletion to complete...")

    with create_progress() as progress:
        task = progress.add_task("Deleting stack...", total=None)

        while time.time() - start_time < timeout:
            try:
                response = cfn.describe_stacks(StackName=stack_name)
                stack = response['Stacks'][0]
                status = stack['StackStatus']

                elapsed = int(time.time() - start_time)
                progress.update(task, description=f"Stack status: {status} ({elapsed}s)")

                if status == 'DELETE_FAILED':
                    print_error("Stack deletion failed")
                    print_stack_events(region, stack_name, limit=10)
                    return False

                time.sleep(10)

            except cfn.exceptions.ClientError as e:
                if 'does not exist' in str(e):
                    print_success("Stack deleted successfully!")
                    return True
                else:
                    print_error(f"Error checking stack status: {e}")
                    return False

    print_error(f"Timeout waiting for stack deletion after {timeout} seconds")
    return False


def get_stack_outputs(region: str, stack_name: str) -> Dict[str, str]:
    """
    Get CloudFormation stack outputs.

    Args:
        region: AWS region
        stack_name: Name of the stack

    Returns:
        Dictionary of output key-value pairs
    """
    cfn = get_cloudformation_client(region)

    try:
        response = cfn.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        outputs = stack.get('Outputs', [])

        return {
            output['OutputKey']: output['OutputValue']
            for output in outputs
        }

    except Exception as e:
        print_error(f"Failed to get stack outputs: {e}")
        return {}


def get_stack_info(region: str, stack_name: str) -> Optional[Dict[str, Any]]:
    """
    Get CloudFormation stack information.

    Args:
        region: AWS region
        stack_name: Name of the stack

    Returns:
        Dictionary with stack information, or None if not found
    """
    cfn = get_cloudformation_client(region)

    try:
        response = cfn.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]

        return {
            'stack_id': stack['StackId'],
            'stack_name': stack['StackName'],
            'status': stack['StackStatus'],
            'creation_time': stack.get('CreationTime'),
            'outputs': {o['OutputKey']: o['OutputValue'] for o in stack.get('Outputs', [])},
            'parameters': {p['ParameterKey']: p['ParameterValue'] for p in stack.get('Parameters', [])},
        }

    except Exception as e:
        print_error(f"Failed to get stack info: {e}")
        return None


def stack_exists(region: str, stack_name: str) -> bool:
    """
    Check if a CloudFormation stack exists.

    Args:
        region: AWS region
        stack_name: Name of the stack

    Returns:
        True if exists, False otherwise
    """
    cfn = get_cloudformation_client(region)

    try:
        cfn.describe_stacks(StackName=stack_name)
        return True
    except cfn.exceptions.ClientError:
        return False


def list_stacks(region: str) -> list[Dict[str, Any]]:
    """
    List all CloudFormation stacks managed by winaws.

    Args:
        region: AWS region

    Returns:
        List of stack dictionaries
    """
    cfn = get_cloudformation_client(region)

    try:
        response = cfn.describe_stacks()
        stacks = []

        for stack in response['Stacks']:
            # Filter for winaws managed stacks
            tags = {tag['Key']: tag['Value'] for tag in stack.get('Tags', [])}
            if tags.get('ManagedBy') == 'winaws':
                stacks.append({
                    'stack_name': stack['StackName'],
                    'status': stack['StackStatus'],
                    'creation_time': stack.get('CreationTime'),
                    'tags': tags,
                })

        return stacks

    except Exception as e:
        print_error(f"Failed to list stacks: {e}")
        return []


def print_stack_events(region: str, stack_name: str, limit: int = 20):
    """
    Print recent CloudFormation stack events.

    Args:
        region: AWS region
        stack_name: Name of the stack
        limit: Maximum number of events to show
    """
    cfn = get_cloudformation_client(region)

    try:
        response = cfn.describe_stack_events(StackName=stack_name)
        events = response['StackEvents'][:limit]

        print_info(f"Recent events for stack '{stack_name}':")
        for event in events:
            status = event['ResourceStatus']
            resource = event['LogicalResourceId']
            reason = event.get('ResourceStatusReason', '')

            if 'FAILED' in status:
                print_error(f"{status}: {resource} - {reason}")
            elif 'COMPLETE' in status:
                print_success(f"{status}: {resource}")
            else:
                print_info(f"{status}: {resource}")

    except Exception as e:
        print_error(f"Failed to get stack events: {e}")
