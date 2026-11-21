from pvm import serving as S


def test_pseudonym_is_stable_and_16_hex_chars():
    a = S.pseudonym('p', 's')
    assert a == S.pseudonym('p', 's') and len(a) == 16 and int(a, 16) >= 0


def test_refire_constant_is_one_hour_at_five_minutes():
    assert S.REFIRE_SAMPLES == 12
