def _load_plugins():
    """
    Dynamically discover any commands supported by the tt program.
    """
    plugins = {}
    import importlib
    import os
    my_folder = os.path.dirname(os.path.abspath(__file__))
    for item in os.listdir(my_folder):
        if item.endswith('.py') and item[0] not in '_.' and item != 'help.py':
            item = item[:-3]
            module = importlib.import_module(f'.{item}', __name__)
            cmd = getattr(module, 'cmd')
            if cmd:
                plugins[item] = cmd
    return plugins


PLUGINS = _load_plugins()
del _load_plugins
