import json
from dataclasses import dataclass


@dataclass
class MCPServer:

    Name: str
    Type: str
    URL: str


@dataclass
class ClaudeJSON:

    mcp_server: list[MCPServer]

    def to_config(self) -> str:
        server = {}
        for mcp in self.mcp_server:
            server[mcp.Name] = {"type": mcp.Type, "url": mcp.URL}

        return json.dumps(
            {"projects": {"/workspace": {"mcpServers": server}}},
            indent=2,
            sort_keys=True,
        )