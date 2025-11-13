from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from config import settings
from chat_agent import agent


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    text: str
    tasks: Optional[Dict[str, Any]] = None
    tool_calls: List[Dict[str, Any]] = []
    thinking: List[str] = []


class TaskProcessRequest(BaseModel):
    """Request model for processing a specific task."""
    task_id: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str


app = FastAPI(
    title="Agentic Chatbot API",
    description="MVP chatbot backend with Gemini AI, task management, and MCP tool support",
    version="1.0.0"
)

# CORS middleware - allows frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development (includes file:// protocol)
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def root():
    return {
        "status": "ok",
        "message": "Agentic Chatbot API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "healthy",
        "message": "Service is operational"
    }


@app.post("/chat/start")
async def start_chat():
    """Start a new chat conversation."""
    try:
        agent.start_conversation()
        return {
            "status": "success",
            "message": "New conversation started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    
    try:
        response = await agent.send_message(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/history")
async def get_history():
    """
    Get the chat history.
    Context is managed automatically by Gemini.
    """
    try:
        history = agent.get_chat_history()
        return {
            "status": "success",
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def get_tasks():
    """Get the current task list."""
    try:
        tasks = agent.get_task_list()
        if tasks:
            return {
                "status": "success",
                "tasks": tasks
            }
        else:
            return {
                "status": "success",
                "message": "No active task list",
                "tasks": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/process")
async def process_task(request: TaskProcessRequest):
    """
    Process a specific task from the task list.
    The agent will work on the task and return the result.
    """
    try:
        result = await agent.process_task(request.task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def get_tools():
    """Get available MCP tools."""
    from chat_agent import mcp_tools
    
    tools = []
    for tool_name, tool_info in mcp_tools.tools.items():
        tools.append({
            "name": tool_info["name"],
            "description": tool_info["description"],
            "parameters": tool_info["parameters"]
        })
    
    return {
        "status": "success",
        "tools": tools
    }


# ============================================================================
# Server Runner
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

