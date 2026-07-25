# langkit

A Python toolkit for building constructed languages. Provides a glossary
format and search engine, base-form reduction for English, part-of-speech
tagging integration, phoneme/syllable primitives, and an orthography
transliterator.

Phonotactic features (`syllable.candidates`, `Lang.syllables`) are
experimental and partially broken — `Lang.syllables` currently raises
`NotImplementedError`. Use `syllable.candidates()` directly if you need
phonotactic syllable generation.

## Install as an editable dependency

From a sibling project, add to your `pyproject.toml` or `requirements.txt`:

```
langkit @ file:///../langkit
```

Or install directly into your virtual environment:

```bash
pip install -e /path/to/langkit
```

## Development setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest langkit/tests/
```

Use the venv — the repo root has a `venv/` that is gitignored. Running
`python` or `pip` outside it may resolve to a different interpreter.

## Quick example: load a glossary and search

```python
from langkit.glossary import Glossary

g = Glossary.load("path/to/glossary.md")
print(f"{g.lemma_count} entries loaded")

# Find entries whose definition contains "fruit"
hits = g.find("d:*fruit", max_hits=10)
for entry in hits:
    print(entry.lemma, "—", entry.defn)

# Fuzzy search across lemma and definition
hits = g.find("apple", try_fuzzy=True)
```

Glossary files are Markdown tables with four pipe-delimited columns:
`lemma | tags | definition | notes`. The file may have arbitrary Markdown
before and after the table.

## Public API

See the [API audit](#api-audit) section in the project's final report
(or read the source — all public names are in the modules listed below).

Key entry points:

| Name | Module | Purpose |
|------|--------|---------|
| `Glossary` | `langkit.glossary` | Load, save, and search a glossary file |
| `Entry` | `langkit.glossary` | A single glossary entry (lemma, tags, defn, notes) |
| `Defn` / `DefnItem` | `langkit.glossary` | Parsed definition with multiple equivalences |
| `SearchExpr` / `MatchExpr` | `langkit.glossary` | Search expression objects |
| `bfr` | `langkit.bfr` | Base-form reduction (inflected English → lemma) |
| `find_by_nltk` | `langkit.pos` | Map an NLTK POS tag to a langkit POS |
| `Lang` | `langkit.lang` | Language object: config + glossary + phonology |
| `TranslationCoach` | `langkit.tcoach` | Hint-based translation assistant |
| `Orthography` | `langkit.ortho` | Bidirectional transliteration |
| `Syllable` / `Pattern` / `candidates` | `langkit.syllable` | Phonotactic syllable primitives |
| `Phoneme` / `ByIPA` / `ByXSampa` | `langkit.phoneme` | IPA phoneme inventory |
