import nltk
try:
    from nltk.corpus import wordnet
except LookupError:
    print("Downloading NLTK resources...")
    nltk.download('wordnet', quiet=True)
    from nltk.corpus import wordnet


# Download NLTK resources if needed.
#if not nltk.data.find('corpora/wordnet'):
#    nltk.download('wordnet')

def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append(lemma.name())
    return set(synonyms)

def get_related_words(word):
    related_words = []
    for synset in wordnet.synsets(word):
        related_words.extend([word for word in synset.hyponyms()])
        related_words.extend([word for word in synset.hypernyms()])
    return set(related_words)

if __name__ == '__main__':
    print(get_synonyms('good'))
    print(get_related_words('good'))