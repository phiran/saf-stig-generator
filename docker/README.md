# Docker Configuration for SAF STIG Generator

This directory contains Docker configuration for the SAF STIG Generator project, including specialized containers for SAF CLI and InSpec Runner services.

## Architecture

The system uses multiple specialized Docker containers:

- **Base Image** (`base.Dockerfile`) - Common Python environment
- **Services** (`services.Dockerfile`) - Generic MCP services (DISA STIG, MITRE Baseline, Memory)
- **Agents** (`agents.Dockerfile`) - ADK agent runtime
- **SAF CLI** (`saf.Dockerfile`) - Based on official `mitre/saf:latest` Docker image
- **InSpec Runner** (`inspec.Dockerfile`) - Based on official `chef/inspec:latest` Docker image

## Official Docker Images Used

### SAF CLI Service

- **Base Image**: `mitre/saf:latest`
- **Documentation**: [SAF CLI Docker Installation](https://saf-cli.mitre.org/#installation-via-docker)
- **Purpose**: Provides `saf generate`, `saf convert`, and other SAF CLI commands
- **Port**: 3000
- **Volume**: `/share` for file operations as per SAF CLI documentation

### InSpec Runner Service

- **Base Image**: `chef/inspec:latest`
- **Documentation**: [Chef InSpec Installation](https://docs.chef.io/inspec/install/)
- **Purpose**: Executes InSpec profiles for testing and validation
- **Port**: 3000
- **Environment**: `CHEF_LICENSE=accept-silent`

## Quick Start

1. **Build all images**:

   ```bash
   ./docker/build.sh
   ```

2. **Deploy services**:

   ```bash
   ./docker/deploy.sh development up
   ```

3. **Check health**:

   ```bash
   ./docker/health-check.sh
   ```

## Service Ports

- **ChromaDB**: 8000
- **DISA STIG Service**: 8001
- **MITRE Baseline Service**: 8002  
- **Memory Service**: 8003
- **SAF CLI Service**: 8004
- **InSpec Runner Service**: 8005
- **Orchestrator Agent**: 8080

## Volume Mounts

- `artifacts_data:/app/artifacts` - Shared artifacts directory
- `artifacts_data:/share` - SAF CLI shared volume (per official documentation)
- `/var/run/docker.sock:/var/run/docker.sock` - Docker socket for InSpec testing

## Examples

### SAF CLI Usage

The SAF CLI service provides access to official MITRE SAF commands:

```bash
# Generate InSpec profile from XCCDF
docker run -v $(pwd):/share mitre/saf generate inspec_profile -X benchmark.xml -o profile

# Convert results formats
docker run -v $(pwd):/share mitre/saf convert hdf2csv -i results.json -o report.csv
```

### InSpec Runner Usage

The InSpec Runner service can execute profiles against targets:

```bash
# Run InSpec profile against Docker container
docker run -v $(pwd):/app chef/inspec exec profile/ --target docker://container_id
```

## Environment Variables

- `SAF_ENVIRONMENT` - deployment environment (development/production)
- `CHEF_LICENSE=accept-silent` - Accept Chef license for InSpec
- `GITHUB_TOKEN` - GitHub token for MITRE baseline searches

## Troubleshooting

1. **SAF CLI not found**: Ensure using the official `mitre/saf` image
2. **InSpec license issues**: Set `CHEF_LICENSE=accept-silent`
3. **Permission issues**: Check volume mount permissions
4. **Port conflicts**: Verify no other services using the same ports

## References

- [SAF CLI Documentation](https://saf-cli.mitre.org/)
- [SAF CLI Docker Guide](https://saf-cli.mitre.org/#installation-via-docker)
- [Chef InSpec Documentation](https://docs.chef.io/inspec/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
