# Unguard Scripts

This directory contains utility scripts and tools for the Unguard project.

## Available Tools

### Dynatrace Integration (`dynatrace/`)

Tools for retrieving and analyzing security vulnerabilities from Dynatrace with Davis AI risk assessments.

**Key Files:**
- `get-vulnerabilities.sh` - Shell script with presets for common queries
- `get_vulnerabilities.py` - Python script for programmatic access
- `get-vulnerabilities.dql` - DQL query examples for Dynatrace Notebooks
- `README.md` - Comprehensive documentation
- `EXAMPLES.md` - Practical usage examples

**Quick Start:**
```bash
cd dynatrace
export DT_TENANT="https://your-tenant.live.dynatrace.com"
export DT_API_TOKEN="your-api-token"

# Get all vulnerabilities
./get-vulnerabilities.sh all

# Get critical vulnerabilities with function in use
./get-vulnerabilities.sh priority --format markdown
```

See the [Dynatrace README](./dynatrace/README.md) for detailed documentation.

## Directory Structure

```
scripts/
├── README.md                           # This file
└── dynatrace/                          # Dynatrace integration tools
    ├── README.md                       # Dynatrace tools documentation
    ├── EXAMPLES.md                     # Usage examples
    ├── get-vulnerabilities.sh          # Shell wrapper script
    ├── get_vulnerabilities.py          # Python implementation
    ├── get-vulnerabilities.dql         # DQL query library
    └── requirements.txt                # Python dependencies
```

## Contributing

When adding new scripts:

1. Create a subdirectory for related scripts (e.g., `scripts/new-tool/`)
2. Include a README.md with usage instructions
3. Add executable permissions to scripts (`chmod +x`)
4. Document required environment variables
5. Update this README with a link to your tool

## License

Scripts in this directory follow the same license as the Unguard project.
