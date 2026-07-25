from ..pos import find_by_nltk

def test_find_nltk():
    assert find_by_nltk('JJ').lk == 'ad'
    assert find_by_nltk('JJ').descrip == 'adjective'
    assert find_by_nltk('does not exist') == None