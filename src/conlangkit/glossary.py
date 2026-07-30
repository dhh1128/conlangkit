import bisect
import os
import re

NARROWER_EQUIV = ">"
BROADER_EQUIV = "<"
ROUGH_EQUIV = "~"
EXPLAINED_EQUIV = ":"
EXACT_EQUIV = ""
EQUIV_CHARS = NARROWER_EQUIV + BROADER_EQUIV + ROUGH_EQUIV + EXPLAINED_EQUIV
EQUIVS_PAT = re.compile(r"\s*([" + EQUIV_CHARS + r"])?(.+?)(/|$)")
COLUMNS = ["lemma", "tags", "definition", "notes"]
COLUMN_COUNT = len(COLUMNS)
COLUMN_SEP = " | "
HEADER = COLUMN_SEP.join(COLUMNS)
DIVIDER = re.sub("[a-zA-Z]", "-", HEADER)
DIVIDER_PAT = re.compile(r"\s*" + r"\s*\|\s*".join(["-+"] * len(COLUMNS)) + r"\s*")

# A definition column may contain a literal '/' (which would otherwise be read as
# the equiv separator) or a literal '\'. On disk these are backslash-escaped:
# '\/' is a literal slash, '\\' a literal backslash. In memory, DefnItem.value is
# always unescaped, so search/gloss/stats operate on the real text; serialization
# re-escapes. Existing slash-free glossaries (Kila, martian) are untouched — they
# contain no '\', so protection/restoration and escaping are all no-ops for them.
_SENT_BACKSLASH = "\x00"  # placeholder for an escaped '\\' while splitting on '/'
_SENT_SLASH = "\x01"  # placeholder for an escaped '\/' while splitting on '/'


def _protect(txt):
    """Hide escaped sequences so only genuine '/' separators remain visible."""
    return txt.replace("\\\\", _SENT_BACKSLASH).replace("\\/", _SENT_SLASH)


def _restore(txt):
    """Turn placeholders back into the literal characters they stood for."""
    return txt.replace(_SENT_SLASH, "/").replace(_SENT_BACKSLASH, "\\")


def _escape(value):
    """Escape a literal value for the definition column (backslash first)."""
    return value.replace("\\", "\\\\").replace("/", "\\/")


class DefnItem:
    def __init__(self, txt):
        ec = txt[0]
        if ec in EQUIV_CHARS:
            self.kind = ec
            self.value = txt[1:].lstrip()
        else:
            self.kind = EXACT_EQUIV
            self.value = txt.lstrip()

    @property
    def gloss(self):
        i = self.value.find("(")
        return self.value if i == -1 else self.value[:i].rstrip()

    @property
    def explanation(self):
        i = self.value.find("(")
        if i > -1:
            j = self.value.find(")", i + 1)
            if j == -1:
                j = len(self.value)
            return self.value[i + 1 : j]
        return ""

    def __str__(self):
        return self.kind + _escape(self.value)

    def __lt__(self, other):
        if self.kind == EXACT_EQUIV:
            if other.kind == EXACT_EQUIV:
                return self.value < other.value
            return True
        else:
            if other.kind == EXACT_EQUIV:
                return False
            i = EQUIV_CHARS.index(self.kind)
            j = EQUIV_CHARS.index(other.kind)
            return True if i < j else (False if j < i else self.value < other.value)


class Defn:
    def __init__(self, txt):
        self.equivs = []
        self.parse(txt)
        self._txt = None

    def parse(self, txt):
        txt = _protect(txt)  # only genuine '/' separators remain visible
        while txt:
            m = EQUIVS_PAT.match(txt)
            if m:
                prefix = m.group(1) if m.group(1) else ""
                self.equivs.append(DefnItem(_restore(prefix + m.group(2).strip())))
                txt = txt[m.end() :]
            else:
                self.equivs.append(DefnItem(_restore(txt)))
                break
        self.equivs.sort()

    def __str__(self):
        if self._txt is None:
            self._txt = " / ".join([str(e) for e in self.equivs])
        return self._txt


class Entry:
    def __init__(self, fields):
        if isinstance(fields, str):
            fields = [f.strip() for f in fields.split("|")]
        self.lemma = fields[0]
        self.tags = fields[1].split() if isinstance(fields[1], str) else fields[1]
        self.defn = Defn(fields[2])
        if len(fields) > 3 and fields[3]:
            self.notes = fields[3]
        else:
            self.notes = ""

    def __lt__(self, other):
        return self.lemma < other.lemma

    def __str__(self):
        suffix = "" if self.notes is None else COLUMN_SEP + self.notes
        return (
            self.lemma
            + COLUMN_SEP
            + " ".join(sorted(self.tags))
            + COLUMN_SEP
            + str(self.defn)
            + suffix
        )


def _is_header(entry: Entry) -> bool:
    return entry.lemma == COLUMNS[0]


_DIVIDER_LEX_PAT = re.compile("-{2,}$")


def _is_divider(entry: Entry) -> bool:
    return bool(_DIVIDER_LEX_PAT.match(entry.lemma))


class MatchExpr:
    def __init__(self, expr, ignore_case: bool = False):
        self.expr = expr
        self.ignore_case = ignore_case
        wildcards = [expr.find(c) for c in "*?!"]
        NO_WILDCARD = 1000000000
        wc1 = NO_WILDCARD
        for i in range(len(wildcards)):
            if wildcards[i] > -1:
                wc1 = min(wc1, wildcards[i])
        self.first_wildcard = -1 if wc1 == NO_WILDCARD else wc1
        self._regex = (
            None
            if self.first_wildcard == -1
            else re.compile(
                expr.replace("?", ".")
                .replace("*", ".*?")
                .replace("!", r"\b")
                .replace("(", r"\(")
                .replace(")", r"\)"),
                re.IGNORECASE if ignore_case else 0,
            )
        )

    @property
    def wildcarded(self):
        return self.first_wildcard != -1

    @property
    def starter(self) -> str:
        return self.expr[: self.first_wildcard] if self.wildcarded else self.expr

    def __str__(self):
        return self.expr

    def matches(self, txt) -> bool:
        if self._regex:
            return bool(self._regex.match(txt))
        if self.ignore_case:
            return self.expr.casefold() == txt.casefold()
        return self.expr == txt


SCOPED_SEARCH_EXPR = re.compile(
    r"(?:^|\s)(l(?:e(?:m(?:m(?:a)?)?)?)?|t(?:a(?:g(?:s)?)?)?|d(?:e(?:f(?:n)?)?)?|n(?:o(?:t(?:e(?:s)?)?)?)?):"
)


class SearchExpr:
    def __init__(self, expr, ignore_case: bool = False):
        self.ignore_case = ignore_case
        criteria = []
        chunks = SCOPED_SEARCH_EXPR.split(expr)
        # split() yields [text, scope, text, scope, text, ...] — an odd count,
        # with the recognized scopes in the captured odd positions. The walk below
        # reads (scope, value) pairs, so chunks[0] always needs a synthetic scope
        # in front of it, even when it is empty (a query that opens with a scope).
        # Skipping it leaves an odd count and the walk runs off the end.
        # Accept text without a field prefix. The meaning of this is that
        # the user wants to search in both the lemma and the definition,
        # unless one of those other fields is specified explicitly.
        first_chars = [x[0] for x in chunks if ":" in x]
        if "l" in first_chars:
            if "d" in first_chars:
                raise ValueError("Bad search syntax.")
            chunks.insert(0, "d:")
        elif "d" in first_chars:
            chunks.insert(0, "l")
        else:
            chunks.insert(0, "x")

        i = 0
        while i < len(chunks):
            m = chunks[i + 1].strip()
            if m:
                criteria.append((chunks[i][0], MatchExpr(m, ignore_case)))
            i += 2
        self.criteria = criteria

    def fuzzify(self):
        changed = False
        for i in range(len(self.criteria)):
            field = self.criteria[i][0]
            if field != "t":
                matcher = self.criteria[i][1]
                expr = matcher.expr
                if matcher.first_wildcard != 0:
                    expr = "*!" + expr
                expr = expr.replace(" ", "*")
                if expr[-1] not in "*?!":
                    expr += "*"
                if expr != matcher.expr:
                    changed = True
                    self.criteria[i] = (field, MatchExpr(expr, self.ignore_case))
        return changed

    def __str__(self):
        return " ".join([f"{f}:{m}" for f, m in self.criteria])

    @property
    def starter(self):
        for field, matcher in self.criteria:
            if field == "l":
                return matcher.starter
        return ""

    def matches(self, entry: Entry) -> bool:
        for field_selector, match_expr in self.criteria:
            possibilities = 2 if field_selector == "x" else 1
            # First look in the simple fields.
            text = None
            if field_selector in "lx":
                text = entry.lemma
            elif field_selector == "n":
                text = entry.notes
            if text and not match_expr.matches(text):
                possibilities -= 1
            # Now look in tags, which might be multiple.
            if field_selector == "t":
                found = False
                for tag in entry.tags:
                    if match_expr.matches(tag):
                        found = True
                        break
                if not found:
                    possibilities -= 1
            # Now look in the definition, which has subfields.
            if possibilities and (field_selector in "dx"):
                found = False
                for defn_item in entry.defn.equivs:
                    if match_expr.matches(defn_item.value):
                        found = True
                        break
                if not found:
                    possibilities -= 1
            if possibilities < 1:
                return False
        return True


class Glossary:
    """A sorted collection of glossary entries.

    Lemma comparison — used for sorting, insertion position, and lookup — is
    **case-sensitive (byte order)** by design: conlangkit targets writing systems
    where casing rules are not English and 'A'/'a' may be unrelated letters, so
    case-folding is not assumed. Callers must therefore use each lemma in its
    canonical case (e.g. `AID` and `aid` are distinct entries)."""

    def __init__(self):
        self.pre = ""
        self.fname = None
        self.entries = []
        self._unsaved = False
        self.post = ""
        self._stats = None

    @property
    def stats(self):
        if self._stats is None:

            def increment(accumulator, key, how_much=1):
                if key not in accumulator:
                    accumulator[key] = 0
                accumulator[key] += how_much

            def tally_defs():
                equivs = {}
                root = {}
                tags = {}
                for entry in self.entries:
                    increment(root, "unique meanings", len(entry.defn.equivs))
                    for tag in entry.tags:
                        increment(tags, tag)
                    for equiv in entry.defn.equivs:
                        kind = equiv.kind if equiv.kind else "simple equiv"
                        increment(equivs, kind)
                root["tags"] = tags
                root["meanings"] = equivs
                root["unique tags"] = len(tags.keys())
                return root

            self._stats = tally_defs()
            self._stats["unique entries"] = len(self.entries)
        return self._stats

    @property
    def lemma_count(self):
        return len(self.entries)

    @staticmethod
    def load(fname):
        g = Glossary()
        g.fname = os.path.normpath(os.path.abspath(fname))
        with open(g.fname) as f:
            lines = f.readlines()
        pre = True
        found_header = False
        found_divider = False
        found_nonblank_post = False
        n = 0
        for line in lines:
            stripped = line.strip()
            n += 1
            entry = "|" in stripped
            if entry:
                e = None
                try:
                    e = Entry(stripped)
                    pre = False
                except Exception:
                    entry = False
                    if g.lemma_count:
                        pre = False
                if e:
                    if _is_header(e):
                        if found_header or found_divider:
                            raise Exception(f"Didn't expect header on line {n}.")
                        found_header = True
                    elif _is_divider(e):
                        if found_divider or not found_header:
                            raise Exception(f"Didn't expect divider on line {n}.")
                        found_divider = True
                    else:
                        if found_nonblank_post:
                            raise Exception(f"Didn't expect a new entry on line {n}.")
                        g.entries.append(e)
                        g.post = ""
            if not entry:
                if pre:
                    g.pre += line
                else:
                    if line.strip():
                        found_nonblank_post = True
                    g.post += line
        g.entries.sort()
        return g

    def save(self, fname=None, handle=None, force: bool = False):
        force = force or bool(handle)
        if fname is None:
            fname = self.fname
        else:
            fname = os.path.normpath(os.path.abspath(fname))
            if self.fname is None:
                self.fname = fname
            else:
                force = fname != self.fname
        if force or self._unsaved:
            f = handle
            if not f:
                f = open(fname, "w")
            try:
                if self.pre.strip():
                    f.write(self.pre)
                f.write(HEADER + "\n" + DIVIDER + "\n")
                for entry in self.entries:
                    f.write(str(entry) + "\n")
                if self.post.strip():
                    f.write(self.post)
                if not force:
                    self._unsaved = False
            finally:
                if not handle:
                    f.close()
            return True

    def find(self, expr, max_hits=5, exclude=None, try_fuzzy=False, ignore_case=False):
        """Search entries with a SearchExpr (or its string form). Matching is
        case-sensitive (see the class docstring); use canonical-case terms.

        Pass ``ignore_case=True`` to fold case instead. That is for searching
        *prose* — definitions and notes, where a capitalized query would otherwise
        miss silently. It is opt-in because lemma identity is byte-exact by design.
        Folding also costs the sorted-scan shortcut (below), so it scans every entry.
        When ``expr`` is already a SearchExpr, its own setting wins.
        """
        hits = []
        s_expr = expr if isinstance(expr, SearchExpr) else SearchExpr(expr, ignore_case)
        # The starter drives two byte-order shortcuts: bisect to the first candidate,
        # and stop once the scan passes where a match could be. Case-folded matches do
        # not sit where byte order predicts ('BANANA' bisects ahead of 'apple'), so
        # folding gives both up — an empty starter disables them together.
        initial_search = "" if s_expr.ignore_case else s_expr.starter
        index = (
            bisect.bisect_left(self.entries, initial_search, key=lambda x: x.lemma)
            if initial_search
            else 0
        )
        while index < self.lemma_count and max_hits != 0:
            entry = self.entries[index]
            if s_expr.matches(entry):
                if not exclude or (entry not in exclude):
                    hits.append(entry)
                    max_hits -= 1
            elif initial_search and entry.lemma > s_expr.starter:
                break
            index += 1
        # Now that we've found hits that start with expr, look
        # for ones that just contain it. The purpose of always
        # doing a fuzzy search is not simply to make finding easier,
        # but to make sure that as glossary edits occur, an awareness
        # of similar words is encouraged.
        if try_fuzzy and max_hits:
            if s_expr.fuzzify():
                hits += self.find(s_expr, max_hits, hits)

        return hits

    def insert(self, entry: Entry):
        index = bisect.bisect_left(self.entries, entry.lemma, key=lambda x: x.lemma)
        self.entries.insert(index, entry)
        self._unsaved = True
        self._stats = None

    def remove(self, entry: Entry):
        self.entries.remove(entry)
        self._unsaved = True
        self._stats = None

    def update(self, entry: Entry, lemma=None, tags=None, defn=None, notes=None):
        """Edit an existing entry in place. Any field left None is unchanged.
        A changed lemma re-sorts the entry so ``entries`` stays ordered. Marks the
        glossary unsaved and invalidates the stats cache. Returns the entry.
        The caller owns collision policy (a lemma rename is not checked here)."""
        lemma_changed = lemma is not None and lemma != entry.lemma
        if lemma is not None:
            entry.lemma = lemma
        if tags is not None:
            entry.tags = tags.split() if isinstance(tags, str) else list(tags)
        if defn is not None:
            entry.defn = defn if isinstance(defn, Defn) else Defn(defn)
        if notes is not None:
            entry.notes = notes
        if lemma_changed:
            # A new lemma sorts differently; re-position to keep entries ordered.
            self.entries.remove(entry)
            self.insert(entry)  # sets _unsaved + invalidates _stats
        else:
            self._unsaved = True
            self._stats = None
        return entry
