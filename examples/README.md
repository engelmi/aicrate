# Examples

```bash
# 1. Clone AIcrate with submodules
$ git clone --recurse-submodules git@github.com:engelmi/aicrate.git

# 2. Explore available skills, agents and mcp
$ ./tools/aicrate-builder skills ls
$ ./tools/aicrate-builder agents ls
$ ./tools/aicrate-builder mcps ls

# 3. Build OCI artifacts for skills and agents, and images for MCP servers
# use the --name option to build only subset, otherwise all are built (supports globbing)
$ ./tools/aicrate-builder skills build
$ ./tools/aicrate-builder agents build
$ ./tools/aicrate-builder mcps build

# 4. Update the examples/aicrate.yml (or create a new one)

# 5. Run aicrate, pass the updated configuration to it and choose the local directory
# mounted into the workbench container
$ PYTHONPATH=. python aicrate/aicrate run --config ./examples/aicrate.yml --workspace ~/<your-directory> --mode podman
```
