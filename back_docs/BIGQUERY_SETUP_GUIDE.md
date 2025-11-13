# BigQuery MCP Integration - Complete Setup Guide

## 🎯 Overview

This guide shows you how to integrate **Official BigQuery MCP Server** for reliable, error-free SQL analytics.

### Why Official MCP?

✅ **Schema-Aware** - Knows your tables and columns  
✅ **Auto-generates SQL** - LLM describes intent, MCP writes correct SQL  
✅ **Zero SQL Errors** - Validated before execution  
✅ **Natural Language** - Just chat naturally  

---

## 🚀 Quick Setup (4 Steps - 10 minutes)

### Step 1: Get Google Cloud Credentials

You need a service account key to access BigQuery:

#### Option A: Use Existing Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your existing project
3. Go to **IAM & Admin** → **Service Accounts**
4. Find existing service account or create new one
5. Click **Keys** → **Add Key** → **Create New Key**
6. Choose **JSON** format
7. Download and save as `bigquery-key.json`

#### Option B: Create New Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a Project** → **New Project**
3. Name it (e.g., "chatbot-analytics")
4. Click **Create**
5. Enable **BigQuery API**:
   - Go to **APIs & Services** → **Library**
   - Search "BigQuery API"
   - Click **Enable**
6. Create service account:
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: "chatbot-bigquery"
   - Click **Create and Continue**
   - Role: **BigQuery Admin** (or custom roles)
   - Click **Done**
7. Create key:
   - Click on the service account
   - Go to **Keys** tab
   - **Add Key** → **Create New Key** → **JSON**
   - Download the JSON file

#### Save the Key

```bash
# Move the key to a secure location
mv ~/Downloads/your-project-*.json ~/.gcp/bigquery-key.json

# Or put it in the project
mv ~/Downloads/your-project-*.json backend/bigquery-key.json
# (Make sure it's in .gitignore!)
```

---

### Step 2: Configure Environment Variables

Edit `backend/.env`:

```env
# BigQuery MCP Configuration
ENABLE_BIGQUERY_MCP=true
BIGQUERY_PROJECT_ID=your-actual-project-id
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourusername/.gcp/bigquery-key.json
```

**Replace**:
- `your-actual-project-id` → Your GCP project ID (from Cloud Console)
- `/Users/yourusername/.gcp/bigquery-key.json` → Actual path to your key file

**Example**:
```env
ENABLE_BIGQUERY_MCP=true
BIGQUERY_PROJECT_ID=chatbot-analytics-123456
GOOGLE_APPLICATION_CREDENTIALS=/Users/pandeak/.gcp/bigquery-key.json
```

---

### Step 3: Install Dependencies

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install BigQuery MCP dependencies
npm install -g @modelcontextprotocol/server-bigquery

# Or install locally
npx -y @modelcontextprotocol/server-bigquery --help
```

---

### Step 4: Test the Connection

```bash
# Test BigQuery credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
export BIGQUERY_PROJECT_ID="your-project-id"

# Test with npx
npx -y @modelcontextprotocol/server-bigquery
```

If successful, you should see the MCP server start!

---

## 🧪 Testing the Integration

### Start the Chatbot

```bash
cd backend
source venv/bin/activate
python api.py
```

### Test Queries

Try these in your chat interface:

```
1. "What datasets do I have in BigQuery?"
   → Lists all your datasets

2. "Show me tables in my analytics dataset"
   → Lists tables in 'analytics' dataset

3. "What columns are in the users table?"
   → Shows table schema

4. "Show me top 10 users by revenue"
   → MCP writes and executes SQL automatically!

5. "What was total revenue last month?"
   → Natural language query, perfect SQL execution
```

---

## 📊 How It Works

### Traditional Approach (Approach B - Error-Prone):
```
You: "Show top users by revenue"
  ↓
Gemini writes SQL: "SELECT * FROM users ORDER BY revenue LIMIT 10"
  ↓
Execute query
  ↓
Error: Table 'users' not found (wrong name!)
```

### MCP Approach (Official - Reliable):
```
You: "Show top users by revenue"
  ↓
Gemini → MCP: "get top users by revenue metric"
  ↓
MCP Server: Checks schema, knows actual table name
  ↓
MCP Server: Writes correct SQL
  ↓
MCP Server: "SELECT user_id, name, total_revenue 
             FROM production.user_analytics 
             ORDER BY total_revenue DESC LIMIT 10"
  ↓
✅ Perfect execution, no errors!
```

---

## 🎯 Available MCP Tools

The BigQuery MCP server provides these tools:

### 1. `bigquery_query`
Execute SQL queries with validation

**Example**: "Show me active users"
- MCP validates schema
- Writes correct SQL
- Returns results

### 2. `bigquery_list_datasets`
List all datasets in your project

**Example**: "What datasets do I have?"

### 3. `bigquery_list_tables`
List tables in a dataset

**Example**: "Show tables in analytics dataset"

### 4. `bigquery_get_table_schema`
Get table structure and column info

**Example**: "What columns are in users table?"

### 5. `bigquery_preview_table`
Preview first few rows

**Example**: "Show me sample data from users"

---

## 🔧 Troubleshooting

### Error: "Could not find credentials"

**Solution**:
```bash
# Check file exists
ls -la /path/to/your/key.json

# Check environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Update .env file with correct path
```

### Error: "Project not found"

**Solution**:
- Verify project ID is correct
- Check you have access to the project
- Ensure BigQuery API is enabled

### Error: "Permission denied"

**Solution**:
- Service account needs BigQuery permissions
- Add role: **BigQuery Data Editor** or **BigQuery Admin**
- In Cloud Console: IAM & Admin → Add role to service account

### Error: "MCP server not starting"

**Solution**:
```bash
# Check Node.js is installed
node --version

# Should be v18+

# Test MCP server manually
npx -y @modelcontextprotocol/server-bigquery \
  --project-id your-project-id \
  --credentials /path/to/key.json
```

---

## 💡 Example Queries

### Analytics Queries

```
"What's our total user count?"
"Show me daily active users for last week"
"What's the average session duration?"
"List top 10 products by sales"
"What's the conversion rate by channel?"
```

### Data Exploration

```
"What tables do we have?"
"Show me the schema of orders table"
"Give me a sample of customer data"
"What datasets are available?"
```

### Business Intelligence

```
"Compare revenue month over month"
"Show user growth trends"
"What's the churn rate this quarter?"
"Identify top performing regions"
```

---

## 🎨 Advanced Configuration

### Custom MCP Server Settings

Edit `backend/mcp_config.json`:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-bigquery"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS}",
        "BIGQUERY_PROJECT_ID": "${BIGQUERY_PROJECT_ID}",
        "BIGQUERY_DEFAULT_DATASET": "analytics",
        "BIGQUERY_MAX_RESULTS": "1000"
      }
    }
  }
}
```

### Multiple BigQuery Projects

You can connect to multiple projects:

```json
{
  "mcpServers": {
    "bigquery-prod": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-bigquery"],
      "env": {
        "BIGQUERY_PROJECT_ID": "production-project",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/prod-key.json"
      }
    },
    "bigquery-staging": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-bigquery"],
      "env": {
        "BIGQUERY_PROJECT_ID": "staging-project",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/staging-key.json"
      }
    }
  }
}
```

---

## 📈 Performance Tips

### 1. Use Caching
- MCP server caches schema information
- Repeated queries are faster

### 2. Limit Result Sets
```
"Show me top 100 users" (good)
vs
"Show me all users" (might be slow for large tables)
```

### 3. Use Specific Dataset Names
```
"Show tables in analytics dataset" (fast)
vs  
"Show all tables" (slower)
```

---

## 🔐 Security Best Practices

### 1. Protect Service Account Key
```bash
# Never commit to git!
echo "bigquery-key.json" >> .gitignore
echo "*.json" >> .gitignore

# Use secure location
chmod 600 ~/.gcp/bigquery-key.json
```

### 2. Limit Permissions
- Use principle of least privilege
- Create custom roles if needed
- Don't use Owner or Editor roles

### 3. Rotate Keys Regularly
- Create new keys every 90 days
- Delete old keys after rotation

---

## 🎉 You're Ready!

Once configured, you can chat naturally:

```
You: "What's our revenue this month?"
Bot: Uses BigQuery MCP → Generates perfect SQL → Returns results

You: "Show me top 10 customers"
Bot: Auto-generates correct query → No errors!

You: "Analyze user retention by cohort"
Bot: Complex SQL, perfectly executed!
```

---

## 📚 Resources

- [BigQuery MCP Server Docs](https://github.com/modelcontextprotocol/servers/tree/main/src/bigquery)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Service Account Keys](https://cloud.google.com/iam/docs/keys-create-delete)

---

## 🆘 Need Help?

**Common Issues**:
1. Credentials error → Check file path in .env
2. Permission denied → Add BigQuery role to service account
3. MCP not starting → Verify Node.js v18+ installed
4. No results → Check project ID and dataset name

**Test Command**:
```bash
# Quick test
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
export BIGQUERY_PROJECT_ID="your-project-id"
npx -y @modelcontextprotocol/server-bigquery
```

---

Happy Querying! 🚀

