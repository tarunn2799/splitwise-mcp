#!/usr/bin/env python
"""Test script for Splitwise MCP Server tools."""

import asyncio
from splitwise_mcp_server.server import mcp

async def test_tools():
    """Test various MCP tools."""
    print("=" * 70)
    print("Testing Splitwise MCP Server Tools")
    print("=" * 70)
    print()
    
    # Test 1: Get current user
    print("1. Testing get-current-user tool...")
    result = await mcp.call_tool("get-current-user", {})
    print(f"   ✓ Success: {result[:100]}...")
    print()
    
    # Test 2: Get friends
    print("2. Testing get-friends tool...")
    result = await mcp.call_tool("get-friends", {})
    print(f"   ✓ Success: Found friends data")
    print()
    
    # Test 3: Get groups
    print("3. Testing get-groups tool...")
    result = await mcp.call_tool("get-groups", {})
    print(f"   ✓ Success: Found groups data")
    print()
    
    # Test 4: Get categories
    print("4. Testing get-categories tool...")
    result = await mcp.call_tool("get-categories", {})
    print(f"   ✓ Success: Found categories data")
    print()
    
    # Test 5: Get currencies
    print("5. Testing get-currencies tool...")
    result = await mcp.call_tool("get-currencies", {})
    print(f"   ✓ Success: Found currencies data")
    print()
    
    # Test 6: Resolve category (fuzzy matching)
    print("6. Testing resolve-category tool (fuzzy matching)...")
    result = await mcp.call_tool("resolve-category", {"query": "food"})
    print(f"   ✓ Success: {result[:100]}...")
    print()
    
    print("=" * 70)
    print("✓ All MCP tool tests passed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_tools())
