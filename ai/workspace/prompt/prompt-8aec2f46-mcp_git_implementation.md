Created: 2026 August 13

# prompt-8aec2f46-mcp_git_implementation

**T04 Prompt — initial implementation, combined (both Tier 3 components)**

---

## Table of Contents

[1.0 Prompt](<#1.0 prompt>)
[2.0 Handoff Command](<#2.0 handoff command>)
[3.0 Cross-References](<#3.0 cross-references>)
[Version History](<#version history>)

---

## 1.0 Prompt

```yaml
# T04 Prompt Template v1.11 - YAML Format

prompt_info:
  id: "prompt-8aec2f46"
  task_type: "code_generation"
  source_ref: "design-f476c153-domain_git_operations"
  target_profile: "claude_code"
  date: "2026-08-13"
  iteration: 1
  # coupled_docs omitted: source_ref is a design document, not a change document
  # (initial implementation exception, governance P03 §1.4.1)

context:
  purpose: "Implement the mcp-git MCP server: 12 git tools spanning the MCP Tool Handler Layer and Git Operations Layer, per the approved Tier 1-3 design."
  integration: "First-time source code for the mcp-git project. Populates src/mcp_git/ (currently a README stub only) per the existing pyproject.toml skeleton. This is a single combined prompt covering both Tier 3 components: design-5b9d57cb-component_git_operations_repository.md (Git Operations Layer) and design-b814443d-component_git_operations_handler.md (MCP Tool Handler Layer). Read both in full before implementing — they contain complete function/method signatures not repeated exhaustively below."
  knowledge_references: []
  constraints:
    - "stdio transport only (req e67ba5a1) — no HTTP/SSE transport"
    - "No outbound network calls (req 30130de3)"
    - "Every operation confined to the repo_path supplied on that call (req 24a9ea35)"
    - "Destructive tools (add, commit, reset, create_branch, init) must not mutate any repository other than the one at the supplied repo_path (req 6468a270)"
    - "PEP 8 (req 9a52683b)"
    - "GitPython is the only git-interaction library — no shelling out to the git binary"

specification:
  description: "Implement three modules per the Tier 3 designs: mcp_git/errors.py (exception hierarchy), mcp_git/operations.py (GitRepository class, init_repository function, BranchType enum), and mcp_git/server.py (FastMCP tool registrations for all 12 tools, 12 Pydantic input models). Also add the required runtime dependencies to pyproject.toml, which currently declares none."
  requirements:
    functional:
      - "req fedee316: git_status"
      - "req 08da738e: git_diff_unstaged"
      - "req 7e8bfefa: git_diff_staged"
      - "req 2f0a1f17: git_diff"
      - "req aa27e381: git_log"
      - "req 8a1fefa4: git_show"
      - "req 0931a0d8: git_branch"
      - "req 56c8f711: git_create_branch"
      - "req 74ef324d: git_commit"
      - "req 3337bf9f: git_add"
      - "req 68fbcc16: git_reset"
      - "req 1c3f7c0f: git_init"
      - "Full acceptance criteria for each requirement are in requirements-mcp-git-master.md"
    technical:
      language: "Python"
      version: ">=3.9"
      standards:
        - "PEP 8"
        - "Comprehensive error handling — no bare exceptions reach the MCP client (req 54f3d219)"
        - "Professional docstrings per the mcp-builder Python guide (full Args/Returns/Raises/Examples structure)"
  performance:
    - target: "tool call latency, excluding underlying git operation cost"
      metric: "< 500ms"

design:
  architecture: "Layered: MCP Tool Handler Layer (server.py) -> Git Operations Layer (operations.py) -> GitPython -> local .git repository. Full detail in design-mcp-git-master.md §1.0 architecture."
  components:
    - name: "errors.py exception hierarchy"
      type: "module"
      purpose: "McpGitError base plus 7 subclasses, per design-5b9d57cb-component_git_operations_repository.md §1.0 error_handling.exception_hierarchy."
      interface:
        inputs: []
        outputs:
          type: "n/a"
          description: "Exception classes only"
        raises:
          - "McpGitError(Exception)"
          - "RepositoryNotFoundError(McpGitError)"
          - "RepositoryAlreadyExistsError(McpGitError)"
          - "InvalidRefError(McpGitError)"
          - "NothingStagedError(McpGitError)"
          - "PathConfinementError(McpGitError)"
          - "BranchAlreadyExistsError(McpGitError)"
          - "PathNotFoundError(McpGitError)"
      logic:
        - "Plain exception classes; no custom __init__ required beyond accepting a message"

    - name: "GitRepository"
      type: "class"
      purpose: "Confined handle to an existing git repository; 11 methods, one per read/write tool other than git_init. Full signatures in design-5b9d57cb-component_git_operations_repository.md §1.0 interfaces.internal."
      interface:
        inputs:
          - name: "repo_path"
            type: "str"
            description: "Constructor argument; establishes the confinement boundary"
        outputs:
          type: "GitRepository"
          description: "Confined repository handle"
        raises:
          - "RepositoryNotFoundError, PathConfinementError (constructor)"
      logic:
        - "__init__ resolves and confines repo_path via GitPython"
        - "status, diff_unstaged, diff_staged, diff, log, show, branch: read-only, no confinement re-check needed beyond constructor"
        - "create_branch, commit, add, reset: check preconditions before any mutating GitPython call (req 6468a270)"

    - name: "init_repository"
      type: "function"
      purpose: "Standalone function (not a GitRepository method) implementing git_init, since no repository exists yet at call time. See design-5b9d57cb-component_git_operations_repository.md §1.0 interfaces.internal."
      interface:
        inputs:
          - name: "repo_path"
            type: "str"
            description: "Path at which to create the repository"
        outputs:
          type: "str"
          description: "repo_path, confirming creation"
        raises:
          - "RepositoryAlreadyExistsError"
      logic:
        - "Validate no .git directory already exists at repo_path, then call GitPython Repo.init"

    - name: "BranchType"
      type: "class"
      purpose: "str Enum (local, remote, all) for git_branch scope selection."
      interface:
        inputs: []
        outputs:
          type: "n/a"
          description: "Enum values LOCAL, REMOTE, ALL"
        raises: []
      logic: []

    - name: "12 tool functions + 12 Pydantic input models"
      type: "module"
      purpose: "server.py — one async tool function and one input model per tool (git_status, git_diff_unstaged, git_diff_staged, git_diff, git_log, git_show, git_branch, git_create_branch, git_commit, git_add, git_reset, git_init). Complete signatures, per-tool docstring requirements, and the full annotation table (readOnlyHint/destructiveHint/idempotentHint/openWorldHint) are in design-b814443d-component_git_operations_handler.md §1.0 interfaces.internal and §2.0."
      interface:
        inputs:
          - name: "params"
            type: "<ToolName>Input (Pydantic BaseModel)"
            description: "One model per tool; every model includes repo_path: str"
        outputs:
          type: "str"
          description: "JSON-formatted success result, or 'Error: {message}' on failure"
        raises: []
      logic:
        - "Construct GitRepository(params.repo_path), except git_init which calls init_repository(params.repo_path) directly"
        - "Invoke the corresponding Git Operations Layer method/function"
        - "Catch McpGitError subclasses -> return 'Error: {message}'"
        - "Catch any other exception -> log server-side, return a generic 'Error: an unexpected error occurred' (never leak a raw traceback, req 54f3d219)"
        - "Register each tool via @mcp.tool(name=..., annotations={...}) per design-b814443d-... §2.0"
  dependencies:
    internal: []
    external:
      - "mcp (MCP Python SDK / FastMCP)"
      - "GitPython"
      - "pydantic"

error_handling:
  strategy: "Confinement and precondition checks run before any GitPython call in operations.py, raising the specific McpGitError subclass. server.py catches McpGitError and formats a structured 'Error: ...' string; unexpected exceptions are logged and translated to a generic structured error, never a raw traceback."
  exceptions:
    - exception: "RepositoryNotFoundError"
      condition: "repo_path does not resolve to an existing git repository (all tools except git_init)"
      handling: "raised by GitRepository.__init__; caught and formatted by the handler"
    - exception: "RepositoryAlreadyExistsError"
      condition: "repo_path already contains a .git directory (git_init)"
      handling: "raised by init_repository; caught and formatted by the handler"
    - exception: "InvalidRefError"
      condition: "target/ref does not resolve (git_diff, git_show)"
      handling: "raised by GitRepository.diff/show; caught and formatted by the handler"
    - exception: "NothingStagedError"
      condition: "index is empty (git_commit)"
      handling: "raised by GitRepository.commit; caught and formatted by the handler"
    - exception: "PathConfinementError"
      condition: "repo_path fails confinement validation"
      handling: "raised before any GitPython call; caught and formatted by the handler"
    - exception: "BranchAlreadyExistsError"
      condition: "branch_name already exists (git_create_branch)"
      handling: "raised by GitRepository.create_branch; caught and formatted by the handler"
    - exception: "PathNotFoundError"
      condition: "a specified file path does not exist in the working tree (git_add)"
      handling: "raised by GitRepository.add; caught and formatted by the handler"
  logging:
    level: "INFO / ERROR"
    format: "flat file, per project logging convention (see design-mcp-git-master.md §1.0 error_handling.logging)"

testing:
  unit_tests: []
  edge_cases: []
  validation: []
  # Test-writing is delegated to this Claude Code execution rather than
  # specified in advance: implement one or more pytest tests per tool
  # (12 minimum, per req 9a52683b), using isolated fixture repositories.
  # T05 test documentation is authored by the Strategic Domain after this
  # implementation completes (governance P06), not before.

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
    - "Add mcp, GitPython, and pydantic to pyproject.toml [project.dependencies] (currently empty)"
  files:
    - path: "src/mcp_git/errors.py"
      content: ""
    - path: "src/mcp_git/operations.py"
      content: ""
    - path: "src/mcp_git/server.py"
      content: ""
    - path: "pyproject.toml"
      content: ""
  documentation: []

success_criteria:
  - "All 12 tools implemented and registered, matching the signatures in design-b814443d-... and design-5b9d57cb-..."
  - "All 9 exception classes present in errors.py (McpGitError base + 8 subclasses, including the 2 added at Tier 3)"
  - "No tool resolves or writes outside the repo_path supplied on that call"
  - "No tool makes an outbound network call"
  - "Server runs over stdio (no HTTP/SSE transport)"
  - "pyproject.toml dependencies updated; pip install -e .[dev] succeeds"
  - "pytest suite exists with at least one test per tool and passes"
  - "PEP 8 compliant"

element_registry:
  source: "ai/workspace/design/design-mcp-git-name_registry-master.md"
  entries:
    modules:
      - name: "mcp_git.server"
        path: "src/mcp_git/server.py"
      - name: "mcp_git.operations"
        path: "src/mcp_git/operations.py"
      - name: "mcp_git.errors"
        path: "src/mcp_git/errors.py"
    classes:
      - name: "GitRepository"
        module: "mcp_git.operations"
      - name: "BranchType"
        module: "mcp_git.operations"
      - name: "McpGitError"
        module: "mcp_git.errors"
      - name: "RepositoryNotFoundError"
        module: "mcp_git.errors"
      - name: "RepositoryAlreadyExistsError"
        module: "mcp_git.errors"
      - name: "InvalidRefError"
        module: "mcp_git.errors"
      - name: "NothingStagedError"
        module: "mcp_git.errors"
      - name: "PathConfinementError"
        module: "mcp_git.errors"
      - name: "BranchAlreadyExistsError"
        module: "mcp_git.errors"
      - name: "PathNotFoundError"
        module: "mcp_git.errors"
      - name: "GitStatusInput"
        module: "mcp_git.server"
      - name: "GitDiffUnstagedInput"
        module: "mcp_git.server"
      - name: "GitDiffStagedInput"
        module: "mcp_git.server"
      - name: "GitDiffInput"
        module: "mcp_git.server"
      - name: "GitLogInput"
        module: "mcp_git.server"
      - name: "GitShowInput"
        module: "mcp_git.server"
      - name: "GitBranchInput"
        module: "mcp_git.server"
      - name: "GitCreateBranchInput"
        module: "mcp_git.server"
      - name: "GitCommitInput"
        module: "mcp_git.server"
      - name: "GitAddInput"
        module: "mcp_git.server"
      - name: "GitResetInput"
        module: "mcp_git.server"
      - name: "GitInitInput"
        module: "mcp_git.server"
    functions:
      - name: "GitRepository.__init__"
        module: "mcp_git.operations"
        signature: "def __init__(self, repo_path: str) -> None"
      - name: "GitRepository.status"
        module: "mcp_git.operations"
        signature: "def status(self) -> dict"
      - name: "GitRepository.diff_unstaged"
        module: "mcp_git.operations"
        signature: "def diff_unstaged(self) -> str"
      - name: "GitRepository.diff_staged"
        module: "mcp_git.operations"
        signature: "def diff_staged(self) -> str"
      - name: "GitRepository.diff"
        module: "mcp_git.operations"
        signature: "def diff(self, target: str) -> str"
      - name: "GitRepository.log"
        module: "mcp_git.operations"
        signature: "def log(self, max_count: int = DEFAULT_LOG_MAX_COUNT) -> list[dict]"
      - name: "GitRepository.show"
        module: "mcp_git.operations"
        signature: "def show(self, ref: str) -> dict"
      - name: "GitRepository.branch"
        module: "mcp_git.operations"
        signature: "def branch(self, branch_type: BranchType = BranchType.LOCAL) -> dict"
      - name: "GitRepository.create_branch"
        module: "mcp_git.operations"
        signature: "def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> str"
      - name: "GitRepository.commit"
        module: "mcp_git.operations"
        signature: "def commit(self, message: str) -> str"
      - name: "GitRepository.add"
        module: "mcp_git.operations"
        signature: "def add(self, files: List[str]) -> dict"
      - name: "GitRepository.reset"
        module: "mcp_git.operations"
        signature: "def reset(self) -> dict"
      - name: "init_repository"
        module: "mcp_git.operations"
        signature: "def init_repository(repo_path: str) -> str"
      - name: "git_status"
        module: "mcp_git.server"
        signature: "async def git_status(params: GitStatusInput) -> str"
      - name: "git_diff_unstaged"
        module: "mcp_git.server"
        signature: "async def git_diff_unstaged(params: GitDiffUnstagedInput) -> str"
      - name: "git_diff_staged"
        module: "mcp_git.server"
        signature: "async def git_diff_staged(params: GitDiffStagedInput) -> str"
      - name: "git_diff"
        module: "mcp_git.server"
        signature: "async def git_diff(params: GitDiffInput) -> str"
      - name: "git_log"
        module: "mcp_git.server"
        signature: "async def git_log(params: GitLogInput) -> str"
      - name: "git_show"
        module: "mcp_git.server"
        signature: "async def git_show(params: GitShowInput) -> str"
      - name: "git_branch"
        module: "mcp_git.server"
        signature: "async def git_branch(params: GitBranchInput) -> str"
      - name: "git_create_branch"
        module: "mcp_git.server"
        signature: "async def git_create_branch(params: GitCreateBranchInput) -> str"
      - name: "git_commit"
        module: "mcp_git.server"
        signature: "async def git_commit(params: GitCommitInput) -> str"
      - name: "git_add"
        module: "mcp_git.server"
        signature: "async def git_add(params: GitAddInput) -> str"
      - name: "git_reset"
        module: "mcp_git.server"
        signature: "async def git_reset(params: GitResetInput) -> str"
      - name: "git_init"
        module: "mcp_git.server"
        signature: "async def git_init(params: GitInitInput) -> str"
    constants:
      - name: "DEFAULT_LOG_MAX_COUNT"
        module: "mcp_git.operations"
        type: "int"

# tactical_brief omitted: not required for target_profile == claude_code

notes: "Read design-5b9d57cb-component_git_operations_repository.md and design-b814443d-component_git_operations_handler.md in full before implementing — they contain the complete per-method/per-tool docstring, parameter, and raises detail this prompt summarises. Tool annotation values (readOnlyHint/destructiveHint/idempotentHint/openWorldHint per tool) are in design-b814443d-... §2.0. On completion: close this prompt T-Doc (move to ai/workspace/prompt/closed/); leave requirements/design T-Docs active; write a completion report to ai/workspace/report/report-8aec2f46-mcp_git_implementation.md per ai/profiles/claude-code.md §5.0."
```

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Handoff Command

Per `ai/profiles/claude-code.md` §5.0, once this prompt is approved, open Claude Code in the project root and issue:

```
implement ai/workspace/prompt/prompt-8aec2f46-mcp_git_implementation.md and close the prompt T-Doc when finished. Leave the issue and change T-Docs active pending test results. Then, once you are finished, write a report of what you have done in ai/workspace/report-8aec2f46-mcp_git_implementation.md.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Cross-References

- **Source (Tier 2 domain):** [design-f476c153-domain_git_operations.md](../design/design-f476c153-domain_git_operations.md)
- **Source (Tier 3, Git Operations Layer):** [design-5b9d57cb-component_git_operations_repository.md](../design/design-5b9d57cb-component_git_operations_repository.md)
- **Source (Tier 3, MCP Tool Handler Layer):** [design-b814443d-component_git_operations_handler.md](../design/design-b814443d-component_git_operations_handler.md)
- **Name registry:** [design-mcp-git-name_registry-master.md](../design/design-mcp-git-name_registry-master.md)
- **Requirements:** [requirements-mcp-git-master.md](../requirements/requirements-mcp-git-master.md)

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-13 | Initial combined T04 prompt covering both Tier 3 components, pending human review |

---

Copyright (c) 2026 William Watson. MIT License.
