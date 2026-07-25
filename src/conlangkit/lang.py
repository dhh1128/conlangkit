import os
import json

from .glossary import Glossary

import importlib.util

def _import_module_from_path(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

CFG_NAME = 'cfg.json'
GLOSSARY_NAME = 'glossary.md'

class Lang:
    def __init__(self, path):
        self.path = os.path.normpath(os.path.abspath(path))
        self.name = os.path.split(self.path)[1]
        self._syl = None
        self._advise_func = 0
        if os.path.isfile(self.cfg_path):
            with open(self.cfg_path, 'rt') as f:
                self.cfg = json.loads(f.read())
        else:
            self.cfg = {}
        self._glossary = None

    @property
    def advise_module_path(self):
        return os.path.join(self.path, 'advise.py')
    
    @property
    def advise_func(self):
        if self._advise_func == 0:
            amp = self.advise_module_path
            if os.path.isfile(amp):
                module = _import_module_from_path('advise', amp)
                self._advise_func = module.advise
            else:
                self._advise_func = None
        return self._advise_func

    @property
    def glossary(self):
        if not self._glossary:
            fname = self.gloss_path
            if os.path.isfile(fname):
                self._glossary = Glossary.load(fname)
            else:
                self._glossary = Glossary()
                self.path = os.path.dirname(fname)
        return self._glossary

    @property
    def cfg_path(self):
        return os.path.join(self.path, CFG_NAME)
    
    @property
    def gloss_path(self):
        return os.path.join(self.path, GLOSSARY_NAME)
    
    @property
    def sylpats(self):
        return self.cfg.get('sylpats', ['V', 'CV'])

    @property
    def vowels(self):
        return self.cfg.get('vowels', ['a', 'i'])

    @property
    def consonants(self):
        return self.cfg.get('consonants', ['k', 't', 'm'])

    @property
    def syllables(self):
        # _FIXgenerate_syllables was removed because it produced phonotactically
        # incorrect syllables. The replacement (syllable.candidates()) requires
        # IPA phoneme strings and has not yet been wired up here.
        raise NotImplementedError(
            "Lang.syllables is not implemented. The old naive syllable generator "
            "was removed. Use syllable.candidates() directly, passing IPA vowels, "
            "consonants, and patterns."
        )
