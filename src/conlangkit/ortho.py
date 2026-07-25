import bisect
from typing import List, Dict, Tuple

# Some typedefs to make code clearer.
Item = str
ForeignItem = Item
SelfItem = Item
ForeignText = str
SelfText = str

# If both alphabets always mapped a single character in their own
# alphabet to a single character in the other alphabet, transcribing
# would be trivial. We could use a dict(char, char) in each direction.
# But what actually happens, often, is that we have many-to-one and
# one-to-many mappings. This means we need an efficient algorithm that,
# when transliterating, is greedy: it consumes as many chars as possible
# in the source, each time it does a mapping. The data structure that
# best supports this is an array (ScanMatrix) of sorted arrays (ScanSets).
# ScanSets are optimized for binary search. Each ScanSet contains tuples
# (ItemPairs) that map a sequence in the source orthography to a sequence
# in the target orthography. All the ItemPairs in a given ScanSet have
# a source sequence (item 0 in the tuple) of the same length, N. The
# ItemPairs are sorted alphabetically within the ScanSet. So we end up
# with a ScanMatrix that looks like this:
#
# [0] = ScanSet with of all source sequences with length N = 1
# [1] = ScanSet with all source sequences with length N = 2
# [2] = ScanSet with all source sequences with length N = 3
# etc.
# 
# Given this matrix, we can transliterate by starting at the high index
# of the matrix and walking backward, toward 0, checking to see if the
# we can find some text to consume. If we are at index 2 in the matrix,
# we are looking at the next 3 characters in the text, doing a binary
# search of matrix[2] to find a tuple where the first member of the tuple
# matches the 3-character fragment. If we don't find any matches in
# matrix[2], then we move to matrix[1], extract the 2-character fragment,
# do a binary search for that fragment in the new ScanSet, and so forth.
ItemPair = Tuple[Item, Item]
ScanSet = List[ItemPair]
ScanMatrix = List[ScanSet]

def _dict_to_scan_matrix(x: Dict[Item, Item]) -> ScanMatrix:
    matrix: ScanMatrix = []
    for key, value in x.items():
        index_in_matrix = len(key) - 1
        # Never leave gaps in the matrix.
        while len(matrix) - 1 < index_in_matrix:
            matrix.append([])
        scan_set = matrix[index_in_matrix]
        scan_set.append((key, value))
    # Now, sort all the ScanSets alphabetically so we can do a binary
    # search for a fragment that matches the first member of the tuple.
    for scanset in matrix:
        scanset.sort(key=lambda x: x[0])
    return matrix

def _transliterate(txt: str, matrix: ScanMatrix, subst) -> str:
    out = ''
    i = 0
    n = len(txt)
    while i < n:
        remaining = n - i
        found = False
        for j in range(min(remaining, len(matrix)), 0, -1):
            scanset = matrix[j - 1]
            if scanset:
                fragment = txt[i:i+j]
                k = bisect.bisect_left(scanset, fragment, key=lambda x: x[0])
                if k < len(scanset) and scanset[k][0] == fragment:
                    out += scanset[k][1]
                    i += j
                    found = True
                    break
        if not found:
            out += subst(fragment) if subst else fragment
            i += 1
    return out

class Orthography:
    def __init__(self, mappings: Dict[ForeignItem, SelfItem]):
        self._foreign_to_self = _dict_to_scan_matrix(mappings)
        self._self_to_foreign = _dict_to_scan_matrix({value: key for key, value in mappings.items()})
        self._foreign_items = sorted(mappings.keys())
        self._items = sorted(mappings.values())

    @property
    def items(self) -> List[SelfItem]:
        """
        What is the set of items in this orthography? 
        """
        return self._items
    
    @property
    def foreign_items(self) -> List[ForeignItem]:
        """
        What is the set of foreign items that this orthography can map? 
        """
        return self._foreign_items

    def from_foreign(self, uni: ForeignText, subst=None) -> SelfText:
        """
        Convert from a universal alphabet to this orthography.

        The subst param is a function that's called whenver an unmappable
        character is found. It returns text that is substituted for what
        was unmappable. If subst is None, the unmappable character is retained. 
        """
        return _transliterate(uni, self._foreign_to_self, subst)
    
    def to_foreign(self, txt, subst=None):
        """
        Convert from a universal alphabet to this orthography.

        The subst param is a function that's called whenver an unmappable
        character is found. It returns text that is substituted for what
        was unmappable. If subst is None, the unmappable character is retained. 
        """
        return _transliterate(txt, self._self_to_foreign, subst)
