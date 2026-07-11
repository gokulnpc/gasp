from api.audit_log import append_audit_log


def test_append_audit_log_returns_id_and_timestamp():
    entry = append_audit_log({"type": "med_log", "payload": {"shift_id": "shift-1"}})
    assert entry["id"]
    assert entry["created_at"]
    assert entry["type"] == "med_log"


def test_append_audit_log_never_overwrites_a_prior_entry():
    first = append_audit_log({"type": "escalation", "payload": {"note": "first"}})
    second = append_audit_log({"type": "escalation", "payload": {"note": "correction"}})
    # Two distinct entries, not one edited in place — the append-only guarantee.
    assert first["id"] != second["id"]
