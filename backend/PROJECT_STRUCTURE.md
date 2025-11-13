# Project Structure

## File Organization

```
backend/
│
├── 📄 app.py                    # Main Flask application (API routes)
│   ├── /health                 # Health check endpoint
│   ├── /chat                   # Send message endpoint
│   ├── /chat/new               # Create new session
│   ├── /chat/history/<id>      # Get conversation history
│   ├── /sessions               # List all sessions
│   └── /chat/delete/<id>       # Delete session
│
├── 🤖 gemini_service.py         # Gemini AI integration
│   └── GeminiService class
│       ├── __init__()          # Configure API
│       ├── create_model()      # Initialize model
│       ├── create_chat_session() # Start new chat
│       ├── send_message()      # Send to AI & parse response
│       └── get_chat_history()  # Extract history
│
├── 💾 session_manager.py        # Session management
│   └── SessionManager class
│       ├── get_or_create_session()
│       ├── create_new_session()
│       ├── delete_session()
│       ├── session_exists()
│       ├── get_session()
│       ├── get_all_session_ids()
│       └── clear_all_sessions()
│
├── ⚙️  config.py                 # Configuration (EDIT THIS!)
│   ├── GEMINI_API_KEY          # 👈 Add your API key here
│   ├── MODEL_NAME
│   ├── TEMPERATURE, TOP_P
│   ├── MAX_OUTPUT_TOKENS
│   └── HOST, PORT, DEBUG
│
├── 📦 requirements.txt          # Python dependencies
│
├── 📖 README.md                 # API documentation
├── 📖 ARCHITECTURE.md           # Architecture details
└── 📖 PROJECT_STRUCTURE.md      # This file
```

## Quick Reference

### Start Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   Edit `config.py` and set your `GEMINI_API_KEY`

3. **Run server:**
   ```bash
   python app.py
   ```

### File Responsibilities

| File | Purpose | Edit? |
|------|---------|-------|
| `config.py` | Settings and API key | ✅ YES - Add your API key |
| `app.py` | API endpoints | ⚠️ Only to add new routes |
| `gemini_service.py` | AI logic | ⚠️ Only to change AI behavior |
| `session_manager.py` | Session handling | ⚠️ Only to change session logic |
| `requirements.txt` | Dependencies | ⚠️ Only to add packages |

### API Endpoints Quick Guide

```
GET    /health                    → Check if server is running
POST   /chat                      → Send message, get AI response
POST   /chat/new                  → Start fresh conversation
GET    /chat/history/<session_id> → View past messages
GET    /sessions                  → List all active chats
DELETE /chat/delete/<session_id>  → Remove a conversation
```

### Data Flow

```
User Request
    ↓
app.py (validate & route)
    ↓
session_manager.py (manage session)
    ↓
gemini_service.py (talk to AI)
    ↓
Gemini API (process & think)
    ↓
gemini_service.py (parse thinking + response)
    ↓
app.py (format JSON)
    ↓
User Response
```

### Key Features

- ✨ **Thinking Data**: Captures AI's reasoning process
- 🔄 **Multi-Session**: Handle multiple conversations
- 🎯 **Clean Architecture**: Separated concerns
- 🛡️ **Error Handling**: Comprehensive validation
- 📝 **Well Documented**: Clear comments and docs

### Development Tips

1. **Testing locally**: Use cURL commands from README.md
2. **Debugging**: Set `DEBUG = True` in config.py
3. **Logs**: Check terminal output for errors
4. **Sessions**: Each user/conversation gets unique session_id
5. **Thinking**: Gemini model includes reasoning in responses

