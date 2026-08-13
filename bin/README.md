Created: 2026 August 13

# bin

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[Version History](<#version history>)

---

## 1.0 Purpose

Project-scoped integration and utility scripts.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Scripts

| Script | Purpose |
|---|---|
| `build.sh` | Bumps the version (pyproject.toml, src/mcp_git/__init__.py), cleans dist/build artefacts, builds a wheel + sdist via `python -m build`. |
| `release.sh` | Publishes a GitHub release (`gh release create`) with the wheel + sdist from `build.sh`. Runs the pytest suite and warns on uncommitted changes before publishing. |
| `install.sh` | End-user installer: `curl -fsSL .../bin/install.sh \| bash`. Resolves the latest GitHub release, installs it into a dedicated venv (`~/.local/share/mcp-git/venv` by default), no clone required. See root `README.md` §2.0. |

mcp-git is a local stdio MCP server with no Raspberry Pi, systemd, or remote-deploy target, so this directory intentionally does not carry service/boot-splash tooling of the kind found in Pi-targeted sibling projects.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-13 | Initial skeleton (P01 project initialisation) |
| 0.2 | 2026-08-13 | Added §2.0 Scripts: documents build.sh and release.sh |
| 0.3 | 2026-08-13 | Added install.sh to §2.0 Scripts |

---

Copyright (c) 2026 William Watson. MIT License.
