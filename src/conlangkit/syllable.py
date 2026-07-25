from typing import List, Optional, Generator, Union

from .phoneme import *

class Syllable:
    def __init__(self, phonemes: StrOrPhonemeList):
        self._phonemes = phonemes if isinstance(phonemes, str) \
            else phonemes_to_ipa(phonemes)
        self._nucleus = -1
        self._coda = -1
        self._analyze()

    def _analyze(self):
        max_sonority = 0
        peak = -1
        for i in range(len(self._phonemes)):
            ph = self._phonemes[i]
            phoneme = ByIPA.get(ph)
            if not phoneme:
                raise ValueError(f"Unrecognized phone /{ph}/.")
            new_sonority = phoneme.sonority
            # Did we find a nucleus (a vowel)?
            if new_sonority >= 1.0:
                # First vowel?
                if self._nucleus == -1:
                    self._nucleus = i
                # Have we already seen something that wasn't a vowel?
                elif self._coda != -1:
                    raise ValueError("Can't have more than one nucleus.")
            # Are we still in the onset?
            elif self._nucleus == -1:
                pass
            # Else we found beginning of coda
            elif self._coda == -1:
                self._coda = i
            if new_sonority > max_sonority:
                peak = i
                max_sonority = new_sonority
        if max_sonority < MINIMUM_VOCALIC_SONORITY:
            raise ValueError(f"No recognizable nucleus in /{self._phonemes}/.")
        elif max_sonority >= GLIDE_SONORITY - 0.01 and max_sonority <= GLIDE_SONORITY + 0.01:
            raise ValueError(f"Glide /{self.nucleus}/ can't be vocalic.")
        elif max_sonority < VOWEL_SONORITY:    
            self._nucleus = peak
            if peak + 1 <= i:
                self._coda = peak + 1
        
    @property
    def coda(self) -> str:
        return self._phonemes[self._coda:] if self._coda > -1 else ''
    
    @property
    def nucleus(self) -> str:
        return self._phonemes[self._nucleus:] if self._coda == -1 else self._phonemes[self._nucleus:self._coda]
    
    @property
    def rime(self) -> str:
        return self._phonemes[self._nucleus:]
    
    @property
    def onset(self) -> str:
        return self._phonemes[:self._nucleus]
    
    def __str__(self):
        return self.onset + self.rime
    
StrOrSyllable = Union[str, Syllable]
EachSyllable = Generator[Syllable, None, None]

class Pattern:
    def __init__(self, pat: str):
        self._pat = pat
        self._n = len(pat)

    @property
    def pat(self) -> str:
        return self._pat

    def matches(self, 
                syllable: StrOrSyllable, 
                inventory=Optional[PhonemeLookup]) -> bool:
        if not inventory:
            inventory = ByIPA
        s = str(syllable)
        if len(s) != self._n:
            return False
        for i in range(0, self._n):
            pat_glyph = self._pat[i]
            syl_glyph = s[i]
            if pat_glyph in 'CV':
                syl_phone = inventory.get(syl_glyph)
                if syl_phone is None:
                    return False
                if pat_glyph == 'C':
                    if not syl_phone.is_consonant:
                        return False
                else:
                    if not syl_phone.is_vowel:
                        return False
            else:
                if pat_glyph != syl_glyph:
                    return False
        return True
    
    def __str__(self):
        return self._pat

StrOrPattern = Union[str, Pattern]
PatternList = List[Pattern]
    
def _why_not_next(
        growing_syllable: PhonemeList, 
        next: Phoneme, 
        allowed_doubles=Optional[PhonemeList]) -> str:
    """
    Analyzes why phonotactic constraints would be violated if next sound were added
    to growing_syllable. Returns either an error string or None, meaning the append
    would be valid.
    
    Different languages have different rules for how sounds combine. This function
    simply imposes a common set of choices that are likely to be true across many
    languages, eliminating the most common nonsensical combinations of sounds.
    """
    # Always allow append if growing syllable is empty.
    if not growing_syllable:
        return None
    
    # Disallow nonsensical repetition.
    prev = growing_syllable[-1]
    same = (next == prev)
    if same:
        if (not allowed_doubles) or (next not in allowed_doubles): return f"Can't double /{next}/."
        if len(growing_syllable) > 1 and next == growing_syllable[-2]: return f"Can't triple /{next}/."

    next_vowel = next.is_vowel
    prev_vowel = prev.is_vowel
    if next_vowel:
        # Disallow double nucleus.
        consonant = False
        for i in range(len(growing_syllable) - 1, -1, -1):
            if growing_syllable[i].is_consonant:
                consonant = True
            elif consonant:
                return f"Already had nucleus /{growing_syllable[i]}/; can't use /{next}/ as another nucleus."
        if prev_vowel:
            if vowel_distance(next, prev) < 1.5:
                return f"/{prev}{next}/ aren't distinct enough to form a dipthong."
    
    # Are we analyzing consecutive consonants?
    elif not prev_vowel:

        if next.place == GLOTTAL:
            return f"Glottals can't follow other consonants."
        
        if next.is_click:
            return f"Clicks can't follow other consonants."
        
        if prev.ipa == 'ʔ':
            return f"Glottal stop can't be followed by a consonant."
        
        if prev.manner == FLAP:
            return f"Flap can't be followed by a consonant."
        
        if (next.manner == prev.manner) and not same:
            if next.place | prev.place != ALVEOLAR | LABIODENTAL:
                return "Consecutive consonants with the same manner are unpronounceable except alveolar + labiodental."

        if prev.manner == AFFRICATE and next.manner == FRICATIVE:
            return "An affricate can't be followed by a fricative."

        if prev.is_glide:
            return "Glides must be next to vowels."

        if next.is_nasal:
            if prev.is_nasal and not same:
                return "Consecutive nasals are not distinct enough."
            if prev.is_interrupted:
                return "Nasal can't follow something that's interrupted."
        
        # Rule 1: can't have the same phone twice on the same side of a
        # vowel, even if not repeated.
        check_dup = False
        # Rule 2: can't have two consonants that both interrupt, on the same
        # side of a vowel.
        check_interrupted = next.is_interrupted
        # Rule 3: can't change voiced twice on the same side of vowel.
        voiced_transition_count = 0
        voiced = next.is_voiced
        for i in range(len(growing_syllable) - 1, -1, -1):
            pre = growing_syllable[i]
            if pre.is_vowel:
                break
            else:
                # Rule 1
                if not check_dup:
                    check_dup = True
                else:
                    if pre == next:
                        return f"/{next}/ can't appear twice on the same side of a vowel."
                # Rule 2`
                if check_interrupted and pre.is_interrupted:
                    return f"Already interrupted with /{pre}/; can't do it again with /{next}/."
                # Rule 3
                if pre.is_voiced != voiced:
                    voiced_transition_count += 1
                    if voiced_transition_count > 1:
                        return f"Can't change voicing of consonants more than once on the same side of a vowel."
                    voiced = pre.is_voiced

def _valid_next(
        pat_char: str, 
        vowels: PhonemeList, 
        consonants: PhonemeList, 
        allowed_doubles: PhonemeList, 
        growing_syllable: PhonemeList) -> EachPhoneme:
    """
    Given a single char from a syllable pattern (typically 'C' or 'V'), vowels,
    consonants, phonemes that can be doubled, and whatever is already part of the
    growing syllable, yield each phoneme that could match the char from the pattern
    while also obeying phonotactic constraints.
    """
    if pat_char == 'C':
        collection = consonants
    elif pat_char == 'V':
        collection = vowels
    else:
        collection = [pat_char]
    # If nothing has come before, then no phonotactic constraints are active.
    if not growing_syllable:
        for phoneme in collection:
            yield phoneme
    else:
        for phoneme in collection:
            # Otherwise, find next phonemes that don't violate rules.
            err = _why_not_next(growing_syllable, phoneme, allowed_doubles)
            if not err:
                yield phoneme

def _get_all_valid_remainders(
        pat: str,
        vowels: PhonemeList, 
        consonants: PhonemeList, 
        allowed_doubles: PhonemeList,
        growing_syllable: PhonemeList) -> EachPhonemeList:
    """
    Given a full or partial syllable pattern, vowels, consonants, phonemes that can be
    doubled, and whatever is already part of the growing syllable, yield arrays of phonemes
    that embody all the ways that the syllable could end in conformance to the pattern
    and to phonotactic constraints.
    """
    # Split pattern into what we're looking at now, and what comes later.
    current_pat_char = pat[0]
    rest_of_pat = pat[1:]
    # For each phoneme that could be fill the current spot in the pattern...
    for phoneme in _valid_next(current_pat_char, vowels, consonants, allowed_doubles, growing_syllable):
        # If there's more pattern to complete...
        if rest_of_pat:
            prefix = growing_syllable + [phoneme] if growing_syllable else [phoneme]
            # Recurse to find what could come after
            for suffix in _get_all_valid_remainders(rest_of_pat, vowels, consonants, allowed_doubles, prefix):
                # Generate what fits in this spot plus all variations that could come after
                yield prefix + suffix
        else:
            yield [phoneme]

def candidates(
        vowels: StrOrPhonemeList, 
        consonants: StrOrPhonemeList,
        allowed_doubles: StrOrPhonemeList,
        *patterns: Union[PatternList, List[str]]) -> EachSyllable:
    """
    Given a set of vowels, a set of consonants, a set of phonemes that
    can be doubled into long versions of themselves, and a set of syllable
    patterns, yield all syllables that make sense according to general
    phonotactic principles, eliminating those that are not pronouncable by
    the human vocal tract or that would be vanishingly unlikely.
    """
    if patterns:
        if isinstance(patterns[0], Pattern):
            patterns = [str(x) for x in patterns]
        if isinstance(vowels, str):
            vowels = ipa_to_phonemes(vowels)
        if isinstance(consonants, str):
            consonants = ipa_to_phonemes(consonants)
        if allowed_doubles and isinstance(allowed_doubles, str):
            allowed_doubles = ipa_to_phonemes(allowed_doubles)
        for pat in patterns:
            for syllable in _get_all_valid_remainders(pat, vowels, consonants, allowed_doubles, None):
                yield Syllable(phonemes_to_ipa(syllable))
