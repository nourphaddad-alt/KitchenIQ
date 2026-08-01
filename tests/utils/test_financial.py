from utils.financial import commission_on


def test_commission_on_returns_expected_value() -> None:
    assert commission_on(100000, 0.25) == 25000


def test_commission_on_zero_amount() -> None:
    assert commission_on(0, 0.25) == 0


def test_commission_on_none_rate() -> None:
    assert commission_on(100000, None) == 0
