Created: 2026 August 13

# mcp-git

---

## Table of Contents

[1.0 Overview](<#1.0 overview>)
[2.0 Installation](<#2.0 installation>)
[2.1 Development install](<#2.1 development install>)
[2.2 De-installation](<#2.2 de-installation>)
[3.0 Configuration](<#3.0 configuration>)
[3.1 Claude Desktop](<#3.1 claude desktop>)
[3.2 Claude Code](<#3.2 claude code>)
[4.0 Tools](<#4.0 tools>)
[Version History](<#version history>)

---

## 1.0 Overview

A local git MCP server. It exposes 12 git operations to an MCP client (e.g. Claude Desktop or Claude Code) over stdio, so the client can inspect and work with a git repository on your machine — status, diffs, log, branches, staging, and commits.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Installation

Requires Python 3.9+. Installs the latest release into its own virtual environment at `~/.local/share/mcp-git/venv` — no clone required:

```bash
curl -fsSL https://raw.githubusercontent.com/William12556/mcp-git/main/bin/install.sh | bash
```

The script prints the full path to the installed `mcp-git` command when it finishes — use that path in your MCP client configuration (§3.0).

To confirm it installed correctly:

```bash
~/.local/share/mcp-git/venv/bin/python -c "import mcp_git; print(mcp_git.__version__)"
```

### 2.1 Development install

To work on mcp-git itself (run tests, use `bin/build.sh` / `bin/release.sh`), clone the repository instead:

```bash
git clone https://github.com/William12556/mcp-git.git
cd mcp-git
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

[Return to Table of Contents](<#table of contents>)

---

### 2.2 De-installation

Remove the install directory:

```bash
rm -rf ~/.local/share/mcp-git
```

If the `MCP_GIT_HOME` environment variable was set to a non-default location during installation, remove that directory instead. Then remove the `mcp-git` entry from your MCP client configuration (§3.0).

For a development install, remove the cloned repository directory in place of the above.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Configuration

Add mcp-git to your MCP client's configuration, pointing at the installed console script. Use the full path printed by the install script (or, for a development install, the venv you created). No startup arguments are needed — every tool call takes its own `repo_path`, so one server instance can work with any repository on your machine.

[Return to Table of Contents](<#table of contents>)

---

### 3.1 Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "git": {
      "command": "/Users/<you>/.local/share/mcp-git/venv/bin/mcp-git"
    }
  }
}
```

[Return to Table of Contents](<#table of contents>)

---

### 3.2 Claude Code

Register the server with the `claude mcp add` command:

```bash
claude mcp add --transport stdio git -- /Users/<you>/.local/share/mcp-git/venv/bin/mcp-git
```

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tools

| Tool | What it does |
|---|---|
| `git_status` | Show staged, unstaged, and untracked files |
| `git_diff_unstaged` | Diff of unstaged working-tree changes |
| `git_diff_staged` | Diff of staged (index) changes |
| `git_diff` | Diff against a branch, tag, or commit |
| `git_log` | Commit history |
| `git_show` | Details and diff of a specific commit |
| `git_branch` | List local, remote, or all branches |
| `git_create_branch` | Create a new branch |
| `git_commit` | Commit staged changes |
| `git_add` | Stage files |
| `git_reset` | Unstage all changes |
| `git_init` | Initialise a new repository |

Every tool operates only on the repository at the `repo_path` you give it — nothing outside that path is touched, and mcp-git makes no network calls.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-13 | Initial skeleton (P01 project initialisation) |
| 0.2 | 2026-08-13 | Added installation, configuration, and tool reference now that the server is implemented |
| 0.3 | 2026-08-13 | Replaced git-clone installation with the curl-piped bin/install.sh; clone retained only for §2.1 Development install |
| 0.4 | 2026-08-13 | Added §2.2 De-installation |
| 0.5 | 2026-08-13 | Split §3.0 Configuration into §3.1 Claude Desktop and §3.2 Claude Code |

---

Copyright (c) 2026 William Watson. MIT License.
