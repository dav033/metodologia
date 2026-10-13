import pytest

@pytest.mark.parametrize('value', range(300))
def test_round_trip(value):
    assert int(str(value)) == value
