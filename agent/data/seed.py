"""Synthetic seed data (no real PHI) - the shape Person 3 will publish.

Caregivers, patients, shifts, med layouts, and per-shift ranked backups.
Console caller defaults to Maria (+15550001).
"""

CAREGIVERS = {
    "cg-maria": {
        "id": "cg-maria", "name": "Maria Lopez", "phone": "+15550001",
        "languages": ["spanish", "english"], "certifications": ["HHA"],
        "home_zip": "11368", "reliability": 0.92,
    },
    "cg-james": {
        "id": "cg-james", "name": "James Carter", "phone": "+15550002",
        "languages": ["english"], "certifications": ["HHA", "CPR"],
        "home_zip": "11369", "reliability": 0.88,
    },
    "cg-aisha": {
        "id": "cg-aisha", "name": "Aisha Khan", "phone": "+15550003",
        "languages": ["english", "urdu"], "certifications": ["HHA"],
        "home_zip": "11372", "reliability": 0.85,
    },
    "cg-elena": {
        "id": "cg-elena", "name": "Elena Petrova", "phone": "+15550004",
        "languages": ["english", "russian"], "certifications": ["RN", "HHA"],
        "home_zip": "11101", "reliability": 0.9,
    },
}

PATIENTS = {
    "pt-chen": {
        "id": "pt-chen", "name": "Mr. Chen", "zip": "11368",
        "languages": ["english", "mandarin"],
        "needs": ["mobility assistance", "medication supervision"],
    },
    "pt-alvarez": {
        "id": "pt-alvarez", "name": "Mrs. Alvarez", "zip": "11372",
        "languages": ["spanish"],
        "needs": ["diabetes care"],
    },
}

# Daily medication layout per patient (SW3 questionnaire runs off this).
MED_LAYOUTS = {
    "pt-chen": [
        {"med_id": "med-1", "name": "Metformin", "dose": "500 mg", "when": "8 AM", "prn": False},
        {"med_id": "med-2", "name": "Lisinopril", "dose": "10 mg", "when": "12 PM", "prn": False},
        {"med_id": "med-3", "name": "Ibuprofen", "dose": "200 mg", "when": "as needed", "prn": True},
    ],
    "pt-alvarez": [
        {"med_id": "med-4", "name": "Insulin glargine", "dose": "20 units", "when": "9 AM", "prn": False},
        {"med_id": "med-5", "name": "Metformin", "dose": "850 mg", "when": "6 PM", "prn": False},
    ],
}

SHIFTS = {
    "shift-1001": {
        "id": "shift-1001", "caregiver_id": "cg-maria", "patient_id": "pt-chen",
        "client_name": "Mr. Chen", "starts_at": "today 10:00 AM",
        "ends_at": "today 2:00 PM", "status": "SCHEDULED",
    },
    "shift-1002": {
        "id": "shift-1002", "caregiver_id": "cg-maria", "patient_id": "pt-alvarez",
        "client_name": "Mrs. Alvarez", "starts_at": "tomorrow 9:00 AM",
        "ends_at": "tomorrow 1:00 PM", "status": "SCHEDULED",
    },
}

# Ranked compliant backups per shift (what Person 3's Cypher query would return).
BACKUPS = {
    "shift-1001": ["cg-james", "cg-aisha", "cg-elena"],
    "shift-1002": ["cg-aisha", "cg-elena", "cg-james"],
}

# Demo script: who says YES to the cascade, and after how many seconds.
CASCADE_YES = {"caregiver_id": "cg-james", "after_s": 4}
