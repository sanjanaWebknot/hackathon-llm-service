#!/usr/bin/env python3
"""
Standalone entry point for MCP server
Uses stdio transport for MCP protocol
"""
import asyncio
import sys
from src.mcp.server import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        sys.exit(1)

