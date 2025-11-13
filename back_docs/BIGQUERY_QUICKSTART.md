# BigQuery MCP - Quick Start (5 Minutes)

## ✅ Prerequisites

- [x] Node.js installed (**v25.1.0 ✓** - Already have this!)
- [ ] Google Cloud project with BigQuery
- [ ] Service account key file

---

## 🚀 Setup (3 Steps)

### Step 1: Get BigQuery Credentials (2 minutes)

1. Go to https://console.cloud.google.com/
2. Select/create a project
3. Go to **IAM & Admin** → **Service Accounts**
4. Create service account or use existing
5. Download JSON key file
6. Save it securely (e.g., `~/.gcp/bigquery-key.json`)

---

### Step 2: Configure Environment (1 minute)

Edit `backend/.env`:

```env
# BigQuery MCP Configuration
ENABLE_BIGQUERY_MCP=true
BIGQUERY_PROJECT_ID=your-actual-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/bigquery-key.json
```

**Example**:
```env
ENABLE_BIGQUERY_MCP=true
BIGQUERY_PROJECT_ID=my-analytics-project
GOOGLE_APPLICATION_CREDENTIALS=/Users/pandeak/.gcp/bigquery-key.json
```

---

### Step 3: Restart Server (30 seconds)

```bash
cd backend
source venv/bin/activate
python api.py
```

You should see:
```
✅ Connected to BigQuery MCP server
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Test It!

Open your chat interface and try:

```
"What datasets do I have?"
"Show me tables in my dataset"
"Query the users table"
"What's the total count from users?"
```

---

## 📊 How It Works

### Without MCP (Error-Prone ❌):
```
You: "Show top users"
Gemini: SELECT * FROM users LIMIT 10
Result: Error - table not found!
```

### With MCP (Reliable ✅):
```
You: "Show top users"
Gemini → MCP: "get top users"
MCP: Checks schema, knows actual table name
MCP: Writes perfect SQL automatically
Result: ✅ Perfect execution!
```

---

## 🔧 Troubleshooting

**Error: "Could not find credentials"**
```bash
# Check file exists
ls -la /path/to/your/key.json

# Update .env with correct path
```

**Error: "Permission denied"**
- Add **BigQuery Admin** role to service account
- In Cloud Console: IAM & Admin → Grant role

**Error: "Project not found"**
- Check project ID is correct
- Ensure BigQuery API is enabled

---

## 📚 Full Documentation

For complete setup guide, see: `BIGQUERY_SETUP_GUIDE.md`

---

## 🎯 You're Ready!

Once configured, you can:
- Query any BigQuery table naturally
- No SQL errors - MCP handles it perfectly
- Get analytics insights through conversation
- Zero SQL knowledge required!

Chat naturally:
```
"What's our revenue this month?"
"Show me top customers"
"Analyze user trends"
```

MCP writes perfect SQL every time! 🎉

