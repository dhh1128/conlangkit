from ..bfr import *


def test_bfr():
    assert bfr("are", "VBP") == ("be", "v")
    assert bfr("am", "VBP") == ("be", "v")
    assert bfr("is", "VBZ") == ("be", "v")
    assert bfr("taken", "VBN") == ("take", "v")
    assert bfr("walked", "VBN") == ("walk", "v")
    assert bfr("running", "VBG") == ("run", "v")
    assert bfr("smiling", "VBG") == ("smile", "v")
    assert bfr("baked", "VBD") == ("bake", "v")
    assert bfr("persuaded", "VBD") == ("persuade", "v")
    assert bfr("caused", "VBD") == ("cause", "v")
    assert bfr("received", "VBD") == ("receive", "v")
    assert bfr("believed", "VBD") == ("believe", "v")
    assert bfr("pleased", "VBD") == ("please", "v")
    assert bfr("repeated", "VBD") == ("repeat", "v")
    assert bfr("obviated", "VBD") == ("obviate", "v")
    assert bfr("influenced", "VBD") == ("influence", "v")
    assert bfr("danced", "VBD") == ("dance", "v")
    assert bfr("abruptly", "RB") == ("abrupt", "ad")
    assert bfr("bigger", "JJR") == ("big", "ad")
    assert bfr("highest", "JJS") == ("high", "ad")
    assert bfr("pelagic", "JJ") == ("pelag", "n")
    assert bfr("childish", "JJ") == ("child", "n")
    assert bfr("childlike", "JJ") == ("child", "n")
    assert bfr("windy", "JJ") == ("wind", "n")
    assert bfr("heavenly", "JJ") == ("heaven", "n")


def test_bfr_irregular_gerund_and_noun_branches():
    # VBD irregular (find_regular hit)
    assert bfr("gave", "VBD") == ("give", "v")
    assert bfr("went", "VBD") == ("go", "v")
    # VBG: doubled consonant, silent-e, and plain
    assert bfr("swimming", "VBG") == ("swim", "v")
    assert bfr("baking", "VBG") == ("bake", "v")
    assert bfr("walking", "VBG") == ("walk", "v")
    # VBZ regular 3rd-person singular
    assert bfr("walks", "VBZ") == ("walk", "v")
    # JJ ending in -ing
    assert bfr("running", "JJ") == ("runn", "v")
    # NN / NNS noun forms
    assert bfr("bodies", "NNS") == ("body", "n")
    assert bfr("smiles", "NNS") == ("smile", "n")
    assert bfr("creation", "NN") == ("crea", "v")
    assert bfr("sailor", "NN") == ("sail", "v")
    assert bfr("farmer", "NN") == ("farm", "v")
    # No transformation applies → (None, None)
    assert bfr("cat", "NN") == (None, None)
    assert bfr("word", "UNKNOWNTAG") == (None, None)


def test_find_regular_and_silent_e_helpers():
    assert find_regular(irregular_past, "gave") == "give"
    assert find_regular(irregular_past, "not-a-real-past-form") is None
    # "nc" ending → silent e likely ("danc" -> "dance")
    assert likely_silent_e("danc") is True
    # two-vowels-plus-consonant in the special list ("iev" -> believe)
    assert likely_silent_e("believ") is True
    # consonant cluster, no silent e
    assert likely_silent_e("walk") is False
    # too short → False
    assert likely_silent_e("go") is False
