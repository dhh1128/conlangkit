# AGENTS.md

Authoritative instructions for AI agents (and humans) working in **conlangkit**,
a Python toolkit for building constructed languages. `CLAUDE.md`, `GEMINI.md`,
`.cursorrules`, and `.github/copilot-instructions.md` are thin pointers to this
file — this is the single source of truth.

## Core principles

1. **Comprehension before code.** Read the surrounding module and its tests
   before changing anything. Match the existing style; this is an older codebase
   mid-modernization.
2. **Test-driven development.** Prefer TDD: write or adjust a failing test first,
   make it pass, then refactor. Every behavior change ships with a test.
3. **Don't break consumers.** The public API is imported by downstream projects
   (see "Public API" below). Names and semantics there are a contract.

## Setup & everyday commands

This project uses [uv](https://docs.astral.sh/uv/). The lockfile (`uv.lock`) is
committed and authoritative.

```bash
uv sync                       # create .venv from the lockfile (incl. dev tools)
uv run pytest                 # run the test suite with coverage
uv run ruff check .           # lint
uv run ruff format            # format
uv run mypy                   # type-check
uv run clk <LANGDIR> <cmd>    # run the CLI against a language directory
uv run pre-commit install     # enable pre-commit hooks (once)
```

Some tests need NLTK corpora. Download them once:

```bash
uv run python -c "import nltk; [nltk.download(p, quiet=True) for p in \
  ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','wordnet']]"
```

## Project layout

```
src/conlangkit/         the package (src/ layout)
  glossary.py           glossary format, parsing, search  (primary API)
  lang.py               Lang: config + glossary + phonology from a language dir
  tcoach.py             translation-coach hints / rewrite rules
  bfr.py                base-form reduction (inflected English -> lemma)
  pos.py                POS-tag mapping over NLTK
  ortho.py              bidirectional transliteration
  phoneme.py syllable.py  EXPERIMENTAL, partially broken phonotactics
  ui.py                 terminal-UI helpers
  app.py commands/      the `clk` CLI and its plugin commands
  data/                 English word lists
  tests/                pytest suite (+ martian/ fixture language)
scripts/check_unicode.py  Trojan-Source / invisible-Unicode guard (run in CI)
```

## Public API (do not break without a coordinated change)

Downstream consumers import these; treat them as a stable contract:

| Import | Used for |
|--------|----------|
| `conlangkit.glossary` — `Glossary`, `Entry`, `Defn`, `SearchExpr` | load/search/edit glossaries |
| `conlangkit.lang.Lang` | a full language (config + glossary + phonology) |
| `conlangkit.tcoach.rewrite_rules` | translation-coach rules |
| `conlangkit.bfr` | base-form reduction |

If you must change one, update the dependents in lockstep and note it in the PR.

## Quality gates (all must pass; CI enforces them)

- `ruff check .` and `ruff format --check` — clean.
- `mypy` — clean. Type-checking is a **ratchet**: the experimental phonotactics
  modules and legacy `ui` are excluded today; tighten over time, don't loosen.
- `pytest` — green, coverage at or above the `fail_under` floor in `pyproject.toml`.
- `scripts/check_unicode.py` — no disallowed Unicode.

Ruff/mypy carry a few **documented** ignores for legacy idioms (star imports,
bare excepts, experimental modules). These are review targets, not license to
add more — prefer fixing over widening an ignore.

## Defect management

Track bugs as GitHub Issues via the `gh` CLI (label `bug`). Fix on a branch
`fix/<issue#>-<slug>` and reference `Fixes #<n>` in the PR. The adversarial
review panel (`/review-board`, see `.claude/` + `prompts/review/`) is the tool
for a structured multi-lens code review.

## Navigation

- `README.md` — install, quickstart, public-API table.
- `ARCHITECTURE.md` — the on-disk language format and library internals.
- `CONTRIBUTING.md` — contributor workflow.
- `SECURITY.md` — vulnerability reporting.
