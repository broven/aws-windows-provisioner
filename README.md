# WinAWS - AWS Windows Provisioner CLI

A Python CLI tool to quickly create and manage Windows instances on AWS.

## Features

- 🚀 Interactive creation of Windows EC2 instances
- 🔐 Automatic password retrieval and decryption
- 📊 Instance lifecycle management (start, stop, terminate)
- 🌐 Automatic VPC and networking setup via CloudFormation
- 💰 Display instance pricing information
- 🎨 Beautiful terminal UI with rich output

## Installation

```bash
pip install -e .
```

## Quick Start

### Create a Windows Instance

```bash
winaws create
```

This will guide you through an interactive setup:
1. Select AWS region
2. Choose Windows version
3. Select instance type
4. Configure name and disk size
5. Set RDP access restrictions

### List Instances

```bash
winaws list
```

### Get Administrator Password

```bash
winaws password <instance-id>
```

### Manage Instance Lifecycle

```bash
# Start instance
winaws start <instance-id>

# Stop instance
winaws stop <instance-id>

# Terminate instance and cleanup resources
winaws terminate <instance-id>

# Check instance status
winaws status <instance-id>
```

## Requirements

- Python 3.10+
- AWS credentials configured (via `aws configure` or environment variables)
- Appropriate AWS IAM permissions for EC2, CloudFormation, and VPC operations

## Architecture

WinAWS uses CloudFormation to provision a complete Windows environment:
- VPC with public subnet
- Internet Gateway and routing
- Security Group (RDP port 3389)
- EC2 Windows instance
- Elastic IP

SSH key pairs are automatically generated and stored in `~/.winaws/keys/` for password decryption.

## License

MIT
