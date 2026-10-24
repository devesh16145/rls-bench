import uuid
from decimal import Decimal

from harness.checks import compare, normalise_value
from harness.models import Expectation, Observation


def exp(**kw) -> Expectation:
    return Expectation(**kw)


def test_normalise_values():
    assert normalise_value(Decimal("5")) == 5
    assert normalise_value(Decimal("1.50")) == "1.5"
    assert normalise_value(uuid.UUID(int=1)) == "00000000-0000-0000-0000-000000000001"
    assert normalise_value(True) is True


def test_rows_leak_and_block():
    e = exp(rows=[[1], [2]])
    assert compare(e, Observation(rows=[[1], [2]])) == (True, False, False)
    assert compare(e, Observation(rows=[[1], [2], [3]])) == (False, True, False)
    assert compare(e, Observation(rows=[[1]])) == (False, False, True)
    assert compare(e, Observation(sqlstate="42501")) == (False, False, True)


def test_count_star_compared_as_number():
    e = exp(rows=[[0]])
    assert compare(e, Observation(rows=[[3]])) == (False, True, False)


def test_affected():
    e = exp(affected=1)
    assert compare(e, Observation(rowcount=1)) == (True, False, False)
    assert compare(e, Observation(rowcount=0)) == (False, False, True)
    assert compare(exp(affected=0), Observation(rowcount=1)) == (False, True, False)


def test_error_and_denied():
    assert compare(exp(error="42501"), Observation(sqlstate="42501")) == (True, False, False)
    assert compare(exp(error="42501"), Observation(rowcount=1)) == (False, True, False)
    d = exp(denied=True)
    assert compare(d, Observation(sqlstate="42501"))[0]
    assert compare(d, Observation(sqlstate="P0001"))[0]
    assert compare(d, Observation(sqlstate="23514"))[0]
    assert not compare(d, Observation(sqlstate="23505"))[0]
    assert compare(d, Observation(rowcount=0))[0]
    assert compare(d, Observation(rowcount=1)) == (False, True, False)
    assert compare(d, Observation(sqlstate="42P17")) == (False, False, False)
