# Contributing to conlangkit

Thanks for your interest! This is a small, focused library — contributions that
keep it that way are especially welcome.

## Setup

conlangkit uses [uv](https://docs.astral.sh/uv/). The committed `uv.lock` is the
source of truth for the dev environment.

```bash
git clone https://github.com/dhh1128/conlangkit
cd conlangkit
uv sync                      # .venv from the lockfile (incl. dev tools)
uv run pre-commit install    # enable the pre-commit hooks

# One-time: NLTK corpora the tests need
uv run python -c "import nltk; [nltk.download(p, quiet=True) for p in \
  ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','wordnet']]"
```

## Before you open a PR

All of these must pass (CI enforces them):

```bash
uv run pytest            # tests + coverage (must stay at/above the floor)
uv run ruff check .      # lint
uv run ruff format       # format
uv run mypy              # type-check
uv run python scripts/check_unicode.py
```

The pre-commit hooks run ruff, mypy, the Unicode guard, and whitespace/format
fixers automatically on `git commit`.

## Conventions

- **TDD.** Write or adjust a failing test first, then make it pass. Every
  behavior change ships with a test.
- **Don't break the public API** (`conlangkit.glossary`, `conlangkit.lang`,
  `conlangkit.tcoach`, `conlangkit.bfr`) without a coordinated change — it has
  downstream consumers. See [AGENTS.md](AGENTS.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
- **Type-checking is a ratchet.** Prefer adding annotations over widening an
  existing mypy/ruff ignore.
- **Sign off your commits** — this repo uses the [Developer Certificate of
  Origin](https://developercertificate.org/). Add a `Signed-off-by` trailer with
  `git commit -s`.
- **Conventional-ish commit subjects** (`fix:`, `feat:`, `docs:`, `ci:`,
  `refactor:`, `chore:`) are appreciated but not required.

## Bugs & issues

File issues on GitHub (label `bug` for defects). If you're fixing one, branch as
`fix/<issue#>-<slug>` and reference `Fixes #<n>` in the PR.

## License

By contributing you agree that your contributions are licensed under
[Apache-2.0](LICENSE).
