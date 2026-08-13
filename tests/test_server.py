"""Tests for the MCP Tool Handler Layer (``mcp_git.server``).

Covers one or more tests per tool (req 9a52683b), the structured error
contract (req 54f3d219), and the tool annotation set (req fab9139d).
"""

import json

import git
import pytest

from mcp_git import server
from mcp_git.operations import BranchType
from mcp_git.server import (
    GENERIC_ERROR,
    GitAddInput,
    GitBranchInput,
    GitCommitInput,
    GitCreateBranchInput,
    GitDiffInput,
    GitDiffStagedInput,
    GitDiffUnstagedInput,
    GitInitInput,
    GitLogInput,
    GitResetInput,
    GitShowInput,
    GitStatusInput,
    git_add,
    git_branch,
    git_commit,
    git_create_branch,
    git_diff,
    git_diff_staged,
    git_diff_unstaged,
    git_init,
    git_log,
    git_reset,
    git_show,
    git_status,
    mcp,
)

EXPECTED_ANNOTATIONS = {
    "git_status": (True, False, True, False),
    "git_diff_unstaged": (True, False, True, False),
    "git_diff_staged": (True, False, True, False),
    "git_diff": (True, False, True, False),
    "git_log": (True, False, True, False),
    "git_show": (True, False, True, False),
    "git_branch": (True, False, True, False),
    "git_create_branch": (False, False, False, False),
    "git_commit": (False, False, False, False),
    "git_add": (False, False, True, False),
    "git_reset": (False, True, True, False),
    "git_init": (False, False, False, False),
}


class TestRegistration:
    """Tool registration and annotations (req fab9139d, req e67ba5a1)."""

    async def test_all_twelve_tools_registered(self):
        names = {tool.name for tool in await mcp.list_tools()}
        assert names == set(EXPECTED_ANNOTATIONS)

    async def test_annotations_match_the_design_table(self):
        for tool in await mcp.list_tools():
            expected = EXPECTED_ANNOTATIONS[tool.name]
            actual = (
                tool.annotations.readOnlyHint,
                tool.annotations.destructiveHint,
                tool.annotations.idempotentHint,
                tool.annotations.openWorldHint,
            )
            assert actual == expected, tool.name

    async def test_every_tool_is_documented(self):
        for tool in await mcp.list_tools():
            assert tool.description


class TestGitStatus:
    """req fedee316."""

    async def test_clean_repository(self, repo):
        result = json.loads(await git_status(GitStatusInput(repo_path=str(repo))))
        assert result["clean"] is True

    async def test_missing_repository_returns_structured_error(self, tmp_path):
        result = await git_status(GitStatusInput(repo_path=str(tmp_path / "no")))
        assert result.startswith("Error: no git repository at repo_path") or (
            result.startswith("Error: no directory at repo_path")
        )
        assert "Traceback" not in result


class TestGitDiffUnstaged:
    """req 08da738e."""

    async def test_reports_working_tree_edit(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        result = await git_diff_unstaged(GitDiffUnstagedInput(repo_path=str(repo)))
        assert "+changed" in result

    async def test_empty_when_clean(self, repo):
        assert await git_diff_unstaged(
            GitDiffUnstagedInput(repo_path=str(repo))
        ) == ""


class TestGitDiffStaged:
    """req 7e8bfefa."""

    async def test_reports_staged_edit(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])
        result = await git_diff_staged(GitDiffStagedInput(repo_path=str(repo)))
        assert "+changed" in result


class TestGitDiff:
    """req 2f0a1f17."""

    async def test_diff_against_head(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        result = await git_diff(GitDiffInput(repo_path=str(repo), target="HEAD"))
        assert "+changed" in result

    async def test_invalid_target_returns_structured_error(self, repo):
        result = await git_diff(
            GitDiffInput(repo_path=str(repo), target="no-such-ref")
        )
        assert result == "Error: ref does not resolve: no-such-ref"


class TestGitLog:
    """req aa27e381."""

    async def test_returns_history(self, repo):
        entries = json.loads(await git_log(GitLogInput(repo_path=str(repo))))
        assert entries[0]["message"] == "initial commit"

    async def test_max_count_is_honoured(self, repo):
        handle = git.Repo(repo)
        (repo / "second.txt").write_text("x\n")
        handle.index.add(["second.txt"])
        handle.index.commit("second commit")

        entries = json.loads(
            await git_log(GitLogInput(repo_path=str(repo), max_count=1))
        )
        assert len(entries) == 1


class TestGitShow:
    """req 8a1fefa4."""

    async def test_returns_commit_detail(self, repo):
        result = json.loads(
            await git_show(GitShowInput(repo_path=str(repo), ref="HEAD"))
        )
        assert result["message"] == "initial commit"
        assert "tracked.txt" in result["diff"]

    async def test_invalid_ref_returns_structured_error(self, repo):
        result = await git_show(GitShowInput(repo_path=str(repo), ref="deadbeef"))
        assert result == "Error: ref does not resolve: deadbeef"


class TestGitBranch:
    """req 0931a0d8."""

    async def test_lists_local_branches(self, repo):
        git.Repo(repo).create_head("feature")
        result = json.loads(await git_branch(GitBranchInput(repo_path=str(repo))))
        assert "feature" in result["branches"]
        assert result["current"] == git.Repo(repo).active_branch.name

    async def test_remote_scope(self, repo):
        result = json.loads(
            await git_branch(
                GitBranchInput(repo_path=str(repo), branch_type=BranchType.REMOTE)
            )
        )
        assert result["branches"] == []


class TestGitCreateBranch:
    """req 56c8f711."""

    async def test_creates_branch(self, repo):
        result = json.loads(
            await git_create_branch(
                GitCreateBranchInput(repo_path=str(repo), branch_name="feature")
            )
        )
        assert result == {"created": "feature"}

    async def test_duplicate_returns_structured_error(self, repo):
        git.Repo(repo).create_head("feature")
        result = await git_create_branch(
            GitCreateBranchInput(repo_path=str(repo), branch_name="feature")
        )
        assert result == "Error: branch already exists: feature"


class TestGitCommit:
    """req 74ef324d."""

    async def test_commits_staged_changes(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])

        result = json.loads(
            await git_commit(GitCommitInput(repo_path=str(repo), message="update"))
        )
        assert result["hash"] == git.Repo(repo).head.commit.hexsha

    async def test_nothing_staged_returns_structured_error(self, repo):
        result = await git_commit(
            GitCommitInput(repo_path=str(repo), message="empty")
        )
        assert result.startswith("Error: nothing staged to commit")


class TestGitAdd:
    """req 3337bf9f."""

    async def test_stages_files(self, repo):
        (repo / "new.txt").write_text("new\n")
        result = json.loads(
            await git_add(GitAddInput(repo_path=str(repo), files=["new.txt"]))
        )
        assert result == {"staged": ["new.txt"]}

    async def test_missing_path_returns_structured_error(self, repo):
        result = await git_add(
            GitAddInput(repo_path=str(repo), files=["absent.txt"])
        )
        assert result.startswith("Error: path does not exist in the working tree")

    async def test_traversal_path_returns_structured_error(self, repo, other_repo):
        result = await git_add(
            GitAddInput(repo_path=str(repo), files=["../other_repo/other.txt"])
        )
        assert result.startswith("Error: path resolves outside repo_path")


class TestGitReset:
    """req 68fbcc16."""

    async def test_unstages_changes(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])

        result = json.loads(await git_reset(GitResetInput(repo_path=str(repo))))
        assert result == {"unstaged_count": 1}

    async def test_leaves_other_repository_untouched(self, repo, other_repo):
        (other_repo / "other.txt").write_text("staged elsewhere\n")
        git.Repo(other_repo).index.add(["other.txt"])
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])

        await git_reset(GitResetInput(repo_path=str(repo)))
        other_status = json.loads(
            await git_status(GitStatusInput(repo_path=str(other_repo)))
        )
        assert other_status["staged"] == ["other.txt"]


class TestGitInit:
    """req 1c3f7c0f."""

    async def test_creates_repository(self, tmp_path):
        target = tmp_path / "fresh"
        result = json.loads(
            await git_init(GitInitInput(repo_path=str(target)))
        )
        assert result == {"repo_path": str(target.resolve())}
        assert (target / ".git").is_dir()

    async def test_existing_repository_returns_structured_error(self, repo):
        result = await git_init(GitInitInput(repo_path=str(repo)))
        assert result.startswith("Error: a git repository already exists at")


class TestErrorContract:
    """req 54f3d219 — no raw exception detail reaches the client."""

    async def test_unexpected_exception_is_generic(self, repo, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError("internal detail that must not leak")

        monkeypatch.setattr(server, "GitRepository", explode)
        result = await git_status(GitStatusInput(repo_path=str(repo)))
        assert result == GENERIC_ERROR
        assert "internal detail" not in result

    @pytest.mark.parametrize(
        "tool, params",
        [
            (git_status, GitStatusInput),
            (git_diff_unstaged, GitDiffUnstagedInput),
            (git_diff_staged, GitDiffStagedInput),
            (git_reset, GitResetInput),
        ],
    )
    async def test_missing_repository_never_leaks_a_traceback(
        self, tmp_path, tool, params
    ):
        result = await tool(params(repo_path=str(tmp_path / "absent")))
        assert result.startswith("Error: ")
        assert "Traceback" not in result
