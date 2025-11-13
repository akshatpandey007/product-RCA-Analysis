# Quick Start Guide - Agentic Chatbot Backend

This guide will get you up and running in 5 minutes.

## Prerequisites

- Python 3.8+
- pip
- A Gemini API key (free from Google)

## Step 1: Install Dependencies

```bash
cd backend
./setup.sh
```

Or manually:

```bash
pip install -r requirements.txt
```

## Step 2: Get Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy your key

## Step 3: Configure

Edit `.env` file and add your API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

## Step 4: Start Server

```bash
python api.py
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 5: Test It!

### Option A: Using cURL

```bash
# Start a conversation
curl -X POST http://localhost:8000/chat/start

# Send a message
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 * 17?"}'

# List available tools
curl http://localhost:8000/tools
```

### Option B: Using the Test Script

```bash
python test_api.py
```

### Option C: Using Browser

Visit: http://localhost:8000/docs

This opens the interactive API documentation where you can test all endpoints!

## Example Conversations

### Simple Calculation

```json
POST /chat/message
{
  "message": "Calculate 123 * 456"
}

Response:
{
  "text": "The result is 56088",
  "tool_calls": [
    {
      "tool": "calculate",
      "arguments": {"expression": "123 * 456"},
      "result": "56088"
    }
  ]
}
```

### Complex Task (Creates Task List)

```json
POST /chat/message
{
  "message": "Create a plan to optimize our database performance"
}

Response:
{
  "text": "I've created a task list to optimize database performance...",
  "tasks": {
    "tasks": [
      {"id": 1, "description": "Analyze slow queries", "status": "pending"},
      {"id": 2, "description": "Review indexing strategy", "status": "pending"},
      {"id": 3, "description": "Check connection pooling", "status": "pending"}
    ]
  }
}
```

Then process tasks:

```json
POST /tasks/process
{
  "task_id": 1
}
```

## Connecting Your Frontend

### JavaScript/React Example

```javascript
// Start conversation
await fetch('http://localhost:8000/chat/start', {
  method: 'POST'
});

// Send message
const response = await fetch('http://localhost:8000/chat/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Hello, analyze this for me...'
  })
});

const data = await response.json();
console.log('Agent response:', data.text);

// Check if tasks were created
if (data.tasks) {
  console.log('Tasks:', data.tasks);
}
```

### Python Client Example

```python
import httpx
import asyncio

async def chat():
    async with httpx.AsyncClient() as client:
        # Start conversation
        await client.post('http://localhost:8000/chat/start')
        
        # Send message
        response = await client.post(
            'http://localhost:8000/chat/message',
            json={'message': 'Explain quantum computing'}
        )
        
        data = response.json()
        print(f"Agent: {data['text']}")
        
        # Check for tasks
        if data['tasks']:
            print(f"Tasks created: {len(data['tasks']['tasks'])}")

asyncio.run(chat())
```

## Adding Custom Tools

See `example_custom_tool.py` for examples. To add a tool:

1. **Create the handler** in `chat_agent.py`:

```python
async def my_custom_tool(param: str) -> str:
    # Your logic here
    return f"Result for {param}"
```

2. **Register it** in `chat_agent.py`:

```python
mcp_tools.register_tool(
    name="my_custom_tool",
    description="What it does",
    parameters={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Description"}
        },
        "required": ["param"]
    },
    handler=my_custom_tool
)
```

3. **Restart the server** - that's it!

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/chat/start` | POST | Start new conversation |
| `/chat/message` | POST | Send message to agent |
| `/chat/history` | GET | Get conversation history |
| `/tasks` | GET | Get current task list |
| `/tasks/process` | POST | Process a specific task |
| `/tools` | GET | List available tools |

## Configuration

All settings in `.env`:

```env
# Required
GEMINI_API_KEY=your_key

# Optional (defaults shown)
GEMINI_MODEL=gemini-2.0-flash-exp
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Troubleshooting

### "Could not find credentials"
- Check your `.env` file exists
- Verify `GEMINI_API_KEY` is set correctly
- Get a new key from https://makersuite.google.com/app/apikey

### CORS Errors from Frontend
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Example: `CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080`

### "Tool not working"
- Check tool is registered in `chat_agent.py`
- Verify tool handler is `async`
- Check `/tools` endpoint to see registered tools
- Restart the server after adding new tools

### Import Errors
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version` (need 3.8+)

## Next Steps

1. **Customize Tools**: Edit `chat_agent.py` to add your own MCP tools
2. **Frontend**: Connect your React/Vue/etc frontend to the API
3. **Deploy**: Use Docker or deploy to cloud (Heroku, AWS, GCP, etc.)
4. **Enhance**: Add logging, monitoring, rate limiting for production

## Resources

- [Backend README](./README.md) - Full documentation
- [Example Tools](./example_custom_tool.py) - Custom tool examples
- [Gemini API Docs](https://ai.google.dev/docs) - Gemini documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/) - FastAPI documentation

## Support

If you run into issues:
1. Check the console output for error messages
2. Verify your API key is valid
3. Try the test script: `python test_api.py`
4. Check the logs in the terminal where you ran `python api.py`

Happy building! 🚀

