# How to Run & Test Your Chatbot

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Server

Open your terminal and run:

```bash
cd backend
source venv/bin/activate
python api.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal open!** The server is now running.

---

### Step 2: Choose Your Testing Method

Pick one of these three easy options:

#### Option A: Browser API Docs (Recommended! 🌟)

1. Open your browser
2. Go to: **http://localhost:8000/docs**
3. You'll see interactive API documentation
4. Click **"Try it out"** on any endpoint
5. Enter your message
6. Click **"Execute"**
7. See the response!

#### Option B: Frontend Chat UI (Beautiful! 💬)

1. Open the file: `backend/frontend_example.html` in your browser
   - On Mac: `open backend/frontend_example.html`
   - Or just double-click the file
2. You'll see a beautiful chat interface
3. Type messages and chat with the AI!

#### Option C: Command Line (For Developers 💻)

Open a **new terminal** (keep server running) and test:

```bash
# Health check
curl http://localhost:8000/health

# Start conversation
curl -X POST http://localhost:8000/chat/start

# Send a message
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "hi"}'

# Test calculator
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 times 17?"}'
```

---

### Step 3: Stop the Server

When you're done testing:

- Press `Ctrl+C` in the terminal where the server is running

---

## 📝 Example Testing Session

### Terminal 1 (Server):
```bash
$ cd backend
$ source venv/bin/activate
(venv) $ python api.py
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Terminal 2 (Testing):
```bash
$ curl http://localhost:8000/health
{"status":"healthy","message":"Service is operational"}

$ curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
{"text":"Hello! How can I help you today?","tasks":null,"tool_calls":[],"thinking":[]}
```

---

## 🧪 Automated Testing

Run the built-in test suite:

```bash
cd backend
source venv/bin/activate
python test_api.py
```

This will automatically test all endpoints and show you the results!

---

## 🎯 What to Test

Try these test cases:

### 1. Simple Greeting
```json
{"message": "hi"}
```
Expected: Friendly greeting response

### 2. Calculator (Tests Tool Usage)
```json
{"message": "What is 123 times 456?"}
```
Expected: "56088" with tool_calls showing calculate was used

### 3. General Question
```json
{"message": "Tell me about quantum computing"}
```
Expected: Detailed explanation

### 4. Complex Task (Creates Task List)
```json
{"message": "Create a plan to optimize database performance"}
```
Expected: Response with a task list

---

## 🔧 Troubleshooting

### Problem: "Port already in use"
**Solution:**
```bash
lsof -ti:8000 | xargs kill -9
python api.py
```

### Problem: "Module not found"
**Solution:**
```bash
source venv/bin/activate  # Make sure venv is activated
```

### Problem: "Connection refused"
**Solution:**
Check if server is running:
```bash
curl http://localhost:8000/health
```

### Problem: Frontend can't connect
**Solution:**
- Server must be running
- Check console for CORS errors
- Make sure you're opening `frontend_example.html` in a browser (not just viewing the file)

---

## 📊 API Endpoints Reference

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/` | GET | Check if API is running |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |
| `/chat/start` | POST | Start new conversation |
| `/chat/message` | POST | Send message to chatbot |
| `/chat/history` | GET | Get conversation history |
| `/tasks` | GET | Get current task list |
| `/tasks/process` | POST | Process specific task |
| `/tools` | GET | List available tools |

---

## 🎨 Using the Frontend Example

The `frontend_example.html` provides a complete chat interface:

**Features:**
- Real-time messaging
- Shows when agent is thinking (loading animation)
- Displays tool usage (when agent uses calculator, search, etc.)
- Shows created tasks
- Beautiful modern UI
- Connection status indicator

**How to use:**
1. Make sure server is running (`python api.py`)
2. Open `frontend_example.html` in any browser
3. Start chatting!

---

## 🔑 Current Configuration

Your chatbot is configured with:

- **Model**: `gemini-2.5-flash` (efficient and cost-effective)
- **Port**: `8000`
- **Tools**: 3 available
  - `search_web` - Web search
  - `calculate` - Math calculations
  - `create_task_list` - Break down complex problems

See configuration in: `backend/.env`

---

## 📚 More Information

- **Full Documentation**: `backend/README.md`
- **Architecture**: `backend/ARCHITECTURE.md`
- **Quick Reference**: `backend/QUICK_REFERENCE.md`
- **Tool Examples**: `backend/example_custom_tool.py`

---

## ✅ Checklist

Before testing, make sure:

- [ ] Virtual environment is activated (`source venv/bin/activate`)
- [ ] Server is running (`python api.py`)
- [ ] You can see "Uvicorn running" message
- [ ] Port 8000 is not already in use

---

**Happy Testing! 🚀**

Your chatbot is ready to use. Try it out with the browser interface at http://localhost:8000/docs!

