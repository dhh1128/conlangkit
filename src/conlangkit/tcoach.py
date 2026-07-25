import bisect
from collections import namedtuple
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

from .pos import find_by_nltk, PLACEHOLDER
from .bfr import *

# Download NLTK resources if needed.
if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt', quiet=True)
if not nltk.data.find('taggers/averaged_perceptron_tagger'):
    nltk.download('averaged_perceptron_tagger', quiet=True)

SimpleNormalizationRule = namedtuple('SimpleNormalizationRule', ['pattern', 'replacement'])
SimpleNormalizationRule.apply = lambda self, text: text.replace(self.pattern, self.replacement)
def snr(pattern, replacement): return SimpleNormalizationRule(pattern, replacement)

DEBUG = False

rewrite_rules = [
    snr('’', "'"),
    snr('“', '"'),
    snr('”', '"'),
    snr("won't", "will not"),
    snr("can't", "cannot"),
    snr("n't", ' not'),
    snr("'re", ' are'),
    snr("y'all", 'you all'),
    snr("'ll", " will"),
    snr("it's", 'it is'),
]

class Hint:
    """
    Represents a hint about how to translate an English word.
    """
    def __init__(self, word, pos, lemma=None, approx=False):
        assert bool(pos) or bool(lemma)
        self.word = word
        self.pos = pos
        self.lemma = lemma
        self.approx = approx
    def __str__(self):
        return self.lemma if self.lemma else f"{self.word} ({self.pos}): ?"
    def __repr__(self):
        return f"{self.word} pos={self.pos} lemma={self.lemma} approx={self.approx}"
    
class TranslationCoach:
    """
    Coaches on translation from English into a given language.
    """
    def __init__(self, glossary, advise_func=None):
        self.glossary = glossary
        self.advise_func = advise_func

    def _find(self, expr):
        hits = self.glossary.find(expr)
        if hits: return hits[0]
        # Automatically try putting verbs in infinitive form.
        if 'p:v' in expr:
            if 'd:to ' not in expr:
                expr = expr.replace('d:', 'd:to ')
                hits = self.glossary.find(expr)
                if hits: return hits[0]
        # Many glossary definitions have explanatory notes about
        # senses, in parentheses. Try matching the word that way.
        if 'd:' in expr and '(' not in expr:
            expr += ' (*'
            hits = self.glossary.find(expr)
            if hits: return hits[0]

    def hints(self, paragraph):
        for nr in rewrite_rules:
            paragraph = nr.apply(paragraph)

        sentences = sent_tokenize(paragraph)
        for sentence in sentences:

            # Tokenize the sentence into words
            words = word_tokenize(sentence)

            # Perform POS tagging
            pos_tags = nltk.pos_tag(words)

            # See if an adviser will help us translate this sentence. This allows
            # externally loaded custom logic on a per-language basis.
            if self.advise_func:
                pos_tags = self.advise_func(pos_tags)

            # Now do the general translation work: look up each word in the glossary.
            i = 0
            for tag in pos_tags:
                entry = None
                approx = False
                word, pos = tag
                
                # Skip the word "to" followed by an uninflected verb; we will
                # end up looking up the uninflected verb in the glossary without
                # looking up "to" before it.
                if pos == "TO" and i < len(pos_tags) - 1 and pos_tags[i + 1][1] == 'VB':
                    i += 1
                    continue 

                # nltk says that the part of speech of punctuation is just the
                # punctuation itself. If we find these tokens, then the lemma
                # (the term the glossary would produce) is just the same as the
                # token, and no further processing is needed. Do the same short
                # circuit for cardinal numbers and proper nouns.
                if not pos[0].isalpha() or pos in ['CD', 'NNP', 'NNPS']:
                   lemma = word
                else:
                    # Normalize case; glossary should have lower-case form of word.
                    if word != "I": word = word.lower()
                    # See if we can convert from nltk parts of speech to the ones used
                    # by lk (LangKit). If yes, we can use POS to look up the word in the
                    # glossary with higher precision.
                    lk_pos = find_by_nltk(pos)
                    if lk_pos and lk_pos.lk:
                        # Lk might have more than one POS for a given nltk category;
                        # look for the word in glossary definitions using each POS
                        # until we find a match.
                        for x in lk_pos.lk.split():
                            expr = f'p:{x} d:{word}'
                            if DEBUG: print(expr)
                            entry = self._find(expr)
                            if entry:
                                if DEBUG: print("found")
                                pos = x
                                break
                    if not entry:
                        # Try looking up the exact word, without a part of speech.
                        entry = self._find(f'd:{word}')
                        if not entry:
                            # Try doing base form reduction on the word. This
                            # will uninflect verbs, among other things.
                            bfr_word, new_pos = bfr(word, tag[1])
                            if bfr_word:
                                expr = f'p:{new_pos} d:{bfr_word}'
                                if DEBUG: print(expr)
                                entry = self._find(expr)
                                if entry:
                                    pos = new_pos
                                    approx = True
                    lemma = None
                    if entry:
                        lemma = entry if isinstance(entry, str) else entry.lemma
                yield Hint(word, pos, lemma, approx)
                i += 1
