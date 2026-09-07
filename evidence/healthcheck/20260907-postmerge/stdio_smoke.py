"""Probe the installed MCP entry point using only read-only tools."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    executable = Path(sys.executable).parent / ("uppaal-mcp.exe" if sys.platform == "win32" else "uppaal-mcp")
    async with stdio_client(StdioServerParameters(command=str(executable))) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            assert initialized.serverInfo.name == "uppaal-mcp"
            assert len(names) == len(set(names))
            calls = []
            for name, arguments in [
                ("uppaal_list_examples", {}),
                ("phy_validate_contract", {}),
                ("mac_validate_contract", {}),
                ("sdn_validate_contract", {}),
            ]:
                assert name in names
                result = await session.call_tool(name, arguments)
                calls.append({"name": name, "arguments": arguments, "result": result.model_dump(mode="json")})
                assert not result.isError, calls[-1]
            print(json.dumps({"server": initialized.model_dump(mode="json"),
                              "tools": names, "tool_count": len(names), "calls": calls}, indent=2))


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=45))
