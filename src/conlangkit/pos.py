import bisect
from collections import namedtuple

PartOfSpeech = namedtuple('PartOfSpeech', ['nltk', 'descrip', 'lk'])
def pos(nltk, descrip, lk): return PartOfSpeech(nltk, descrip, lk)

INVENTORY = [
    pos('CC', 'coordinating conjunction', 'conj'),
    pos('CD', 'cardinal digit', ''),
    pos('DT', 'determiner', 'quant det'),
    pos('EX', 'existential there', ''),
    pos('FW', 'foreign word', ''),
    pos('IN', 'preposition/subordinating conjunction', 'prep'),
    pos('JJ', 'adjective', 'ad'),
    pos('JJR', 'adjective, comparative', 'ad'),
    pos('JJS', 'adjective, superlative', 'ad'),
    pos('LS', 'list marker', 'punct'),
    pos('MD', 'modal (could, will)', 'modal'),
    pos('NN', 'noun, singular or mass', 'n'),
    pos('NNS', 'noun plural', 'n'),
    pos('NNP', 'proper noun, singular', 'n'),
    pos('NNPS', 'proper noun, plural', 'n'),
    pos('PDT', 'predeterminer (all, both)', 'quant'),
    pos('POS', 'possessive ending', ''),
    pos('PRP', 'personal pronoun', 'pronoun'),
    pos('PRP$', 'possessive pronoun (my, our)', ''),
    pos('RB', 'adverb', 'ad'),
    pos('RBR', 'adverb, comparative', 'ad'),
    pos('RBS', 'adverb, superlative', 'ad'),
    pos('RP', 'particle (about)', ''),
    pos('TO', 'to', 'prep'),
    pos('UH', 'interjection', 'inter'),
    pos('VB', 'verb base form', 'v'),
    pos('VBD', 'verb past tense', 'v'),
    pos('VBG', 'verb gerund/present participle', 'v'),
    pos('VBN', 'verb past participle', 'v'),
    pos('VBP', 'verb non-3rd person singular present', 'v'),
    pos('VBZ', 'verb 3rd person singular present', 'v'),
    pos('WDT', 'wh-determiner (which, that)', 'det'),
    pos('WP', 'wh-pronoun (who, what)', 'pronoun'),
    pos('WP$', 'possessive wh-pronoun (whose)', ''),
    pos('WRB', 'wh-adverb (where, when)', '')
]

PLACEHOLDER = pos('~', 'placeholder', '')

def find_by_nltk(nltk):
    i = bisect.bisect_left(INVENTORY, nltk, key=lambda p: p.nltk)
    if i != len(INVENTORY) and INVENTORY[i].nltk == nltk:
        return INVENTORY[i]
