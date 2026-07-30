import io
import os
import random

import pytest

from ..glossary import *

SAMPLE_GLOSS_PATH = os.path.join(os.path.dirname(__file__), "martian", "glossary.txt")
g = Glossary.load(SAMPLE_GLOSS_PATH)

SAMPLE_MD_GLOSS_PATH = SAMPLE_GLOSS_PATH.replace(".txt", ".md")
g_md = Glossary.load(SAMPLE_MD_GLOSS_PATH)
MD_PRE = "# A glossary\n\na paragraph of text\n* some stuff\n* some more stuff\n\n## Glossary"
MD_POST = "# A section after glossary\nsome stuff after a glossary"


def test_MatchExpr():
    def assert_me(text, starter, fw):
        me = MatchExpr(text)
        assert me.starter == starter
        assert me.first_wildcard == fw
        assert bool(fw > -1) == me.wildcarded

    assert_me("abc", "abc", -1)
    assert_me("ab*c", "ab", 2)
    assert_me("ab?c", "ab", 2)
    assert_me("*abc", "", 0)
    assert_me("?abc", "", 0)


def test_searchexpr():
    entry = Entry(("abc", "123", "def xyz", "notes"))

    def assert_matches(expr):
        se = SearchExpr(expr)
        assert se.matches(entry)

    assert_matches("le:abc")
    assert_matches("lem:!abc")
    assert_matches("lem:abc!")
    assert_matches("l:abc")
    assert_matches("tags:123")
    assert_matches("defn:*xyz")
    assert_matches("not:notes")
    assert_matches("abc*")


def test_searchexpr_tolerates_a_colon_that_is_not_a_scope():
    # A colon the scope pattern does not recognize is ordinary text. It used to
    # crash the parser: the synthetic leading scope was skipped, leaving an odd
    # number of chunks for a walk that reads them in (scope, value) pairs.
    entry = Entry(("ratio", "n", "a 3:1 proportion", "see: the note"))
    # The stray colon is carried into the match text rather than read as a scope.
    assert str(SearchExpr("3:1")) == "x:3:1"
    assert str(SearchExpr("https://example.com")) == "x:https://example.com"
    assert SearchExpr("d:*3:1*").matches(entry)
    assert SearchExpr("n:see: the note").matches(entry)


def test_searchexpr_rejects_lemma_and_defn_with_loose_text():
    with pytest.raises(ValueError):
        SearchExpr("bare t:lish:1 t:dish:2")


def test_searchexpr_starter():
    def assert_starter(expr, starter):
        se = SearchExpr(expr)
        assert se.starter == starter

    assert_starter("lemma:abc tag:v", "abc")
    assert_starter("t:v le:ab*c", "ab")
    assert_starter("def:abc tags:v", "")
    assert_starter("lem:*abc notes:notes pos:v", "")


def test_searchexpr_fuzzify():
    def assert_fuzzy(expr, fuzzy_equiv):
        se = SearchExpr(expr)
        original = str(se)
        changed = se.fuzzify()
        assert str(se) == fuzzy_equiv
        assert changed == (original != fuzzy_equiv)

    assert_fuzzy("lemma:abc", "l:*!abc*")
    assert_fuzzy("tags:abc", "t:abc")
    assert_fuzzy("notes:?abc", "n:?abc*")
    assert_fuzzy("defn:?abc?", "d:?abc?")
    assert_fuzzy("defn:abc xyz", "d:*!abc*xyz*")


def assert_di(x, kind, txt=None):
    di = DefnItem(x)
    assert di.kind == kind
    if txt is None:
        txt = x.strip()
    assert str(di) == txt


def test_DefnItem_simple():
    assert_di("pickle", EXACT_EQUIV)
    for equiv in EQUIV_CHARS:
        assert_di(equiv + "pickle", equiv)


def test_DefnItem_spaces():
    for equiv in EQUIV_CHARS:
        for ch in " \t\r\n":
            assert_di(equiv + ch + "pickle", equiv, equiv + "pickle")
            assert_di(equiv + " " + ch + "pickle", equiv, equiv + "pickle")
    for ch in " \t\r\n":
        assert_di(ch + "pickle", EXACT_EQUIV, "pickle")
        assert_di(" " + ch + "pickle", EXACT_EQUIV, "pickle")


def test_DefnItem_sort():
    for i in range(10):
        items = [DefnItem("x")]
        content_chars = "abcdefghijk"
        for j in range(len(EQUIV_CHARS)):
            equiv = EQUIV_CHARS[(j + 2) % len(EQUIV_CHARS)]
            items.append(DefnItem(equiv + content_chars[j : j + 2]))
        random.shuffle(items)
        items.sort()
        assert items[0].kind == EXACT_EQUIV
        for j in range(len(EQUIV_CHARS)):
            assert items[1 + j].kind == EQUIV_CHARS[j]


def test_DefnItem_gloss_and_explanation():
    def assert_gex(item, gloss, explanation):
        di = DefnItem(item)
        assert di.gloss == gloss
        assert di.explanation == explanation

    assert_gex("abc", "abc", "")
    assert_gex("abc (xyz)", "abc", "xyz")
    assert_gex("abc (xyz", "abc", "xyz")
    assert_gex("abc xyz)", "abc xyz)", "")


def test_Defn_multi():
    defn = Defn("~def/ <a/> bc / :something/ another something")
    assert len(defn.equivs) == 5
    # Should render in different order, with all spacing canonicalized
    assert str(defn) == "another something / >bc / <a / ~def / :something"


def test_load():
    # prove basic loading and that empty lines are ignored
    assert len(g.entries) == 6
    assert g.entries[2].lemma == "fry"  # prove entries are sorted


def test_load_markdown():
    assert len(g_md.entries) == 6
    assert g_md.entries[2].lemma == "fry"
    assert g_md.pre.find(MD_PRE) > -1
    assert g_md.post.find(MD_POST) > -1


def test_save_simple():
    buf = io.StringIO()
    g.save(handle=buf)
    output = buf.getvalue()
    assert HEADER in output
    assert DIVIDER in output
    i = output.find("fry |")
    j = output.find("swallow |")
    assert i > -1
    assert j > -1
    assert i < j


def test_save_markdown():
    buf = io.StringIO()
    g_md.save(handle=buf)
    txt = buf.getvalue()
    assert txt.find(MD_PRE) > -1
    assert txt.find(MD_POST) > -1
    assert txt.find("sweet | a | ~having a sugary flavor") > -1


def test_find_simple():
    assert g.find("l:fry")
    assert not g.find("l:not-there")
    assert not g.find("d:fry")
    assert g.find("d:to cook*")


def test_find_lemma_wildcards():
    assert g.find("l:fr*")
    assert g.find("l:?ry")
    assert g.find("l:*ry")
    assert not g.find("l:*not*")


def test_find_defn_simple():
    assert g.find("d:a yellow fruit")
    assert not g.find("d:purple vegetable")


def test_find_defn_wildcards():
    assert len(g.find("d:*fruit")) > 1


def test_find_anywhere():
    assert len(g.find("swallow")) == 1
    assert len(g.find("vinegar", try_fuzzy=True)) == 1


# ── case-insensitive matching (opt-in) ─────────────────────────────────────────
# Lemma comparison is byte-order by design, so folding is never the default. But
# definitions and notes are prose, where a capitalized query would otherwise miss
# silently; callers that search prose can ask for folding explicitly.


def test_MatchExpr_ignore_case():
    # The exact (non-wildcard) path.
    assert not MatchExpr("abc").matches("ABC")
    assert MatchExpr("abc", ignore_case=True).matches("ABC")
    assert MatchExpr("ABC", ignore_case=True).matches("abc")
    # ...and the wildcard/regex path.
    assert not MatchExpr("ab*").matches("ABC")
    assert MatchExpr("ab*", ignore_case=True).matches("ABC")


def test_searchexpr_ignore_case():
    entry = Entry(("Abc", "Tag", "Def Xyz", "Notes"))
    assert not SearchExpr("l:abc").matches(entry)
    assert SearchExpr("l:abc", ignore_case=True).matches(entry)
    assert SearchExpr("t:tag", ignore_case=True).matches(entry)
    assert SearchExpr("d:*xyz", ignore_case=True).matches(entry)
    assert SearchExpr("n:notes", ignore_case=True).matches(entry)


def test_searchexpr_fuzzify_preserves_ignore_case():
    # fuzzify() rebuilds its MatchExprs; the folding setting must survive that.
    se = SearchExpr("d:Abc", ignore_case=True)
    assert se.fuzzify()
    assert se.matches(Entry(("x", "v", "an ABC thing", "")))


def test_find_ignore_case_is_opt_in():
    assert not g.find("l:APPLE")
    assert g.find("l:APPLE", ignore_case=True)
    assert not g.find("d:A YELLOW FRUIT")
    assert g.find("d:A YELLOW FRUIT", ignore_case=True)


def test_find_ignore_case_scans_past_byte_order():
    # 'BANANA' bisects to the front (uppercase sorts before lowercase) and the
    # first entry examined, 'apple', is byte-order greater than the starter — so
    # the sorted-scan shortcut would stop before reaching 'banana'. Folding must
    # disable both the bisect and the early break, since byte order no longer
    # predicts where a case-insensitive match lives.
    assert g.find("l:BANANA", ignore_case=True)
    assert g.find("l:SWEET", ignore_case=True)


def test_find_ignore_case_survives_the_fuzzy_pass():
    # The fuzzy pass recurses with an already-built SearchExpr; folding has to
    # travel on the expression, not just on the find() argument.
    assert len(g.find("VINEGAR", try_fuzzy=True)) == 0
    assert len(g.find("VINEGAR", try_fuzzy=True, ignore_case=True)) == 1
    assert len(g.find("d:*FRUIT", ignore_case=True)) > 1


# ── Backslash escaping in the definition column ────────────────────────────────
# A literal '/' in a definition is written on disk as '\/', a literal '\' as '\\'.
# In memory, values are always UNESCAPED (so search/gloss operate on real text);
# on disk, they are re-escaped so a bare '/' remains the equiv separator.


def test_defn_literal_slash_is_one_equiv():
    d = Defn(r"bakobo\/heti, over keripy")
    assert len(d.equivs) == 1
    assert d.equivs[0].kind == EXACT_EQUIV
    assert d.equivs[0].value == "bakobo/heti, over keripy"  # unescaped in memory
    assert str(d) == r"bakobo\/heti, over keripy"  # re-escaped on disk


def test_defn_bare_slash_still_splits():
    # Regression: an unescaped '/' is still the equiv separator (Kila/martian rely on this).
    d = Defn("a red fruit / >jonathan")
    assert len(d.equivs) == 2


def test_defn_mixed_literal_slash_and_separator():
    d = Defn(r"allow\/ask\/deny / >other")
    assert len(d.equivs) == 2
    assert any(e.kind == EXACT_EQUIV and e.value == "allow/ask/deny" for e in d.equivs)
    assert any(e.kind == NARROWER_EQUIV and e.value == "other" for e in d.equivs)


def test_defn_literal_backslash_roundtrips():
    d = Defn(r"a\\b")  # file has two backslashes
    assert len(d.equivs) == 1
    assert d.equivs[0].value == "a\\b"  # one backslash in memory
    assert str(d) == r"a\\b"  # doubled on disk


def test_defn_backslash_then_separator():
    # '\\' (literal backslash) followed by an unescaped '/' separator -> two equivs.
    d = Defn(r"a\\ / b")
    assert len(d.equivs) == 2
    assert any(e.value == "a\\" for e in d.equivs)
    assert any(e.value == "b" for e in d.equivs)


def test_entry_literal_slash_roundtrips():
    line = r"heti | component | bakobo\/heti over keripy | a dependency"
    e = Entry(line)
    assert e.defn.equivs[0].value == "bakobo/heti over keripy"
    assert str(e) == line


def test_search_operates_on_unescaped_value():
    e = Entry(r"heti | component | bakobo\/heti over keripy | note")
    assert SearchExpr("d:*bakobo/heti*").matches(e)


def test_escaped_glossary_roundtrips_byte_identical():
    src = (
        "lemma | tags | definition | notes\n"
        "----- | ---- | ---------- | -----\n"
        r"deny | concept | allow\/ask\/deny artifact | the verdict" + "\n"
        r"heti | component | bakobo\/heti, over keripy | a dependency" + "\n"
    )
    io.StringIO(src)
    gl = Glossary()
    # load() takes a filename; exercise the round-trip via a temp file
    import tempfile

    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as tf:
        tf.write(src)
        path = tf.name
    gl = Glossary.load(path)
    out = io.StringIO()
    gl.save(handle=out)
    assert out.getvalue() == src
    os.remove(path)


# ── Glossary.update / Glossary.remove ──────────────────────────────────────────
# These encapsulate the entry-editing idiom that commands/repl.py used to open-code
# (mutate fields, re-sort on lemma change, invalidate the stats cache).


def test_glossary_remove():
    gl = Glossary.load(SAMPLE_MD_GLOSS_PATH)
    _ = gl.stats  # populate the stats cache
    e = gl.find("l:fry!")[0]
    gl.remove(e)
    assert e not in gl.entries
    assert gl._unsaved is True
    assert gl._stats is None  # cache invalidated


def test_glossary_update_fields_no_rename():
    gl = Glossary.load(SAMPLE_MD_GLOSS_PATH)
    _ = gl.stats
    e = gl.find("l:fry!")[0]
    ret = gl.update(e, tags="v zzz", notes="hot oil")
    assert ret is e
    assert sorted(e.tags) == ["v", "zzz"]
    assert e.notes == "hot oil"
    assert gl._stats is None
    assert "zzz" in gl.stats["tags"]  # recomputed after invalidation


def test_glossary_update_defn_accepts_str_and_Defn():
    gl = Glossary.load(SAMPLE_MD_GLOSS_PATH)
    e = gl.find("l:fry!")[0]
    gl.update(e, defn="to saute")
    assert str(e.defn) == "to saute"
    gl.update(e, defn=Defn("to fry"))
    assert str(e.defn) == "to fry"


def test_glossary_update_rename_resorts():
    gl = Glossary.load(SAMPLE_MD_GLOSS_PATH)
    e = gl.find("l:apple!")[0]
    gl.update(e, lemma="zebra")
    lemmas = [x.lemma for x in gl.entries]
    assert lemmas == sorted(lemmas)  # still sorted after the rename
    assert gl.find("l:zebra!")
    assert not gl.find("l:apple!")


def test_glossary_update_partial_noop_when_all_none():
    gl = Glossary.load(SAMPLE_MD_GLOSS_PATH)
    e = gl.find("l:fry!")[0]
    before = str(e)
    gl.update(e)
    assert str(e) == before
