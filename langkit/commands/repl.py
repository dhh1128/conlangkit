import os
import re
import traceback

from ..ui import *
from ..glossary import Entry, Defn, Glossary
from ..tcoach import *


def find(ctx, expr, try_fuzzy=True):
    ctx.last_find_expr = expr
    ctx.hits = ctx.lang.glossary.find(expr, try_fuzzy=try_fuzzy)

def show_entry(e, num=None):
    if num:
        cwrite(f"\n{num}", PROMPT_COLOR)
        write(". ")
    cwrite(e.lemma, LEX_COLOR)
    write(" (")
    cwrite(' '.join(e.tags), TAG_COLOR)
    write(")")
    for equiv in e.defn.equivs:
        cwrite('\n   * ', EQUIV_COLOR)
        write(equiv)
    if e.notes:
        write('\n')
        cwrite(wrap_line_with_indent('   # ' + e.notes), NOTE_COLOR)
    print('')

def show_hits(ctx, which=None, with_number=True):
    if not which:
        which = ctx.hits
    if which:
        i = 1
        for hit in which:
            show_entry(hit, i if with_number else None)
            i += 1
        return True

def delete(ctx, entry):
    g = ctx.lang.glossary
    g.remove(entry)
    g.save(force=True)
    print(f"Deleted {entry.lemma}.")

def edit(ctx, entry):
    g = ctx.lang.glossary
    # Collect edits into a dict and apply them all at once via Glossary.update,
    # which maintains sort order and invalidates the stats cache. Accumulating
    # first (rather than mutating field-by-field) also means a mid-edit
    # KeyboardInterrupt leaves the entry untouched — no undo needed.
    changes = {}
    try:
        write('\n')
        new = prompt_options(f"   lex: {entry.lemma}")
        if new and new != entry.lemma:
            redundant = g.find(f'l:{new}')
            if redundant:
                warn("Edit would overwrite {lex} entry that already exists.")
                return
            changes['lemma'] = new
        new = prompt_options(f"   tags: {' '.join(entry.tags)}")
        if new: changes['tags'] = new.split()
        new = prompt_options(f"   defn: {entry.defn} (/ to append)")
        if new:
            if new.startswith('/'):
                new = str(entry.defn) + ' ' + new
            changes['defn'] = Defn(new)
        notes = entry.notes if entry.notes else '.'
        new = prompt_options(f"   notes: {notes} (. = none)")
        if new:
            if new == '.':
                if entry.notes:
                    changes['notes'] = ''
            else:
                changes['notes'] = new
    except KeyboardInterrupt:
        changes = {}   # nothing applied yet; discard pending edits
    print()
    if changes:
        g.update(entry, **changes)
        g.save(force=True)
        show_hits(ctx, [entry], with_number=False)
    else:
        print("Abandoned edit.")

def arg_else_prompt(args, n, prompt):
    if len(args) > n:
        arg = args[n]
        print(f"{prompt}> {arg}")
        return arg
    return prompt_options(prompt)

def add(ctx, args):
    g = ctx.lang.glossary
    entry = None
    try:
        lemma = arg_else_prompt(args, 0, "   lex")
        if lemma:
            redundant = g.find(f'l:{lemma}!')
            if redundant:
                show_hits(ctx, redundant, with_number=False)
                if warn_confirm("Similar words exist. Continue?"):
                    redundant = None
            if not redundant:
                tags = arg_else_prompt(args, 1, "   tags")
                if tags:
                    defn = arg_else_prompt(args, 2, "   defn")
                    if defn:
                        # If the item has a part of speech that doesn't typically
                        # get inflected, then when we look up synonyms, look
                        # only for ones with the same part of speech.
                        pos_criterion = '' if tags[0] in 'nva' else f"t:{tags} "
                        redundant = g.find(f'{pos_criterion}d:*!{defn}')
                        if redundant:
                            show_hits(ctx, redundant, with_number=False)
                            if warn_confirm("There may already be a synonym. Continue?"):
                                redundant = None
                        if not redundant:
                            notes = arg_else_prompt(args, 3, "   notes")
                            entry = Entry((lemma, tags, defn, notes))
    except KeyboardInterrupt:
        pass
    print()
    if entry:
        g.insert(entry)
        g.save()
        show_hits(ctx, [entry], with_number=False)
    else:
        print("Abandoned add.")

def show_help():
    doc = """
find <expr> - lookup data in glossary

  expr can be a simple string to query lemma+def, or can reference specific fields (lemma: pos: defn: notes: or short forms thereof) 

add [lemma [pos [defn [notes]]]] - add a glossary entry

edit [number or lemma] - edit a glossary entry

del [number or lemma] - delete a glossary entry

trans [fname or sentence] - provide coaching on possible translations of text

scan [sd:scan directory] [sfp:scan filename pattern] regex - scan files for text

stats

quit
"""
    lines = doc.strip().splitlines()
    for line in lines:
        if not line.startswith(' '):
            if ' ' in line:
                cmd, rest = line.split(' ', 1)
                rest = ' ' + rest
                cwrite(cmd, CMD_COLOR)
                cprint(wrap_line_with_indent(rest, indent="    ", first_width=-1 * (len(cmd) + 1)))
            else:
                cprint(line, CMD_COLOR)
        else:
            print(wrap_line_with_indent(line))

def show_stats(ctx):
    s = ctx.lang.glossary.stats
    def write_section(name, color):
        label = f"unique {name}"
        write(f"{label}: ")
        n = s[label]
        cprint(f"{n}", color)
        detail = s.get(name)
        if detail:
            keys = sorted(detail.keys())
            for item in keys:
                cwrite(f"  {item}", color)
                print(f": x{detail[item]}")
    print()
    write_section("entries", LEX_COLOR)
    write_section("tags", TAG_COLOR)
    write_section("meanings", EQUIV_COLOR)

def thesaurus(word):
    print("lookup synonyms for word")

def scan(ctx, args):
    # See if args contain sd:<folder> or sfp:<regex>, to change scan behavior.
    while args:
        i = args[0].find(':')
        if i <= 0: break
        prefix = args[0][:i]
        rest = args[0][i+1:]
        if prefix.lower() == 'sd':
            ctx.scan_dirs = [os.path.abspath(x) for x in rest.split(';')]
            print(f"Scanning directories: {ctx.scan_dirs}")
            ctx.scan_settings_reported = False
            del args[0]
            for item in ctx.scan_dirs:
                if not os.path.exists(item):
                    cprint(f"{item} is not a valid directory to scan.", ERROR_COLOR)
        elif prefix.lower() == 'sfp':
            try: 
                ctx.scan_fname_pat = re.compile(rest, re.I)
                ctx.scan_settings_reported = False
                del args[0]
            except:
                cprint(f'"{rest}" is not a valid regex.', ERROR_COLOR)
                return
    
    if not ctx.scan_settings_reported:
        print()
        dirlist = "\n  ".join(ctx.scan_dirs)
        print(f'Scanning files with names like:\n  "{ctx.scan_fname_pat.pattern}"\nwithin:\n  {dirlist}.')
        ctx.scan_settings_reported = True

    if args:
        try:
            rest = ' '.join(args)
            regex = re.compile(rest, re.DOTALL)
        except:
            cprint(f'"{rest}" is not a valid regex.', ERROR_COLOR)
            return
        match_count = 0
        file_count = 0
        for scan_dir in ctx.scan_dirs:
            if not os.path.isdir(scan_dir): continue
            for folder, dirnames, file_names in os.walk(scan_dir):
                # Skip hidden folders.
                dirnames[:] = [d for d in dirnames if d[0] not in '._']
                for fname in file_names:
                    if ctx.scan_fname_pat.match(fname):
                        file_count += 1
                        file_path = os.path.join(folder, fname)
                        printed_file_path = False
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                # Read each line in the file
                                for line_number, line in enumerate(f, start=1):
                                    # Search for the pattern in the line
                                    line = line.strip()
                                    if regex.search(line):
                                        match_count += 1
                                        if not printed_file_path:
                                            print()
                                            cprint(os.path.relpath(file_path, scan_dir), OPTION_COLOR)
                                            printed_file_path = True
                                        print(f"  line {line_number}:")
                                        text = wrap_line_with_indent("    " + line)
                                        # Re-find the match
                                        m = regex.search(text)
                                        # Print the match with highlight
                                        write(text[:m.start()])
                                        cwrite(text[m.start():m.end()], LEX_COLOR)
                                        print(text[m.end():])
                        except Exception as e:
                            traceback.print_exc()
                            cprint(f"Error scanning '{file_path}': {e}", ERROR_COLOR)
        print(f"\nFound {match_count} matches in {file_count} files.")

def get_entry_from_args(ctx, args):
    # Was an entry specified?
    which = args[1] if len(args) > 1 else "1"
    # Was it identified by number?
    n = None
    try: n = int(which)
    except: pass
    try:
        if n and len(ctx.hits) >= n:
            return ctx.hits[n - 1]
        else:
            for item in ctx.hits:
                if item.lemma == which:
                    return item
    except: pass
    cprint(f"{which}: no such entry.", ERROR_COLOR)

def give_hints(coach, text):
    print()
    verbose = get_verbose()
    column = 1
    width = get_terminal_size()[0]
    for hint in coach.hints(text):
        if verbose:
            out = repr(hint) + ' '
        else:
            out = hint.lemma if hint.lemma else str(hint)
            if column + len(out) >= width:
                print()
                column = 1
            if column > 1:
                write(' ')
                column += 1
        if hint.lemma and not verbose:
            color = EQUIV_COLOR if hint.approx else LEX_COLOR
            cwrite(out, color)
        else:
            write(out)
        column += len(out)
    print()

def trans(ctx, args):
    if ctx.tcoach is None:
        ctx.tcoach = TranslationCoach(ctx.lang.glossary, ctx.lang.advise_func)
    coach = ctx.tcoach
    if not args:
        if ctx.last_trans:
            give_hints(coach, ctx.last_trans)
        while True:
            try:
                text = prompt("\nSource text? >")
                if text: 
                    give_hints(coach, text)
                    ctx.last_trans = text
                else:
                    break
            except KeyboardInterrupt:
                break
    else:
        if len(args) == 1 and os.path.isfile(args[0]):
            with open(args[0], 'r') as f:
                text = f.read()
        else:
            text = ' '.join(args)
        give_hints(coach, text)
        ctx.last_trans = text

SHORT_ENTRY_CMD_PAT = re.compile(r'^([ed])(\d+)$')

def cmd(lang, *args):
    """
    - run interactive commands in a REPL loop
    """

    # Define a REPL context that we can pass to our helper functions.
    class ReplContext: pass
    ctx = ReplContext
    ctx.lang = lang
    ctx.hits = []
    ctx.scan_dirs = [os.path.abspath('.')]
    ctx.scan_fname_pat = re.compile(r'.*\.(md|html?|txt)$', re.I)
    ctx.scan_settings_reported = False
    ctx.last_find = None
    ctx.tcoach = None
    ctx.last_trans = None

    # Show some stuff to orient user.
    show_stats(ctx)
    print()
    show_help()

    # REPL
    while True:
        args = prompt('\n>').strip().split()
        if args:
            cmd = args[0].lower()

            # Tolerate a very short form, like e1 for edit 1
            m = SHORT_ENTRY_CMD_PAT.match(cmd)
            if m:
                cmd = m.group(1)
                args.insert(1, m.group(2))
            cmd_is = lambda token: input_matches(cmd, token)

            if cmd_is("find"):
                expr = ' '.join(args[1:]) if len(args) > 1 else ctx.last_find_expr
                find(ctx, expr)
                if not show_hits(ctx): print("Nothing found.")
            elif cmd_is("scan"):
                scan(ctx, args[1:])
            elif cmd_is("add"):
                add(ctx, args[1:])
            elif cmd_is("edit"):
                entry = get_entry_from_args(ctx, args)
                if entry: edit(ctx, entry)
            elif cmd_is("delete"):
                entry = get_entry_from_args(ctx, args)
                if entry: delete(ctx, entry)
            elif cmd_is("stats"):
                show_stats(ctx)
            elif cmd_is("trans"):
                trans(ctx, args[1:])
            elif cmd_is("thesaurus"):
                thesaurus(args[1:])
            elif cmd_is("quit"):
                break
            else:
                show_help()
