"""Async client for the local CRM MCP server."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import TracebackType
from typing import Any

from mcp import Client, StdioServerParameters


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = PROJECT_ROOT / "src" / "mcp_server.py"

EXPECTED_SERVER_NAME = "salesforce-crm-troubleshooting"


class MCPClient:
    '''Manage one connection to the local MCP server'''

    def __init__(self) -> None:
        self._context: Any | None = None
        self.client: Any | None = None

    async def __aenter__(self) -> MCPClient:
        '''Connect to and initialize the MCP Server'''
        server = StdioServerParameters(
            command = sys.executable,
            args=[str(SERVER_PATH)],
            cwd = PROJECT_ROOT
        )
        self._context = Client(
            server,
            read_timeout_seconds=10,
        )
        self.client = await self._context.__aenter__()
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        '''Close the MCP server connection'''
        if self._context is not None:
            await self._context.__aexit__(
                exc_type,
                exc_value,
                traceback,
            )
        self.client = None
        self._context = None

    def _require_client(self) -> Any:
        '''Return the active client'''
        if self.client is None:
            raise RuntimeError(
                'MCPClient must be used inside "async with".'
            )

        return self.client

    async def list_tools(self) -> list[Any]:
        '''Return the MCP server's tools and schemas'''
        client = self._require_client()
        result = await client.list_tools()
        return list(result.tools)

    async def call_tool(
            self,
            name: str,
            arguments: dict[str,Any],
    )-> Any :
        '''Call one MCP tool and return its raw result.'''

        client = self._require_client()
        return await client.call_tool(
            name,
            arguments,
        )
