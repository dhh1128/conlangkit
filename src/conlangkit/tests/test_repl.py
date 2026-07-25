"""Behavioural tests for commands/repl.py's glossary editing, proving the edit/
delete commands still work after they were refactored to call Glossary.update /
Glossary.remove instead of open-coding the mutate + re-sort + `_stats = None`
sequence. The stats-cache invalidation (previously an inline poke of the private
`_stats`) is asserted here."""

import os
import tempfile
from types import SimpleNamespace

from ..commands import repl
from ..glossary import Glossary

GLOSS = (
    "lemma | tags | definition | notes\n"
    "----- | ---- | ---------- | -----\n"
    "apple | n | a red fruit | \n"
    "fry | v | to cook in hot oil | \n"
)


def _load_temp():
    fd, path = tempfile.mkstemp(suffix=".md")
    os.write(fd, GLOSS.encode())
    os.close(fd)
    return Glossary.load(path), path


def _ctx(g):
    return SimpleNamespace(lang=SimpleNamespace(glossary=g))


def _script(monkeypatch, answers):
    it = iter(answers)
    monkeypatch.setattr(repl, "prompt_options", lambda *a, **k: next(it))
    monkeypatch.setattr(repl, "write", lambda *a, **k: None)
    monkeypatch.setattr(repl, "warn", lambda *a, **k: None)
    monkeypatch.setattr(repl, "show_hits", lambda *a, **k: None)


def test_edit_field_change_invalidates_stats_and_persists(monkeypatch):
    g, path = _load_temp()
    try:
        assert "zzz" not in g.stats["tags"]  # populate + assert cache
        _script(monkeypatch, ["", "v zzz", "", ""])  # lex same, tags, defn none, notes none
        repl.edit(_ctx(g), g.find("l:fry!")[0])
        assert "zzz" in g.stats["tags"]  # cache was invalidated + recomputed
        assert "zzz" in Glossary.load(path).find("l:fry!")[0].tags  # saved to disk
    finally:
        os.remove(path)


def test_edit_rename_resorts_and_persists(monkeypatch):
    g, path = _load_temp()
    try:
        _script(monkeypatch, ["zebra", "", "", ""])  # rename apple -> zebra
        repl.edit(_ctx(g), g.find("l:apple!")[0])
        lemmas = [e.lemma for e in g.entries]
        assert lemmas == sorted(lemmas)  # still ordered after rename
        assert g.find("l:zebra!") and not g.find("l:apple!")
        reloaded = [e.lemma for e in Glossary.load(path).entries]
        assert "zebra" in reloaded and "apple" not in reloaded
    finally:
        os.remove(path)


def test_edit_abandoned_when_no_changes(monkeypatch):
    g, path = _load_temp()
    try:
        _script(monkeypatch, ["", "", "", ""])  # all blank -> no change
        before = str(g.find("l:fry!")[0])
        repl.edit(_ctx(g), g.find("l:fry!")[0])
        assert str(g.find("l:fry!")[0]) == before
    finally:
        os.remove(path)


def test_delete_removes_invalidates_stats_and_persists(monkeypatch):
    g, path = _load_temp()
    try:
        _ = g.stats  # populate cache
        repl.delete(_ctx(g), g.find("l:fry!")[0])
        assert not g.find("l:fry!")
        assert g._stats is None  # invalidated via Glossary.remove
        assert not Glossary.load(path).find("l:fry!")
    finally:
        os.remove(path)
