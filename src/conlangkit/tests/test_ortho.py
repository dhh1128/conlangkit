from ..ortho import *

o = Orthography({'a': 'A', 'b': 'B'})

def test_simple():
    assert o.from_foreign('appleb') == 'AppleB'
    assert o.to_foreign('AppleB') == 'appleb'

def test_simple_delete():
    delete = lambda x: ''
    assert o.from_foreign('appleb', delete) == 'AB'
    assert o.to_foreign('AppleB', delete) == 'ab'

def test_simple_x():
    x = lambda x: 'x'
    assert o.from_foreign('appleb', x) == 'AxxxxB'
    assert o.to_foreign('AppleB', x) == 'axxxxb'

def test_doubles():
    oo = Orthography({'tʃ': 'T', 'ʃ': 'SH', 't': '*', 'a': 'A', 'b': 'B', 'c': 'CH'})
    assert oo.from_foreign('appleb') == 'AppleB'
    assert oo.to_foreign('AppleB') == 'appleb'
    assert oo.from_foreign('atʃb') == 'ATB'
    assert oo.from_foreign('atʃtʃb') == 'ATTB'
    assert oo.from_foreign('attʃb') == 'A*TB'
    assert oo.from_foreign('atʃʃb') == 'ATSHB'
    assert oo.from_foreign('atxʃb') == 'A*xSHB'
    assert oo.from_foreign('atxʃbc') == 'A*xSHBCH'
    assert oo.to_foreign('ATB') == 'atʃb' 
    assert oo.to_foreign('ATTB') == 'atʃtʃb'
    assert oo.to_foreign('A*TB') == 'attʃb'
    assert oo.to_foreign('ATSHB') == 'atʃʃb'
    assert oo.to_foreign('A*xSHB') == 'atxʃb'
    assert oo.to_foreign('A*xSHBCH') == 'atxʃbc'
    assert oo.to_foreign('A*xSHBcCH') == 'atxʃbcc'
    assert oo.to_foreign('A*xSHBCCH') == 'atxʃbCc'
    assert oo.to_foreign('A*xSHBCHH') == 'atxʃbcH'

def test_triples():
    ooo = Orthography({'abc': '1', 'def': '11', 'ab': '2', 'cd': '22', 'a': '3', 'b': '33'})
    assert ooo.from_foreign('abcaba') == '123'
    assert ooo.to_foreign('123') == 'abcaba'
    assert ooo.to_foreign('112233') == 'defcdb'
