"""
Agentic chat agent with Gemini integration, task management, and MCP tool support.
"""

import json
import re
import asyncio
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
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


async def get_current_datetime_tool(timezone: Optional[str] = None) -> str:
    """
    Get the current date and time.
    
    Args:
        timezone: Optional timezone (e.g., 'UTC', 'America/New_York'). 
                  If not provided, returns local time.
    
    Returns:
        Current date and time in ISO format with timezone info.
    """
    now = datetime.now()
    
    if timezone:
        try:
            # Try zoneinfo (Python 3.9+)
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(timezone)
                now = datetime.now(tz)
            except ImportError:
                # Fallback to pytz if zoneinfo not available
                try:
                    import pytz
                    tz = pytz.timezone(timezone)
                    now = datetime.now(tz)
                except (ImportError, Exception):
                    # If timezone is invalid or libraries unavailable, use local time
                    pass
        except Exception:
            # If timezone is invalid, fall back to local time
            pass
    
    # Return in ISO format with timezone
    return now.isoformat()


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

mcp_tools.register_tool(
    name="get_current_datetime",
    description="Get the current date and time. Useful for determining 'today', 'yesterday', or relative dates when analyzing data. Returns ISO format datetime with timezone information.",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "Optional timezone (e.g., 'UTC', 'America/New_York'). If not provided, returns local server time."
            }
        },
        "required": []
    },
    handler=get_current_datetime_tool
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
        
        # Initialize MCP if enabled (connection will happen lazily on first use)
        self.mcp_connected = False
        self.mcp_connection_attempted = False
        
        # Load system prompt
        system_prompt = self._load_system_prompt()
        
        # Initialize model with tool support and system prompt
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools=self._get_gemini_tools(),
            system_instruction=system_prompt
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
    
    def _load_system_prompt(self) -> str:
        """
        Load the system prompt from SYSTEM_PROMPT1.md file.
        
        Returns:
            System prompt string
        """
        import os
        prompt_path = os.path.join(os.path.dirname(__file__), "SYSTEM_PROMPT1.md")
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: System prompt file not found at {prompt_path}, using default behavior")
            return ""
        except Exception as e:
            print(f"Warning: Error loading system prompt: {e}, using default behavior")
            return ""
    
    def start_conversation(self):
        """Start a new conversation session."""
        self.chat = self.model.start_chat(history=[])
        self.current_task_list = None
    
    
    async def send_message(self, message: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Send a message to the agent and get a response.
        Handles tool calling automatically.
        
        Args:
            message: User message
            timeout: Maximum seconds to wait for response (default: 120)
            
        Returns:
            Response dictionary with text, tasks, and tool calls
        """
        # Lazy connect to MCP on first use
        if MCP_ENABLED and not self.mcp_connection_attempted:
            self.mcp_connection_attempted = True
            try:
                await self._connect_bigquery_mcp()
            except Exception as e:
                print(f"Warning: Could not connect to BigQuery MCP: {e}")
        
        if not self.chat:
            self.start_conversation()
        
        response_data = {
            "text": "",
            "tasks": None,
            "tool_calls": [],
            "thinking": []
        }
        
        try:
            # Log user query and plan
            print(f"\n{'='*80}")
            print(f"📋 USER QUERY: {message}")
            print(f"{'='*80}")
            print(f"📝 Agent will analyze the query and create an execution plan...")
            
            # Send message to Gemini with timeout
            print(f"⏳ Sending message to Gemini (timeout: {timeout}s)...")
            try:
                response = self.chat.send_message(
                    message,
                    request_options={"timeout": timeout}
                )
            except (TimeoutError, FuturesTimeoutError) as e:
                response_data["text"] = f"⏱️ Request timed out after {timeout} seconds. The LLM took too long to respond. Please try again with a simpler query."
                response_data["error"] = f"Timeout: {str(e)}"
                return response_data
            
            # Check finish_reason for initial response
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason:
                    print(f"📊 Initial response finish_reason: {finish_reason}")
                    if finish_reason not in [1, "STOP"]:  # 1 is STOP in protobuf enum
                        print(f"⚠️ Warning: Response finished with reason {finish_reason} (not STOP). This may indicate an incomplete or malformed response.")
                        if finish_reason in [2, "MAX_TOKENS"]:
                            print("⚠️ Response was truncated due to MAX_TOKENS. Consider increasing max_output_tokens.")
                        elif finish_reason in [3, "SAFETY"]:
                            print("⚠️ Response was blocked by safety filters.")
                        elif finish_reason in [4, "RECITATION"]:
                            print("⚠️ Response was blocked due to recitation detection.")
                        elif finish_reason in [5, "OTHER"]:
                            print("⚠️ Response finished with OTHER reason - may be incomplete.")
                        elif finish_reason in [6, "MALFORMED_FUNCTION_CALL"]:
                            print("❌ Response had MALFORMED_FUNCTION_CALL - this is a critical error.")
            
            # Handle function calls (tool usage) with timeout tracking
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            # Safety check: ensure we have candidates
            if not response.candidates or len(response.candidates) == 0:
                print("⚠️ No candidates in response")
                response_data["text"] = "No response generated. Please try again."
                return response_data
            
            while response and response.candidates and response.candidates[0].content.parts and iteration < max_iterations:
                iteration += 1
                print(f"\n{'='*80}")
                print(f"🔄 ITERATION {iteration}/{max_iterations}")
                print(f"{'='*80}")
                part = response.candidates[0].content.parts[0]
                
                # Check if it's a function call
                if hasattr(part, 'function_call') and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    tool_args = dict(func_call.args)
                    
                    print(f"🔧 Executing tool: {tool_name}")
                    
                    # Log full arguments for SQL queries with prominent formatting
                    if tool_name == "bigquery_query":
                        sql_query = None
                        if "query" in tool_args:
                            sql_query = tool_args["query"]
                        elif "sql_query" in tool_args:
                            sql_query = tool_args["sql_query"]
                        
                        if sql_query:
                            print(f"\n{'='*80}")
                            print(f"📝 SQL QUERY EXECUTED BY GEMINI:")
                            print(f"{'='*80}")
                            print(sql_query)
                            print(f"{'='*80}\n")
                        else:
                            print(f"📝 Tool arguments: {json.dumps(tool_args, indent=2)}")
                    elif tool_args:
                        print(f"📝 Tool arguments: {json.dumps(tool_args, indent=2)}")
                    
                    # Execute the tool
                    try:
                        tool_result = await mcp_tools.execute_tool(tool_name, tool_args)
                        
                        # Log full result for debugging
                        if tool_name == "bigquery_query":
                            print(f"\n{'='*80}")
                            print(f"✅ SQL QUERY RESULT:")
                            print(f"{'='*80}")
                            print(str(tool_result))
                            print(f"{'='*80}\n")
                            
                            # Check if query failed or returned no results
                            tool_result_str = str(tool_result)
                            query_failed = (
                                "Query Failed" in tool_result_str or 
                                "❌" in tool_result_str or
                                "Error:" in tool_result_str or
                                "Unrecognized name" in tool_result_str or
                                "not found" in tool_result_str.lower()
                            )
                            
                            # Check if query returned zero results
                            no_results = (
                                "returned 0 rows" in tool_result_str.lower() or
                                "no results" in tool_result_str.lower() or
                                "Query executed successfully but returned no results" in tool_result_str
                            )
                            
                            if query_failed:
                                print("⚠️ Query execution failed - will prompt LLM to fix and continue")
                            elif no_results:
                                print("⚠️ Query returned zero results - will prompt LLM to find available dates")
                        
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
                        
                        # Send tool result back to model with timeout
                        try:
                            # Format the result for Gemini
                            if isinstance(tool_result, dict):
                                formatted_result = tool_result
                            else:
                                formatted_result = {"result": str(tool_result)}
                            
                            # Add instruction to ALL tool results: process internally, never return JSON
                            tool_result_str = str(tool_result)
                            
                            # Base instruction: never return JSON structures
                            base_instruction = "🔧 CRITICAL: Process this tool result internally. Extract the information you need. Do NOT return this JSON structure or any JSON to the user. Convert everything to natural language only. Never show tool response formats like {\"bigquery_query_response\": {...}} to the user.\n\n"
                            
                            # If query failed, add explicit instruction to fix and continue
                            if tool_name == "bigquery_query":
                                if ("Query Failed" in tool_result_str or 
                                    "❌" in tool_result_str or
                                    ("Error:" in tool_result_str and "Query" in tool_result_str)):
                                    
                                    # Prepend both instructions
                                    instruction = base_instruction + "🔧 INSTRUCTION: The query failed. Analyze the error message above, identify the issue (e.g., wrong column name, syntax error), fix the SQL query, and immediately call bigquery_query again with the corrected query. Do NOT return text to the user - continue with the fixed query execution.\n\n"
                                    formatted_result = {"result": instruction + tool_result_str}
                                    print("📝 Added fix-and-continue instruction for failed query")
                                elif (no_results or 
                                      "returned 0 rows" in tool_result_str.lower() or
                                      "no results" in tool_result_str.lower() or
                                      "Query executed successfully but returned no results" in tool_result_str):
                                    # Query returned zero results - instruct to find available dates
                                    date_finding_instruction = base_instruction + "🔧 CRITICAL - ZERO RESULTS DETECTED: This query returned zero results. DO NOT give up or return 'no data'. Instead: (1) First query to find available dates using: SELECT DISTINCT event_date FROM ratings_analytics.table_name ORDER BY event_date DESC LIMIT 10, (2) Use the most recent available date with data, (3) If the requested date has no data, automatically use the most recent available date instead, (4) Check dates going backwards (D-1, D-2, D-3, etc.) until you find data, (5) Only report 'no data' if you've checked the last 30 days and found nothing. ALWAYS find and use available data.\n\n"
                                    formatted_result = {"result": date_finding_instruction + tool_result_str}
                                    print("📝 Added date-finding instruction for zero results")
                                else:
                                    # Query succeeded - add validation instruction
                                    validation_instruction = "🔧 VALIDATION: Before reporting on any segment (e.g., 'Bronze Android users'), verify that this combination actually exists in the query results above with non-zero counts. Only report on segments that appear in the actual query results. Never report on segments that don't exist in the data.\n\n"
                                    formatted_result = {"result": base_instruction + validation_instruction + tool_result_str}
                            else:
                                # For all other tools, add the no-JSON instruction
                                formatted_result = {"result": base_instruction + tool_result_str}
                            
                            response = self.chat.send_message(
                                genai.protos.Content(
                                    parts=[
                                        genai.protos.Part(
                                            function_response=genai.protos.FunctionResponse(
                                                name=tool_name,
                                                response=formatted_result
                                            )
                                        )
                                    ]
                                ),
                                request_options={"timeout": timeout}
                            )
                            
                            # Check finish_reason after tool result
                            if hasattr(response, 'candidates') and response.candidates:
                                candidate = response.candidates[0]
                                finish_reason = getattr(candidate, 'finish_reason', None)
                                if finish_reason:
                                    print(f"📊 Tool response finish_reason: {finish_reason}")
                                    if finish_reason not in [1, "STOP"]:
                                        print(f"⚠️ Warning: Tool response finished with reason {finish_reason} (not STOP).")
                                        if finish_reason in [6, "MALFORMED_FUNCTION_CALL"]:
                                            print("❌ MALFORMED_FUNCTION_CALL detected - clearing response to force continuation")
                                            # Clear any partial text to force continuation
                                            if "text" in response_data:
                                                response_data["text"] = ""
                                        elif finish_reason in [2, "MAX_TOKENS"]:
                                            print("⚠️ Response truncated - may be incomplete")
                                            
                        except (TimeoutError, FuturesTimeoutError) as e:
                            response_data["text"] = f"⏱️ Timeout while processing tool result. The LLM took too long to respond."
                            response_data["error"] = f"Timeout: {str(e)}"
                            return response_data
                        except Exception as e:
                            error_msg = f"Error sending tool result to model: {str(e)}"
                            print(f"❌ {error_msg}")
                            # Break the loop if we can't send tool result
                            break
                        
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        print(f"❌ {error_msg}")
                        
                        response_data["tool_calls"].append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "error": error_msg
                        })
                        break
                
                # Get text response
                elif hasattr(part, 'text'):
                    text_content = part.text
                    
                    # Check if text contains JSON patterns - if so, send continuation message
                    json_indicators = [
                        r'\{"bigquery_query_response"',
                        r'\{"bigquery_get_schema_response"',
                        r'\{"bigquery_list_tables_response"',
                        r'\{"[^"]+_response"\s*:',
                    ]
                    
                    has_json_in_text = False
                    for pattern in json_indicators:
                        if re.search(pattern, text_content):
                            has_json_in_text = True
                            print(f"⚠️ Detected JSON in text response - sending continuation message to force query execution")
                            break
                    
                    if has_json_in_text:
                        # Clear the text so it doesn't get returned
                        response_data["text"] = ""
                        # Send a message to Gemini to continue with query execution
                        try:
                            # Determine context-aware continuation message
                            if any("bigquery_get_schema" in call.get("tool", "") for call in response_data.get("tool_calls", [])):
                                continuation_msg = "You have the schema information. Now execute the SQL queries to get the data. Do NOT return JSON structures. Process tool results internally, execute queries, and complete all steps before returning any text."
                            elif any("bigquery_query" in call.get("tool", "") for call in response_data.get("tool_calls", [])):
                                continuation_msg = "Continue executing the remaining queries. Do NOT return JSON structures. Process all tool results internally and complete the full analysis before returning any text."
                            else:
                                continuation_msg = "Continue executing the queries. Do NOT return JSON structures. Process tool results internally and execute the next query. Complete all steps before returning any text."
                            
                            print(f"\n{'='*80}")
                            print(f"🔄 SENDING CONTINUATION MESSAGE TO GEMINI:")
                            print(f"{'='*80}")
                            print(continuation_msg)
                            print(f"{'='*80}\n")
                            
                            response = self.chat.send_message(
                                continuation_msg,
                                request_options={"timeout": timeout}
                            )
                            
                            print(f"📥 CONTINUATION RESPONSE RECEIVED:")
                            if hasattr(response, 'candidates') and response.candidates:
                                candidate = response.candidates[0]
                                finish_reason = getattr(candidate, 'finish_reason', None)
                                print(f"   Finish reason: {finish_reason}")
                                if hasattr(candidate, 'content') and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'function_call') and part.function_call:
                                            print(f"   Function call detected: {part.function_call.name}")
                                        elif hasattr(part, 'text') and part.text:
                                            print(f"   Text response: {part.text[:200]}...")
                            
                            # Don't increment iteration here - we'll increment at the start of next loop
                            # Continue the loop to process the new response
                            iteration -= 1  # Decrement so next iteration doesn't skip
                            continue
                        except Exception as e:
                            print(f"⚠️ Error sending continuation message: {e}")
                            break
                    else:
                        # No JSON detected - this is valid text response
                        response_data["text"] = text_content
                    break
                else:
                    break
            
            if iteration >= max_iterations:
                print(f"⚠️ Maximum iterations ({max_iterations}) reached in tool call loop")
            
            # Log execution summary
            if response_data.get("tool_calls"):
                print(f"\n{'='*80}")
                print(f"📊 EXECUTION PLAN SUMMARY:")
                print(f"{'='*80}")
                print(f"Total tools executed: {len(response_data['tool_calls'])}")
                
                # Track SQL queries separately for prominent display
                sql_queries = []
                for i, tool_call in enumerate(response_data['tool_calls'], 1):
                    tool_name = tool_call.get('tool', 'unknown')
                    print(f"  {i}. {tool_name}")
                    if tool_name == "bigquery_query" and "arguments" in tool_call:
                        query = tool_call["arguments"].get("query") or tool_call["arguments"].get("sql_query", "")
                        if query:
                            sql_queries.append(query)
                            print(f"     SQL Query:")
                            # Print full query with indentation
                            for line in query.split('\n'):
                                print(f"       {line}")
                
                # Show SQL queries summary prominently
                if sql_queries:
                    print(f"\n{'='*80}")
                    print(f"📝 ALL SQL QUERIES EXECUTED ({len(sql_queries)} total):")
                    print(f"{'='*80}")
                    for i, query in enumerate(sql_queries, 1):
                        print(f"\n--- Query {i} ---")
                        print(query)
                    print(f"{'='*80}\n")
                else:
                    print(f"\n⚠️ NO SQL QUERIES WERE EXECUTED")
                    print(f"{'='*80}\n")
            
            # Extract final text if not set
            if not response_data["text"]:
                try:
                    if hasattr(response, 'text') and response.text:
                        response_data["text"] = response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_data["text"] = part.text
                                    break
                except Exception as e:
                    print(f"Warning: Could not extract text from response: {e}")
            
            # Final validation: Check finish_reason and validate response quality
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason and finish_reason not in [1, "STOP"]:
                    print(f"⚠️ Final response finish_reason: {finish_reason} (not STOP)")
                    # If response is incomplete or malformed, clear it
                    if finish_reason in [6, "MALFORMED_FUNCTION_CALL", 5, "OTHER"]:
                        print("❌ Clearing incomplete/malformed response")
                        response_data["text"] = ""
                    elif finish_reason in [2, "MAX_TOKENS"]:
                        print("⚠️ Response was truncated - may be incomplete")
                        # Keep the text but log the warning
            
            # Validate final text - check for raw JSON or incomplete responses
            if response_data.get("text"):
                text = response_data["text"].strip()
                
                # Check if entire response is raw JSON
                if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
                    try:
                        json.loads(text)
                        print("⚠️ Detected raw JSON in final response - clearing to force continuation")
                        response_data["text"] = ""
                    except json.JSONDecodeError:
                        pass  # Not valid JSON, might be natural language
                
                # Check if response contains embedded raw JSON (e.g., {"bigquery_query_response": ...})
                # Look for common tool response JSON patterns
                # Patterns that indicate raw tool response JSON
                json_indicators = [
                    r'\{"bigquery_query_response"',
                    r'\{"bigquery_get_schema_response"',
                    r'\{"bigquery_list_tables_response"',
                    r'\{"bigquery_list_datasets_response"',
                    r'\{"tool_response"',
                    r'\{"result"\s*:\s*\{',
                    r'\{"[^"]+_response"\s*:',  # Any ..._response pattern
                    r'\{[^{}]*"[^"]*response[^"]*"',  # Any JSON containing "response"
                    r'\{"[^"]*query[^"]*"\s*:\s*\{',  # Query-related JSON
                    r'\{"[^"]*schema[^"]*"\s*:\s*\{',  # Schema-related JSON
                    r'\{"[^"]*table[^"]*"\s*:\s*\{',  # Table-related JSON
                ]
                
                has_json = False
                for pattern in json_indicators:
                    if re.search(pattern, text):
                        has_json = True
                        print(f"⚠️ Detected embedded raw JSON pattern in response: {pattern}")
                        break
                
                if has_json:
                    # Aggressively strip ALL JSON patterns using regex
                    try:
                        cleaned_text = text
                        
                        # Use a more robust approach: find and remove JSON blocks by matching braces
                        # This handles deeply nested JSON structures
                        def remove_json_blocks(text):
                            """Remove all JSON blocks that match our patterns"""
                            result = text
                            
                            # Find all JSON blocks that start with {"..._response"
                            # Match from opening { to matching closing }
                            pattern = r'\{"[^"]+_response"\s*:\s*\{'
                            matches = list(re.finditer(pattern, result))
                            
                            # Process matches in reverse to maintain indices
                            for match in reversed(matches):
                                start = match.start()
                                # Find matching closing brace
                                brace_count = 0
                                json_end = -1
                                for i in range(start, len(result)):
                                    if result[i] == '{':
                                        brace_count += 1
                                    elif result[i] == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_end = i
                                            break
                                
                                if json_end > start:
                                    # Remove this JSON block
                                    result = result[:start] + result[json_end + 1:]
                            
                            return result
                        
                        # Remove JSON blocks using brace matching
                        cleaned_text = remove_json_blocks(cleaned_text)
                        
                        # Additional regex patterns for simpler cases
                        # Pattern 1: Remove {..._response": "..."} (simple string values)
                        pattern1 = r'\{"[^"]+_response"\s*:\s*"[^"]*"\s*\}'
                        cleaned_text = re.sub(pattern1, '', cleaned_text)
                        
                        # Pattern 2: Remove {"result": "..."} patterns
                        pattern2 = r'\{"result"\s*:\s*"[^"]*"\s*\}'
                        cleaned_text = re.sub(pattern2, '', cleaned_text)
                        
                        # Pattern 3: Remove any remaining JSON that contains "response"
                        pattern3 = r'\{[^{}]*"[^"]*response[^"]*"[^{}]*\}'
                        cleaned_text = re.sub(pattern3, '', cleaned_text, flags=re.DOTALL)
                        
                        # Clean up: remove multiple spaces, newlines, and trim
                        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                        
                        # Check if cleaned text still contains JSON patterns
                        still_has_json = False
                        for pattern in json_indicators:
                            if re.search(pattern, cleaned_text):
                                still_has_json = True
                                break
                        
                        # Also check if it starts with { or [ (likely JSON)
                        if cleaned_text.startswith('{') or cleaned_text.startswith('['):
                            still_has_json = True
                        
                        if still_has_json or not cleaned_text or len(cleaned_text) < 10:
                            # Still has JSON or is too short - clear entirely to force continuation
                            response_data["text"] = ""
                            print("⚠️ Response still contains JSON after cleaning - clearing to force continuation")
                        else:
                            # Use cleaned text
                            response_data["text"] = cleaned_text
                            print(f"✅ Cleaned response: removed all JSON patterns, kept: {cleaned_text[:100]}...")
                            
                    except Exception as e:
                        print(f"⚠️ Error cleaning JSON from response: {e} - clearing response")
                        response_data["text"] = ""
                
                # Check if response looks incomplete (ends mid-sentence or is very short after tool calls)
                if response_data.get("tool_calls") and len(text) < 50:
                    print("⚠️ Response seems incomplete after tool calls - may need continuation")
            
            # If we executed tool calls but have no final text, request a summary
            if response_data.get("tool_calls") and not response_data.get("text"):
                print("⚠️ Tool calls executed but no final text - requesting summary from Gemini")
                try:
                    summary_request = "Based on all the tool results you just processed, provide a complete summary of your findings in natural language. Do NOT return any JSON structures. Convert all the data you analyzed into a clear, conversational explanation."
                    final_response = self.chat.send_message(
                        summary_request,
                        request_options={"timeout": timeout}
                    )
                    
                    # Extract text from final response
                    if hasattr(final_response, 'text') and final_response.text:
                        final_text = final_response.text.strip()
                        # Check for JSON one more time
                        if not (final_text.startswith("{") or final_text.startswith("[")):
                            # Check for embedded JSON patterns
                            json_patterns = [
                                r'\{"bigquery_query_response"',
                                r'\{"bigquery_get_schema_response"',
                                r'\{"bigquery_list_tables_response"',
                                r'\{"[^"]+_response"\s*:',
                            ]
                            has_json = False
                            for pattern in json_patterns:
                                if re.search(pattern, final_text):
                                    has_json = True
                                    break
                            if not has_json:
                                response_data["text"] = final_text
                                print("✅ Got final summary from Gemini")
                    elif hasattr(final_response, 'candidates') and final_response.candidates:
                        candidate = final_response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    final_text = part.text.strip()
                                    # Quick JSON check
                                    if not (final_text.startswith("{") or final_text.startswith("[")):
                                        response_data["text"] = final_text
                                        print("✅ Got final summary from Gemini")
                                        break
                except Exception as e:
                    print(f"⚠️ Error requesting summary: {e}")
                    # If we still have no text, provide a default message
                    if not response_data.get("text"):
                        response_data["text"] = "Analysis completed. Please check the tool calls for details or try rephrasing your query."
            
            # Always include updated task list in response
            if self.current_task_list:
                response_data["tasks"] = self.current_task_list.to_dict()
            
        except (TimeoutError, FuturesTimeoutError) as e:
            response_data["text"] = f"⏱️ Request timed out after {timeout} seconds. Please try again."
            response_data["error"] = f"Timeout: {str(e)}"
        except Exception as e:
            error_str = str(e)
            if 'timeout' in error_str.lower() or 'deadline' in error_str.lower():
                response_data["text"] = f"⏱️ Request timed out. The LLM took too long to respond. Error: {error_str}"
            else:
                response_data["text"] = f"Error: {error_str}"
            response_data["error"] = error_str
        
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

