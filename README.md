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
# Run a containerized AI agent with the current directory as workspace
# and no additional skills or agents
$ aicrate run

# ...use a different workspace, and skills and agents as defined in the config
$ aicrate run --workspace ~/myproject --config ./examples/aicrate.yml
```

After running `aicrate run`, the user is automatically dropped into the `/workspace`.

## Configuration

Define your AI environment in a YAML configuration file:

```yaml
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
  - image: quay.io/aicrate/mcp-testing-farm-mcp:latest
    port: 8081
    env:
      - MCP_TRANSPORT: sse
      - MCP_PORT: 8081
```

See [`examples/aicrate.yml`](./examples/aicrate.yml) for a complete configuration with 30+ skills and agents.

See [aicrate on quay.io](https://quay.io/organization/aicrate) for pre-built and ready to pull artifacts.


## Similar projects

- [LobsterTrap/puzzlepod](https://github.com/LobsterTrap/puzzlepod) \
`PuzzlePod` and aicrate leverage Podman and systemd and run the agents inside a container. However, while PuzzlePod adds a governance layer on top (e.g. automated commit/rollback decisions), `aicrate` leverages [OCI artifacts](https://edu.chainguard.dev/open-source/oci/what-are-oci-artifacts/) to manage skills and agents in OCI registries.
- [NVIDIA/OpenShell](https://github.com/NVIDIA/OpenShell) \
`OpenShell` provides a safe, private runtime for autonomous AI agents. Its goal are multi-tenant enterprise deployments while `aicrate` is intended for local usage by a single developer.
- [fletchgpc/agentbox](https://github.com/fletchgqc/agentbox) \
`agentbox` provides a container-based environment for automated AI agents for more safety. `aicrate` adds the concepts of skills and agents as OCI artifacts to use, share and maintain them.
