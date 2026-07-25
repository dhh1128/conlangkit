# conlangkit

[![CI](https://github.com/dhh1128/conlangkit/actions/workflows/ci.yml/badge.svg)](https://github.com/dhh1128/conlangkit/actions/workflows/ci.yml)
[![CodeQL](https://github.com/dhh1128/conlangkit/actions/workflows/codeql.yml/badge.svg)](https://github.com/dhh1128/conlangkit/actions/workflows/codeql.yml)
[![PyPI](https://img.shields.io/pypi/v/conlangkit.svg)](https://pypi.org/project/conlangkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/conlangkit.svg)](https://pypi.org/project/conlangkit/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

A Python toolkit for building **constructed languages**. It provides a glossary
format and search engine, base-form reduction for English, part-of-speech
tagging integration, an orthography transliterator, and phoneme/syllable
primitives — plus a `clk` command-line tool for working with a language on disk.

> **Experimental:** the phonotactic features (`syllable.candidates`,
> `Lang.syllables`) are partially implemented. `Lang.syllables` currently raises
> `NotImplementedError`; call `syllable.candidates()` directly if you need
> phonotactic syllable generation.

> **Name note:** the import package is `conlangkit`. It is unrelated to the
> `langkit` project on PyPI (WhyLabs' LLM-monitoring library).

## Install

```bash
pip install conlangkit      # or: uv add conlangkit
```

This installs the library and the `clk` command-line tool.

## Quick example

```python
from conlangkit.glossary import Glossary

g = Glossary.load("path/to/glossary.md")
print(f"{g.lemma_count} entries loaded")

# Find entries whose definition contains "fruit"
for entry in g.find("d:*fruit", max_hits=10):
    print(entry.lemma, "—", entry.defn)

# Fuzzy search across lemma and definition
hits = g.find("apple", try_fuzzy=True)
```

Glossary files are Markdown tables with four pipe-delimited columns —
`lemma | tags | definition | notes` — and may have arbitrary Markdown before and
after the table. See [ARCHITECTURE.md](ARCHITECTURE.md) for the full format.

## Command-line tool

```bash
clk <LANGDIR> repl      # interactive REPL over the language in <LANGDIR>
clk <LANGDIR>           # defaults to the repl
clk help                # general help
```

`<LANGDIR>` is a directory containing a language (`cfg.json` + `glossary.md`).

## Public API

The supported surface (imported directly from its submodule):

| Name | Module | Purpose |
|------|--------|---------|
| `Glossary` | `conlangkit.glossary` | Load, save, and search a glossary file |
| `Entry` | `conlangkit.glossary` | A single glossary entry (lemma, tags, defn, notes) |
| `Defn` / `DefnItem` | `conlangkit.glossary` | Parsed definition with multiple equivalences |
| `SearchExpr` / `MatchExpr` | `conlangkit.glossary` | Search-expression objects |
| `Lang` | `conlangkit.lang` | Language object: config + glossary + phonology |
| `TranslationCoach` / `rewrite_rules` | `conlangkit.tcoach` | Hint-based translation assistant |
| `bfr` | `conlangkit.bfr` | Base-form reduction (inflected English → lemma) |
| `find_by_nltk` | `conlangkit.pos` | Map an NLTK POS tag to a conlangkit POS |
| `Orthography` | `conlangkit.ortho` | Bidirectional transliteration |
| `Syllable` / `candidates` | `conlangkit.syllable` | Phonotactic primitives (experimental) |
| `Phoneme` / `ByIPA` / `ByXSampa` | `conlangkit.phoneme` | IPA phoneme inventory (experimental) |

The package ships a `py.typed` marker, so type checkers see its annotations.

## Developer quickstart

Prerequisite: [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/dhh1128/conlangkit
cd conlangkit
uv sync                 # create .venv from uv.lock (incl. dev tools)

# One-time: fetch the NLTK corpora the tests use
uv run python -c "import nltk; [nltk.download(p, quiet=True) for p in \
  ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','wordnet']]"

uv run pytest           # tests + coverage
uv run ruff check .     # lint
uv run mypy             # type-check
uv run pre-commit install   # enable pre-commit hooks (once)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[AGENTS.md](AGENTS.md) for the conventions AI agents and developers follow here.

## License

[Apache-2.0](LICENSE).
