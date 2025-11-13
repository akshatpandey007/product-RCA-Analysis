# BigQuery MCP Integration Guide

## 🎯 Overview

This guide shows you how to integrate **existing MCP BigQuery tools** with your chatbot, rather than creating custom implementations.

### Why Use Existing MCP Tools?

✅ **Standard Protocol** - Use official MCP servers  
✅ **Pre-built** - No need to reinvent the wheel  
✅ **Maintained** - Community-supported implementations  
✅ **Easy Integration** - Just connect and use  

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Install BigQuery MCP Server

The official BigQuery MCP server is available via npm:

```bash
# Install Node.js if you don't have it
# On Mac: brew install node

# The server will be installed on-demand via npx
# No manual installation needed!
```

### Step 2: Set Up Google Cloud Credentials

You need a service account key for BigQuery access:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Go to **IAM & Admin** → **Service Accounts**
4. Create a service account (or use existing)
5. Give it **BigQuery Admin** role (or custom roles)
6. Create a JSON key and download it
7. Save it securely (e.g., `~/bigquery-key.json`)

### Step 3: Configure MCP Connection

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
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/yourusername/bigquery-key.json",
        "BIGQUERY_PROJECT_ID": "your-gcp-project-id"
      }
    }
  }
}
```

**Important**: Replace:
- `/Users/yourusername/bigquery-key.json` with actual path to your key
- `your-gcp-project-id` with your GCP project ID

---

## 🔧 Alternative: Use Python BigQuery Library Directly

If you don't want to use the Node.js MCP server, you can create a simple Python wrapper:

```bash
# Already added to requirements.txt
pip install google-cloud-bigquery
```

Then use the simpler approach - I'll create Python functions that wrap BigQuery.

---

## 📊 What BigQuery MCP Tools Provide

The official MCP BigQuery server provides these tools:

1. **query** - Run SQL queries
2. **list_datasets** - List available datasets
3. **list_tables** - List tables in a dataset
4. **get_table_schema** - Get table structure
5. **get_table_preview** - Preview table data

---

## 🎯 Which Approach to Use?

### Approach 1: Official MCP Server (Standard)
**Pros:**
- Standard MCP protocol
- Pre-built and maintained
- Full feature set

**Cons:**
- Requires Node.js
- More complex setup
- External process

### Approach 2: Python BigQuery Library (Simpler) ⭐
**Pros:**
- Pure Python (already using Python)
- Simpler setup
- Direct integration
- No external processes

**Cons:**
- Custom wrapper (but simple)
- Not using MCP protocol

---

## 💡 Recommended: Python BigQuery Integration

For your use case (hackathon MVP), I recommend **Approach 2** - using the Python BigQuery library directly.

### Why?

1. **Simpler** - No Node.js dependency
2. **Faster** - Direct Python integration
3. **MVP-friendly** - Matches your project philosophy
4. **Easy to extend** - Add custom analytics logic

---

## 🚀 Implementation Options

### Option A: Use Official MCP Server

```bash
# I've already created mcp_client.py for this
# Just configure mcp_config.json and start!
```

### Option B: Use Python BigQuery Library (Recommended)

```python
# I'll create bigquery_tools.py with simple Python functions
# No external dependencies, pure Python integration
```

---

## 🤔 Which Should You Choose?

**Choose Official MCP Server if:**
- You want standard MCP protocol
- You have Node.js already
- You want to use other MCP servers too
- You want community-maintained tools

**Choose Python Library if:**
- You want simplest setup (recommended for MVP)
- You don't want Node.js dependency
- You want full control over functionality
- You want to add custom analytics logic

---

## 📝 What I'll Implement

Let me create **both options** and you can choose:

1. **mcp_client.py** ✅ Already created - for official MCP servers
2. **bigquery_tools.py** - Simple Python wrapper (I'll create this)
3. **Integration examples** - Show both approaches

---

## 🎯 Next Steps

Tell me which approach you prefer:

**A) Official MCP Server**
- I'll help you set up Node.js and configure the MCP server
- More "proper" but more setup

**B) Python BigQuery Library** (Recommended)
- I'll create simple Python functions
- Quick and easy, perfect for MVP

Which would you like?

