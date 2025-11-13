# Architecture Overview

## System Design

This is a clean, MVP-focused agentic chatbot backend designed for hackathons and rapid prototyping.

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend  │ ◄─────► │  FastAPI     │ ◄─────► │   Gemini AI  │
│  (React/    │  HTTP   │  (api.py)    │   API   │   (Context)  │
│   Vue/etc)  │         │              │         │              │
└─────────────┘         └──────┬───────┘         └──────────────┘
                               │
                               │
                        ┌──────▼────────┐
                        │  Chat Agent   │
                        │ (chat_agent.py)│
                        └──────┬────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
              ┌─────▼───┐ ┌───▼─────┐ ┌──▼──────┐
              │  Task   │ │   MCP   │ │ History │
              │  Mgmt   │ │  Tools  │ │ (Gemini)│
              └─────────┘ └─────────┘ └─────────┘
```

## File Structure

```
backend/
├── api.py                    # FastAPI endpoints (frontend integration)
├── chat_agent.py             # Core agent logic (Gemini + tools + tasks)
├── config.py                 # Configuration management (environment vars)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (API keys, etc.)
├── .gitignore               # Git ignore rules
│
├── README.md                 # Full documentation
├── QUICKSTART.md            # 5-minute setup guide
├── ARCHITECTURE.md          # This file
│
├── setup.sh                 # Automated setup script
├── test_api.py             # API testing script
└── example_custom_tool.py  # Examples for adding tools
```

## Core Components

### 1. API Layer (`api.py`)

**Responsibility**: Frontend communication

**Endpoints**:
- `POST /chat/start` - Initialize new conversation
- `POST /chat/message` - Send user message
- `GET /chat/history` - Retrieve conversation history
- `GET /tasks` - Get current task list
- `POST /tasks/process` - Execute specific task
- `GET /tools` - List available tools

**Key Features**:
- CORS enabled for frontend integration
- Single-user design (no auth needed for MVP)
- FastAPI auto-generates API docs at `/docs`
- Clean request/response models with Pydantic

### 2. Chat Agent (`chat_agent.py`)

**Responsibility**: Core intelligence and orchestration

**Components**:

#### A. ChatAgent Class
- Manages Gemini conversation state
- Handles automatic context management
- Orchestrates tool calling
- Manages task execution

#### B. Task Management System
- `Task`: Individual task model
- `TaskList`: Task collection with lifecycle management
- Auto-creates tasks for complex requests
- Tracks status (pending, in_progress, completed, failed)

#### C. MCP Tool Registry
- `MCPToolRegistry`: Tool registration and execution
- Easy copy-paste tool addition
- Automatic Gemini function calling integration
- Type-safe parameter validation

**Workflow**:
```
User Message → Agent → Gemini API
                ↓
         Needs Tool? ─Yes→ Execute Tool → Return to Gemini
                ↓
                No
                ↓
         Complex? ─Yes→ Create Tasks → Return with Task List
                ↓
                No
                ↓
         Return Response
```

### 3. Configuration (`config.py`)

**Responsibility**: Environment management

**Features**:
- Pydantic-based settings validation
- `.env` file support
- Type-safe configuration access
- Default values for optional settings

### 4. Supporting Files

#### `test_api.py`
Automated testing script that verifies:
- Health endpoints
- Chat functionality
- Tool availability
- Task creation

#### `example_custom_tool.py`
Copy-paste examples for common tool patterns:
- HTTP API integration
- Data analysis tools
- Text processing
- File system operations

#### `setup.sh`
One-command setup:
```bash
./setup.sh
```

## Data Flow

### Simple Message Flow

```
1. Frontend sends POST /chat/message {"message": "What's 5+3?"}
2. API receives request → calls agent.send_message()
3. Agent sends to Gemini
4. Gemini identifies calculate tool needed
5. Agent executes calculate("5+3") → "8"
6. Agent sends result back to Gemini
7. Gemini formulates response
8. Agent returns to API → Frontend
```

### Complex Request with Tasks

```
1. Frontend: "Optimize our database performance"
2. Agent → Gemini
3. Gemini calls create_task_list tool
4. Agent creates TaskList with 4 tasks
5. Returns response + task list to frontend
6. Frontend displays tasks
7. User selects task #1
8. Frontend: POST /tasks/process {"task_id": 1}
9. Agent works on task #1
10. Returns task result
```

## Design Decisions

### Why FastAPI?
- **Fast**: High performance async framework
- **Modern**: Native Python 3.8+ features
- **Auto-docs**: Swagger UI at `/docs`
- **Type-safe**: Pydantic integration
- **CORS built-in**: Easy frontend integration

### Why Gemini API?
- **Context Management**: Built-in conversation history
- **Function Calling**: Native tool support
- **No Storage Needed**: Context maintained by API
- **Cost Effective**: Free tier available
- **Latest Models**: Access to newest Gemini models

### Why Single User?
- **MVP Focus**: Hackathon/prototype speed
- **No Auth Overhead**: Faster development
- **Local Development**: Frontend + backend on same machine
- **Easy to Extend**: Add auth later if needed

### Why Separate api.py and chat_agent.py?
- **Separation of Concerns**: API vs business logic
- **Testability**: Can test agent without API
- **Reusability**: Agent can be used in other contexts
- **Clarity**: Clear responsibilities

### Why MCP Tool Registry?
- **Extensibility**: Add tools without modifying core code
- **Copy-Paste Simple**: Minimal boilerplate
- **Type Safe**: Parameter validation
- **Discoverable**: `/tools` endpoint lists all tools

## Extension Points

### 1. Adding New Tools

```python
# Step 1: Define handler
async def my_tool(param: str) -> str:
    return result

# Step 2: Register
mcp_tools.register_tool(
    name="my_tool",
    description="What it does",
    parameters={...},
    handler=my_tool
)
```

### 2. Adding Authentication

```python
# In api.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat/message")
async def send_message(
    request: ChatRequest,
    credentials = Depends(security)
):
    # Validate token
    validate_token(credentials.credentials)
    # ... rest of logic
```

### 3. Adding Database Storage

```python
# In chat_agent.py
from sqlalchemy.orm import Session

class ChatAgent:
    def __init__(self, db: Session):
        self.db = db
        # Save history to DB instead of relying on Gemini
```

### 4. Adding Multiple Users

```python
# In api.py
sessions = {}  # user_id -> ChatAgent

@app.post("/chat/message")
async def send_message(
    request: ChatRequest,
    user_id: str = Header(...)
):
    if user_id not in sessions:
        sessions[user_id] = ChatAgent()
    
    return await sessions[user_id].send_message(request.message)
```

## Performance Considerations

### Current Setup (MVP)
- **Single instance**: One agent per backend instance
- **In-memory state**: Chat state in memory
- **Async operations**: Non-blocking I/O
- **Auto-context**: Gemini manages conversation history

### For Production
1. **Add Redis**: Store session state
2. **Add Queue**: Process long-running tasks
3. **Add Load Balancer**: Multiple backend instances
4. **Add Monitoring**: Logging, metrics, tracing
5. **Add Caching**: Cache frequent tool results

## Security Considerations

### Current Setup (MVP)
- ⚠️ No authentication
- ⚠️ No rate limiting
- ⚠️ Open CORS (configurable)
- ✅ Environment-based secrets

### For Production
1. **Add API Keys**: Require auth tokens
2. **Rate Limiting**: Prevent abuse
3. **Input Validation**: Sanitize user input
4. **Tool Sandboxing**: Limit tool capabilities
5. **HTTPS Only**: Encrypt in transit

## Troubleshooting

### Agent Not Responding
```python
# Check Gemini configuration
print(f"Model: {settings.gemini_model}")
print(f"API Key set: {bool(settings.gemini_api_key)}")
```

### Tools Not Being Called
```python
# List registered tools
from chat_agent import mcp_tools
print(mcp_tools.tools.keys())
```

### Context Not Persisting
- Gemini manages context automatically
- Each `/chat/start` creates new session
- Don't call `/chat/start` mid-conversation

## Testing Strategy

### Unit Tests (Future)
```python
# Test tools
result = await mcp_tools.execute_tool("calculate", {"expression": "5+3"})
assert result == "8"

# Test task management
task_list = TaskList()
task = task_list.add_task("Test task")
assert task.status == "pending"
```

### Integration Tests (Current)
```bash
python test_api.py  # Tests full API flow
```

### Manual Testing
```bash
# Use FastAPI docs
open http://localhost:8000/docs

# Or cURL
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

## Future Enhancements

### Phase 1 (Production Ready)
- [ ] Add authentication
- [ ] Add rate limiting
- [ ] Add proper logging
- [ ] Add error tracking (Sentry)
- [ ] Add health metrics

### Phase 2 (Scale)
- [ ] Redis for session storage
- [ ] Queue for async tasks
- [ ] Database for chat history
- [ ] WebSocket support for streaming
- [ ] Docker containerization

### Phase 3 (Advanced)
- [ ] Multi-model support (GPT-4, Claude, etc.)
- [ ] Custom fine-tuned models
- [ ] Advanced RAG integration
- [ ] Tool marketplace
- [ ] Analytics dashboard

## Conclusion

This architecture prioritizes:
1. **Speed**: Get running in 5 minutes
2. **Simplicity**: Minimal code, maximum libraries
3. **Extensibility**: Easy to add tools and features
4. **Clarity**: Separated concerns, clear structure

Perfect for hackathons, MVPs, and rapid prototyping!
