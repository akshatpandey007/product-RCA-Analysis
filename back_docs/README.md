# Agentic Chatbot Backend

A clean, MVP-focused agentic chatbot backend with Gemini AI integration, task management, and extensible MCP tool support.

## Features

- 🤖 **Gemini AI Integration** - Direct API integration with automatic context management
- 🛠️ **MCP Tool Support** - Easy copy-paste configuration to add new tools
- ✅ **Task Management** - Automatically breaks down complex requests into tasks
- 🚀 **FastAPI Backend** - Modern, fast Python web framework
- 🔌 **Simple Frontend Integration** - CORS-enabled REST API
- 📦 **No Unnecessary Code** - MVP-focused, uses libraries for everything

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Run the Server

```bash
python api.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health Check

```bash
GET /health
```

### Start Conversation

```bash
POST /chat/start
```

### Send Message

```bash
POST /chat/message
Content-Type: application/json

{
  "message": "Analyze the root cause of high memory usage in our production system"
}
```

Response includes:
- `text`: Agent's response
- `tasks`: Task list if created (for complex requests)
- `tool_calls`: Any tools the agent used

### Get Chat History

```bash
GET /chat/history
```

Context is automatically managed by Gemini - no need for external storage.

### Get Tasks

```bash
GET /tasks
```

### Process Specific Task

```bash
POST /tasks/process
Content-Type: application/json

{
  "task_id": 1
}
```

### List Available Tools

```bash
GET /tools
```

## Adding MCP Tools

Tools are super easy to add! Just follow this pattern in `chat_agent.py`:

### 1. Create the Tool Handler

```python
async def your_tool_name(param1: str, param2: int) -> str:
    """Your tool implementation."""
    # Your logic here
    return result
```

### 2. Register the Tool

Find the "Copy-Paste Configuration Area" in `chat_agent.py` and add:

```python
mcp_tools.register_tool(
    name="your_tool_name",
    description="What your tool does - the LLM uses this to decide when to call it",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Description of param1"},
            "param2": {"type": "integer", "description": "Description of param2"}
        },
        "required": ["param1", "param2"]
    },
    handler=your_tool_name
)
```

That's it! The agent will automatically use your tool when appropriate.

### Example Tools Included

1. **search_web** - Web search capability
2. **calculate** - Mathematical calculations
3. **create_task_list** - Break down complex problems into tasks

## Architecture

```
backend/
├── api.py              # FastAPI endpoints (frontend integration)
├── chat_agent.py       # Gemini agent + task management + MCP tools
├── config.py           # Configuration management
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
└── README.md          # This file
```

### Key Design Decisions

- **No Multi-User Management**: Single-user MVP, no authentication/sessions
- **Gemini Context Management**: Context handled directly by Gemini API, no RAG or file storage
- **Library-First**: Using FastAPI, Pydantic, google-generativeai instead of custom code
- **Separated Concerns**: API layer (api.py) separate from agent logic (chat_agent.py)
- **Extensibility**: MCP tools use a registry pattern for easy additions

## Example Usage Flow

1. **Simple Query**:
   ```
   User: "What's 25 * 17?"
   Agent: Uses calculate tool → Returns "425"
   ```

2. **Complex Query (Creates Tasks)**:
   ```
   User: "Analyze our production system performance and create optimization plan"
   Agent: 
   - Creates task list with 4 tasks
   - Returns task list to frontend
   - Frontend can request agent to process each task
   ```

3. **Tool Usage**:
   ```
   User: "Search for recent updates on Gemini API"
   Agent: Uses search_web tool → Returns search results
   ```

## Configuration

All settings in `.env`:

```env
# Required
GEMINI_API_KEY=your_key

# Optional (with defaults)
GEMINI_MODEL=gemini-2.0-flash-exp
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Start conversation
curl -X POST http://localhost:8000/chat/start

# Send message
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Get available tools
curl http://localhost:8000/tools
```

## Development Tips

- **Hot Reload**: Server auto-reloads on code changes (DEBUG=true)
- **CORS**: Add your frontend URL to CORS_ORIGINS
- **Tool Testing**: Use /tools endpoint to verify tools are registered
- **Context**: Gemini manages context automatically - no need to send history

## Troubleshooting

**API Key Issues**:
- Verify key in `.env` file
- Check key at https://makersuite.google.com/app/apikey

**CORS Issues**:
- Add your frontend URL to CORS_ORIGINS in `.env`

**Tool Not Working**:
- Check tool is registered in chat_agent.py
- Verify tool handler is async
- Check /tools endpoint to see registered tools

## Next Steps

For production deployment:
- Add API authentication
- Add rate limiting
- Add logging and monitoring
- Add error tracking (Sentry)
- Deploy with Docker/Kubernetes
