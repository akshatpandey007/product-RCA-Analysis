"""
Agentic chat agent with Gemini integration, task management, and MCP tool support.
"""

import json
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from config import settings

# Load RCA system prompt backend/rca_system_prompt.text
with open("rca_system_prompt.txt", "r") as f:
    RCA_SYSTEM_PROMPT = f.read()

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
        task_id = len(self.tasks) + 1
        task = Task(id=task_id, description=description)
        self.tasks.append(task)
        return task
    
    def update_task(self, task_id: int, status: str, result: Optional[str] = None):
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                if result:
                    task.result = result
                break
    
    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.status == "pending"]
    
    def to_dict(self) -> Dict[str, Any]:
        return {"tasks": [task.model_dump() for task in self.tasks]}


# ============================================================================
# MCP Tool Integration
# ============================================================================

class MCPToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: callable):
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        declarations = []
        for tool in self.tools.values():
            declarations.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            })
        return declarations
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        handler = self.tools[name]["handler"]
        return await handler(**arguments)


# ============================================================================
# Example MCP Tools
# ============================================================================

async def search_web_tool(query: str) -> str:
    return f"Search results for: {query}"


async def calculate_tool(expression: str) -> str:
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


async def create_task_list_tool(tasks: List[str]) -> Dict[str, Any]:
    task_list = TaskList()
    for task_desc in tasks:
        task_list.add_task(task_desc)
    return task_list.to_dict()


# ============================================================================
# Initialize Tool Registry
# ============================================================================

mcp_tools = MCPToolRegistry()

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
    description="Create a task list",
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
# BigQuery Tools
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
        description="List all available BigQuery datasets",
        parameters={"type": "object", "properties": {}},
        handler=bigquery_list_datasets
    )
    
    mcp_tools.register_tool(
        name="bigquery_list_tables",
        description="List all tables in a dataset",
        parameters={
            "type": "object",
            "properties": {
                "dataset_id": {"type": "string", "description": "Dataset ID"}
            },
            "required": ["dataset_id"]
        },
        handler=bigquery_list_tables
    )
    
    mcp_tools.register_tool(
        name="bigquery_get_schema",
        description="Get BigQuery table schema",
        parameters={
            "type": "object",
            "properties": {
                "dataset_id": {"type": "string"},
                "table_id": {"type": "string"}
            },
            "required": ["dataset_id", "table_id"]
        },
        handler=bigquery_get_schema
    )
    
    mcp_tools.register_tool(
        name="bigquery_query",
        description="Run SQL on BigQuery",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        },
        handler=bigquery_query
    )


# ============================================================================
# Chat Agent
# ============================================================================

class ChatAgent:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        
        self.mcp_connected = False
        if MCP_ENABLED:
            try:
                asyncio.create_task(self._connect_bigquery_mcp())
            except Exception as e:
                print(f"Warning: Could not connect to BigQuery MCP: {e}")
        
        # ***** INSERTED: system_instruction *****
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools=self._get_gemini_tools(),
            system_instruction=RCA_SYSTEM_PROMPT
        )
        
        self.chat = None
        self.current_task_list: Optional[TaskList] = None
    
    async def _connect_bigquery_mcp(self):
        if not MCP_ENABLED:
            return
        
        try:
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
        def convert_schema(schema_def: Dict[str, Any]) -> genai.protos.Schema:
            schema_type = getattr(genai.protos.Type, schema_def.get("type", "STRING").upper())
            schema_args = {
                "type": schema_type,
                "description": schema_def.get("description", "")
            }
            if schema_def.get("type") == "array" and "items" in schema_def:
                schema_args["items"] = convert_schema(schema_def["items"])
            return genai.protos.Schema(**schema_args)
        
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
        self.chat = self.model.start_chat(history=[])
        self.current_task_list = None
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        if not self.chat:
            self.start_conversation()
        
        response_data = {"text": "", "tasks": None, "tool_calls": [], "thinking": []}
        
        try:
            response = self.chat.send_message(message)
            
            while response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                
                if hasattr(part, 'function_call') and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    tool_args = dict(func_call.args)
                    
                    try:
                        tool_result = await mcp_tools.execute_tool(tool_name, tool_args)
                        
                        if tool_name == "create_task_list":
                            self.current_task_list = TaskList(**tool_result)
                            response_data["tasks"] = self.current_task_list.to_dict()
                        
                        response_data["tool_calls"].append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })
                        
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
                        response_data["tool_calls"].append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "error": f"Error executing tool {tool_name}: {str(e)}"
                        })
                        break
                
                elif hasattr(part, 'text'):
                    response_data["text"] = part.text
                    break
                else:
                    break
            
            if not response_data["text"] and response.text:
                response_data["text"] = response.text
        
        except Exception as e:
            response_data["text"] = f"Error: {str(e)}"
            response_data["error"] = str(e)
        
        return response_data
    
    async def process_task(self, task_id: int) -> Dict[str, Any]:
        if not self.current_task_list:
            return {"error": "No active task list"}
        
        task = next((t for t in self.current_task_list.tasks if t.id == task_id), None)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        self.current_task_list.update_task(task_id, "in_progress")
        
        try:
            result = await self.send_message(f"Complete this task: {task.description}")
            self.current_task_list.update_task(task_id, "completed", result.get("text", ""))
            
            return {"task_id": task_id, "status": "completed", "result": result}
        except Exception as e:
            self.current_task_list.update_task(task_id, "failed", str(e))
            return {"task_id": task_id, "status": "failed", "error": str(e)}
    
    def get_task_list(self) -> Optional[Dict[str, Any]]:
        if self.current_task_list:
            return self.current_task_list.to_dict()
        return None
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
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
