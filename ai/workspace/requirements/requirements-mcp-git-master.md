Created: 2026 August 13

# requirements-mcp-git-master

---

## Table of Contents

[1.0 Requirements](<#1.0 requirements>)
[Version History](<#version history>)

---

## 1.0 Requirements

```yaml
# T07 Requirements Template v1.0 - YAML Format

project_info:
  name: "mcp-git"
  version: "0.1"
  date: "2026-08-13"
  author: "William Watson"
  status: "active"

naming_conventions:
  package_name: "mcp_git"
  module_style: "snake_case"
  class_style: "PascalCase"
  function_style: "snake_case"
  constant_style: "UPPER_SNAKE_CASE"
  notes: "PEP 8. Import package name uses underscore convention; distribution name in pyproject.toml remains mcp-git."

functional_requirements:
  - id: "fedee316"
    type: "functional"
    description: "git_status: report working tree status (staged, unstaged, untracked files)."
    acceptance_criteria:
      - "Returns a structured listing of staged, unstaged, and untracked files for the repository at repo_path."
      - "Returns an explicit clean-tree result when no changes are present."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Baseline read-only tool; required for status inspection before other operations."
    dependencies: []

  - id: "08da738e"
    type: "functional"
    description: "git_diff_unstaged: return diff of unstaged changes in the working tree."
    acceptance_criteria:
      - "Returns unified diff text for all tracked files with unstaged modifications."
      - "Returns an empty result when no unstaged changes exist."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Read-only inspection of working-tree changes not yet staged."
    dependencies: []

  - id: "7e8bfefa"
    type: "functional"
    description: "git_diff_staged: return diff of staged (index) changes."
    acceptance_criteria:
      - "Returns unified diff text for all files staged in the index."
      - "Returns an empty result when the index matches HEAD."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Read-only inspection of changes staged for the next commit."
    dependencies: []

  - id: "2f0a1f17"
    type: "functional"
    description: "git_diff: return diff of the working tree against an arbitrary branch or commit target."
    acceptance_criteria:
      - "Accepts a target (branch name, tag, or commit hash) parameter."
      - "Returns unified diff text between the working tree and the specified target."
      - "Returns a clear error when the target does not resolve to a valid ref."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Read-only comparison beyond the staged/unstaged pair."
    dependencies: []

  - id: "aa27e381"
    type: "functional"
    description: "git_log: return commit history."
    acceptance_criteria:
      - "Accepts an optional max_count parameter limiting the number of entries returned."
      - "Each entry includes commit hash, author, date, and message."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Read-only history inspection."
    dependencies: []

  - id: "8a1fefa4"
    type: "functional"
    description: "git_show: return contents and diff of a specific commit."
    acceptance_criteria:
      - "Accepts a commit hash or ref parameter."
      - "Returns commit metadata and the associated diff."
      - "Returns a clear error when the ref does not resolve."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Read-only inspection of a single commit."
    dependencies: []

  - id: "0931a0d8"
    type: "functional"
    description: "git_branch: list branches (local, remote, or all)."
    acceptance_criteria:
      - "Accepts a branch_type parameter (local, remote, all)."
      - "Returns the current branch clearly marked in the listing."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Read-only branch enumeration."
    dependencies: []

  - id: "56c8f711"
    type: "functional"
    description: "git_create_branch: create a new branch from a base ref."
    acceptance_criteria:
      - "Accepts branch_name and an optional base_branch (defaults to current HEAD)."
      - "Fails with a clear error if branch_name already exists."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Mutating tool required for full reference parity."
    dependencies:
      - "0931a0d8"

  - id: "74ef324d"
    type: "functional"
    description: "git_commit: create a commit from currently staged changes."
    acceptance_criteria:
      - "Accepts a required commit message parameter."
      - "Fails with a clear error when the index is empty (nothing staged)."
      - "Returns the resulting commit hash on success."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Mutating tool required for full reference parity."
    dependencies:
      - "3337bf9f"

  - id: "3337bf9f"
    type: "functional"
    description: "git_add: stage specified files."
    acceptance_criteria:
      - "Accepts a list of file paths relative to repo_path."
      - "Fails with a clear error if a specified path does not exist in the working tree."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Mutating tool required for full reference parity."
    dependencies: []

  - id: "68fbcc16"
    type: "functional"
    description: "git_reset: unstage all currently staged changes."
    acceptance_criteria:
      - "Reverts the index to match HEAD without altering the working tree."
      - "Returns confirmation of the number of files unstaged."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Mutating tool required for full reference parity."
    dependencies: []

  - id: "1c3f7c0f"
    type: "functional"
    description: "git_init: initialize a new git repository at a specified path."
    acceptance_criteria:
      - "Accepts a repo_path parameter."
      - "Fails with a clear error if a git repository already exists at that path."
    source: "reference implementation (modelcontextprotocol/servers/src/git)"
    rationale: "Mutating tool required for full reference parity."
    dependencies: []

non_functional_requirements:
  - id: "24a9ea35"
    type: "non_functional"
    category: "security"
    description: "Repository path confinement: every tool call operates only within the repo_path supplied for that call."
    acceptance_criteria:
      - "No tool resolves or writes outside the supplied repo_path."
      - "Path traversal inputs (e.g. ../) are rejected or normalised within bounds."
    target_metric: "n/a (boolean control)"
    source: "constraint"
    rationale: "Local server must not act on repositories other than the one specified by the caller."
    dependencies: []

  - id: "6468a270"
    type: "non_functional"
    category: "reliability"
    description: "Destructive tools (git_reset, git_commit, git_init) act only on the specified repository and produce no unintended side effects on unrelated repositories or files."
    acceptance_criteria:
      - "Each destructive tool is exercised in an isolated test repository fixture with no cross-repository effect observed."
    target_metric: "n/a (boolean control)"
    source: "constraint"
    rationale: "Prevents accidental data loss from mutating tools."
    dependencies: []

  - id: "54f3d219"
    type: "non_functional"
    category: "usability"
    description: "Errors are returned as structured, human-readable MCP tool error responses rather than raw exceptions or stack traces."
    acceptance_criteria:
      - "Every tool's error path returns a message describing the failure condition without a raw Python traceback."
    target_metric: "n/a (boolean control)"
    source: "constraint"
    rationale: "Improves diagnosability for the calling LLM and operator."
    dependencies: []

  - id: "9a52683b"
    type: "non_functional"
    category: "maintainability"
    description: "Code conforms to PEP 8 and each tool has pytest coverage."
    acceptance_criteria:
      - "One or more pytest test functions exist per tool."
      - "pytest suite passes under the project's configured test command."
    target_metric: "minimum one pytest test module per tool"
    source: "CLAUDE.md code style directive"
    rationale: "Aligns with existing project conventions (pyproject.toml pytest configuration)."
    dependencies: []

architectural_requirements:
  - id: "b3c783db"
    type: "architectural"
    description: "Server implemented in Python, packaged per the existing pyproject.toml (setuptools build backend)."
    acceptance_criteria:
      - "Installable via pip install -e .[dev] as already defined in pyproject.toml."
    constraints:
      - "Python >=3.9"
      - "MCP Python SDK"
    source: "scope decision, 2026-08-13"
    rationale: "Matches the existing project skeleton and CLAUDE.md technology stack."
    dependencies: []

  - id: "e67ba5a1"
    type: "architectural"
    description: "Server uses stdio transport exclusively for this initial scope."
    acceptance_criteria:
      - "Server is invoked as a local subprocess communicating over stdio; no HTTP/SSE transport is implemented."
    constraints: []
    source: "scope decision, 2026-08-13"
    rationale: "Matches local, single-user, single-machine target platform (CLAUDE.md)."
    dependencies: []

  - id: "fab9139d"
    type: "architectural"
    description: "Tool definitions annotate read-only tools separately from destructive/mutating tools."
    acceptance_criteria:
      - "git_status, git_diff_unstaged, git_diff_staged, git_diff, git_log, git_show, git_branch are annotated read-only."
      - "git_add, git_commit, git_reset, git_create_branch, git_init are annotated destructive/mutating."
    constraints:
      - "MCP tool annotation conventions (readOnlyHint / destructiveHint)"
    source: "scope decision, 2026-08-13"
    rationale: "Allows calling clients to distinguish safe inspection from state-changing operations."
    dependencies: []

  - id: "30130de3"
    type: "architectural"
    description: "No network dependency; the server operates exclusively on local filesystem git repositories."
    acceptance_criteria:
      - "No tool makes an outbound network call (e.g. no remote push/pull/fetch tools in this scope)."
    constraints: []
    source: "scope decision, 2026-08-13"
    rationale: "Consistent with local-server target platform; remote operations are out of scope."
    dependencies: []

traceability:
  design_refs: []
  test_refs: []
  code_refs: []

validation:
  completeness_check: "12 functional requirements provide full reference-server tool parity per confirmed scope decision (2026-08-13). 4 non-functional and 4 architectural requirements capture the remaining constraints identified during scoping."
  clarity_check: "Each requirement addresses a single tool or single constraint with unambiguous wording."
  testability_check: "Each requirement has at least one objective, pytest-verifiable acceptance criterion."
  conflicts_identified: []

version_history:
  - version: "0.1"
    date: "2026-08-13"
    author: "William Watson"
    changes:
      - "Initial requirements baseline: 12 functional (full tool parity), 4 non-functional, 4 architectural requirements"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t07_requirements"
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-13 | Initial requirements baseline (P10 Requirements) |

---

Copyright (c) 2026 William Watson. MIT License.
