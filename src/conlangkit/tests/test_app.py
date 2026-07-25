import os

import pytest

from .. import app
from ..commands import PLUGINS

MARTIAN = os.path.join(os.path.dirname(__file__), "martian")


def test_no_args_shows_help_and_exits(capsys):
    with pytest.raises(SystemExit) as e:
        app.main(["clk"])
    assert e.value.code == 1
    assert "clk -- develop" in capsys.readouterr().out


def test_verbose_flag_then_help(capsys):
    # "-v" is consumed, leaving too few args → help + exit.
    with pytest.raises(SystemExit) as e:
        app.main(["clk", "-v"])
    assert e.value.code == 1


def test_nonexistent_langdir_reports_and_exits(capsys):
    with pytest.raises(SystemExit) as e:
        app.main(["clk", "/no/such/dir", "help"])
    assert e.value.code == 1
    assert "must be a folder" in capsys.readouterr().out


def test_bad_command_reports_and_exits(capsys):
    with pytest.raises(SystemExit) as e:
        app.main(["clk", MARTIAN, "definitely-not-a-command"])
    assert e.value.code == 1
    assert "Bad command-line syntax" in capsys.readouterr().err


def test_successful_command_dispatch(capsys):
    # Inject a non-interactive command to exercise the cmd(lang, *args) path.
    def _noop(lang, *args):
        """[x] - no-op test command"""
        print("ran-noop", lang.name)

    PLUGINS["noopcmd"] = _noop
    try:
        app.main(["clk", MARTIAN, "noopcmd"])  # returns normally, no SystemExit
    finally:
        PLUGINS.pop("noopcmd", None)
    assert "ran-noop" in capsys.readouterr().out


def test_command_exception_is_caught(capsys):
    def _boom(lang, *args):
        """[x] - always raises, for testing the error path"""
        raise ValueError("boom")

    PLUGINS["boomcmd"] = _boom
    try:
        with pytest.raises(SystemExit) as e:
            app.main(["clk", MARTIAN, "boomcmd"])
    finally:
        PLUGINS.pop("boomcmd", None)
    assert e.value.code == 1


def test_match_command_unknown_returns_none():
    assert app.match_command("definitely-not-a-command") is None
