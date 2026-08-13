"""Exception hierarchy for the mcp-git server.

Every failure the Git Operations Layer can report is expressed as a subclass
of :class:`McpGitError`. The MCP Tool Handler Layer catches this base class
and translates it into a structured, human-readable tool result; no GitPython
or built-in exception is allowed to reach the MCP client (req 54f3d219).

Example:
    >>> try:
    ...     raise RepositoryNotFoundError("no repository at /tmp/nowhere")
    ... except McpGitError as exc:
    ...     print(f"Error: {exc}")
    Error: no repository at /tmp/nowhere
"""

__all__ = [
    "McpGitError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "InvalidRefError",
    "NothingStagedError",
    "PathConfinementError",
    "BranchAlreadyExistsError",
    "PathNotFoundError",
]


class McpGitError(Exception):
    """Base class for every error raised by the mcp-git server.

    All operations-layer failures derive from this class so that the handler
    layer can catch a single type and format a structured error response.
    """


class RepositoryNotFoundError(McpGitError):
    """Raised when repo_path does not resolve to an existing git repository."""


class RepositoryAlreadyExistsError(McpGitError):
    """Raised when git_init targets a path that is already a repository."""


class InvalidRefError(McpGitError):
    """Raised when a supplied branch, tag, or commit ref does not resolve."""


class NothingStagedError(McpGitError):
    """Raised when a commit is requested but the index holds no changes."""


class PathConfinementError(McpGitError):
    """Raised when a path would resolve outside the confinement boundary.

    The confinement boundary is the repo_path supplied on the current tool
    call (req 24a9ea35).
    """


class BranchAlreadyExistsError(McpGitError):
    """Raised when create_branch is asked for a branch name already in use."""


class PathNotFoundError(McpGitError):
    """Raised when a file path to be staged does not exist in the work tree."""
