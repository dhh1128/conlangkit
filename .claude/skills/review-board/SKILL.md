---
name: review-board
description: >-
  Run conlangkit's multi-persona adversarial review panel over this repo. Spawns
  a vendored Workflow that fans out specialized reviewers — security,
  maintainability, testability, api-contract & consumer-stability, and
  computational-linguistics by default (devops, architect, and first-principles
  skeptic on request) — adversarially refutes high-stakes findings, dedupes by
  concept, and writes per-persona + synthesis reports to reviews/. Use when the
  user says "run the review board", "run a review panel on conlangkit", "review
  the code with the personas", or wants a broad multi-lens code review at a
  milestone. Read-only on source; writes only to reviews/ (uncommitted). Opt-in /
  explicit invocation only — it can spawn many subagents.
user-invocable: true
allowed-tools: Bash, Read, Workflow
---

# /review-board — conlangkit multi-persona adversarial review panel

Runs conlangkit's own vendored review panel: a deterministic `Workflow` that
spawns one specialized reviewer per persona, verifies the high-stakes findings,
dedupes across personas, and persists the reports to `reviews/`.

This is **conlangkit-specific tooling** — self-contained in this repo, with no
dependency on any external prompt clone. The persona prompts live in
[`prompts/review/`](../../../prompts/review/) and the workflow script in
[`.claude/workflows/review-panel.js`](../../workflows/review-panel.js). The panel
reads source **read-only** and writes its output to `reviews/` (uncommitted); it
never commits.

## When to run

At a milestone, before a release, or after a substantial change to the glossary
core, the `Lang`/CLI plumbing, the linguistic modules, or the CI/CD pipeline. It
is **opt-in**: only run it when the user explicitly asks (it can spawn many
subagents and is token-heavy).

## How to run

1. **Resolve the target.** This skill always reviews **this repo**. Capture the
   repo root and today's date from a trustworthy shell (the session cwd), so the
   workflow targets the right tree and stamps the milestone:
   ```bash
   git rev-parse --show-toplevel
   git rev-parse --abbrev-ref HEAD
   date +%F
   ```

2. **Pick the persona set.** Default panel (omit `personas`): `SEC, MNT, TST,
   API, LNG`. Add opt-in lenses by naming them, e.g.
   `personas: ['SEC','MNT','TST','API','LNG','OPS','ARC','SKP']`, or pass
   `personas: 'auto'` to let a git-aware Scope phase choose lenses from the diff
   and skip ones a recent review already covers. The user may also name a subset
   (e.g. "just security and the api contract" → `personas: ['SEC','API']`).

3. **Invoke the Workflow** with the resolved absolute repo root as `target` and a
   dated milestone label. Example:
   ```
   Workflow({
     scriptPath: '<repo-root>/.claude/workflows/review-panel.js',
     args: {
       target: '<repo-root>',                 // absolute path from step 1
       milestone: '<YYYY-MM-DD> review',       // from `date +%F`
       // personas: ['SEC','MNT','TST','API','LNG'],  // omit for the default five
       // verify: 'default',  // 'off' | 'default' | 'all' — adversarial refutation of high-stakes findings
     }
   })
   ```
   The Workflow returns immediately with a task id and notifies you on
   completion; watch live progress with `/workflows`.

4. **Relay the result.** When it completes, read the synthesis report it wrote
   (`reviews/review-panel-<milestone>.md`) and summarize for the user: the
   posture, the CRITICAL/HIGH `recommend-fix` blockers, anything the verify pass
   refuted, and the per-persona report filenames. The reports are uncommitted —
   leave committing to the user.

## Knobs (all optional)

| Arg | Default | Meaning |
|---|---|---|
| `target` | — (required) | Absolute repo root (or relative + `baseDir`). |
| `milestone` | `"review"` | Run label; goes in every report filename. |
| `personas` | the default five | Array of prefixes/names, or `'auto'` for git-aware scoping. |
| `verify` | `'default'` | `'off'` / `'default'` (api-contract, security, or any CRITICAL) / `'all'` (every CRITICAL+HIGH recommend-fix). |
| `effort` | per-persona | Run-wide override (`'medium'`/`'deep'`). |
| `model` | per-persona | Run-wide model override. |
| `overrides` | — | Per-persona `{PREFIX: {effort, model}}`. |
| `concurrency` | `2` | Personas fan out in chunks of this many (RAM ceiling). |

## Personas

| Prefix | Lens | Default | Panel |
|---|---|---|---|
| `SEC` | Security — path traversal, dynamic-import code execution (`advise.py`, `commands/`), untrusted glossary parsing, NLTK/subprocess, supply-chain | medium / Sonnet | default |
| `MNT` | Maintainability — naming, dead code, DRY (duplicated help), star imports, bare excepts, module globals, stale docs | medium / Sonnet | default |
| `TST` | Testability — TDD discipline, the pytest-cov `fail_under` floor, determinism, fixture/isolation quality | medium / Sonnet | default |
| `API` | API-contract & consumer-stability — docstring-vs-behavior, public-API stability, type/`py.typed` accuracy, semver | deep / strongest model | default |
| `LNG` | Computational-linguistics — soundness & cross-linguistic fidelity of the phonology/morphology/POS/orthography/lexical-semantic modeling; Anglocentrism | deep / Sonnet | default |
| `OPS` | DevOps — CI/CD, release gating, Trusted Publishing, uv `--locked`, SHA-pinned actions, CodeQL, dependabot, rulesets, unicode-guard | medium / Sonnet | opt-in |
| `ARC` | Architecture — module decomposition, glossary/lang/tcoach boundaries, the CLI plugin model, public-API surface design | deep / Sonnet | opt-in |
| `SKP` | First-principles skeptic — is the problem real & present, premature generality, steelman the status quo, YAGNI-minimal | medium / Sonnet | opt-in |

**Default panel:** `SEC, MNT, TST, API, LNG`. `OPS`, `ARC`, and `SKP` are named
opt-ins.

See [`prompts/review/orchestrating-reviews.md`](../../../prompts/review/orchestrating-reviews.md)
for the severity scale, the `dedupe_key` convention, and the manifest schema the
personas share, and [`prompts/review/review-house-style.md`](../../../prompts/review/review-house-style.md)
for the shared adversarial disposition every persona loads first.
