#!/usr/bin/env python3
"""
Test script to verify WebSocket client functionality
Run this after starting the main application to test connections
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_connection(host="127.0.0.1", port=8081):
    """Test WebSocket connection to a peer"""
    uri = f"ws://{host}:{port}"
    
    try:
        print(f"🔗 Testing WebSocket connection to {uri}")
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send a test message
            test_message = {
                'type': 'text',
                'content': 'Hello from test client!',
                'timestamp': '2025-01-01T00:00:00',
                'sender': 'TestClient'
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent test message: {test_message}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received within 5 seconds")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "127.0.0.1"
    
    print(f"🧪 Testing WebSocket connection to {host}:8081")
    asyncio.run(test_websocket_connection(host))

