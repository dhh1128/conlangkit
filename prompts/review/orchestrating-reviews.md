# Orchestrating Adversarial Code Reviews — conlangkit

The orchestrator-side companion to the review-persona prompts in this folder
(`security-hawk.md`, `maintainability-expert.md`, `testability-hawk.md`,
`api-contract-auditor.md`, `computational-linguist.md`, `devops-engineer.md`,
`architect.md`, `first-principles-skeptic.md`).

Use this when you run the personas as **subagents at a milestone** — spawning
several, collecting their findings, deduplicating across them, and adjudicating
dispositions, with no human in the loop (or with human input deferred). Each
persona prompt describes *its* half of the contract; this doc describes how to
drive the panel and combine the results.

> **About this vendored set.** conlangkit is a Python toolkit for building
> constructed languages: a `uv`-managed library + `clk` CLI (deps `nltk` +
> `termcolor`), `src/` layout, mid-modernization from an older codebase. It
> exposes a stable **consumer API** (`conlangkit.glossary`,
> `conlangkit.lang.Lang`, `conlangkit.tcoach.rewrite_rules`, `conlangkit.bfr`)
> and models real linguistic domains (phonology, morphology, POS, orthography,
> lexical semantics). These personas were adapted from a general multi-persona
> panel and **deliberately de-coupled from any specific employer platform,
> methodology, or service architecture.** They assume only what this repo
> actually is. Two lenses are bespoke to conlangkit — **api-contract**
> (docstring-vs-behavior conformance, public-API stability, type/`py.typed`
> accuracy, semver implications) and **computational-linguist** (is the domain
> modeling linguistically defensible and free of silent Anglocentrism?) —
> because those are the project's headline claims and no generic lens covers
> them. conlangkit has **no normative RFC-style specification**; the "contract"
> is the public API's documented behavior, not a spec document.

---

## 1. Spawning a persona

Each prompt has an **Invocation Contract** section defining two modes and a set
of knobs. To run one unattended, set `mode: unattended` and pass whatever else
applies:

| Knob | Meaning |
|---|---|
| `mode` | `interactive` (default) or `unattended`. Unattended = no human answers mid-run; the persona never blocks. |
| `effort` | `medium` (default) or `deep`. |
| `max_findings` | size of the Top Findings list (default 5; api-contract and computational-linguist default 7, because conlangkit has a broad public surface and many linguistic sub-domains). |
| `run_label` | goes in the report filename so milestones/concurrent runs don't collide (default: today's date). |
| `prior_dispositions` | findings already adjudicated in earlier runs (accepted-risk / deferred / rebutted). The persona must not re-litigate these unless it has new evidence. |

When driving the panel as a **Workflow** (§7), these orchestrator-level knobs
also apply: `model` (run-wide model override), `overrides` (per-persona
`{PREFIX: {effort, model}}`), `verify` (`off`/`default`/`all` pre-merge
refutation pass), and `personas: 'auto'` (git-aware lens scoping).

### Per-persona effort/model tiering

Each persona carries a default effort + model. For conlangkit: **api-contract**
runs **deep on the strongest model** (a stable consumer API is the project's
headline claim and a silent break there cascades into every dependent);
**computational-linguist** and **architect** run **deep**; the inherited defect
lenses (security, testability, maintainability, devops, skeptic) run **medium**
unless escalated. Resolution at fan-out is per-persona `overrides[PREFIX]` →
run-wide `effort`/`model` → persona default.

### Verification pass

Before the exact-key merge, a `Verify` phase adversarially tries to **refute**
high-stakes findings against the repo (each finding needs only itself + the
tree, not the merged view). Scope is gated by `verify`: `off` skips it;
`default` verifies findings from `api-contract-auditor`/`security-hawk` or any
`CRITICAL`; `all` verifies every `CRITICAL`/`HIGH` `recommend-fix`. A
**refuted** finding is removed from the queue that flows into merge + synthesis
but is **recorded** in the report's `## Refuted (excluded from findings)`
section, so nothing is silently lost.

For conlangkit specifically: an api-contract finding that claims "the docstring
promises X but the code does Y" or "this change breaks the public signature" is
*verifiable against the source and the tests* and is exactly the kind of claim
the verify pass should challenge — confirm the cited symbol/signature/docstring
exists and the behavior truly diverges before it survives.

---

## 2. Severity is a fix-obligation, not a bug-triage score

All defect-lens personas use one scale: **CRITICAL / HIGH / MEDIUM / LOW**.
There is no per-persona variant, so sort the merged queue directly.

The scale measures **how mandatory the fix is, relative to tolerating the code
as-is** — e.g. before raising a PR, or before declaring the work "good enough":

| Level | Obligation |
|---|---|
| **CRITICAL** | Must be fixed before this code is tolerated as-is. Leaving it is not acceptable. |
| **HIGH** | Default expectation is "fix before moving on." Deferring requires an explicit, recorded decision (accepted risk). |
| **MEDIUM** | Worth fixing; acceptable to defer with a note. |
| **LOW** | Optional; fix if convenient. |

### Severity vs. recommended_disposition

- **severity** = the finding's intrinsic fix-obligation (a property of the finding).
- **recommended_disposition** = what the reviewer recommends doing *now*, given milestone context (`recommend-fix` / `recommend-defer` / `recommend-accept-risk`).

A CRITICAL almost always maps to `recommend-fix`. **conlangkit-specific
tension:** a fix to a public signature or a documented behavior may carry
HIGH/CRITICAL severity *and* a large `fix_effort`, because changing it is a
**breaking change** for downstream consumers (see the Public API contract in
`AGENTS.md`). A reviewer who recommends deferring such a finding MUST say so
loudly and name the compensating control (e.g. "gated behind the next MAJOR
version bump, with a deprecation shim").

---

## 3. The `dedupe_key` convention

Two personas seeing the same issue must produce the **same** key so the
orchestrator can merge them. The key names the *concept*, not the evidence
location (file and line live in the finding's `location` field).

**Grammar:** `<subject>-<adjective>[-<qualifier>]`, all lowercase-kebab.
- **subject** — the most stable identifier available: module / file-stem /
  public symbol / artifact. For repo-global issues, the artifact itself
  (`glossary`, `lang`, `tcoach`, `bfr`, `pos`, `ortho`, `phoneme`, `syllable`,
  `ui`, `repl`, `commands`, `app`, `py-typed`, `github-actions`, `ci-yml`,
  `release-yml`).
- **adjective** — the defect class, preferably from the recommended set below.
- **qualifier** — optional condition: `-on-untrusted-input`, `-for-non-english`,
  `-at-import-time`, `-cross-consumer`.

### Recommended adjective set (open — extend as needed)

| Adjective | Means | Usual lens |
|---|---|---|
| `unsafe` | exploitable (path traversal, arbitrary code execution) | security |
| `injectable` | untrusted input reaches a dangerous sink | security |
| `unbounded` | no cap / blows up on pathological input | security, testability |
| `unpinned` | mutable dependency / action / tag | security, devops |
| `ungated` | a release/deploy step runs without a test gate | devops |
| `breaking` | changes a public signature/behavior consumers depend on | api-contract |
| `undocumented` | public symbol lacks a docstring, or the type is absent/wrong | api-contract |
| `divergent` | docstring/type annotation and actual behavior disagree | api-contract, maintainability |
| `anglocentric` | bakes English/Latin-script assumptions into a general tool | computational-linguist |
| `unsound` | the linguistic/domain model is wrong or misleading | computational-linguist |
| `nondeterministic` | output depends on time/locale/env/order/randomness | testability |
| `unhandled` | sad path / error condition not handled (or not rejected) | testability |
| `flaky` | nondeterministic / environment-coupled test | testability |
| `untested` | lacks adequate coverage, or structurally resists testing | testability |
| `duplicated` | repeated logic/constant that should be shared | maintainability |
| `coupled` | improper dependency / hidden ordering constraint | architect |
| `missing` | a required thing is absent (doc, error condition, test) | any |
| `stale` | comment/docstring/label contradicts current behavior | maintainability |
| `unnecessary` | surface added ahead of a demonstrated present need | skeptic |

**If none fits:** use the most natural single adjective and flag it as a
candidate addition in your synthesis. The set is meant to grow.

**Fuzzy-merge safety net:** exact `dedupe_key` matching under-merges, because
independent personas emit different keys for the same issue. The panel handles
this in a **synthesis-stage semantic clustering pass** (judging sameness from
title + location + rationale, conservatively); the canonical entry is the
member with the **most-obligated severity**, with the union of reporters and
locations.

Examples where the convention collapses cross-persona findings to one item:
- `commands-unsafe-at-import-time` (import-time scan + dynamic import) ← security + architect
- `advise-unsafe` (importlib exec of `advise.py`) ← security + api-contract
- `bfr-anglocentric` (English morphology baked into a general tool) ← computational-linguist + skeptic
- `lang-syllables-unhandled` (`NotImplementedError`) ← testability + api-contract
- `help-duplicated` (help rendering in app.py and commands/help.py) ← maintainability + architect

---

## 4. Manifest schema

Every persona emits a fenced-YAML manifest as the final section of its report
(and, in unattended mode, as part of its returned message). Core fields:

| Field | Notes |
|---|---|
| `id` | persona-prefixed, e.g. `SEC-F1`, `API-F2`, `LNG-F3`. |
| `persona` | which reviewer produced it. |
| `title` | short human-readable summary. |
| `severity` | CRITICAL / HIGH / MEDIUM / LOW. |
| `confidence` | CONFIRMED / LIKELY / SPECULATIVE. |
| `location` | `path:line` or module/symbol. |
| `dedupe_key` | per §3. |
| `recommended_disposition` | recommend-fix / recommend-defer / recommend-accept-risk. |
| `rationale` | one line; enough for the orchestrator to overrule without re-deriving. |
| `revisit_condition` | required when `recommend-defer`. |
| `fix_effort` | small / medium / large. |

The workflow hands each persona's `agent()` call a JSON Schema with exactly
these required fields (plus nullable `revisit_condition`, `tier`,
`cost_category`, `measurement`), so the harness enforces the shape. Emit only
these fields.

---

## 5. Collect → merge → adjudicate

1. **Collect** every persona's returned manifest (the file is durable backup).
2. **Merge** by `dedupe_key`: fold shared-key findings into one item with a
   `reported_by: [...]` list, the **most-obligated** severity, and the union of
   locations. Then run the synthesis-stage semantic clustering pass (§3).
3. **Adjudicate** against milestone policy. A sensible default:
   - any unresolved **CRITICAL** `recommend-fix` → milestone is **blocked**;
   - **HIGH** `recommend-fix` → blocked unless explicitly deferred with a recorded reason;
   - **MEDIUM/LOW** → logged, not blocking.
   Record each decision so it can be passed back as `prior_dispositions` next
   run. Where a finding is real, material debt, recommend filing a **GitHub
   Issue** on `dhh1128/conlangkit` (labeled `bug` where it is a defect), per
   `AGENTS.md`. The orchestrator does not file Issues autonomously in unattended
   mode; it surfaces the recommendation.

---

## 6. The conlangkit persona roster

| Prefix | File | Lens | Default effort/model |
|---|---|---|---|
| `SEC` | `security-hawk.md` | implementation security: path traversal, dynamic-import code execution, untrusted glossary parsing, subprocess/NLTK, supply-chain | medium |
| `MNT` | `maintainability-expert.md` | naming, dead code, DRY, star imports, bare excepts, duplicated help, module globals, stale docs | medium |
| `TST` | `testability-hawk.md` | TDD discipline, coverage floor, determinism, test quality (pytest + pytest-cov) | medium |
| `API` | `api-contract-auditor.md` | docstring-vs-behavior conformance, public-API stability, type/`py.typed` accuracy, semver implications | deep / strongest |
| `LNG` | `computational-linguist.md` | linguistic correctness & cross-linguistic fidelity of the domain modeling (phonology, morphology, POS, orthography, lexical semantics) | deep |
| `OPS` | `devops-engineer.md` | CI/CD, release/publish gating, uv `--locked`, action pinning, Trusted Publishing, CodeQL, dependabot, rulesets, unicode-guard | medium |
| `ARC` | `architect.md` | module decomposition, the glossary/lang/tcoach boundaries, the CLI plugin model, public-API surface design | deep |
| `SKP` | `first-principles-skeptic.md` | is the problem real & present, premature generality, steelman the status quo, YAGNI-minimal | medium |

**Default panel:** `SEC, MNT, TST, API, LNG`. `OPS`, `ARC`, and `SKP` are named
opt-ins. (The api-contract and computational-linguist lenses are conlangkit's
primary risk surface — a silent consumer break or an unsound linguistic model
is the worst failure mode — and security/maintainability/testability run on
every panel because the tool parses untrusted input, dynamically imports code,
and is mid-modernization.)

---

## 7. Running the panel as a Workflow

The vendored workflow script lives at
[`.claude/workflows/review-panel.js`](../../.claude/workflows/review-panel.js)
and is invoked by the `review-board` skill. It is **opt-in** (ask to "run a
review panel" / "run review-board").

It is **self-contained**: `PROMPTS_DIR` defaults to this folder
(`<repo>/prompts/review/`), so the panel does not depend on any external clone.
Targeting is explicit and verified: a preflight agent canonicalizes
`args.target` to the enclosing git repo root and aborts if it isn't a git repo
(or `args.branch` doesn't match). Each persona agent re-confirms the resolved
tree before reviewing.

```
Workflow({ scriptPath: '<repo>/.claude/workflows/review-panel.js',
           args: { target: '<repo abs path>', milestone: 'YYYY-MM-DD review',
                   personas: ['SEC','MNT','TST','API','LNG'] } })
```

It mirrors the standing subagent rules on this machine: personas fan out **in
chunks of ≤2** (RAM ceiling), each agent prompt carries **`nice -n 19 ionice -c
3`** for heavy shell work, findings merge by `dedupe_key` with **most-obligated
severity winning**, refined by the synthesis-stage semantic clustering pass.

**Persistence.** The run is read-only on source but **writes its output to
`<repo>/reviews/`** (uncommitted): a synthesis index
`review-panel-<milestone>.md` (executive summary, a table of every finding, a
fenced-JSON copy of the merged manifest) plus one `<persona>-<milestone>.md`
narrative report per persona. The workflow does **not** commit.

---

*Canonical definitions live here. The persona prompts reference this doc for
severity semantics and the `dedupe_key` convention rather than restating them,
so there is one source of truth.*
