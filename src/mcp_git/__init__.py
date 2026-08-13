"""mcp-git: a local git MCP server.

Exposes 12 git tools over the Model Context Protocol (stdio transport only)
against caller-supplied local repositories. The package is organised in two
layers:

- ``mcp_git.server``: MCP Tool Handler Layer (FastMCP tool registrations).
- ``mcp_git.operations``: Git Operations Layer (GitPython-backed operations).

Errors raised by the operations layer are defined in ``mcp_git.errors``.
"""

__all__ = ["__version__"]

__version__ = "0.1.2"
