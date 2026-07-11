from api.masking import mask_name, mask_phone, mask_record


def test_mask_phone_hides_the_middle_digits():
    assert mask_phone("+19179070164") == "+1917***0164"


def test_mask_phone_handles_short_or_empty_input():
    assert mask_phone("") == "***"
    assert mask_phone("123") == "***"


def test_mask_name_reduces_to_initials():
    assert mask_name("Maria Alvarez") == "M. A."


def test_mask_record_masks_phone_and_name_but_leaves_other_fields():
    record = {"id": "cg-1", "name": "Maria Alvarez", "phone": "+19179070164", "status": "available"}
    masked = mask_record(record)
    assert masked["name"] == "M. A."
    assert masked["phone"] == "+1917***0164"
    assert masked["id"] == "cg-1"
    assert masked["status"] == "available"
    # original untouched
    assert record["name"] == "Maria Alvarez"
