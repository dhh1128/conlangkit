from ..lang import *


FOO = Lang('foo')
FOO.cfg = {
    "vowels": "aeiou",
    "consonants": "stpnmfhzdb",
    "sylpats": ["CV", "CCV", "CVC", "VC", "V"]
}

MARTIAN = Lang(os.path.join(os.path.dirname(os.path.abspath(__file__)),'martian'))

def test_no_data():
    l = FOO
    assert l.name == 'foo'
    assert l.vowels == "aeiou"
    assert l.consonants == "stpnmfhzdb"
    assert len(l.sylpats) == 5
    assert l.glossary.lemma_count == 0

def test_load_from_disk():
    l = MARTIAN
    assert l.name == 'martian'
    assert l.vowels == "eio"
    assert l.consonants == "spx"
    assert len(l.sylpats) == 2
    assert l.glossary.lemma_count > 5

def test_advise_func():
    assert MARTIAN.advise_func(['a', 'b', 'c']) == ['a', 'b']

def FIXtest_syllables():
    count = sum(1 for _ in MARTIAN.syllables)
    assert count > 25
