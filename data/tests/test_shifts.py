from concurrent.futures import ThreadPoolExecutor

from api.shifts import accept_shift, get_shift, update_shift


def test_get_shift_returns_known_fields():
    shift = get_shift("shift-2")
    assert shift is not None
    assert shift["status"] == "OPEN"


def test_get_shift_returns_none_for_unknown_id():
    assert get_shift("no-such-shift") is None


def test_accept_shift_claims_an_open_shift():
    # shift-5 is seeded OPEN; use it in isolation from the concurrency test below.
    won = accept_shift("shift-5", "cg-4")
    assert won is True
    assert get_shift("shift-5")["status"] == "FILLED"


def test_accept_shift_fails_on_an_already_filled_shift():
    # shift-1 is seeded FILLED from the start.
    won = accept_shift("shift-1", "cg-2")
    assert won is False
    assert get_shift("shift-1")["status"] == "FILLED"


def test_accept_shift_is_race_safe_under_concurrent_claims():
    """The core safety requirement: if two caregivers accept the same OPEN
    shift at (near) the same instant, exactly one must win.
    """
    shift_id = "shift-4"
    assert get_shift(shift_id)["status"] == "OPEN"

    caregiver_ids = ["cg-2", "cg-3", "cg-4", "cg-6", "cg-7"]
    with ThreadPoolExecutor(max_workers=len(caregiver_ids)) as pool:
        results = list(pool.map(lambda cg: accept_shift(shift_id, cg), caregiver_ids))

    assert results.count(True) == 1
    assert get_shift(shift_id)["status"] == "FILLED"


def test_update_shift_sets_arbitrary_fields():
    updated = update_shift("shift-6", status="CANCELLED")
    assert updated["status"] == "CANCELLED"
