# Aqua Security License Utility

A command-line tool for extracting and analyzing license utilization data from Aqua Security platform.

## Features

- Extract license information in JSON or table format
- Generate license breakdown by application scope
- Export data to CSV and JSON files
- Secure credential storage with profile management
- Clean JSON output for automation and integration

## Installation

### From source (recommended)

```bash
git clone https://github.com/andreazorzetto/aquasec-license-util.git
cd aquasec-license-util
pip install -r requirements.txt
```

### Using Docker

```bash
docker pull ghcr.io/andreazorzetto/aquasec-license-util:latest
```

### Prerequisites

This utility requires the `aquasec` library:

```bash
pip install aquasec
```

## Quick Start

### Initial Setup

```bash
# Interactive setup wizard
python aqua_license_util.py setup

# Or using Docker
docker run -it -v ~/.aqua:/root/.aqua ghcr.io/andreazorzetto/aquasec-license-util:latest setup
```

### Basic Usage

```bash
# Show license information (JSON output)
python aqua_license_util.py show

# Show license information in table format
python aqua_license_util.py show -v

# Generate license breakdown
python aqua_license_util.py breakdown

# Export to files
python aqua_license_util.py breakdown --csv-file report.csv --json-file report.json
```

### Using Docker

```bash
# Run with saved profile
docker run -v ~/.aqua:/root/.aqua ghcr.io/andreazorzetto/aquasec-license-util:latest show

# Run with environment variables
docker run --env-file aqua.env ghcr.io/andreazorzetto/aquasec-license-util:latest breakdown

# Export files to host
docker run -v ~/.aqua:/root/.aqua -v $(pwd):/output \
  ghcr.io/andreazorzetto/aquasec-license-util:latest \
  breakdown --csv-file /output/report.csv
```

## Output Modes

1. **Default**: Clean JSON output only
2. **Verbose (-v)**: Human-readable tables and messages
3. **Debug (-d)**: Detailed execution with API calls

## Environment Variables

If you prefer environment variables over the setup wizard:

```bash
# API Keys (recommended)
export AQUA_KEY=your-api-key
export AQUA_SECRET=your-api-secret
export AQUA_ROLE=Administrator
export AQUA_METHODS=ANY
export AQUA_ENDPOINT='https://api.cloudsploit.com'
export CSP_ENDPOINT='https://xyz.cloud.aquasec.com'

# Username/Password
export AQUA_USER=your-email@company.com
export AQUA_PASSWORD=your-password
export CSP_ENDPOINT='https://xyz.cloud.aquasec.com'
```

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
    docker run -v ${{ secrets.AQUA_CREDS }}:/root/.aqua \
      ghcr.io/andreazorzetto/aquasec-license-util:latest show > license.json
    
    # Process the JSON output
    jq '.num_repositories' license.json
```

### Monitoring Script

```bash
#!/bin/bash
# Get license data as JSON
LICENSE_DATA=$(docker run -v ~/.aqua:/root/.aqua \
  ghcr.io/andreazorzetto/aquasec-license-util:latest show)

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