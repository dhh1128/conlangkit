from ..commands import PLUGINS


def cmd(_, args=None):
    """
    [cmd] - display general help, or display help on a specific command
    """

    print("""
clk -- develop artifacts for artificial languages

Available commands
""")
    # To avoid a circular import problem, we didn't load the help plugin dynamically.
    # Add it manually.
    if "help" not in PLUGINS.keys():
        PLUGINS["help"] = cmd
    for name, func in PLUGINS.items():
        doc = func.__doc__.strip()
        i = doc.find("-")
        syntax, doc = doc[:i].rstrip(), doc[i + 1 :].lstrip()
        print(f"  clk LANGDIR {name} {syntax}\n      {doc}\n")
