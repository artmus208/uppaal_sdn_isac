"""Record a real initialize/tools-list exchange with the installed entry point."""
from __future__ import annotations

import asyncio
import json
import os
import sysconfig
from importlib.metadata import version
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def smoke() -> None:
    executable = Path(sysconfig.get_path("scripts")) / (
        "uppaal-mcp.exe" if os.name == "nt" else "uppaal-mcp"
    )
    parameters = StdioServerParameters(command=str(executable))
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert initialized.serverInfo.name == "uppaal-mcp"
            assert initialized.capabilities.tools is not None
            assert {"uppaal_version", "phy_extract_contract", "mac_extract_contract",
                    "sdn_extract_contract"}.issubset(names)
            assert len(names) == len(tools.tools)
            print(json.dumps({
                "evidence_class": "software startup diagnostics; no model checking",
                "status": "success",
                "sdk_version": version("mcp"),
                "server_command": [str(executable)],
                "initialize": initialized.model_dump(mode="json"),
                "tool_count": len(tools.tools),
                "tools_list": tools.model_dump(mode="json"),
            }, indent=2))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(smoke(), timeout=30))
