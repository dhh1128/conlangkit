import bisect

irregular_past_parts = [
    ("awoken", "awake"),
    ("been", "be"),
    ("begotten", "beget"),
    ("begun", "begin"),
    ("bent", "bend"),
    ("bitten", "bite"),
    ("bought", "buy"),
    ("bound", "bind"),
    ("broken", "break"),
    ("built", "build"),
    ("burnt", "burn"),
    ("caught", "catch"),
    ("chosen", "choose"),
    ("done", "do"),
    ("driven", "drive"),
    ("dwelt", "dwell"),
    ("eaten", "eat"),
    ("fallen", "fall"),
    ("fed", "feed"),
    ("felt", "feel"),
    ("fled", "flee"),
    ("flown", "fly"),
    ("forgotten", "forget"),
    ("found", "find"),
    ("frozen", "freeze"),
    ("given", "give"),
    ("gone", "go"),
    ("ground", "grind"),
    ("heard", "hear"),
    ("held", "hold"),
    ("hidden", "hide"),
    ("knelt", "kneel"),
    ("known", "know"),
    ("laid", "lay"),
    ("lain", "lie"),
    ("lit", "light"),
    ("meant", "mean"),
    ("overcome", "overcome"),
    ("overthrown", "overthrow"),
    ("paid", "pay"),
    ("pleaded", "plead"),
    ("proven", "prove"),
    ("ridden", "ride"),
    ("risen", "rise"),
    ("sawn", "saw"),
    ("seen", "see"),
    ("sent", "send"),
    ("shaken", "shake"),
    ("shone", "shine"),
    ("shorn", "shear"),
    ("shot", "shoot"),
    ("shown", "show"),
    ("slain", "slay"),
    ("slept", "sleep"),
    ("slid", "slide"),
    ("smelt", "smell"),
    ("sown", "sow"),
    ("spent", "spend"),
    ("spilt", "spill"),
    ("spoilt", "spoil"),
    ("spoken", "speak"),
    ("stolen", "steal"),
    ("stood", "stand"),
    ("stridden", "stride"),
    ("struck", "strike"),
    ("stuck", "stick"),
    ("sung", "sing"),
    ("swept", "sweep"),
    ("swollen", "swell"),
    ("sworn", "swear"),
    ("swum", "swim"),
    ("taken", "take"),
    ("taught", "teach"),
    ("thought", "think"),
    ("thrown", "throw"),
    ("told", "tell"),
    ("torn", "tear"),
    ("understood", "understand"),
    ("wept", "weep"),
    ("woken", "wake"),
    ("won", "win"),
    ("worn", "wear"),
    ("wound", "wind"),
    ("written", "write"),
]

irregular_past = [
    ("ate", "eat"),
    ("began", "begin"),
    ("begat", "beget"),
    ("bit", "bite"),
    ("bought", "buy"),
    ("broke", "break"),
    ("brought", "bring"),
    ("built", "build"),
    ("came", "come"),
    ("caught", "catch"),
    ("chose", "choose"),
    ("dealt", "deal"),
    ("did", "do"),
    ("drank", "drink"),
    ("dreamt", "dream"),
    ("drew", "draw"),
    ("drove", "drive"),
    ("fed", "feed"),
    ("fell", "fall"),
    ("felt", "feel"),
    ("flew", "fly"),
    ("forgave", "forgive"),
    ("forgot", "forget"),
    ("fought", "fight"),
    ("found", "find"),
    ("froze", "freeze"),
    ("gave", "give"),
    ("got", "get"),
    ("grew", "grow"),
    ("had", "have"),
    ("heard", "hear"),
    ("held", "hold"),
    ("hid", "hide"),
    ("hit", "hit"),
    ("hung", "hang"),
    ("hurt", "hurt"),
    ("kept", "keep"),
    ("knew", "know"),
    ("laid", "lay"),
    ("led", "lead"),
    ("left", "leave"),
    ("lent", "lend"),
    ("let", "let"),
    ("lit", "light"),
    ("lost", "lose"),
    ("made", "make"),
    ("meant", "mean"),
    ("met", "meet"),
    ("paid", "pay"),
    ("put", "put"),
    ("ran", "run"),
    ("rang", "ring"),
    ("read", "read"),
    ("rode", "ride"),
    ("rose", "rise"),
    ("said", "say"),
    ("sang", "sing"),
    ("sank", "sink"),
    ("sat", "sit"),
    ("saw", "see"),
    ("sent", "send"),
    ("set", "set"),
    ("shone", "shine"),
    ("shook", "shake"),
    ("shot", "shoot"),
    ("showed", "show"),
    ("shut", "shut"),
    ("slept", "sleep"),
    ("slew", "slay"),
    ("slid", "slide"),
    ("smelt", "smell"),
    ("sold", "sell"),
    ("sought", "seek"),
    ("sowed", "sow"),
    ("spat", "spit"),
    ("spent", "spend"),
    ("spoke", "speak"),
    ("spread", "spread"),
    ("spun", "spin"),
    ("stole", "steal"),
    ("stood", "stand"),
    ("struck", "strike"),
    ("stuck", "stick"),
    ("stung", "sting"),
    ("stunk", "stink"),
    ("swam", "swim"),
    ("swept", "sweep"),
    ("swore", "swear"),
    ("swung", "swing"),
    ("taught", "teach"),
    ("thought", "think"),
    ("threw", "throw"),
    ("told", "tell"),
    ("took", "take"),
    ("tore", "tear"),
    ("understood", "understand"),
    ("was", "be"),
    ("went", "go"),
    ("wept", "weep"),
    ("were", "be"),
    ("withdrew", "withdraw"),
    ("woke", "wake"),
    ("won", "win"),
    ("wore", "wear"),
    ("wound", "wind"),
    ("wrote", "write"),
    ("wrung", "wring"),
]

def find_regular(pairs, irregular):
    index = bisect.bisect_left(pairs, (irregular, ""))
    if index != len(pairs):
        found = pairs[index]
        if found[0] == irregular:
            return found[1]
        

vowels = "aeiou"
two_vowels_plus_cons_with_silent_e = ['iev', 'eiv', 'eas', 'aus', 'uad', 'iat']

def likely_silent_e(verb_root):
    if len(verb_root) >= 3:
        if verb_root[-1] not in vowels:
            if verb_root[-2:] == "nc": return True
            if verb_root[-2] in vowels:
                if verb_root[-3:] in two_vowels_plus_cons_with_silent_e:
                    return True                
                return verb_root[-3] not in vowels
    return False

def bfr(word, pos):
    """
    Generate possible base forms of a word, and a new part of speech, given
    the inflected word and its nltk part of speech.

    This algorithm is very crude. It only aims to increase the success
    of glossary lookup a modest amount.
    """
    if pos == 'VBD': # verb past tense: gave, walked
        regular = find_regular(irregular_past, word)
        if regular: return (regular, 'v')
        if word.endswith('ed'):
            cutoff = -1 if likely_silent_e(word[:-2]) else -2 
            return (word[:cutoff], 'v')
    elif pos == 'VBG': # verb gerund/present participle: walking
        if word.endswith('ing'):
            word = word[:-3]
            # Undo doubled consonants if present (e.g., swimming, hitting)
            if word[-1] == word[-2]: return (word[:-1], 'v')
            # Add silent e in places where it likely belongs.
            if likely_silent_e(word): return (word + 'e', 'v')
            return (word, 'v')
    elif pos == 'VBN': # verb past participle: given, walked
        regular = find_regular(irregular_past_parts, word)
        if regular: return (regular, 'v')
        if word.endswith('ed'): 
            cutoff = -1 if likely_silent_e(word[:-2]) else -2 
            return (word[:cutoff], 'v')
    elif pos == 'VBP': # verb non-3rd person singular present: walk
        if word in ['are', 'am']: return ('be', 'v')
    elif pos == 'VBZ': # verb 3rd person singular present: walks
        if word.endswith('s'):
            return ('be', 'v') if word == 'is' else (word[:-1], 'v')
    elif pos == 'RB':
        if word.endswith('ly'): return (word[:-2], 'ad')
    elif pos == 'JJR':
        if word.endswith('er'):
            word = word[:-2]
            return (word[:-1], 'ad') if word[-1] == word[-2] else (word, 'ad')
    elif pos == 'JJS':
        if word.endswith('est'): return (word[:-3], 'ad')
    elif pos == 'JJ':
        if word.endswith('ly'): return (word[:-2], 'n')
        if word.endswith('ic'): return (word[:-2], 'n')
        if word.endswith('ish'): return (word[:-3], 'n')
        if word.endswith('like'): return (word[:-4], 'n')	
        if word.endswith('y'): return (word[:-1], 'n')
        if word.endswith('ing'): return (word[:-3], 'v')
    elif pos.startswith('NN'):
        modified = False
        if word.endswith('ies'): return (word[:-3] + 'y', 'n') #bodies
        if word.endswith('s') and pos == 'NNS': 
            word = word[:-1] #smiles
            modified = True
        if word.endswith('tion'): return (word[:-4], 'v') #creation
        if word.endswith('or'): return (word[:-2], 'v') #sailor
        if word.endswith('er'): return (word[:-2], 'v') #farmer
        if modified: return (word, 'n')
    return None, None

