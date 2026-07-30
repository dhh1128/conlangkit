# Architecture

This document orients developers who want to consume conlangkit as a library or
work on its internals. For install/usage see the [README](README.md); for the
contribution workflow see [CONTRIBUTING.md](CONTRIBUTING.md).

## On-disk language format

A *language* is a directory. `conlangkit.lang.Lang(path)` reads:

| File | Required | Purpose |
|------|----------|---------|
| `glossary.md` | for a glossary | the word list (Markdown table, see below) |
| `cfg.json` | no | phonology config: `vowels`, `consonants`, `sylpats` |
| `advise.py` | no | optional module exposing an `advise` function used by the coach |

`cfg.json` example (the `martian` test fixture):

```json
{
  "vowels": "eio",
  "consonants": "spx",
  "sylpats": ["CV", "CCV"]
}
```

### Glossary file (`glossary.md`)

A Markdown document with a single four-column pipe table. Arbitrary Markdown may
appear before and after the table; only the table is parsed.

```
lemma | tags | definition | notes
--- | --- | --- | ---
apple|n|a red fruit / >jonathan
swallow|v|:to move food from mouth to stomach
sweet|a|~having a sugary flavor
fry|v|to cook in hot oil | often deep-fried
```

- **lemma** — the headword. Comparison is **case-sensitive by design** (writing
  systems where casing is not English; `AID` and `aid` are distinct).
- **tags** — whitespace-separated (e.g. part-of-speech markers).
- **definition** — one or more *equivalences* separated by `/`. Each may carry a
  leading operator:

  | Prefix | Meaning |
  |--------|---------|
  | *(none)* | exact equivalent |
  | `>` | narrower than the lemma |
  | `<` | broader than the lemma |
  | `~` | rough/approximate |
  | `:` | explained (a gloss, not a synonym) |

  A literal `/` or `\` in a definition is backslash-escaped on disk (`\/`, `\\`)
  and unescaped in memory; serialization re-escapes. Parentheses in a value are
  treated as an inline explanation (`gloss (explanation)`).
- **notes** — free text (optional).

`Defn` holds the parsed equivalences (`DefnItem`s, sorted); `Entry` bundles
lemma + tags + defn + notes.

## Search expressions

`Glossary.find(expr, ...)` parses `expr` into a `SearchExpr` of field-scoped
`MatchExpr` criteria:

- **Field scopes:** `l:` lemma, `t:` tags, `d:` definition, `n:` notes (each
  prefix is abbreviable, e.g. `lem:`, `def:`). Unprefixed text searches lemma
  and definition together.
- **Wildcards** inside a match: `*` (any run), `?` (any char), `!` (word
  boundary). `try_fuzzy=True` loosens a query into a wildcarded form.
- **Case** is significant by default, matching lemma comparison. `ignore_case=True`
  folds it — meant for searching *prose* (definitions, notes), where a capitalized
  query would otherwise miss silently. Folding forgoes the bisect-and-stop
  shortcut, because a case-insensitive match need not sit where byte order
  predicts, so the search scans every entry.

## Modules

| Module | Role |
|--------|------|
| `glossary` | glossary format, parsing, `Glossary`/`Entry`/`Defn`/`SearchExpr` — the primary API |
| `lang` | `Lang`: ties a directory's `cfg.json` + `glossary.md` (+ `advise.py`) together |
| `tcoach` | translation-coach hints and `rewrite_rules` |
| `bfr` | base-form reduction: inflected English → lemma (hardcoded morphology tables) |
| `pos` | maps NLTK POS tags to conlangkit parts of speech |
| `ortho` | bidirectional transliteration (`Orthography`) |
| `phoneme`, `syllable` | **experimental**, partially broken phonotactics (IPA inventory, syllable candidates) |
| `ui` | terminal-UI helpers (used by the CLI) |
| `app`, `commands/` | the `clk` CLI and its auto-discovered plugin commands |

### CLI plugin model

`clk <LANGDIR> <command> [args]` builds a `Lang` from `<LANGDIR>` and dispatches
to a command. Commands are discovered at import time from `commands/` — any
non-underscore module exposing a `cmd` callable is registered. `repl` is the
default command.

## Consumer contract

Downstream projects import a stable subset — `conlangkit.glossary`
(`Glossary`, `Entry`, `Defn`, `SearchExpr`), `conlangkit.lang.Lang`,
`conlangkit.tcoach.rewrite_rules`, `conlangkit.bfr`. Changing those signatures is
a breaking change requiring a coordinated update of dependents. See
[AGENTS.md](AGENTS.md).
