# aicrate - containerize your AI agents

`aicrate` is a Python CLI tool that packages and orchestrates AI agents, skills, and MCP (Model Context Protocol) servers as OCI artifacts in isolated container environments. It enables you to build reproducible, shareable AI workspaces by bundling these artifacts and tools into unified pods.

## Prerequisites

- python 3.9+
- [podman](https://podman.io/)
- [git](https://git-scm.com/)s

## Installation

```bash
pip install aicrate
```

## Basic Usage

```bash
# Run an AI environment with your workspace
aicrate run --workspace ~/myproject --config ./examples/aicrate.yml --mode podman

# Automatically dropped into the cli containers workspace (mounted project directory)
$ pwd
/workspace

# claude is ready to go
$ claude
```

## Configuration

Define your AI environment in a YAML configuration file:

```yaml
default:
  aicrate:
    image: quay.io/rhivos-ai-tools/aicrate:latest
    workspace: ~/
  skills:
    - quay.io/aicrate/anthropic/claude-api:latest
    - quay.io/aicrate/anthropic/pdf:latest
    - quay.io/aicrate/obra/test-driven-development:latest
  agents:
    - quay.io/aicrate/agency/engineering-code-reviewer:latest
  mcp:
    - image: quay.io/rhivos-ai-tools/mcp-testing-farm-mcp:latest
      port: 8081
      env:
        - MCP_TRANSPORT: sse
        - MCP_PORT: 8081
```

See [`examples/aicrate.yml`](./examples/aicrate.yml) for a complete configuration with 30+ skills and agents.

See [aicrate on quay.io](https://quay.io/organization/aicrate) for pre-built and ready to pull artifacts.
