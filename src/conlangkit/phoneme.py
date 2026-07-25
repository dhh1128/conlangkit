from typing import Generator, List, Union, Dict
import math

UNDEFINED = 0
PULMONIC = 1 # bit 0
VOWEL = 1 << 1
# There are 2 mutually exclusive choices for roundedness.
# We could represent that in 1 bit, but then we'd have
# no numeric difference between VOWEL and UNROUNDED. So
# use 2 bits -- bits 2 and 3.
ROUNDING_MASK = 3 << 2
ROUNDED = 1 << 2
UNROUNDED = 2 << 2 
# There are 3 mutually exclusive choices for where a vowel
# is pronounced, front-to-back. Use 2 bits -- bits 4 and 5.
VOWEL_POSITION_MASK = 3 << 4
BACK = 1 << 4
CENTRAL = 2 << 4
FRONT = 3 << 4
# There are 7 mutually exclusive choices for how open the
# mouth is with a vowel. Use 3 bits -- bits 6, 7, and 8.
VOWEL_OPENNESS_MASK = 7 << 6
OPEN = 1 << 6
NEAR_OPEN = 2 << 6
OPEN_MID = 3 << 6
MID = 4 << 6
CLOSE_MID = 5 << 6
NEAR_CLOSE = 6 << 6
CLOSE = 7 << 6
# There are 12 places of articulation. We use individual
# bits for these to support co-articulation.
POA_MASK = 8191 << 9
BILABIAL = 1 << 9 
LABIODENTAL = 1 << 10
# Labial is a generic term for anything involving the lips
LABIAL = BILABIAL | LABIODENTAL
DENTAL = 1 << 11
ALVEOLAR = 1 << 12
POSTALVEOLAR = 1 << 13
RETROFLEX = 1 << 14
# Coronal is a general term for anything using front of tongue
CORONAL = DENTAL | ALVEOLAR | POSTALVEOLAR | RETROFLEX
PALATAL = 1 << 15
VELAR = 1 << 16
UVULAR = 1 << 17
# Dorsal is a general term for anything using back of tongue
DORSAL = PALATAL | VELAR | UVULAR
PHARYNGEAL = 1 << 18
EPIGLOTTAL = 1 << 19
GLOTTAL = 1 << 20
# Laryngeal is a general term for anything at back of throat
LARYNGEAL = PHARYNGEAL | EPIGLOTTAL | GLOTTAL
LATERAL = 1 << 21
# There are 8 manners of articulation (excluding clicks).
# Since these are mutually exclusive, we use 3 bits --
# bits 22, 23, 24
MANNER_MASK = 7 << 22
NASAL = 1 << 22
STOP = 2 << 22
PLOSIVE = STOP
FRICATIVE = 3 << 22
APPROXIMANT = 4 << 22
TRILL = 5 << 22
TAP = 6 << 22
FLAP = TAP
AFFRICATE = 7 << 22
# Non-pulmonics
NON_PULMONIC_MASK = 7 << 25
CLICK = 1 << 25
IMPLOSIVE = 1 << 26
EJECTIVE = 1 << 27
# There are 2 mutually exclusive choices for voicing.
# We could represent that in 1 bit, but then we'd have
# no numeric difference between PULMONIC and VOICELESS.
# So use 2 bits -- bits 28 and 29.
VOICING_MASK =  3 << 28
VOICED = 1 << 28
VOICELESS = 2 << 28
LATERAL_FRICATIVE = LATERAL | FRICATIVE
LATERAL_APPROXIMANT = LATERAL | APPROXIMANT
LATERAL_FLAP = LATERAL | FLAP
# Coarticulations
ALVEOLO_PALATAL = ALVEOLAR | PALATAL
LABIAL_VELAR = BILABIAL | VELAR
PALATAL_VELAR = PALATAL | VELAR
LABIAL_PALATAL = LABIAL | PALATAL

# Define mappings between strings and these numeric constants,
# so we can convert either direction.
_n2v = {}
_v2n = {}
# force name and value into globals list so globals() doesn't change while iterating
name = value = None 
for name, value in globals().items():
    if name.upper() == name:
        name = name.lower()
        _n2v[name] = value
        if '_' in name:
            name = name.replace('_', '-')
            _n2v[name] = value
            _n2v[name.replace('-', '')] = value
        _v2n[value] = name


# Some of these arrays must go from highest to lowest numerical value to lowest,
# because the lowest values are present in the bits of the higher values, and we
# test for their bits to decide whether a particular attribute is
# present.
VOWEL_OPENNESS = [CLOSE, NEAR_CLOSE, CLOSE_MID, MID, OPEN_MID, NEAR_OPEN, OPEN]
VOWEL_POSITIONS = [FRONT, CENTRAL, BACK]
VOWEL_ROUNDEDNESS = [ROUNDED, UNROUNDED]
NON_PULMONICS = [CLICK, IMPLOSIVE, EJECTIVE]
MANNERS = [AFFRICATE, FLAP, TRILL, APPROXIMANT, FRICATIVE, PLOSIVE, NASAL]
PLACES = [GLOTTAL, EPIGLOTTAL, PHARYNGEAL, UVULAR, VELAR, PALATAL, RETROFLEX, POSTALVEOLAR, ALVEOLAR, DENTAL, LABIODENTAL, BILABIAL]
IMPLIED_VOICINGS = [NASAL, APPROXIMANT, TRILL, FLAP]
COARTICULATIONS = [ALVEOLO_PALATAL, LABIAL_VELAR, PALATAL_VELAR, LABIAL_PALATAL]
INTERRUPTED_MANNERS = [PLOSIVE, FLAP, AFFRICATE] 
VOWEL_SONORITY = 1.0
GLIDE_SONORITY = 0.925
LIQUID_SONORITY = 0.875
NASAL_SONORITY = 0.825
MINIMUM_VOCALIC_SONORITY = 0.8
FRICATIVE_SONORITY = 0.74
AFFRICATE_SONORITY = 0.64
PLOSIVE_SONORITY = 0.54
NON_PULMONIC_SONORITY = 0.4
VOICED_SONORITY_BOOST = 0.01

def attrib_name_to_value(name):
    name = name.lower().replace('_', '').replace('-', '')
    return _n2v[name]

def attrib_bits_to_name(bits):
    return _v2n[bits]

def _try_attrib(attrib, bits, words, position=0):
    if (bits & attrib) == attrib:
        words.insert(position, attrib_bits_to_name(attrib))
        return True

def attrib_bits_to_phrase(bits):
    words = []
    if _try_attrib(VOWEL, bits, words):
        for r in VOWEL_ROUNDEDNESS:
            if _try_attrib(r, bits, words):
                break
        for p in VOWEL_POSITIONS:
            if _try_attrib(p, bits, words):
                break
        for o in VOWEL_OPENNESS:
            if _try_attrib(o, bits, words):
                break
    else:
        voicing_implied = True
        if (bits & PULMONIC) == PULMONIC:
            manner = bits & MANNER_MASK
            for m in MANNERS:
                if manner == m:
                    # Laryngeal stops are inherently unvoiced. The one in
                    # the glottal position is conventionally called a "stop"
                    # rather than a "plosive". 
                    if (m == STOP) and ((LARYNGEAL & bits) > 0):
                        voicing_implied = True
                        words.insert(0, "stop" if (GLOTTAL & bits) else "plosive")
                    else:
                        words.insert(0, attrib_bits_to_name(m))
                        voicing_implied = m in IMPLIED_VOICINGS
        else:
            voicing_implied = (bits & IMPLOSIVE) == 0
            for np in NON_PULMONICS:
                _try_attrib(np, bits, words)
        _try_attrib(LATERAL, bits, words)
        found_place = False
        for ca in COARTICULATIONS:
            if _try_attrib(ca, bits, words):
                found_place = True
        if not found_place:
            for poa in PLACES:
                if _try_attrib(poa, bits, words):
                    break
        if not voicing_implied:
            if not _try_attrib(VOICED, bits, words):
                words.insert(0, "voiceless")

    return ' '.join(words)

def attrib_phrase_to_bits(phrase):
    bits = 0
    words = phrase.lower().split(' ')
    for word in words:
        new_bits = _n2v[word]
        bits |= new_bits
        if new_bits in IMPLIED_VOICINGS:
            bits |= VOICED
    # Now add bits to make implicit info explicit.
    if not (bits & VOWEL):
        if not (bits & NON_PULMONIC_MASK):
            bits |= PULMONIC
    return bits

"""
Phonemes defined in the IPA. This is not intended to be an exhaustive list -- just
ones that are likely to be interesting in many language projects.
"""
_ph = [
    ('a', 'a', 'open front unrounded vowel', 'French dame [dam]'),
    ('b', 'b', 'voiced bilabial plosive', 'English bed [bEd], French bon [bO~]'),
    ('b_<', 'ɓ', 'voiced bilabial implosive', 'Sindhi ɓarʊ [b_<arU]'),
    ('c', 'c', 'voiceless palatal plosive', 'Hungarian latyak ["lQcQk]'),
    ('d', 'd', 'voiced alveolar plosive', 'English dig [dIg], French doigt [dwa]'),
    ('d`', 'ɖ', 'voiced retroflex plosive', 'Swedish hord [hu:d`]'),
    ('d_<', 'ɗ', 'voiced alveolar implosive', 'Sindhi ɗarʊ [d_<arU]'),
    ('e', 'e', 'close-mid front unrounded vowel', 'French blé [ble]'),
    ('f', 'f', 'voiceless labiodental fricative', 'English five [faIv], French femme [fam]'),
    ('g', 'ɡ', 'voiced velar plosive', 'English game [geIm], French longue [lO~g]'),
    ('g_<', 'ɠ', 'voiced velar implosive', 'Sindhi ɠəro [g_<@ro]'),
    ('h', 'h', 'voiceless glottal fricative', 'English house [haUs]'),
    ('h\\', 'ɦ', 'voiced glottal fricative', 'Czech hrad [h\\rat]'),
    ('i', 'i', 'close front unrounded vowel', 'English be [bi:], French oui [wi], Spanish si [si]'),
    ('j', 'j', 'palatal approximant', 'English yes [jEs], French yeux [j2]'),
    ('j\\', 'ʝ', 'voiced palatal fricative', 'Greek γειά [j\\a]'),
    ('k', 'k', 'voiceless velar plosive', 'English skip [skIp], Spanish carro ["karo]'),
    ('l', 'l', 'alveolar lateral approximant', 'English lay [leI], French mal [mal]'),
    ('l`', 'ɭ', 'retroflex lateral approximant', 'Svealand Swedish sorl [so:l`]'),
    ('l\\', 'ɺ', 'alveolar lateral flap', 'Wayuu püülükü [pM:l\\MkM]'),
    ('m', 'm', 'bilabial nasal', 'English mouse [maUs], French homme [Om]'),
    ('n', 'n', 'alveolar nasal', 'English nap [n{p], French non [nO~]'),
    ('n`', 'ɳ', 'retroflex nasal', 'Swedish hörn [h2:n`]'),
    ('o', 'o', 'close-mid back rounded vowel', 'French veau [vo]'),
    ('p', 'p', 'voiceless bilabial plosive', 'English speak [spik], French pose [poz], Spanish perro ["pero]'),
    ('p\\', 'ɸ', 'voiceless bilabial fricative', 'Japanese fuku '),
    ('q', 'q', 'voiceless uvular plosive', 'Arabic qasbah ["qQs_Gba]'),
    ('r', 'r', 'alveolar trill', 'Spanish perro ["pero]'),
    ('r`', 'ɽ', 'retroflex flap', 'Bengali gari [gar`i:]'),
    ('r\\', 'ɹ', 'alveolar approximant', 'English red [r\\Ed]'),
    ('r\\`', 'ɻ', 'retroflex approximant', 'Malayalam വഴി ["v@r\\`i]'),
    ('s', 's', 'voiceless alveolar fricative', 'English seem [si:m], French session [sE"sjO~]'),
    ('s`', 'ʂ', 'voiceless retroflex fricative', 'Swedish mars [mas`]'),
    ('s\\', 'ɕ', 'voiceless alveolo-palatal fricative', 'Polish świerszcz [s\\v\'ers`ts`]'),
    ('t', 't', 'voiceless alveolar plosive', 'English stew [stju:], French raté [Ra"te]'),
    ('t`', 'ʈ', 'voiceless retroflex plosive', 'Swedish mört [m2t`]'),
    ('u', 'u', 'close back rounded vowel', 'English boom [bu:m], Spanish su [su]'),
    ('v', 'v', 'voiced labiodental fricative', 'English vest [vEst], French voix [vwa]'),
    #('v\\', 'ʋ', 'labiodental approximant', 'Dutch west [v\\Est]/[PEst]'),
    ('w', 'w', 'labial-velar approximant', 'English west [wEst], French oui [wi]'),
    ('x', 'x', 'voiceless velar fricative', 'Scots loch [lOx] or [5Ox]; German Buch, Dach; Spanish caja, gestión'),
    ('x\\', 'ɧ', 'voiceless palatal-velar fricative', 'Swedish sjal [x\\A:l]'),
    ('y', 'y', 'close front rounded vowel', 'French tu [ty] German über ["y:b6]'),
    ('z', 'z', 'voiced alveolar fricative', 'English zoo [zu:], French azote [a"zOt]'),
    ('z`', 'ʐ', 'voiced retroflex fricative', 'Mandarin Chinese rang [z`aN]'),
    ('z\\', 'ʑ', 'voiced alveolo-palatal fricative', 'Polish źrebak ["z\\rEbak]'),
    ('A', 'ɑ', 'open back unrounded vowel', 'English father ["fA:D@(r\\)] (RP and Gen.Am.)'),
    ('B', 'β', 'voiced bilabial fricative', 'Spanish lavar [la"Ba4]'),
    ('B\\', 'ʙ', 'bilabial trill', 'Reminiscent of shivering ("brrr")'),
    ('C', 'ç', 'voiceless palatal fricative', 'German ich [IC], English human ["Cjum@n] (broad transcription uses [hj-])'),
    ('D', 'ð', 'voiced dental fricative', 'English then [DEn]'),
    ('E', 'ɛ', 'open-mid front unrounded vowel', 'French même [mE:m], English met [mEt] (RP and Gen.Am.)'),
    ('F', 'ɱ', 'labiodental nasal', 'English emphasis ["EFf@sIs] (spoken quickly, otherwise uses [Emf-])'),
    ('G', 'ɣ', 'voiced velar fricative', 'Greek γωνία [Go"nia]'),
    ('G\\', 'ɢ', 'voiced uvular plosive', 'Inuktitut nirivvik [niG\\ivvik]'),
    ('G\\_<', 'ʛ', 'voiced uvular implosive', 'Mam ʛa [G\\_<a]'),
    ('H', 'ɥ', 'labial-palatal approximant', 'French huit [Hit]'),
    ('H\\', 'ʜ', 'voiceless epiglottal fricative', 'Agul мехӀ [mEH\\]'),
    ('I', 'ɪ', 'near-close front unrounded vowel', 'English kit [kIt]'),
    ('I\\', 'ᵻ', 'near-close central unrounded vowel', 'Polish ryba [rI\\bA]'),
    ('J', 'ɲ', 'palatal nasal', 'Spanish año ["aJo], English canyon ["k{J@n] (broad transcription uses [-nj-])'),
    ('J\\', 'ɟ', 'voiced palatal plosive', 'Hungarian egy [EJ\\]'),
    ('J\\_<', 'ʄ', 'voiced palatal implosive', 'Sindhi ʄaro [J\\_<aro]'),
    ('K', 'ɬ', 'voiceless alveolar lateral fricative', 'Welsh llaw [KaU]'),
    ('K\\', 'ɮ', 'voiced alveolar lateral fricative', 'Mongolian долоо [tOK\\O:]'),
    ('L', 'ʎ', 'palatal lateral approximant', 'Italian famiglia [fa"miLLa], Castilian: llamar [La"mar]'),
    ('L\\', 'ʟ', 'velar lateral approximant', 'Korean 달구지 [t6L\\gudz\\i]'),
    ('M', 'ɯ', 'close back unrounded vowel', 'Korean 음식 [M:ms\\_hik_}]'),
    ('M\\', 'ɰ', 'velar approximant', 'Spanish fuego ["fweM\\o]'),
    ('N', 'ŋ', 'velar nasal', 'English thing [TIN]'),
    ('N\\', 'ɴ', 'uvular nasal', 'Japanese さん san [saN\\]'),
    ('O', 'ɔ', 'open-mid back rounded vowel', 'American English off [O:f]'),
    ('O\\', 'ʘ', 'bilabial click', ''),
    ('P', 'ʋ', 'labiodental approximant', 'Dutch west [PEst]/[v\\Est], allophone of English phoneme /r\\/'),
    ('Q', 'ɒ', 'open back rounded vowel', 'RP lot [lQt]'),
    ('R', 'ʁ', 'voiced uvular fricative', 'German rein [RaIn]'),
    ('R\\', 'ʀ', 'uvular trill', 'French roi [R\\wa]'),
    ('S', 'ʃ', 'voiceless postalveolar fricative', 'English ship [SIp]'),
    ('T', 'θ', 'voiceless dental fricative', 'English thin [TIn]'),
    ('U', 'ʊ', 'near-close back rounded vowel', 'English foot [fUt]'),
    ('U\\', 'ᵿ', 'near-close central rounded vowel', 'English euphoria [jU\\"fO@r\\i@]'),
    ('V', 'ʌ', 'open-mid back unrounded vowel', 'Scottish English strut [str\\Vt]'),
    ('W', 'ʍ', 'voiceless labial-velar fricative', 'Scots when [WEn]'),
    ('X', 'χ', 'voiceless uvular fricative', 'Klallam sχaʔqʷaʔ [sXa?q_wa?]'),
    ('X\\', 'ħ', 'voiceless pharyngeal fricative', 'Arabic ح ḥāʾ [X\\A:]'),
    ('Y', 'ʏ', 'near-close front rounded vowel', 'German hübsch [hYpS]'),
    ('Z', 'ʒ', 'voiced postalveolar fricative', 'English vision ["vIZ@n]'),
    ('@', 'ə', 'mid central unrounded vowel', 'schwa, English arena [@"r\\i:n@]'),
    ('@\\', 'ɘ', 'close-mid central unrounded vowel', 'Paicĩ kɘ̄ɾɘ [k@\\_M4@\\_M]'),
    ('{', 'æ', 'near-open front unrounded vowel', 'English trap [tr\\{p]'),
    ('}', 'ʉ', 'close central rounded vowel', 'Swedish sju [x\\}:]; AuE/NZE boot [b}:t]'),
    ('1', 'ɨ', 'close central unrounded vowel', 'Welsh tu [t1], American English rose\'s ["r\\oUz1z]'),
    ('2', 'ø', 'close-mid front rounded vowel', 'Danish købe ["k2:b@], French deux [d2]'),
    ('3', 'ɜ', 'open-mid central unrounded vowel', 'English nurse [n3:s] (RP) or [n3`s] (Gen.Am.)'),
    ('3\\', 'ɞ', 'open-mid central rounded vowel', 'Irish tomhail [t3\\:l\']'),
    ('4', 'ɾ', 'alveolar flap', 'Spanish pero ["pe4o], American English better ["bE4@`]'),
    ('6', 'ɐ', 'near-open central unrounded vowel', 'German besser ["bEs6], Australian English mud [m6d]'),
    ('7', 'ɤ', 'close-mid back unrounded vowel', 'Estonian kõik [k7ik], Vietnamese mơ [m7_M]'),
    ('8', 'ɵ', 'close-mid central rounded vowel', 'Swedish buss [b8s]'),
    ('9', 'œ', 'open-mid front rounded vowel', 'French neuf [n9f], Danish drømme [dR9m@]'),
    ('&', 'ɶ', 'open front rounded vowel', 'Swedish skörd [x\\&d`]'),
    ('?', 'ʔ', 'glottal stop', 'Cockney English bottle ["bQ?o]'),
    ('?\\', 'ʕ', 'voiced pharyngeal fricative', 'Arabic ع ʿayn [?\\Ajn]'),
    ('<\\', 'ʢ', 'voiced epiglottal fricative', 'Siwi arˤbˤəʢa (four) [ar_?\\b_?\\@<\\a]'),
    ('>\\', 'ʡ', 'epiglottal plosive', 'Archi гӀарз (complaint) [>\\arz]'),
    ('!\\', 'ǃ', 'postalveolar click', 'Zulu iqaqa (polecat) [i:!\\a:!\\a]'),
    ('|\\', 'ǀ', 'dental click', 'Zulu icici (earring) [i:|\\i:|\\i]'),
    ('|\\|\\', 'ǁ', 'alveolar lateral click', 'Zulu xoxa (to converse) [|\\|\\O:|\\|\\a]'),
    ('=\\', 'ǂ', 'palatal click', '')
]

class Phoneme:
    def __init__(self, x_sampa, ipa, descrip, example):
        self._x_sampa = x_sampa
        self._ipa = ipa
        self._descrip = descrip
        self._example = example
        self._bits = attrib_phrase_to_bits(descrip)
    @property
    def ipa(self) -> str:
        return self._ipa
    @property
    def x_sampa(self) -> str:
        return self._x_sampa
    @property
    def descrip(self) -> str:
        return self._descrip
    @property
    def example(self) -> str:
        return self._example
    @property
    def is_glide(self) -> bool:
        return self._ipa in ['j', 'w', 'ɥ', 'ɰ', 'ʋ']
    @property
    def is_liquid(self) -> bool:
        return self._ipa in ['l', 'ɹ', 'ɾ', 'ɻ', 'ʎ']  # 'ɭ', 'ʟ'
    @property
    def is_fricative(self) -> bool:
        return (self._bits & MANNER_MASK) == FRICATIVE
    @property
    def is_plosive(self) -> bool:
        return (self._bits & MANNER_MASK) == PLOSIVE
    @property
    def is_affricate(self) -> bool:
        return (self._bits & MANNER_MASK) == AFFRICATE
    @property
    def is_click(self) -> bool:
        return (self._bits & NON_PULMONIC_MASK) == CLICK
    @property
    def is_ejective(self) -> bool:
        return (self._bits & NON_PULMONIC_MASK) == EJECTIVE
    @property
    def is_implosive(self) -> bool:
        return (self._bits & NON_PULMONIC_MASK) == IMPLOSIVE
    @property
    def sonority(self) -> float:
        if self.is_vowel: return VOWEL_SONORITY
        if self.is_glide: return GLIDE_SONORITY
        if self.is_liquid: return LIQUID_SONORITY
        if self.is_nasal: return NASAL_SONORITY
        if self.is_fricative: n = FRICATIVE_SONORITY
        elif self.is_affricate: n = AFFRICATE_SONORITY
        elif self.is_plosive: n = PLOSIVE_SONORITY
        else: n = NON_PULMONIC_SONORITY
        if self.is_voiced:
            n += VOICED_SONORITY_BOOST
        return n
    @property
    def can_be_vocalic(self) -> bool:
        return self.sonority >= NASAL_SONORITY
    @property
    def is_interrupted(self) -> bool:
        if self.is_consonant:
            if self.is_pulmonic:
                return self.manner in INTERRUPTED_MANNERS
            else:
                return (self._bits & NON_PULMONIC_MASK) != 0
    @property
    def is_rounded(self) -> bool:
        return (self._bits & ROUNDING_MASK) == ROUNDED
    @property
    def is_vowel(self) -> bool:
        return (self._bits & VOWEL) == VOWEL
    @property
    def is_consonant(self) -> bool:
        return (self._bits & VOWEL) != VOWEL
    @property
    def is_voiced(self) -> bool:
        return (self._bits & VOICED) == VOICED
    @property
    def is_nasal(self) -> bool:
        return (self._bits & MANNER_MASK) == NASAL
    @property
    def is_pulmonic(self) -> bool:
        return (self._bits & PULMONIC) == PULMONIC
    @property
    def place(self) -> int:
        return (self._bits & POA_MASK)
    @property
    def manner(self) -> int:
        return (self._bits & MANNER_MASK)
    @property
    def position(self) -> int:
        return (self._bits & VOWEL_POSITION_MASK)
    @property
    def openness(self) -> int:
        return (self._bits & VOWEL_OPENNESS_MASK)
    def __str__(self):
        return self._ipa
    def __lt__(self, other):
        return self._ipa < other._ipa if isinstance(other, Phoneme) else self._ipa < other
    def __eq__(self, other):
        if isinstance(other, Phoneme):
            return self._ipa == other._ipa
        return False
    
EachPhoneme = Generator[Phoneme, None, None]
PhonemeList = List[Phoneme]
StrOrPhonemeList = Union[str, PhonemeList]
EachPhonemeList = Generator[PhonemeList, None, None]
IPAStr = str
XSampaStr = str
PhonemeLookup = Dict[str, Phoneme]
PhonemeLookupByIPA = Dict[IPAStr, Phoneme]
PhonemeLookupByXSampa = Dict[XSampaStr, Phoneme]

ByIPA = {}
ByXSampa = {}
for p in _ph:
    phone = Phoneme(p[0], p[1], p[2], p[3])
    ByIPA[phone.ipa] = phone
    ByXSampa[phone.x_sampa] = phone

SCHWA = ByIPA['ə']

def vowel_distance(vowel_a: Phoneme, vowel_b: Phoneme) -> float:
    """
    Computes the distance between two vowels -- one unit of distance for their
    separation front-to-back, and one unit of distance for their separation
    open-to-close.
    """
    a_pos = vowel_a.position >> 4
    b_pos = vowel_b.position >> 4
    a_openness = vowel_a.openness >> 6
    b_openness = vowel_b.openness >> 6
    return math.sqrt(abs(a_pos - b_pos)**2 + abs(a_openness - b_openness)**2)

def ipa_to_phonemes(ipa: str) -> PhonemeList:
    return [ByIPA[ch] for ch in ipa]

def phonemes_to_ipa(phonemes: PhonemeList) -> str:
    return ''.join([ph.ipa for ph in phonemes])