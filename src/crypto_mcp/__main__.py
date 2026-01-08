"""Entry point for running the MCP server via python -m crypto_mcp."""

from crypto_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
