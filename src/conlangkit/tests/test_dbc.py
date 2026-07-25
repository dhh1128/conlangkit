import pytest

from ..dbc import (
    InvariantViolation,
    Postcondition,
    PostconditionViolation,
    PreconditionViolation,
    postcondition,
    precondition,
)


def test_precondition_passes():
    precondition(True, "always ok")  # must not raise


def test_precondition_raises_with_comment():
    with pytest.raises(PreconditionViolation) as e:
        precondition(False, "x must be positive")
    assert "x must be positive" in str(e.value)


def test_postcondition_passes():
    postcondition(True, "always ok")


def test_postcondition_raises_with_comment():
    with pytest.raises(PostconditionViolation) as e:
        postcondition(False, "result must be sorted")
    assert "result must be sorted" in str(e.value)


def test_violation_messages():
    assert "Precondition violated" in str(PreconditionViolation("a"))
    assert "Postcondition violated" in str(PostconditionViolation("b"))
    assert "Invariant violated" in str(InvariantViolation("c"))


def test_postcondition_context_manager_pass():
    # Checker returns True on exit → no exception propagates.
    with Postcondition(lambda: True, "must hold"):
        pass


def test_postcondition_context_manager_fail_uses_self_comment():
    # Regression guard: __exit__ must raise PostconditionViolation(self.comment),
    # NOT a NameError on an undefined `comment` (the pre-fix behavior).
    with pytest.raises(PostconditionViolation) as e:
        with Postcondition(lambda: False, "postcheck failed"):
            pass
    assert "postcheck failed" in str(e.value)
