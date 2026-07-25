
from ..syllable import *
from ..syllable import _why_not_next

def assert_match(pat, text, expected, inventory=None):
    p = Pattern(pat)
    assert p.matches(text, inventory) == expected

def test_positive_pattern_matches():
    def yes(pat, text): assert_match(pat, text, True)
    yes("a", "a")
    yes("V", "i")
    yes("CV", "ka")
    yes("VV", "ea")
    yes("VVC", "euj")
    yes("CuC", "tus")
    yes("C7C", "t7s")
    yes("CCVl", "spol")

def test_negative_pattern_matches():
    def no(pat, text): assert_match(pat, text, False)
    no("a", "b")
    no("a", "ab")
    no("V", "t")
    no("CV", "ak")
    no("VV", "we")
    no("C7C", "t8s")
    no("CCVC", "sp_t")

def test_constrained_pattern_matches():
    phones = 'aeistpk'
    inventory = {k: v for k, v in zip(phones, map(lambda x: ByIPA[x], phones))}
    def expect(pat, text, true_or_false): assert_match(pat, text, true_or_false, inventory)
    expect("u", "u", True)
    expect("V", "a", True)
    expect("V", "o", False)
    expect("C", "k", True)
    expect("C", "m", False)

def test_good_syllables():
    for x in [
        # vocalic nasals
        ('n', '', 'n', ''),
        ('nt', '', 'n', 't'),
        ('snt', 's', 'n', 't'),
        # vocalic liquid
        ('nl', 'n', 'l', ''),
        ('nls', 'n', 'l', 's'),
        ('slt', 's', 'l', 't'),
        # normal vowels
        ('a', '', 'a', ''),
        ('ak', '', 'a', 'k'),
        ('ank', '', 'a', 'nk'),
        ('anks', '', 'a', 'nks'),
        ('ka', 'k', 'a', ''),
        ('kja', 'kj', 'a', ''),
        ('kat', 'k', 'a', 't'),
        ('kjat', 'kj', 'a', 't'),
        ('stak', 'st', 'a', 'k'),
        ('stlak', 'stl', 'a', 'k'),
        ('stla', 'stl', 'a', ''),
        ('kants', 'k', 'a', 'nts'),
        ('kant', 'k', 'a', 'nt'),
        ('splants', 'spl', 'a', 'nts'),
        ('ai', '', 'ai', ''),
        ('aik', '', 'ai', 'k'),
        ('aink', '', 'ai', 'nk'),
        ('ainks', '', 'ai', 'nks'),
        ('kai', 'k', 'ai', ''),
        ('kjai', 'kj', 'ai', ''),
        ('kait', 'k', 'ai', 't'),
        ('kjait', 'kj', 'ai', 't'),
        ('staik', 'st', 'ai', 'k'),
        ('splaik', 'spl', 'ai', 'k'),
        ('splai', 'spl', 'ai', ''),
        ('kaints', 'k', 'ai', 'nts'),
        ('kaint', 'k', 'ai', 'nt'),
        ('splaints', 'spl', 'ai', 'nts'),
        ]:
        syl = Syllable(x[0])
        assert syl.onset == x[1]
        assert syl.nucleus == x[2]
        assert syl.coda == x[3]
        assert syl.rime == syl.nucleus + syl.coda

def test_bad_syllables():
    for syl in [
        # glides can only exist next to a vowel 
        'j', 'sj', 'js'
        # missing vowels
        's', 'sk',
        # two nucleuses
        'aka',
        # unrecognized phoneme
        '7kat',
        ]:
        try:
            Syllable(syl)
            raise ValueError(f"Expected /{syl}/ to be invalid.")
        except:
            pass

def check_wnn(current_and_next, expected_error=None, allow_doubles=None):
    current = [ByIPA[ph] for ph in current_and_next[:-1]]
    next = ByIPA[current_and_next[-1]]
    err = _why_not_next(current, next, allow_doubles)
    if expected_error:
        err = err.lower() if err else ''
        assert expected_error in err
    else:
        assert not err

def test_why_not_next_vowels():
    def check_vowels(vowels, err=None):
        # Make sure vowel errors occur whether the vowels are solo or after consonant
        check_wnn(vowels, err)
        check_wnn('k' + vowels, err)

    for vowels in ["a", "ai", "oa", "ui"]:
        check_vowels(vowels)

    for pair in [('aa', "can't double"), ('æɞ', "aren't distinct enough")]:
        check_vowels(pair[0], pair[1])

def test_why_not_next_double_triple_nasals():
    check_wnn('mm', "can't double")
    check_wnn('mm', "", [ByIPA["m"]])
    check_wnn('mmm', "can't triple", [ByIPA["m"]])

def test_why_not_next_misc():
    check_wnn('sʘ', "can't follow")
    check_wnn('ʔs', "can't be followed by a consonant")
    check_wnn('kh', "glottals can't follow")
    check_wnn('ɽs', "flap can't be followed by a consonant")
    check_wnn('vz')
    check_wnn('sf')
    check_wnn('sx', "unpronounceable")
    check_wnn('ws', "next to vowels")
    check_wnn('sw')
    check_wnn('tlt', "can't appear twice")
    check_wnn('tlk', "already interrupted")
    check_wnn('tls', "change voicing")
    check_wnn('alts')
    check_wnn('armps')
    check_wnn('str')

NO_MAX = 1000000
def assert_syl(vowels, consonants, pats, min_count=0, 
               max_count=NO_MAX, must_include=None, cant_include=None):
    n = 0
    cant = []
    s = []
    for item in candidates(vowels, consonants, None, *pats):
        item = str(item)
        s.append(item)
        if must_include:
            try:
                i = must_include.index(item)
                del must_include[i]
            except ValueError:
                pass
        if cant_include:
            if item in cant_include:
                cant.append(item)
        n += 1
    if min_count > 0:
        assert n >= min_count
    if max_count >= 0 and max_count <= NO_MAX:
        assert n <= max_count
    if must_include == []: must_include = None
    if cant == []: cant = None
    assert must_include is None
    assert cant is None
    return s
    
def test_syllables_easy():
    assert_syl('ai', 'sm', ['V', 'CV'], 6, 6, ['a', 'sa'], ['sm', 'aa'])

def test_syllables_complex():
    # These are some good vowels and consonants, and this is a single
    # syllable pattern that could be used to combine them. However,
    # none of these consonants should be capable of participating in
    # a 3-consonant cluster with the other consonants, so we should
    # generate no real syllables.
    syl = assert_syl('aeiou', 'smphntk', ['CCCV'], 40)
    i = 0
    for s in syl:
        #print(f"{i} {s}")
        i += 1
    long_syl = [s for s in syl if len(s) == 4]
    assert long_syl == []


