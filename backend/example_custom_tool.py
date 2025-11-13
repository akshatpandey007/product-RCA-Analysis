"""
Example: How to add custom MCP tools to the chatbot

This file demonstrates how easy it is to extend the agent with new tools.
Copy the patterns here into chat_agent.py to add your own tools.
"""

import httpx
import json
from typing import Dict, Any, List


# ============================================================================
# Example 1: HTTP API Tool
# ============================================================================

async def fetch_github_user(username: str) -> Dict[str, Any]:
    """
    Example tool that fetches GitHub user information.
    
    To add to chat_agent.py:
    1. Copy this function
    2. Register it with mcp_tools.register_tool()
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.github.com/users/{username}")
        if response.status_code == 200:
            data = response.json()
            return {
                "username": data.get("login"),
                "name": data.get("name"),
                "bio": data.get("bio"),
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers")
            }
        else:
            return {"error": f"User not found: {username}"}


# Registration (add this to chat_agent.py):
"""
mcp_tools.register_tool(
    name="fetch_github_user",
    description="Fetch information about a GitHub user",
    parameters={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "GitHub username"}
        },
        "required": ["username"]
    },
    handler=fetch_github_user
)
"""


# ============================================================================
# Example 2: Data Analysis Tool
# ============================================================================

async def analyze_numbers(numbers: List[float]) -> Dict[str, float]:
    """
    Example tool that performs basic statistical analysis.
    """
    if not numbers:
        return {"error": "No numbers provided"}
    
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "mean": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "range": max(numbers) - min(numbers)
    }


# Registration:
"""
mcp_tools.register_tool(
    name="analyze_numbers",
    description="Perform statistical analysis on a list of numbers",
    parameters={
        "type": "object",
        "properties": {
            "numbers": {
                "type": "array",
                "items": {"type": "number"},
                "description": "List of numbers to analyze"
            }
        },
        "required": ["numbers"]
    },
    handler=analyze_numbers
)
"""


# ============================================================================
# Example 3: Text Processing Tool
# ============================================================================

async def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Example tool that extracts keywords from text.
    (Simple implementation - can be enhanced with NLP libraries)
    """
    # Simple keyword extraction (remove common words)
    common_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
        'in', 'with', 'to', 'for', 'of', 'as', 'by', 'this', 'that', 'it'
    }
    
    words = text.lower().split()
    keywords = [w for w in words if w not in common_words and len(w) > 3]
    
    # Count frequency
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]


# Registration:
"""
mcp_tools.register_tool(
    name="extract_keywords",
    description="Extract important keywords from text",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to analyze"},
            "max_keywords": {
                "type": "integer",
                "description": "Maximum number of keywords to return",
                "default": 5
            }
        },
        "required": ["text"]
    },
    handler=extract_keywords
)
"""


# ============================================================================
# Example 4: File System Tool (if needed)
# ============================================================================

async def read_file_content(filepath: str) -> str:
    """
    Example tool to read file contents.
    Use with caution - validate paths in production!
    """
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Registration:
"""
mcp_tools.register_tool(
    name="read_file",
    description="Read contents of a file",
    parameters={
        "type": "object",
        "properties": {
            "filepath": {"type": "string", "description": "Path to the file"}
        },
        "required": ["filepath"]
    },
    handler=read_file_content
)
"""


# ============================================================================
# How to Use These Examples
# ============================================================================

"""
To add any of these tools to your chatbot:

1. Copy the function definition to chat_agent.py

2. Copy the registration code to the "Copy-Paste Configuration Area" 
   in chat_agent.py (around line 170)

3. Restart the server (python api.py)

4. Test your tool:
   curl -X POST http://localhost:8000/chat/message \
     -H "Content-Type: application/json" \
     -d '{"message": "Get information about GitHub user octocat"}'

The agent will automatically use your tool when appropriate!

Example conversation:
User: "Analyze these numbers: 5, 10, 15, 20, 25"
Agent: *calls analyze_numbers tool* → Returns statistics

User: "What are the main keywords in this text: ..."
Agent: *calls extract_keywords tool* → Returns keywords
"""

