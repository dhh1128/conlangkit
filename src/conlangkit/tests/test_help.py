from ..commands import PLUGINS
from ..commands import help as help_cmd


def test_help_cmd_lists_commands(capsys):
    try:
        help_cmd.cmd(None)
        out = capsys.readouterr().out
        assert "clk -- develop" in out
        assert "repl" in out
    finally:
        # cmd() registers itself into PLUGINS as a side effect; keep tests isolated.
        PLUGINS.pop("help", None)
