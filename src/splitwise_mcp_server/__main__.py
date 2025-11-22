"""Entry point for the Splitwise MCP Server."""

import asyncio
import sys
from splitwise_mcp_server.server import create_server


def main():
    """Main entry point for the MCP server."""
    try:
        server = create_server()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nShutting down Splitwise MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
