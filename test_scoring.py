import pytest

from sitesel import data, scoring


@pytest.fixture(scope="module")
def sets():
    return data.make_candidates(), data.make_demand()


def test_haversine_jakarta_bandung():
    d = scoring.haversine_km(-6.2088, 106.8456, -6.9175, 107.6191)
    assert 110 < d < 122


def test_weights_normalized():
    w = scoring.normalize_weights({"coverage": 2, "flood": 2})
    assert abs(sum(w.values()) - 1) < 1e-9 and w["price"] == 0


@pytest.mark.parametrize("bad", [{"foo": 1}, {"coverage": -1}, {"coverage": 0}])
def test_bad_weights(bad):
    with pytest.raises(ValueError):
        scoring.normalize_weights(bad)


def test_evaluate_sorted_and_bounded(sets):
    r = scoring.evaluate(*sets)
    assert r["score"].is_monotonic_decreasing
    assert r["score"].between(0, 1).all() and r["coverage"].between(0, 1).all()
    assert list(r["rank"]) == list(range(1, len(r) + 1))


def test_larger_radius_never_reduces_coverage(sets):
    a = scoring.evaluate(*sets, radius_km=3).set_index("id")["coverage"]
    b = scoring.evaluate(*sets, radius_km=8).set_index("id")["coverage"].reindex(a.index)
    assert (b >= a - 1e-12).all()


def test_greedy_monotonic_and_unique(sets):
    h = scoring.greedy_hubs(*sets, k=4, radius_km=5)
    assert h["cakupan_kumulatif"].is_monotonic_increasing
    assert h["id"].is_unique
