# Aqua Security License Utility

A command-line tool for extracting and analyzing license utilization data from Aqua Security platform.

## Features

- Extract license information in JSON or table format
- Generate license breakdown by application scope
- Export data to CSV and JSON files
- Secure credential storage with profile management
- Clean JSON output for automation and integration

## Installation

### From source

```bash
git clone https://github.com/andreazorzetto/aquasec-license-util.git
cd aquasec-license-util

# Optionally create a Python vitrual environment
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Prerequisites

- **Authentication**: This utility requires username/password authentication to connect to Aqua Security platform
- **Python library**: The `aquasec` library must be installed:

```bash
pip install aquasec
```

## Quick Start

### Initial Setup

```bash
# Interactive setup wizard
python aqua_license_util.py setup
```

### Basic Usage

```bash
# Show license information (JSON output)
python aqua_license_util.py show

# Show license information in table format
python aqua_license_util.py show -v

# Generate license breakdown (JSON output)
python aqua_license_util.py breakdown

# Generate license breakdown in table format
python aqua_license_util.py breakdown -v

# Export to files
python aqua_license_util.py breakdown --csv-file report.csv --json-file report.json
```

## Output Modes

1. **Default**: Clean JSON output only
2. **Verbose (-v)**: Human-readable tables and messages
3. **Debug (-d)**: Detailed execution with API calls

## Environment Variables

If you prefer environment variables over the setup wizard:

```bash
# Username/Password (Required)
export AQUA_USER=your-email@company.com
export AQUA_PASSWORD=your-password
export CSP_ENDPOINT='https://xyz.cloud.aquasec.com'
```

**Note**: This utility requires username/password authentication. API key authentication is not supported in this implementation.

## Profile Management

```bash
# List profiles
python aqua_license_util.py profiles

# Create a new profile
python aqua_license_util.py setup --profile production

# Use specific profile
python aqua_license_util.py show --profile production
```

## Examples

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Check Aqua License Usage
  run: |
    python aqua_license_util.py show > license.json
    
    # Process the JSON output
    jq '.num_repositories' license.json
```

### Monitoring Script

```bash
#!/bin/bash
# Get license data as JSON
LICENSE_DATA=$(python aqua_license_util.py show)

# Extract metrics
REPOS=$(echo "$LICENSE_DATA" | jq '.num_repositories')
ENFORCERS=$(echo "$LICENSE_DATA" | jq '.num_enforcers')

# Alert if approaching limits
if [ $REPOS -gt 900 ]; then
  echo "Warning: Repository usage at $REPOS/1000"
fi
```

## License

MIT License

## Contributing

Issues and pull requests are welcome at [github.com/andreazorzetto/aquasec-license-util](https://github.com/andreazorzetto/aquasec-license-util)