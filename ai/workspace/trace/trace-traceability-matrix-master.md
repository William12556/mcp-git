Created: 2026 August 13

# Traceability Matrix (Master)

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Matrix](<#2.0 matrix>)
[Version History](<#version history>)

---

## 1.0 Purpose

Tracks requirement-to-design-to-implementation-to-test traceability across the mcp-git project, updated at every phase transition per governance.md P05.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Matrix

### 2.1 Functional Requirements

| Requirement | Description | Design | Implementation | Test | Status |
|---|---|---|---|---|---|
| fedee316 | git_status | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 08da738e | git_diff_unstaged | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 7e8bfefa | git_diff_staged | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 2f0a1f17 | git_diff | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| aa27e381 | git_log | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 8a1fefa4 | git_show | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 0931a0d8 | git_branch | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 56c8f711 | git_create_branch | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 74ef324d | git_commit | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 3337bf9f | git_add | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 68fbcc16 | git_reset | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 1c3f7c0f | git_init | b814443d, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |

### 2.2 Non-Functional Requirements

| Requirement | Description | Design | Implementation | Test | Status |
|---|---|---|---|---|---|
| 24a9ea35 | Repository path confinement (security) | mcp-git-master, f476c153, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 6468a270 | Destructive-tool isolation (reliability) | mcp-git-master, 5b9d57cb | prompt-8aec2f46 (pending) | — | prompted |
| 54f3d219 | Structured error responses (usability) | mcp-git-master, b814443d | prompt-8aec2f46 (pending) | — | prompted |
| 9a52683b | PEP 8 + pytest coverage (maintainability) | mcp-git-master | prompt-8aec2f46 (pending) | — | prompted |

### 2.3 Architectural Requirements

| Requirement | Description | Design | Implementation | Test | Status |
|---|---|---|---|---|---|
| b3c783db | Python / pyproject.toml packaging | mcp-git-master | prompt-8aec2f46 (pending) | — | prompted |
| e67ba5a1 | stdio transport only | mcp-git-master | prompt-8aec2f46 (pending) | — | prompted |
| fab9139d | Read-only vs. destructive tool annotation | mcp-git-master, b814443d | prompt-8aec2f46 (pending) | — | prompted |
| 30130de3 | No network dependency | mcp-git-master | prompt-8aec2f46 (pending) | — | prompted |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-13 | Initial skeleton (P01 project initialisation) |
| 0.2 | 2026-08-13 | Initialised with 20 requirements from requirements-mcp-git-master.md (P10 baseline) |
| 0.3 | 2026-08-13 | Design column populated (Tier 1-3 approved); Implementation column links prompt-8aec2f46 (pending execution); status baselined -> prompted |

---

Copyright (c) 2026 William Watson. MIT License.
