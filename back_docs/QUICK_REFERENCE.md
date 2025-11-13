# Quick Reference Card

## 🚀 Start Server

```bash
cd backend
source venv/bin/activate
python api.py
```

Server runs at: **http://localhost:8000**

---

## 🧪 Test Endpoints

### Browser
- **API Docs**: http://localhost:8000/docs (Interactive UI)
- **Frontend**: Open `frontend_example.html` in browser

### cURL
```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools

# Start chat
curl -X POST http://localhost:8000/chat/start

# Send message
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 * 17?"}'
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root/status |
| GET | `/health` | Health check |
| POST | `/chat/start` | Start conversation |
| POST | `/chat/message` | Send message |
| GET | `/chat/history` | Get history |
| GET | `/tasks` | Get task list |
| POST | `/tasks/process` | Process task |
| GET | `/tools` | List tools |
| GET | `/docs` | API documentation |

---

## 🔑 Configure API Key

1. Get key: https://makersuite.google.com/app/apikey
2. Edit `backend/.env`:
   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```
3. Restart server

---

## 🛠️ Add Custom Tool (30 seconds)

In `chat_agent.py`:

```python
# 1. Create handler
async def my_tool(param: str) -> str:
    return f"Result: {param}"

# 2. Register (around line 170)
mcp_tools.register_tool(
    name="my_tool",
    description="What it does",
    parameters={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Input"}
        },
        "required": ["param"]
    },
    handler=my_tool
)
```

Restart server - done!

---

## 📂 Key Files

- **`api.py`** - REST API endpoints
- **`chat_agent.py`** - Gemini agent + tools
- **`config.py`** - Configuration
- **`.env`** - API key & settings
- **`requirements.txt`** - Dependencies

---

## 🔧 Common Commands

```bash
# Install dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run server
python api.py

# Run tests (once you add API key)
python test_api.py

# Deactivate venv
deactivate
```

---

## 🐛 Troubleshooting

**Server won't start?**
- Check you're in venv: `source venv/bin/activate`
- Check port 8000 is free: `lsof -i :8000`

**API key error?**
- Verify `.env` has valid key
- Get new key: https://makersuite.google.com/app/apikey

**CORS errors?**
- Add your frontend URL to `.env`:
  ```env
  CORS_ORIGINS=http://localhost:3000,http://localhost:5173
  ```

---

## 📖 Documentation

- **QUICKSTART.md** - 5-minute setup
- **README.md** - Full documentation  
- **ARCHITECTURE.md** - System design
- **example_custom_tool.py** - Tool examples

---

## ✅ What's Tested & Working

✅ Virtual environment setup
✅ All dependencies installed
✅ Server running on port 8000
✅ All 8 API endpoints responding
✅ 3 tools registered (search, calculate, tasks)
✅ CORS configured
✅ Error handling working
✅ Request/response validation
✅ Gemini integration ready (add API key)

---

**Server Status**: 🟢 RUNNING at http://localhost:8000

**Next**: Add your Gemini API key to `.env` and start chatting!

