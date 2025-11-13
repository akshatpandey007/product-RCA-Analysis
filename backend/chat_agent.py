"""
Agentic chat agent with Gemini integration, task management, and MCP tool support.
"""

import json
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from config import settings

# Optional: Import MCP client if BigQuery integration is enabled
try:
    if settings.enable_bigquery_mcp:
        from mcp_client import mcp_client
        MCP_ENABLED = True
    else:
        MCP_ENABLED = False
except Exception:
    MCP_ENABLED = False


# ============================================================================
# Task Management Models
# ============================================================================

class Task(BaseModel):
    """Represents a single task in the agent's task list."""
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None


class TaskList(BaseModel):
    """Manages a list of tasks for the agent."""
    tasks: List[Task] = []
    
    def add_task(self, description: str) -> Task:
        """Add a new task to the list."""
        task_id = len(self.tasks) + 1
        task = Task(id=task_id, description=description)
        self.tasks.append(task)
        return task
    
    def update_task(self, task_id: int, status: str, result: Optional[str] = None):
        """Update task status and result."""
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                if result:
                    task.result = result
                break
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return [t for t in self.tasks if t.status == "pending"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task list to dictionary."""
        return {"tasks": [task.model_dump() for task in self.tasks]}


# ============================================================================
# MCP Tool Integration
# ============================================================================

class MCPToolRegistry:
    """
    Registry for MCP server tools. 
    Add your MCP tools here with simple copy-paste configuration.
    """
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: callable):
        """
        Register an MCP tool.
        
        Args:
            name: Tool name
            description: Tool description for the LLM
            parameters: JSON schema for tool parameters
            handler: Async function to execute the tool
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """Get tool declarations in Gemini function calling format."""
        declarations = []
        for tool in self.tools.values():
            declarations.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            })
        return declarations
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered tool."""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        
        handler = self.tools[name]["handler"]
        return await handler(**arguments)


# ============================================================================
# Example MCP Tools (Easy to extend)
# ============================================================================

async def search_web_tool(query: str) -> str:
    """Example: Web search tool."""
    # Placeholder - integrate your actual search API
    return f"Search results for: {query}"


async def calculate_tool(expression: str) -> str:
    """Example: Calculator tool."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


async def create_task_list_tool(tasks: List[str]) -> Dict[str, Any]:
    """Tool to create a task list."""
    task_list = TaskList()
    for task_desc in tasks:
        task_list.add_task(task_desc)
    return task_list.to_dict()


# ============================================================================
# Initialize Tool Registry (Copy-Paste Configuration Area)
# ============================================================================

mcp_tools = MCPToolRegistry()

# Register tools here - simple copy-paste to add new tools
mcp_tools.register_tool(
    name="search_web",
    description="Search the web for information",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"]
    },
    handler=search_web_tool
)

mcp_tools.register_tool(
    name="calculate",
    description="Perform mathematical calculations",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
        },
        "required": ["expression"]
    },
    handler=calculate_tool
)

mcp_tools.register_tool(
    name="create_task_list",
    description="Create a task list to break down complex problems",
    parameters={
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of task descriptions"
            }
        },
        "required": ["tasks"]
    },
    handler=create_task_list_tool
)

# ============================================================================
# BigQuery Tools (if enabled)
# ============================================================================

if MCP_ENABLED and settings.enable_bigquery_mcp:
    from bigquery_tools import (
        bigquery_list_datasets,
        bigquery_list_tables,
        bigquery_get_schema,
        bigquery_query
    )
    
    mcp_tools.register_tool(
        name="bigquery_list_datasets",
        description="List all available BigQuery datasets in the project",
        parameters={
            "type": "object",
            "properties": {}
        },
        handler=bigquery_list_datasets
    )
    
    mcp_tools.register_tool(
        name="bigquery_list_tables",
        description="List all tables in a specific BigQuery dataset",
        parameters={
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "string",
                    "description": "The ID of the dataset to list tables from"
                }
            },
            "required": ["dataset_id"]
        },
        handler=bigquery_list_tables
    )
    
    mcp_tools.register_tool(
        name="bigquery_get_schema",
        description="Get the schema (columns and types) of a BigQuery table",
        parameters={
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "string",
                    "description": "The dataset ID"
                },
                "table_id": {
                    "type": "string",
                    "description": "The table ID"
                }
            },
            "required": ["dataset_id", "table_id"]
        },
        handler=bigquery_get_schema
    )
    
    mcp_tools.register_tool(
        name="bigquery_query",
        description="Execute a SQL query on BigQuery. Use this to analyze data, get insights, and answer questions about the data. The query will automatically be limited to 100 rows if no LIMIT is specified for safety.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The BigQuery SQL query to execute. Use backticks for table names like `project.dataset.table`"
                }
            },
            "required": ["query"]
        },
        handler=bigquery_query
    )


# ============================================================================
# Chat Agent
# ============================================================================

class ChatAgent:
    """
    Agentic chat agent with Gemini integration.
    Handles conversation context, tool calling, and task management.
    """
    
    def __init__(self):
        """Initialize the chat agent."""
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize MCP if enabled
        self.mcp_connected = False
        if MCP_ENABLED:
            try:
                # Connect to BigQuery MCP server
                asyncio.create_task(self._connect_bigquery_mcp())
            except Exception as e:
                print(f"Warning: Could not connect to BigQuery MCP: {e}")
        
        # Initialize model with tool support
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools=self._get_gemini_tools()
        )
        
        # Chat session (handles context automatically)
        self.chat = None
        
        # Task management
        self.current_task_list: Optional[TaskList] = None
    
    async def _connect_bigquery_mcp(self):
        """Connect to BigQuery MCP server if enabled."""
        if not MCP_ENABLED:
            return
        
        try:
            # Connect to BigQuery MCP server
            await mcp_client.connect_server(
                server_name="bigquery",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-bigquery"],
                env={
                    "GOOGLE_APPLICATION_CREDENTIALS": settings.google_application_credentials,
                    "BIGQUERY_PROJECT_ID": settings.bigquery_project_id
                }
            )
            self.mcp_connected = True
            print("✅ Connected to BigQuery MCP server")
        except Exception as e:
            print(f"⚠️ BigQuery MCP connection failed: {e}")
            self.mcp_connected = False
    
    def _get_gemini_tools(self) -> List[Any]:
        """Convert MCP tools to Gemini function declarations."""
        def convert_schema(schema_def: Dict[str, Any]) -> genai.protos.Schema:
            """Recursively convert JSON schema to Gemini Schema."""
            schema_type = getattr(genai.protos.Type, schema_def.get("type", "STRING").upper())
            schema_args = {
                "type": schema_type,
                "description": schema_def.get("description", "")
            }
            
            # Handle array items
            if schema_def.get("type") == "array" and "items" in schema_def:
                schema_args["items"] = convert_schema(schema_def["items"])
            
            return genai.protos.Schema(**schema_args)
        
        # Gemini uses its own format for function calling
        tool_declarations = []
        for tool_info in mcp_tools.tools.values():
            tool_declarations.append(
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name=tool_info["name"],
                            description=tool_info["description"],
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    k: convert_schema(v)
                                    for k, v in tool_info["parameters"].get("properties", {}).items()
                                },
                                required=tool_info["parameters"].get("required", [])
                            )
                        )
                    ]
                )
            )
        return tool_declarations
    
    def start_conversation(self):
        """Start a new conversation session."""
        self.chat = self.model.start_chat(history=[])
        self.current_task_list = None
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """
        Send a message to the agent and get a response.
        Handles tool calling and task management automatically.
        
        Args:
            message: User message
            
        Returns:
            Response dictionary with text, tasks, and tool calls
        """
        if not self.chat:
            self.start_conversation()
        
        response_data = {
            "text": "",
            "tasks": None,
            "tool_calls": [],
            "thinking": []
        }
        
        try:
            # Send message to Gemini
            response = self.chat.send_message(message)
            
            # Handle function calls (tool usage)
            while response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                # Check if it's a function call
                if hasattr(part, 'function_call') and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    tool_args = dict(func_call.args)
                    
                    # Execute the tool
                    try:
                        tool_result = await mcp_tools.execute_tool(tool_name, tool_args)
                        
                        # Handle task list creation
                        if tool_name == "create_task_list":
                            self.current_task_list = TaskList(**tool_result)
                            response_data["tasks"] = self.current_task_list.to_dict()
                        
                        # Record tool call
                        response_data["tool_calls"].append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })
                        
                        # Send tool result back to model
                        response = self.chat.send_message(
                            genai.protos.Content(
                                parts=[
                                    genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=tool_name,
                                            response={"result": tool_result}
                                        )
                                    )
                                ]
                            )
                        )
                        
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        response_data["tool_calls"].append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "error": error_msg
                        })
                        break
                
                # Get text response
                elif hasattr(part, 'text'):
                    response_data["text"] = part.text
                    break
                else:
                    break
            
            # Extract final text if not set
            if not response_data["text"] and response.text:
                response_data["text"] = response.text
            
        except Exception as e:
            response_data["text"] = f"Error: {str(e)}"
            response_data["error"] = str(e)
        
        return response_data
    
    async def process_task(self, task_id: int) -> Dict[str, Any]:
        """
        Process a specific task from the current task list.
        
        Args:
            task_id: ID of the task to process
            
        Returns:
            Task processing result
        """
        if not self.current_task_list:
            return {"error": "No active task list"}
        
        # Find the task
        task = next((t for t in self.current_task_list.tasks if t.id == task_id), None)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        # Update task status
        self.current_task_list.update_task(task_id, "in_progress")
        
        try:
            # Send task to agent
            result = await self.send_message(f"Complete this task: {task.description}")
            
            # Update task with result
            self.current_task_list.update_task(
                task_id,
                "completed",
                result.get("text", "")
            )
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            self.current_task_list.update_task(task_id, "failed", str(e))
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
    
    def get_task_list(self) -> Optional[Dict[str, Any]]:
        """Get the current task list."""
        if self.current_task_list:
            return self.current_task_list.to_dict()
        return None
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Get chat history from Gemini (context is managed automatically).
        """
        if not self.chat:
            return []
        
        history = []
        for message in self.chat.history:
            history.append({
                "role": message.role,
                "parts": [{"text": part.text} for part in message.parts if hasattr(part, 'text')]
            })
        return history


# Global agent instance
agent = ChatAgent()

