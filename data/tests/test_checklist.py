import seed
from api.checklist import get_med_layout


def test_get_med_layout_returns_only_active_medications_for_a_patient():
    layout = get_med_layout("pt-1")
    expected = {m["name"] for m in seed.MEDICATIONS if m["patient"] == "pt-1" and m["active"]}
    assert {m["name"] for m in layout} == expected
    assert all(m["active"] for m in layout)


def test_get_med_layout_excludes_inactive_medications():
    # pt-8 has Ibuprofen seeded as active=False — must not appear.
    layout = get_med_layout("pt-8")
    assert all(m["name"] != "Ibuprofen" for m in layout)


def test_get_med_layout_returns_empty_for_patient_with_no_medications():
    # pt-3 has no entries in seed.MEDICATIONS at all.
    assert get_med_layout("pt-3") == []
