"""Tests for the Git Operations Layer (``mcp_git.operations``)."""

import git
import pytest

from mcp_git.errors import (
    BranchAlreadyExistsError,
    InvalidRefError,
    NothingStagedError,
    PathConfinementError,
    PathNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryNotFoundError,
)
from mcp_git.operations import (
    DEFAULT_LOG_MAX_COUNT,
    BranchType,
    GitRepository,
    init_repository,
)


class TestConstruction:
    """GitRepository construction and confinement (req 24a9ea35)."""

    def test_opens_existing_repository(self, repo):
        assert GitRepository(str(repo)).repo_path == str(repo.resolve())

    def test_missing_path_raises_repository_not_found(self, tmp_path):
        with pytest.raises(RepositoryNotFoundError):
            GitRepository(str(tmp_path / "nowhere"))

    def test_non_repository_directory_raises_repository_not_found(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        with pytest.raises(RepositoryNotFoundError):
            GitRepository(str(plain))

    def test_subdirectory_does_not_widen_to_parent_repository(self, repo):
        nested = repo / "nested"
        nested.mkdir()
        with pytest.raises(RepositoryNotFoundError):
            GitRepository(str(nested))

    def test_bare_repository_has_no_confinement_boundary(self, tmp_path):
        bare = tmp_path / "bare.git"
        git.Repo.init(bare, bare=True)
        with pytest.raises(PathConfinementError):
            GitRepository(str(bare))


class TestStatus:
    """req fedee316 — git_status."""

    def test_clean_tree(self, repo):
        status = GitRepository(str(repo)).status()
        assert status == {
            "staged": [],
            "unstaged": [],
            "untracked": [],
            "clean": True,
        }

    def test_reports_staged_unstaged_and_untracked(self, repo):
        (repo / "tracked.txt").write_text("modified\n")
        (repo / "untracked.txt").write_text("new\n")
        (repo / "staged.txt").write_text("staged\n")
        git.Repo(repo).index.add(["staged.txt"])

        status = GitRepository(str(repo)).status()
        assert status["staged"] == ["staged.txt"]
        assert status["unstaged"] == ["tracked.txt"]
        assert status["untracked"] == ["untracked.txt"]
        assert status["clean"] is False

    def test_status_on_repository_without_commits(self, empty_repo):
        (empty_repo / "new.txt").write_text("new\n")
        git.Repo(empty_repo).index.add(["new.txt"])
        assert GitRepository(str(empty_repo)).status()["staged"] == ["new.txt"]


class TestDiffUnstaged:
    """req 08da738e — git_diff_unstaged."""

    def test_empty_when_no_changes(self, repo):
        assert GitRepository(str(repo)).diff_unstaged() == ""

    def test_reports_working_tree_edits(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        diff = GitRepository(str(repo)).diff_unstaged()
        assert "tracked.txt" in diff
        assert "+changed" in diff


class TestDiffStaged:
    """req 7e8bfefa — git_diff_staged."""

    def test_empty_when_index_matches_head(self, repo):
        assert GitRepository(str(repo)).diff_staged() == ""

    def test_reports_index_changes(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])
        assert "+changed" in GitRepository(str(repo)).diff_staged()


class TestDiff:
    """req 2f0a1f17 — git_diff."""

    def test_diff_against_branch(self, repo):
        handle = git.Repo(repo)
        base = handle.active_branch.name
        handle.create_head("feature")
        handle.heads.feature.checkout()
        (repo / "tracked.txt").write_text("on feature\n")
        handle.index.add(["tracked.txt"])
        handle.index.commit("feature change")

        assert "+on feature" in GitRepository(str(repo)).diff(base)

    def test_invalid_ref_raises(self, repo):
        with pytest.raises(InvalidRefError):
            GitRepository(str(repo)).diff("no-such-ref")


class TestLog:
    """req aa27e381 — git_log."""

    def test_entries_carry_required_fields(self, repo):
        entries = GitRepository(str(repo)).log()
        assert len(entries) == 1
        assert set(entries[0]) == {"hash", "author", "date", "message"}
        assert entries[0]["message"] == "initial commit"

    def test_max_count_limits_entries(self, repo):
        handle = git.Repo(repo)
        for index in range(3):
            (repo / f"file{index}.txt").write_text("x\n")
            handle.index.add([f"file{index}.txt"])
            handle.index.commit(f"commit {index}")

        assert len(GitRepository(str(repo)).log(max_count=2)) == 2

    def test_default_max_count(self, repo):
        assert DEFAULT_LOG_MAX_COUNT == 10

    def test_empty_repository_has_no_history(self, empty_repo):
        assert GitRepository(str(empty_repo)).log() == []


class TestShow:
    """req 8a1fefa4 — git_show."""

    def test_returns_metadata_and_diff(self, repo):
        result = GitRepository(str(repo)).show("HEAD")
        assert set(result) == {"hash", "author", "date", "message", "diff"}
        assert result["message"] == "initial commit"
        assert "tracked.txt" in result["diff"]

    def test_invalid_ref_raises(self, repo):
        with pytest.raises(InvalidRefError):
            GitRepository(str(repo)).show("deadbeef")


class TestBranch:
    """req 0931a0d8 — git_branch."""

    def test_lists_local_branches_and_marks_current(self, repo):
        git.Repo(repo).create_head("feature")
        result = GitRepository(str(repo)).branch()
        assert "feature" in result["branches"]
        assert result["current"] == git.Repo(repo).active_branch.name

    def test_remote_scope_is_empty_without_remotes(self, repo):
        assert GitRepository(str(repo)).branch(BranchType.REMOTE)["branches"] == []

    def test_all_scope_includes_local(self, repo):
        result = GitRepository(str(repo)).branch(BranchType.ALL)
        assert git.Repo(repo).active_branch.name in result["branches"]


class TestCreateBranch:
    """req 56c8f711 — git_create_branch."""

    def test_creates_from_head_by_default(self, repo):
        assert GitRepository(str(repo)).create_branch("feature") == "feature"
        assert "feature" in [head.name for head in git.Repo(repo).heads]

    def test_creates_from_explicit_base(self, repo):
        handle = git.Repo(repo)
        base = handle.active_branch.name
        GitRepository(str(repo)).create_branch("from-base", base)
        assert handle.heads["from-base"].commit == handle.commit(base)

    def test_duplicate_name_raises(self, repo):
        GitRepository(str(repo)).create_branch("feature")
        with pytest.raises(BranchAlreadyExistsError):
            GitRepository(str(repo)).create_branch("feature")

    def test_invalid_base_raises_and_creates_nothing(self, repo):
        with pytest.raises(InvalidRefError):
            GitRepository(str(repo)).create_branch("feature", "no-such-base")
        assert "feature" not in [head.name for head in git.Repo(repo).heads]


class TestCommit:
    """req 74ef324d — git_commit."""

    def test_commits_staged_changes(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])

        commit_hash = GitRepository(str(repo)).commit("update tracked")
        assert git.Repo(repo).head.commit.hexsha == commit_hash
        assert git.Repo(repo).head.commit.message.strip() == "update tracked"

    def test_empty_index_raises(self, repo):
        before = git.Repo(repo).head.commit.hexsha
        with pytest.raises(NothingStagedError):
            GitRepository(str(repo)).commit("nothing here")
        assert git.Repo(repo).head.commit.hexsha == before

    def test_does_not_touch_other_repository(self, repo, other_repo):
        other_head = git.Repo(other_repo).head.commit.hexsha
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])
        GitRepository(str(repo)).commit("confined commit")
        assert git.Repo(other_repo).head.commit.hexsha == other_head


class TestAdd:
    """req 3337bf9f — git_add."""

    def test_stages_listed_files(self, repo):
        (repo / "new.txt").write_text("new\n")
        assert GitRepository(str(repo)).add(["new.txt"]) == {"staged": ["new.txt"]}
        assert "new.txt" in [path for path, _ in git.Repo(repo).index.entries]

    def test_missing_path_raises_and_stages_nothing(self, repo):
        (repo / "new.txt").write_text("new\n")
        with pytest.raises(PathNotFoundError):
            GitRepository(str(repo)).add(["new.txt", "absent.txt"])
        assert GitRepository(str(repo)).status()["staged"] == []

    def test_traversal_path_is_rejected(self, repo, other_repo):
        with pytest.raises(PathConfinementError):
            GitRepository(str(repo)).add(["../other_repo/other.txt"])


class TestReset:
    """req 68fbcc16 — git_reset."""

    def test_unstages_and_reports_count(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])

        assert GitRepository(str(repo)).reset() == {"unstaged_count": 1}
        assert GitRepository(str(repo)).status()["staged"] == []

    def test_leaves_working_tree_untouched(self, repo):
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])
        GitRepository(str(repo)).reset()
        assert (repo / "tracked.txt").read_text() == "changed\n"

    def test_does_not_touch_other_repository(self, repo, other_repo):
        (other_repo / "other.txt").write_text("staged elsewhere\n")
        git.Repo(other_repo).index.add(["other.txt"])
        (repo / "tracked.txt").write_text("changed\n")
        git.Repo(repo).index.add(["tracked.txt"])

        GitRepository(str(repo)).reset()
        assert GitRepository(str(other_repo)).status()["staged"] == ["other.txt"]


class TestInitRepository:
    """req 1c3f7c0f — git_init."""

    def test_creates_repository(self, tmp_path):
        target = tmp_path / "fresh"
        assert init_repository(str(target)) == str(target.resolve())
        assert (target / ".git").is_dir()

    def test_existing_repository_raises(self, repo):
        with pytest.raises(RepositoryAlreadyExistsError):
            init_repository(str(repo))
