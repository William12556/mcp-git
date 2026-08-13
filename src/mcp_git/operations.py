"""Git Operations Layer for the mcp-git server.

Implements the 12 git operations against a caller-supplied repository using
GitPython. :class:`GitRepository` owns the 11 operations that act on an
existing repository; :func:`init_repository` is a module-level function
because git_init runs before any repository exists.

Two invariants hold throughout this module:

- **Confinement** (req 24a9ea35): every operation acts only through the
  repository resolved at construction time, and any caller-supplied file path
  is resolved and checked against that repository's work tree before use.
- **Fail closed** (req 6468a270): destructive operations validate their
  preconditions before the first mutating GitPython call, so a rejected call
  leaves the repository untouched.

Failures are raised as :class:`~mcp_git.errors.McpGitError` subclasses; no raw
GitPython exception escapes this module.

Example:
    >>> repo = GitRepository("/path/to/repo")     # doctest: +SKIP
    >>> repo.status()                             # doctest: +SKIP
    {'staged': [], 'unstaged': [], 'untracked': [], 'clean': True}
"""

import logging
import os
from enum import Enum
from typing import List, Optional

import git
from git.exc import BadName, GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from mcp_git.errors import (
    BranchAlreadyExistsError,
    InvalidRefError,
    McpGitError,
    NothingStagedError,
    PathConfinementError,
    PathNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryNotFoundError,
)

__all__ = [
    "DEFAULT_LOG_MAX_COUNT",
    "BranchType",
    "GitRepository",
    "init_repository",
]

logger = logging.getLogger(__name__)

#: Number of commits returned by :meth:`GitRepository.log` when the caller
#: does not specify ``max_count``.
DEFAULT_LOG_MAX_COUNT = 10


class BranchType(str, Enum):
    """Scope selector for :meth:`GitRepository.branch`.

    Attributes:
        LOCAL: Local branches only (the default).
        REMOTE: Remote-tracking branches only.
        ALL: Local and remote-tracking branches.
    """

    LOCAL = "local"
    REMOTE = "remote"
    ALL = "all"


def _resolve(path: str) -> str:
    """Normalise a caller-supplied path to an absolute, symlink-free path.

    Args:
        path: Any filesystem path, possibly relative, containing ``~`` or
            traversal segments such as ``..``.

    Returns:
        The absolute, fully resolved path.
    """
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


class GitRepository:
    """A confined handle to an existing local git repository.

    The repository is resolved once, at construction time. Every method acts
    through that handle only; no method accepts or resolves an alternate
    repository path, which is what makes the confinement guarantee of
    req 24a9ea35 structural rather than per-method.

    Attributes:
        repo_path: The resolved absolute path of the repository work tree.

    Example:
        >>> repo = GitRepository("/path/to/repo")   # doctest: +SKIP
        >>> repo.commit("feat: add parser")         # doctest: +SKIP
        '9f2c1a...'
    """

    def __init__(self, repo_path: str) -> None:
        """Resolve and confine the repository at ``repo_path``.

        The path is resolved without searching parent directories, so passing
        a subdirectory of a repository is an error rather than a silent
        widening of the confinement boundary.

        Args:
            repo_path: Filesystem path to the target repository work tree.

        Raises:
            RepositoryNotFoundError: ``repo_path`` does not exist, is not a
                directory, or is not a git repository.
            PathConfinementError: ``repo_path`` resolves to a repository whose
                work tree is not ``repo_path`` itself — including bare
                repositories, which have no work tree to confine to.
        """
        resolved = _resolve(repo_path)

        if not os.path.isdir(resolved):
            raise RepositoryNotFoundError(
                f"no directory at repo_path: {repo_path}"
            )

        try:
            repo = git.Repo(resolved, search_parent_directories=False)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise RepositoryNotFoundError(
                f"no git repository at repo_path: {repo_path}"
            ) from exc

        work_tree = repo.working_tree_dir
        if work_tree is None:
            raise PathConfinementError(
                f"repo_path is a bare repository, which has no work tree: "
                f"{repo_path}"
            )
        if _resolve(work_tree) != resolved:
            raise PathConfinementError(
                f"repo_path resolves outside its own repository work tree: "
                f"{repo_path}"
            )

        self.repo_path = resolved
        self._repo = repo
        logger.info("opened repository: %s", self.repo_path)

    def _confined_relpath(self, file_path: str) -> str:
        """Resolve a caller-supplied file path inside the work tree.

        Args:
            file_path: A path relative to ``repo_path``, or an absolute path
                inside it.

        Returns:
            The path relative to the repository root, using forward slashes.

        Raises:
            PathConfinementError: The path resolves outside the repository.
            PathNotFoundError: The path does not exist in the work tree.
        """
        candidate = file_path if os.path.isabs(file_path) else os.path.join(
            self.repo_path, file_path
        )
        resolved = _resolve(candidate)

        if resolved != self.repo_path and not resolved.startswith(
            self.repo_path + os.sep
        ):
            raise PathConfinementError(
                f"path resolves outside repo_path: {file_path}"
            )
        if not os.path.exists(resolved):
            raise PathNotFoundError(
                f"path does not exist in the working tree: {file_path}"
            )

        return os.path.relpath(resolved, self.repo_path).replace(os.sep, "/")

    def _has_commits(self) -> bool:
        """Report whether the repository has at least one commit.

        Returns:
            True when HEAD resolves to a commit; False on an unborn branch.
        """
        return self._repo.head.is_valid()

    def status(self) -> dict:
        """Report the state of the working tree.

        Returns:
            A dict with keys ``staged``, ``unstaged``, and ``untracked``
            (each a list of repository-relative paths) and ``clean``, True
            when all three lists are empty.

        Example:
            >>> repo.status()                       # doctest: +SKIP
            {'staged': ['a.txt'], 'unstaged': [], 'untracked': [], 'clean': False}
        """
        repo = self._repo

        if self._has_commits():
            staged = sorted(
                {d.a_path or d.b_path for d in repo.index.diff("HEAD")}
            )
        else:
            staged = sorted(path for path, _ in repo.index.entries)

        unstaged = sorted({d.a_path or d.b_path for d in repo.index.diff(None)})
        untracked = sorted(repo.untracked_files)

        return {
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "clean": not (staged or unstaged or untracked),
        }

    def diff_unstaged(self) -> str:
        """Return the diff of unstaged working-tree changes.

        Returns:
            Unified diff text; an empty string when there are no unstaged
            changes to tracked files.
        """
        return self._repo.git.diff()

    def diff_staged(self) -> str:
        """Return the diff of changes staged in the index.

        Returns:
            Unified diff text; an empty string when the index matches HEAD.
        """
        return self._repo.git.diff("--cached")

    def diff(self, target: str) -> str:
        """Return the diff of the working tree against an arbitrary ref.

        Args:
            target: Branch name, tag, or commit hash to diff against.

        Returns:
            Unified diff text between ``target`` and the working tree.

        Raises:
            InvalidRefError: ``target`` does not resolve to a valid ref.

        Example:
            >>> repo.diff("main")                   # doctest: +SKIP
            'diff --git a/a.txt b/a.txt\\n...'
        """
        self._require_commit(target)
        return self._repo.git.diff(target)

    def log(self, max_count: int = DEFAULT_LOG_MAX_COUNT) -> list:  # list[dict]
        """Return commit history, most recent first.

        Args:
            max_count: Maximum number of entries to return. Defaults to
                :data:`DEFAULT_LOG_MAX_COUNT`.

        Returns:
            A list of dicts, each with ``hash``, ``author``, ``date``, and
            ``message`` keys. Empty when the repository has no commits.
        """
        if not self._has_commits():
            return []

        entries = []
        for commit in self._repo.iter_commits(max_count=max_count):
            entries.append(
                {
                    "hash": commit.hexsha,
                    "author": f"{commit.author.name} <{commit.author.email}>",
                    "date": commit.authored_datetime.isoformat(),
                    "message": commit.message.strip(),
                }
            )
        return entries

    def show(self, ref: str) -> dict:
        """Return the metadata and diff of a single commit.

        Args:
            ref: Commit hash, tag, or branch name identifying the commit.

        Returns:
            A dict with ``hash``, ``author``, ``date``, ``message``, and
            ``diff`` keys. ``diff`` is the commit's patch text, which is
            empty for an empty commit.

        Raises:
            InvalidRefError: ``ref`` does not resolve to a commit.
        """
        commit = self._require_commit(ref)

        try:
            diff_text = self._repo.git.show(
                "--format=", "--patch", commit.hexsha
            )
        except GitCommandError as exc:
            raise McpGitError(f"unable to show commit {ref}: {exc}") from exc

        return {
            "hash": commit.hexsha,
            "author": f"{commit.author.name} <{commit.author.email}>",
            "date": commit.authored_datetime.isoformat(),
            "message": commit.message.strip(),
            "diff": diff_text,
        }

    def branch(self, branch_type: BranchType = BranchType.LOCAL) -> dict:
        """List branches in the repository.

        Args:
            branch_type: Which branches to list — local, remote, or all.
                Defaults to :attr:`BranchType.LOCAL`.

        Returns:
            A dict with ``current`` (the checked-out branch name, or None on
            a detached HEAD) and ``branches`` (a sorted list of names).
        """
        branch_type = BranchType(branch_type)
        repo = self._repo

        local = [head.name for head in repo.heads]
        remote = [ref.name for remote in repo.remotes for ref in remote.refs]

        if branch_type is BranchType.LOCAL:
            branches = local
        elif branch_type is BranchType.REMOTE:
            branches = remote
        else:
            branches = local + remote

        try:
            current = repo.active_branch.name
        except TypeError:
            current = None

        return {"current": current, "branches": sorted(branches)}

    def create_branch(
        self, branch_name: str, base_branch: Optional[str] = None
    ) -> str:
        """Create a new branch from a base ref.

        Preconditions are checked before the branch is created, so a rejected
        call leaves the repository unchanged (req 6468a270).

        Args:
            branch_name: Name of the branch to create.
            base_branch: Ref to branch from. Defaults to current HEAD.

        Returns:
            The created branch name.

        Raises:
            BranchAlreadyExistsError: ``branch_name`` already exists.
            InvalidRefError: ``base_branch`` does not resolve.
            McpGitError: The repository has no commit to branch from.
        """
        repo = self._repo

        if branch_name in {head.name for head in repo.heads}:
            raise BranchAlreadyExistsError(
                f"branch already exists: {branch_name}"
            )

        if base_branch is not None:
            base = self._require_commit(base_branch)
        elif self._has_commits():
            base = repo.head.commit
        else:
            raise McpGitError(
                "cannot create a branch: the repository has no commits yet"
            )

        try:
            repo.create_head(branch_name, base)
        except (GitCommandError, ValueError, OSError) as exc:
            raise McpGitError(
                f"unable to create branch {branch_name}: {exc}"
            ) from exc

        logger.info("created branch %s in %s", branch_name, self.repo_path)
        return branch_name

    def commit(self, message: str) -> str:
        """Create a commit from the currently staged changes.

        The index is checked before the commit is created, so a call with
        nothing staged leaves the repository unchanged (req 6468a270).

        Args:
            message: The commit message.

        Returns:
            The hash of the resulting commit.

        Raises:
            NothingStagedError: No changes are staged in the index.
            McpGitError: Git refused the commit.
        """
        repo = self._repo

        if self._has_commits():
            staged = list(repo.index.diff("HEAD"))
        else:
            staged = list(repo.index.entries)

        if not staged:
            raise NothingStagedError(
                "nothing staged to commit; stage changes with git_add first"
            )

        try:
            new_commit = repo.index.commit(message)
        except (GitCommandError, ValueError, OSError) as exc:
            raise McpGitError(f"unable to create commit: {exc}") from exc

        logger.info("committed %s in %s", new_commit.hexsha, self.repo_path)
        return new_commit.hexsha

    def add(self, files: List[str]) -> dict:
        """Stage the specified files.

        Every path is resolved and confinement-checked before anything is
        staged, so a call naming an invalid path stages nothing at all
        (req 6468a270).

        Args:
            files: Paths relative to ``repo_path`` (absolute paths inside the
                repository are also accepted).

        Returns:
            A dict with a ``staged`` key listing the repository-relative
            paths that were staged.

        Raises:
            PathNotFoundError: A named path does not exist in the work tree.
            PathConfinementError: A named path resolves outside the
                repository.
            McpGitError: ``files`` is empty, or git refused the operation.
        """
        if not files:
            raise McpGitError("no files supplied to stage")

        relpaths = [self._confined_relpath(file_path) for file_path in files]

        try:
            self._repo.index.add(relpaths)
        except (GitCommandError, ValueError, OSError) as exc:
            raise McpGitError(f"unable to stage files: {exc}") from exc

        logger.info("staged %d path(s) in %s", len(relpaths), self.repo_path)
        return {"staged": relpaths}

    def reset(self) -> dict:
        """Unstage every currently staged change.

        The index is reverted to match HEAD; the working tree is untouched.

        Returns:
            A dict with an ``unstaged_count`` key giving the number of paths
            that were unstaged.

        Raises:
            McpGitError: Git refused the reset.
        """
        repo = self._repo

        if self._has_commits():
            count = len({d.a_path or d.b_path for d in repo.index.diff("HEAD")})
        else:
            count = len(repo.index.entries)

        try:
            repo.git.reset()
        except GitCommandError as exc:
            raise McpGitError(f"unable to reset the index: {exc}") from exc

        logger.info("unstaged %d path(s) in %s", count, self.repo_path)
        return {"unstaged_count": count}

    def _require_commit(self, ref: str) -> "git.Commit":
        """Resolve a ref to a commit within this repository.

        Args:
            ref: Branch name, tag, or commit hash.

        Returns:
            The resolved commit object.

        Raises:
            InvalidRefError: The ref does not resolve to a commit.
        """
        try:
            return self._repo.commit(ref)
        except (BadName, ValueError, GitCommandError, IndexError) as exc:
            raise InvalidRefError(f"ref does not resolve: {ref}") from exc


def init_repository(repo_path: str) -> str:
    """Initialise a new git repository at ``repo_path``.

    This is a module-level function rather than a :class:`GitRepository`
    method because it runs before any repository exists, so there is no
    repository handle to confine it to. The target is checked before
    anything is written, so a call against an existing repository leaves it
    untouched (req 6468a270).

    Args:
        repo_path: Filesystem path at which to create the repository. Parent
            directories are created if needed.

    Returns:
        The resolved absolute path of the created repository.

    Raises:
        RepositoryAlreadyExistsError: ``repo_path`` already contains a git
            repository.
        McpGitError: The path could not be created or initialised.

    Example:
        >>> init_repository("/tmp/new-repo")        # doctest: +SKIP
        '/tmp/new-repo'
    """
    resolved = _resolve(repo_path)

    if os.path.exists(os.path.join(resolved, ".git")):
        raise RepositoryAlreadyExistsError(
            f"a git repository already exists at: {repo_path}"
        )

    try:
        git.Repo.init(resolved, mkdir=True)
    except (GitCommandError, OSError) as exc:
        raise McpGitError(
            f"unable to initialise a repository at {repo_path}: {exc}"
        ) from exc

    logger.info("initialised repository: %s", resolved)
    return resolved
