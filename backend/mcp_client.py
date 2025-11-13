"""
MCP Client for connecting to external MCP servers (like BigQuery).
This allows using existing MCP tools without creating custom implementations.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Client for connecting to MCP servers and using their tools."""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, Dict[str, Any]] = {}
    
    async def connect_server(self, server_name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """
        Connect to an MCP server.
        
        Args:
            server_name: Name to identify this server
            command: Command to run the MCP server
            args: Command arguments
            env: Environment variables for the server
        """
        if args is None:
            args = []
        if env is None:
            env = {}
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        # Connect to the server
        stdio_transport = await stdio_client(server_params)
        session = ClientSession(stdio_transport[0], stdio_transport[1])
        
        await session.initialize()
        
        # Store session
        self.sessions[server_name] = session
        
        # Get available tools from this server
        tools_list = await session.list_tools()
        for tool in tools_list.tools:
            tool_key = f"{server_name}:{tool.name}"
            self.available_tools[tool_key] = {
                "server": server_name,
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        
        return len(tools_list.tools)
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on an MCP server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool result
        """
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        
        return result
    
    def get_tools_for_gemini(self) -> List[Dict[str, Any]]:
        """
        Get tool declarations in Gemini-compatible format.
        
        Returns:
            List of tool declarations for Gemini function calling
        """
        tools = []
        for tool_key, tool_info in self.available_tools.items():
            tools.append({
                "name": tool_key.replace(":", "_"),  # Replace : with _ for Gemini
                "description": tool_info["description"],
                "parameters": tool_info["input_schema"]
            })
        return tools
    
    async def disconnect_all(self):
        """Disconnect all MCP servers."""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()
        self.available_tools.clear()


# Global MCP client instance
mcp_client = MCPClient()

