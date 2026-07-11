import seed
from api.callers import get_caller_by_phone


def test_finds_a_caregiver_by_phone():
    cg = seed.CAREGIVERS[0]
    result = get_caller_by_phone(cg["phone"])
    assert result is not None
    assert result["type"] == "caregiver"
    assert result["id"] == cg["id"]
    assert result["name"] == cg["name"]


def test_finds_a_patient_by_phone():
    pt = seed.PATIENTS[0]
    result = get_caller_by_phone(pt["phone"])
    assert result is not None
    assert result["type"] == "patient"
    assert result["id"] == pt["id"]
    assert result["name"] == pt["name"]


def test_unknown_number_returns_none():
    assert get_caller_by_phone("+10000000000") is None
