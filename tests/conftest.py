"""Shared pytest fixtures for the mcp-git test suite.

Every fixture builds an isolated repository under pytest's ``tmp_path``, so
destructive tools are never exercised against a real repository and no test
can observe a cross-repository effect (req 6468a270).
"""

import git
import pytest


@pytest.fixture
def empty_repo(tmp_path):
    """An initialised repository with no commits.

    Returns:
        pathlib.Path: The repository work-tree root.
    """
    path = tmp_path / "empty_repo"
    path.mkdir()
    repo = git.Repo.init(path)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")
    return path


@pytest.fixture
def repo(empty_repo):
    """A repository with one commit containing ``tracked.txt``.

    Returns:
        pathlib.Path: The repository work-tree root.
    """
    handle = git.Repo(empty_repo)
    (empty_repo / "tracked.txt").write_text("original\n")
    handle.index.add(["tracked.txt"])
    handle.index.commit("initial commit")
    return empty_repo


@pytest.fixture
def other_repo(tmp_path):
    """A second, unrelated repository used to prove cross-repo isolation.

    Returns:
        pathlib.Path: The repository work-tree root.
    """
    path = tmp_path / "other_repo"
    path.mkdir()
    handle = git.Repo.init(path)
    with handle.config_writer() as cw:
        cw.set_value("user", "name", "Other User")
        cw.set_value("user", "email", "other@example.com")
    (path / "other.txt").write_text("untouched\n")
    handle.index.add(["other.txt"])
    handle.index.commit("other initial commit")
    return path
