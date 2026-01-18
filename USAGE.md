# WinAWS Usage Guide

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from source
pip install .
```

## Prerequisites

1. **AWS Credentials**: Configure your AWS credentials using one of these methods:
   ```bash
   # Using AWS CLI
   aws configure

   # Or set environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

2. **IAM Permissions**: Your AWS user/role needs permissions for:
   - EC2 (create, describe, start, stop, terminate instances)
   - CloudFormation (create, delete stacks)
   - VPC (create VPCs, subnets, security groups, etc.)
   - Key Pairs (create, delete key pairs)

## Quick Start

### Create a Windows Instance (Interactive Mode)

```bash
winaws create
```

This will guide you through:
1. Selecting AWS region
2. Choosing Windows version (Server 2019, 2022, etc.)
3. Selecting instance type (t3.medium, t3.large, etc.)
4. Naming your instance
5. Setting disk size
6. Configuring RDP access restrictions

The tool will:
- Create a VPC with all necessary networking
- Launch the Windows instance
- Generate and store SSH key pair
- Wait for instance to boot
- Retrieve and decrypt the Administrator password
- Display connection information

### Create with Command-Line Options

```bash
winaws create \
  --region us-east-1 \
  --type t3.medium \
  --name my-windows-server \
  --ami ami-0c2b0d3fb02824d92 \
  --volume-size 80 \
  --rdp-cidr 203.0.113.0/24
```

### List All Instances

```bash
# List instances in a specific region
winaws list --region us-east-1

# List instances in all regions
winaws list --all
```

### Get Instance Status

```bash
# Specify instance ID
winaws status i-1234567890abcdef0 --region us-east-1

# Or select from a list
winaws status --region us-east-1
```

### Get Administrator Password

```bash
# Specify instance ID
winaws password i-1234567890abcdef0 --region us-east-1

# Or select from a list
winaws password --region us-east-1
```

Note: Password retrieval requires:
- The instance must be running
- Password data takes 4-5 minutes to become available after launch
- The private key must be stored in `~/.winaws/keys/`

### Start a Stopped Instance

```bash
# Specify instance ID
winaws start i-1234567890abcdef0 --region us-east-1

# Or select from a list of stopped instances
winaws start --region us-east-1
```

### Stop a Running Instance

```bash
# Specify instance ID
winaws stop i-1234567890abcdef0 --region us-east-1

# Or select from a list of running instances
winaws stop --region us-east-1
```

### Terminate Instance and Cleanup

```bash
# Specify instance ID
winaws terminate i-1234567890abcdef0 --region us-east-1

# Or select from a list
winaws terminate --region us-east-1

# Skip confirmation prompt
winaws terminate i-1234567890abcdef0 --region us-east-1 --yes
```

This will delete:
- The EC2 instance
- CloudFormation stack (including VPC, subnets, security groups, etc.)
- EC2 key pair (from AWS and local storage)

## Connecting to Your Instance

### Using Windows Remote Desktop (mstsc)

```bash
# On Windows
mstsc /v:<public-ip>:3389

# On macOS (requires Microsoft Remote Desktop from App Store)
open rdp://Administrator@<public-ip>

# On Linux (requires rdesktop or freerdp)
xfreerdp /v:<public-ip>:3389 /u:Administrator /p:<password>
```

**Credentials:**
- Username: `Administrator`
- Password: Retrieved using `winaws password <instance-id>`

## Advanced Usage

### Custom RDP Access Control

When creating an instance, you can restrict RDP access:

1. **Your IP only** (recommended):
   ```bash
   # Detected automatically in interactive mode
   winaws create --rdp-cidr $(curl -s https://api.ipify.org)/32
   ```

2. **Specific CIDR block**:
   ```bash
   winaws create --rdp-cidr 203.0.113.0/24
   ```

3. **Anywhere** (not recommended):
   ```bash
   winaws create --rdp-cidr 0.0.0.0/0
   ```

### Skip Password Retrieval

If you want to create the instance faster and retrieve the password later:

```bash
winaws create --skip-password
# ... later ...
winaws password <instance-id>
```

### Find Instances Across Regions

```bash
winaws list --all
```

This searches all AWS regions and displays all managed instances.

## File Locations

- **Private Keys**: `~/.winaws/keys/<instance-name>.pem`
- **CloudFormation Template**: Embedded in the package

## Troubleshooting

### Password Not Available

If password retrieval times out:
```bash
# Wait a few more minutes, then try again
winaws password <instance-id> --region <region>
```

### Cannot Connect via RDP

1. Check instance is running:
   ```bash
   winaws status <instance-id>
   ```

2. Verify security group allows your IP:
   - Check the RDP source CIDR used during creation
   - If your IP changed, you may need to update the security group manually

3. Check Windows is fully booted:
   - Wait 5-10 minutes after instance shows "running"
   - Check system logs in AWS console

### Region Auto-Detection Failed

Always specify `--region` if auto-detection fails:
```bash
winaws <command> <instance-id> --region us-east-1
```

### Instance Not Found in List

Make sure you're checking the correct region:
```bash
# Check all regions
winaws list --all
```

## Cost Management

Remember to stop or terminate instances when not in use to save costs:

- **Stopped instances**: Still incur EBS storage charges but no compute charges
- **Terminated instances**: All resources deleted, no charges (except EBS snapshots if created)

```bash
# Stop for temporary pause
winaws stop <instance-id>

# Terminate to completely remove
winaws terminate <instance-id>
```

## Security Best Practices

1. **Restrict RDP access**: Always use `--rdp-cidr` with your specific IP or CIDR block
2. **Rotate passwords**: Change Administrator password after first login
3. **Keep instances patched**: Run Windows Update regularly
4. **Use strong passwords**: The auto-generated password is complex, keep it secure
5. **Monitor usage**: Use `winaws list` to track all instances

## Example Workflows

### Quick Test Server

```bash
# Create a small Windows server for testing
winaws create
# Select region: us-east-1
# Select Windows: Server 2022
# Select type: t3.medium
# Name: test-server
# Volume: 50 GB
# RDP: My IP only

# Use it...
# Then cleanup
winaws terminate test-server
```

### Development Environment

```bash
# Create a larger instance for development
winaws create \
  --region us-west-2 \
  --type t3.xlarge \
  --name dev-windows \
  --volume-size 100 \
  --rdp-cidr $(curl -s https://api.ipify.org)/32

# Stop it overnight
winaws stop dev-windows --region us-west-2

# Start it next day
winaws start dev-windows --region us-west-2
```

## Getting Help

```bash
# General help
winaws --help

# Command-specific help
winaws create --help
winaws list --help
winaws status --help
```

## Version Information

```bash
winaws --version
```
