from __future__ import annotations

import asyncio
import builtins
import sys
import unittest
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from uppaal_mcp.server import build_mcp


class McpDependencyDiagnosticsTests(unittest.TestCase):
    def import_failure(self, error: ImportError, sdk_version: str | None) -> RuntimeError:
        real_import = builtins.__import__

        def fail_fastmcp(name, *args, **kwargs):
            if name == "mcp.server.fastmcp":
                raise error
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fail_fastmcp), patch(
            "uppaal_mcp.server.version",
            return_value=sdk_version,
            side_effect=PackageNotFoundError("mcp") if sdk_version is None else None,
        ):
            with self.assertRaises(RuntimeError) as caught:
                build_mcp()
        self.assertIs(caught.exception.__cause__, error)
        self.assertIn('python -m pip install "mcp>=1.28,<2"', str(caught.exception))
        return caught.exception

    def test_missing_sdk_is_reported_as_missing(self) -> None:
        error = ModuleNotFoundError("No module named 'mcp'", name="mcp")
        result = self.import_failure(error, None)
        self.assertIn("'mcp' Python package is not installed", str(result))

    def test_missing_fastmcp_api_is_reported_as_incompatible(self) -> None:
        error = ModuleNotFoundError(
            "No module named 'mcp.server.fastmcp'", name="mcp.server.fastmcp"
        )
        result = self.import_failure(error, "2.1.1")
        self.assertIn("mcp version 2.1.1", str(result))
        self.assertIn("incompatible or incomplete", str(result))
        self.assertNotIn("package is not installed", str(result))

    def test_missing_fastmcp_symbol_preserves_import_error(self) -> None:
        error = ImportError("cannot import name 'FastMCP' from 'mcp.server.fastmcp'")
        result = self.import_failure(error, "2.1.1")
        self.assertIn(str(error), str(result))

    def test_missing_transitive_dependency_is_not_reported_as_missing_sdk(self) -> None:
        error = ModuleNotFoundError("No module named 'anyio'", name="anyio")
        result = self.import_failure(error, "1.28.0")
        self.assertIn("No module named 'anyio'", str(result))
        self.assertNotIn("package is not installed", str(result))

    def test_import_failure_without_distribution_metadata_keeps_cause(self) -> None:
        error = ImportError("broken local mcp module")
        result = self.import_failure(error, None)
        self.assertIn("mcp version unknown", str(result))
        self.assertIn(str(error), str(result))


class McpStdioStartupTests(unittest.TestCase):
    def test_server_initializes_and_lists_registered_tools(self) -> None:
        # MCP is a required dependency: failed imports/startup must fail this test.
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def smoke() -> None:
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "uppaal_mcp.server"],
            )
            async with stdio_client(parameters) as (read, write):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    self.assertEqual(initialized.serverInfo.name, "uppaal-mcp")
                    self.assertIsNotNone(initialized.capabilities.tools)
                    result = await session.list_tools()
                    names = {tool.name for tool in result.tools}
                    expected = {tool.name for tool in await build_mcp().list_tools()}
                    self.assertEqual(names, expected)
                    self.assertEqual(len(names), len(result.tools))
                    self.assertTrue(
                        {
                            "uppaal_version",
                            "uppaal_validate_model",
                            "phy_extract_contract",
                            "mac_extract_contract",
                            "sdn_extract_contract",
                        }.issubset(names)
                    )

        asyncio.run(asyncio.wait_for(smoke(), timeout=30))


if __name__ == "__main__":
    unittest.main()
