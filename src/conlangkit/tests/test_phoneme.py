from ..phoneme import *
from ..phoneme import _ph, _v2n, _n2v

def test_uniqueness():
    dups = []
    for i in range(len(_ph)):
        a = _ph[i]
        for j in range(len(_ph)):
            if j != i:
                b = _ph[j]
                for n in range(len(a)):
                    if a[n] and (a[n] == b[n]):
                        dups = f"item {i} ({a}) and {j} ({b}) are identical in field {n}"
    assert not dups

def test_attrib_name_to_value():
    unrecognized_words = []
    for p in _ph:
        attrib_words = p[2].split(' ')
        for word in attrib_words:
            if attrib_name_to_value(word) is None:
                unrecognized_words.append(word)
    assert not unrecognized_words

def test_attrib_bits_to_name():
    for i in range(0, 29 + 1):
        try:
            assert attrib_bits_to_name(1 << i)
        except:
            print (_v2n)
            raise

def test_attrib_bits_to_phrase_vowels():
    broken = []
    descrips = [p[2] for p in _ph if 'vowel' in p[2]]
    # Conceivable vowels that I have manually confirmed do not exist in IPA or X-SAMPA's inventory
    exceptions = [
        OPEN | CENTRAL | UNROUNDED, 
        OPEN | CENTRAL | ROUNDED, 
        NEAR_OPEN | FRONT | ROUNDED,
        NEAR_OPEN | CENTRAL | ROUNDED,
        NEAR_OPEN | BACK | UNROUNDED,
        NEAR_OPEN | BACK | ROUNDED,
        MID | FRONT | ROUNDED,
        MID | FRONT | UNROUNDED,
        MID | CENTRAL | ROUNDED,
        MID | BACK | ROUNDED,
        MID | BACK | UNROUNDED,
        NEAR_CLOSE | BACK | UNROUNDED
    ]
    for o in VOWEL_OPENNESS:
        for p in VOWEL_POSITIONS:
            for r in VOWEL_ROUNDEDNESS:
                attribs = o | p | r
                if attribs not in exceptions:
                    phrase = attrib_bits_to_phrase(VOWEL | attribs)
                    if phrase not in descrips:
                        broken.append(f"{phrase} is missing")
    assert not broken

def show_relevant_bits(mask):
    shown = ''
    for k, v in _n2v.items():
        if '-' in k or '_' in k or 'mask' in k:
            continue
        if (mask & v) != v:
            continue
        shown += f"  {k} = {hex(v)}\n"
    return shown

def test_attrib_phrase_to_bits():
    broken = []
    def check(phrase, bits):
        n = attrib_phrase_to_bits(phrase)
        if n != bits:
             actual = attrib_bits_to_phrase(n)
             expected = attrib_bits_to_phrase(bits)
             print(show_relevant_bits(n | bits))
             error = f"{phrase} yielded {hex(n)} ({actual}), not {hex(bits)} ({expected})"
             assert not error
    check('alveolar lateral click', ALVEOLAR | LATERAL | CLICK)
    check('postalveolar click', POSTALVEOLAR | CLICK)
    check('velar approximant', VOICED | VELAR | APPROXIMANT | PULMONIC)
    check('voiceless palatal-velar fricative', VOICELESS | PALATAL_VELAR | FRICATIVE | PULMONIC)
    check('voiceless uvular plosive', VOICELESS | UVULAR | PLOSIVE | PULMONIC)
    check('retroflex lateral approximant', VOICED | RETROFLEX | LATERAL | APPROXIMANT | PULMONIC)
    check('alveolar trill', VOICED | ALVEOLAR | TRILL | PULMONIC)
    check('alveolar nasal', VOICED | ALVEOLAR | NASAL | PULMONIC)
    check('voiced glottal fricative', VOICED | GLOTTAL | FRICATIVE | PULMONIC)
    check('voiced velar implosive', VOICED | VELAR | IMPLOSIVE)
    check('voiceless palatal plosive', VOICELESS | PLOSIVE | PALATAL | PULMONIC)
    check('near-open central rounded vowel', NEAR_OPEN | CENTRAL | ROUNDED | VOWEL)
    check('open front unrounded vowel', OPEN | FRONT | UNROUNDED | VOWEL)

def test_attrib_bits_to_phrase_round_trip():
    y = attrib_phrase_to_bits("voiced bilabial plosive")
    #print(show_relevant_bits(y))
    x = attrib_bits_to_phrase(BILABIAL | PLOSIVE | VOICED)
    broken = []
    for p in _ph:
        expected = p[2]
        actual = attrib_bits_to_phrase(attrib_phrase_to_bits(expected))
        assert actual == expected

def check_2(func, should_be_true, should_be_false):
    assert func(ByIPA[should_be_true]) == True
    assert func(ByIPA[should_be_false]) == False

def test_is_rounded():
    check_2(lambda x: x.is_rounded, 'o', 'i')

def test_is_vowel():
    check_2(lambda x: x.is_vowel, 'a', 's')

def test_is_voiced():
    check_2(lambda x: x.is_voiced, 'd', 'x')

def test_is_interrupted():
    check_2(lambda x: x.is_interrupted, 'd', 'x')

def test_is_nasal():
    check_2(lambda x: x.is_nasal, 'm', 'x')

def test_is_consonant():
    check_2(lambda x: x.is_consonant, 'p', 'u')

def test_is_plosive():
    check_2(lambda x: x.is_plosive, 'p', 's')

def test_is_affricate():
    print('DISABLED - NO AFFRICATES IN IPA TABLE YET')
    #check_2(lambda x: x.is_affricate, 'ts', 't')

def test_is_click():
    check_2(lambda x: x.is_click, 'ǃ', 'k')

def test_is_ejective():
    print('DISABLED - NO EJECTIVES IN IPA TABLE YET')
    #check_2(lambda x: x.is_ejective, "p'", 'k')

def test_is_implosive():
    check_2(lambda x: x.is_implosive, 'ʄ', 'p')

def test_place():
    assert ByIPA['a'].place == UNDEFINED
    assert ByIPA['t'].place == ALVEOLAR

def test_manner():
   assert ByIPA['a'].manner == UNDEFINED
   assert ByIPA['s'].manner == FRICATIVE

def check_mex(func1, func2):
    for xsampa, phone in ByXSampa.items():
        a = func1(phone)
        b = func2(phone)
        if a or b:
            assert a != b

def test_mutually_exclusive():
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_consonant)
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_nasal)
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_glide)
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_liquid)
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_affricate)
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_plosive)
    check_mex(lambda ph: ph.is_vowel, lambda ph: ph.is_interrupted)
    check_mex(lambda ph: ph.is_rounded, lambda ph: ph.is_consonant)
    check_mex(lambda ph: ph.is_glide, lambda ph: ph.is_plosive)
    check_mex(lambda ph: ph.is_glide, lambda ph: ph.is_liquid)

def test_sonority():
    def assert_gt(a, b):
        assert ByIPA[a].sonority > ByIPA[b].sonority
    assert_gt('a', 'j')
    assert_gt('j', 'l')
    assert_gt('l', 'n')
    assert_gt('n', 'z')
    assert_gt('z', 's')
    assert_gt('s', 'd')
    assert_gt('d', 't')
    assert_gt('t', 'ʘ')

def test_vowel_distance():
    def assert_approx(actual, expected):
        assert (actual >= expected * 0.99) and (actual <= expected * 1.01)
    def vd(a, b, val):
        assert_approx(vowel_distance(ByIPA[a], ByIPA[b]), val)
    vd('a', 'i', 6) # open front to close front
    vd('u', 'i', 2) # close back to close front
    vd('a', 'u', 6.32) # open front to close back
    vd('æ', 'ɞ', 1.414) # near-open front to open-mid central 

def test_can_be_vocalic():
    assert ByIPA['n'].can_be_vocalic
    assert ByIPA['l'].can_be_vocalic
    assert ByIPA['s'].can_be_vocalic == False
