import seed
from api.matching import find_backups, match_caregivers


def _caregiver_lookup():
    return {cg["id"]: cg for cg in seed.CAREGIVERS}


def test_match_caregivers_respects_certification_and_language():
    patient = seed.PATIENTS[1]  # pt-2: requires HHA, prefers Spanish
    results = match_caregivers(patient["id"])
    caregivers = _caregiver_lookup()

    assert len(results) > 0
    for match in results:
        cg = caregivers[match["id"]]
        assert patient["requires_cert"] in cg["certs"]
        assert patient["prefers_language"] in cg["languages"]
        assert cg["status"] == "available"


def test_match_caregivers_excludes_unavailable_caregivers():
    # cg-5 (Lucia Fernandez) is seeded as "unavailable" and otherwise
    # qualifies for HHA + Spanish patients — must never appear in results.
    patient = seed.PATIENTS[1]
    results = match_caregivers(patient["id"])
    assert all(match["id"] != "cg-5" for match in results)


def test_match_caregivers_is_sorted_by_proximity_ascending():
    patient = seed.PATIENTS[1]
    results = match_caregivers(patient["id"])
    proximities = [r["proximity_minutes"] for r in results]
    assert proximities == sorted(proximities)


def test_match_caregivers_returns_empty_list_for_unreachable_patient():
    # A patient with no qualifying caregiver anywhere nearby.
    fake_patient_id = "does-not-exist"
    assert match_caregivers(fake_patient_id) == []


def test_find_backups_matches_the_shifts_patient_requirements():
    shift = next(s for s in seed.SHIFTS if s["id"] == "shift-4")  # pt-4: RN, Spanish
    patient = next(p for p in seed.PATIENTS if p["id"] == shift["patient"])
    caregivers = _caregiver_lookup()

    results = find_backups(shift["id"])
    assert len(results) > 0
    for match in results:
        cg = caregivers[match["id"]]
        assert patient["requires_cert"] in cg["certs"]
        assert patient["prefers_language"] in cg["languages"]
