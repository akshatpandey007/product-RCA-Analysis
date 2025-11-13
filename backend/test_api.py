"""
Simple test script to verify the API is working correctly.
Run this after starting the server with: python api.py
"""

import httpx
import asyncio
import json


BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    print("🔍 Testing /health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
    print("   ✅ Health check passed\n")


async def test_start_chat():
    """Test starting a new chat."""
    print("🔍 Testing /chat/start endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/chat/start")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
    print("   ✅ Chat started\n")


async def test_send_message():
    """Test sending a message."""
    print("🔍 Testing /chat/message endpoint...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/chat/message",
            json={"message": "Hello! What's 5 + 3?"}
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Response text: {data.get('text', '')[:200]}")
        if data.get('tool_calls'):
            print(f"   Tools used: {[t['tool'] for t in data['tool_calls']]}")
        assert response.status_code == 200
    print("   ✅ Message sent and response received\n")


async def test_get_tools():
    """Test getting available tools."""
    print("🔍 Testing /tools endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/tools")
        print(f"   Status: {response.status_code}")
        data = response.json()
        tools = data.get('tools', [])
        print(f"   Available tools: {len(tools)}")
        for tool in tools:
            print(f"     - {tool['name']}: {tool['description']}")
        assert response.status_code == 200
    print("   ✅ Tools retrieved\n")


async def test_complex_request():
    """Test a complex request that should create tasks."""
    print("🔍 Testing complex request (task creation)...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/chat/message",
            json={
                "message": "Break down the process of analyzing a production system's performance into tasks"
            }
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Response text: {data.get('text', '')[:200]}")
        if data.get('tasks'):
            print(f"   ✅ Tasks created: {len(data['tasks']['tasks'])} tasks")
            for task in data['tasks']['tasks']:
                print(f"     - Task {task['id']}: {task['description']}")
        else:
            print(f"   ℹ️  No tasks created (agent may have answered directly)")
        assert response.status_code == 200
    print()


async def main():
    """Run all tests."""
    print("🚀 Starting API Tests\n")
    print("=" * 60)
    
    try:
        await test_health()
        await test_get_tools()
        await test_start_chat()
        await test_send_message()
        await test_complex_request()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("\n💡 Your API is working correctly!")
        
    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to the API")
        print("   Make sure the server is running: python api.py")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

