"""MCP Tool Handler Layer for the mcp-git server.

Registers the 12 git tools with FastMCP, validates their input with Pydantic
models, dispatches to the Git Operations Layer, and formats structured
results and errors.

Every tool follows the same shape: construct a
:class:`~mcp_git.operations.GitRepository` at ``params.repo_path`` (or, for
git_init, call :func:`~mcp_git.operations.init_repository` directly), invoke
the matching operation, and return a JSON string. A
:class:`~mcp_git.errors.McpGitError` becomes ``"Error: {message}"``; any other
exception is logged server-side and reported as a generic error, so no raw
traceback ever reaches the MCP client (req 54f3d219).

The server speaks MCP over stdio only (req e67ba5a1) and makes no outbound
network calls (req 30130de3).

Example:
    Run the server as a local subprocess::

        $ python -m mcp_git.server
"""

import json
import logging
from typing import Any, Callable, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from mcp_git.errors import McpGitError
from mcp_git.operations import (
    DEFAULT_LOG_MAX_COUNT,
    BranchType,
    GitRepository,
    init_repository,
)

__all__ = ["mcp", "main"]

logger = logging.getLogger(__name__)

mcp = FastMCP("mcp-git")

GENERIC_ERROR = "Error: an unexpected error occurred"

_REPO_PATH_FIELD = Field(
    ...,
    description=(
        "Absolute path to the git repository to operate on. Every operation "
        "in this call is confined to this repository."
    ),
)


def _dispatch(tool_name: str, repo_path: str, operation: Callable[[], Any]) -> str:
    """Run an operations-layer call and format its result for MCP.

    Args:
        tool_name: Name of the calling tool, used for logging.
        repo_path: The repo_path supplied on this call, used for logging.
        operation: Zero-argument callable performing the operation.

    Returns:
        The operation's result as a JSON string (str results are returned
        verbatim), or a structured ``"Error: ..."`` string on failure.
    """
    try:
        result = operation()
    except McpGitError as exc:
        logger.error(
            "%s failed on %s: %s: %s",
            tool_name,
            repo_path,
            type(exc).__name__,
            exc,
        )
        return f"Error: {exc}"
    except Exception:  # noqa: BLE001 - deliberate boundary; see req 54f3d219
        logger.exception("%s raised unexpectedly on %s", tool_name, repo_path)
        return GENERIC_ERROR

    if isinstance(result, str):
        return result
    return json.dumps(result, indent=2)


class GitStatusInput(BaseModel):
    """Input for the git_status tool."""

    repo_path: str = _REPO_PATH_FIELD


class GitDiffUnstagedInput(BaseModel):
    """Input for the git_diff_unstaged tool."""

    repo_path: str = _REPO_PATH_FIELD


class GitDiffStagedInput(BaseModel):
    """Input for the git_diff_staged tool."""

    repo_path: str = _REPO_PATH_FIELD


class GitDiffInput(BaseModel):
    """Input for the git_diff tool."""

    repo_path: str = _REPO_PATH_FIELD
    target: str = Field(
        ...,
        description="Branch name, tag, or commit hash to diff the work tree against.",
    )


class GitLogInput(BaseModel):
    """Input for the git_log tool."""

    repo_path: str = _REPO_PATH_FIELD
    max_count: int = Field(
        DEFAULT_LOG_MAX_COUNT,
        ge=1,
        description="Maximum number of commits to return, most recent first.",
    )


class GitShowInput(BaseModel):
    """Input for the git_show tool."""

    repo_path: str = _REPO_PATH_FIELD
    ref: str = Field(
        ...,
        description="Commit hash, tag, or branch name identifying the commit to show.",
    )


class GitBranchInput(BaseModel):
    """Input for the git_branch tool."""

    repo_path: str = _REPO_PATH_FIELD
    branch_type: BranchType = Field(
        BranchType.LOCAL,
        description="Which branches to list: local, remote, or all.",
    )


class GitCreateBranchInput(BaseModel):
    """Input for the git_create_branch tool."""

    repo_path: str = _REPO_PATH_FIELD
    branch_name: str = Field(..., description="Name of the branch to create.")
    base_branch: Optional[str] = Field(
        None,
        description="Ref to branch from. Defaults to the current HEAD when omitted.",
    )


class GitCommitInput(BaseModel):
    """Input for the git_commit tool."""

    repo_path: str = _REPO_PATH_FIELD
    message: str = Field(..., description="Commit message.")


class GitAddInput(BaseModel):
    """Input for the git_add tool."""

    repo_path: str = _REPO_PATH_FIELD
    files: List[str] = Field(
        ...,
        description="File paths, relative to repo_path, to stage.",
    )


class GitResetInput(BaseModel):
    """Input for the git_reset tool."""

    repo_path: str = _REPO_PATH_FIELD


class GitInitInput(BaseModel):
    """Input for the git_init tool."""

    repo_path: str = Field(
        ...,
        description="Absolute path at which to create the new git repository.",
    )


@mcp.tool(
    name="git_status",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_status(params: GitStatusInput) -> str:
    """Report the working tree status of a git repository.

    Use this to see what has been staged, what has been modified but not
    staged, and what is untracked, before deciding on further git operations.

    Args:
        params: repo_path — the repository to inspect.

    Returns:
        A JSON object with ``staged``, ``unstaged``, and ``untracked`` file
        lists and a ``clean`` boolean, or an ``"Error: ..."`` string when the
        repository cannot be opened.

    Example:
        >>> await git_status(GitStatusInput(repo_path="/repo"))  # doctest: +SKIP
        '{"staged": [], "unstaged": [], "untracked": [], "clean": true}'
    """
    return _dispatch(
        "git_status",
        params.repo_path,
        lambda: GitRepository(params.repo_path).status(),
    )


@mcp.tool(
    name="git_diff_unstaged",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_diff_unstaged(params: GitDiffUnstagedInput) -> str:
    """Show the diff of changes not yet staged for commit.

    Use this to review edits in the working tree before staging them.

    Args:
        params: repo_path — the repository to inspect.

    Returns:
        Unified diff text, empty when there are no unstaged changes, or an
        ``"Error: ..."`` string on failure.
    """
    return _dispatch(
        "git_diff_unstaged",
        params.repo_path,
        lambda: GitRepository(params.repo_path).diff_unstaged(),
    )


@mcp.tool(
    name="git_diff_staged",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_diff_staged(params: GitDiffStagedInput) -> str:
    """Show the diff of changes staged for the next commit.

    Use this to review exactly what a subsequent git_commit would record.

    Args:
        params: repo_path — the repository to inspect.

    Returns:
        Unified diff text, empty when the index matches HEAD, or an
        ``"Error: ..."`` string on failure.
    """
    return _dispatch(
        "git_diff_staged",
        params.repo_path,
        lambda: GitRepository(params.repo_path).diff_staged(),
    )


@mcp.tool(
    name="git_diff",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_diff(params: GitDiffInput) -> str:
    """Show the diff between the working tree and an arbitrary ref.

    Use this to compare the current state against a branch, tag, or commit
    other than HEAD.

    Args:
        params: repo_path — the repository to inspect; target — the branch
            name, tag, or commit hash to compare against.

    Returns:
        Unified diff text, or an ``"Error: ..."`` string — for example when
        ``target`` does not resolve to a valid ref.
    """
    return _dispatch(
        "git_diff",
        params.repo_path,
        lambda: GitRepository(params.repo_path).diff(params.target),
    )


@mcp.tool(
    name="git_log",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_log(params: GitLogInput) -> str:
    """List recent commits, most recent first.

    Use this to understand a repository's history before diffing or showing
    an individual commit.

    Args:
        params: repo_path — the repository to inspect; max_count — how many
            commits to return (default 10).

    Returns:
        A JSON array of objects with ``hash``, ``author``, ``date``, and
        ``message`` keys, or an ``"Error: ..."`` string on failure.
    """
    return _dispatch(
        "git_log",
        params.repo_path,
        lambda: GitRepository(params.repo_path).log(params.max_count),
    )


@mcp.tool(
    name="git_show",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_show(params: GitShowInput) -> str:
    """Show the metadata and diff of a single commit.

    Use this after git_log to inspect what one specific commit changed.

    Args:
        params: repo_path — the repository to inspect; ref — the commit hash,
            tag, or branch name to show.

    Returns:
        A JSON object with ``hash``, ``author``, ``date``, ``message``, and
        ``diff`` keys, or an ``"Error: ..."`` string — for example when
        ``ref`` does not resolve.
    """
    return _dispatch(
        "git_show",
        params.repo_path,
        lambda: GitRepository(params.repo_path).show(params.ref),
    )


@mcp.tool(
    name="git_branch",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_branch(params: GitBranchInput) -> str:
    """List the branches in a repository.

    Use this to discover available branches and which one is checked out.

    Args:
        params: repo_path — the repository to inspect; branch_type — local
            (default), remote, or all.

    Returns:
        A JSON object with ``current`` (the checked-out branch, or null on a
        detached HEAD) and ``branches``, or an ``"Error: ..."`` string on
        failure.
    """
    return _dispatch(
        "git_branch",
        params.repo_path,
        lambda: GitRepository(params.repo_path).branch(params.branch_type),
    )


@mcp.tool(
    name="git_create_branch",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
async def git_create_branch(params: GitCreateBranchInput) -> str:
    """Create a new branch from a base ref.

    The branch is created but not checked out. The call fails without
    changing anything if the branch name is already in use.

    Args:
        params: repo_path — the repository to modify; branch_name — the name
            to create; base_branch — the ref to branch from (defaults to the
            current HEAD).

    Returns:
        A JSON object confirming the created branch, or an ``"Error: ..."``
        string — for example when the branch already exists.
    """
    return _dispatch(
        "git_create_branch",
        params.repo_path,
        lambda: {
            "created": GitRepository(params.repo_path).create_branch(
                params.branch_name, params.base_branch
            )
        },
    )


@mcp.tool(
    name="git_commit",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
async def git_commit(params: GitCommitInput) -> str:
    """Record the staged changes as a new commit.

    Stage files with git_add first; this tool commits only what is already
    in the index, and fails without changing anything when nothing is staged.

    Args:
        params: repo_path — the repository to modify; message — the commit
            message.

    Returns:
        A JSON object with the resulting commit ``hash``, or an
        ``"Error: ..."`` string — for example when nothing is staged.
    """
    return _dispatch(
        "git_commit",
        params.repo_path,
        lambda: {
            "hash": GitRepository(params.repo_path).commit(params.message)
        },
    )


@mcp.tool(
    name="git_add",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_add(params: GitAddInput) -> str:
    """Stage the specified files for the next commit.

    All paths are validated before anything is staged, so a call naming a
    path that does not exist stages nothing.

    Args:
        params: repo_path — the repository to modify; files — paths relative
            to repo_path to stage.

    Returns:
        A JSON object with a ``staged`` list, or an ``"Error: ..."`` string —
        for example when a path does not exist in the working tree.
    """
    return _dispatch(
        "git_add",
        params.repo_path,
        lambda: GitRepository(params.repo_path).add(params.files),
    )


@mcp.tool(
    name="git_reset",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def git_reset(params: GitResetInput) -> str:
    """Unstage all currently staged changes.

    The index is reverted to match HEAD. Working-tree files are not modified,
    but staged intent is discarded and must be rebuilt with git_add.

    Args:
        params: repo_path — the repository to modify.

    Returns:
        A JSON object with ``unstaged_count``, or an ``"Error: ..."`` string
        on failure.
    """
    return _dispatch(
        "git_reset",
        params.repo_path,
        lambda: GitRepository(params.repo_path).reset(),
    )


@mcp.tool(
    name="git_init",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
async def git_init(params: GitInitInput) -> str:
    """Initialise a new git repository at the given path.

    Creates the directory if needed. The call fails without changing
    anything if a repository already exists at that path.

    Args:
        params: repo_path — the path at which to create the repository.

    Returns:
        A JSON object with the ``repo_path`` of the created repository, or an
        ``"Error: ..."`` string — for example when a repository already
        exists there.
    """
    return _dispatch(
        "git_init",
        params.repo_path,
        lambda: {"repo_path": init_repository(params.repo_path)},
    )


def main() -> None:
    """Run the mcp-git server over stdio.

    This is the console-script entry point. The server communicates as a
    local subprocess over stdin/stdout only; no HTTP or SSE transport is
    provided (req e67ba5a1).
    """
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
