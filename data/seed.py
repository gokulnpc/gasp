"""Fills the graph with a small synthetic (non-PHI) dataset: caregivers,
patients, certifications, languages (English + Spanish), locations, and
shifts. Safe to re-run — it wipes and reloads everything.
"""

from db import get_driver

CERTIFICATIONS = ["CNA", "HHA", "RN"]
LANGUAGES = [("en", "English"), ("es", "Spanish")]

LOCATIONS = [
    {"id": "loc-1", "zip": "10001"},
    {"id": "loc-2", "zip": "10002"},
    {"id": "loc-3", "zip": "10003"},
    {"id": "loc-4", "zip": "10004"},
    {"id": "loc-5", "zip": "10005"},
]

# NEAR is bidirectional in reality; we write it both ways so traversal works
# starting from either side. Not every pair is connected, so proximity
# queries have to handle "no path found" too.
LOCATION_PROXIMITY = [
    ("loc-1", "loc-2", 10),
    ("loc-2", "loc-3", 15),
    ("loc-1", "loc-3", 20),
    ("loc-3", "loc-4", 8),
    ("loc-4", "loc-5", 12),
    ("loc-2", "loc-4", 18),
    ("loc-1", "loc-5", 25),
]

CAREGIVERS = [
    {"id": "cg-1", "name": "Maria Alvarez", "phone": "+19179070164", "status": "available",
     "certs": ["HHA"], "languages": ["en", "es"], "location": "loc-1"},
    {"id": "cg-2", "name": "James Carter", "phone": "+15550101", "status": "available",
     "certs": ["CNA"], "languages": ["en"], "location": "loc-2"},
    {"id": "cg-3", "name": "Sofia Reyes", "phone": "+15550102", "status": "available",
     "certs": ["RN", "HHA"], "languages": ["es"], "location": "loc-3"},
    {"id": "cg-4", "name": "David Okafor", "phone": "+15550103", "status": "available",
     "certs": ["CNA", "HHA"], "languages": ["en"], "location": "loc-4"},
    {"id": "cg-5", "name": "Lucia Fernandez", "phone": "+15550104", "status": "unavailable",
     "certs": ["HHA"], "languages": ["es", "en"], "location": "loc-5"},
    {"id": "cg-6", "name": "Michael Torres", "phone": "+15550105", "status": "available",
     "certs": ["RN"], "languages": ["en", "es"], "location": "loc-2"},
    {"id": "cg-7", "name": "Aisha Bello", "phone": "+15550106", "status": "available",
     "certs": ["CNA"], "languages": ["en"], "location": "loc-5"},
]

PATIENTS = [
    {"id": "pt-1", "name": "Robert Kim", "phone": "+15513629724", "age": 78, "gender": "male",
     "requires_cert": "HHA", "prefers_language": "en", "location": "loc-1"},
    {"id": "pt-2", "name": "Elena Cruz", "phone": "+15550201", "age": 84, "gender": "female",
     "requires_cert": "HHA", "prefers_language": "es", "location": "loc-2"},
    {"id": "pt-3", "name": "William Park", "phone": "+15550202", "age": 69, "gender": "male",
     "requires_cert": "CNA", "prefers_language": "en", "location": "loc-3"},
    {"id": "pt-4", "name": "Isabella Gomez", "phone": "+15550203", "age": 91, "gender": "female",
     "requires_cert": "RN", "prefers_language": "es", "location": "loc-4"},
    {"id": "pt-5", "name": "Thomas Nguyen", "phone": "+15550204", "age": 73, "gender": "male",
     "requires_cert": "HHA", "prefers_language": "en", "location": "loc-5"},
    {"id": "pt-6", "name": "Camila Rodriguez", "phone": "+15550205", "age": 88, "gender": "female",
     "requires_cert": "CNA", "prefers_language": "es", "location": "loc-1"},
    {"id": "pt-7", "name": "George Wilson", "phone": "+15550206", "age": 76, "gender": "male",
     "requires_cert": "RN", "prefers_language": "en", "location": "loc-2"},
    {"id": "pt-8", "name": "Valentina Morales", "phone": "+15550207", "age": 82, "gender": "female",
     "requires_cert": "HHA", "prefers_language": "es", "location": "loc-3"},
    {"id": "pt-9", "name": "Daniel Lee", "phone": "+15550208", "age": 67, "gender": "male",
     "requires_cert": "CNA", "prefers_language": "en", "location": "loc-4"},
    {"id": "pt-10", "name": "Gabriela Santos", "phone": "+15550209", "age": 79, "gender": "female",
     "requires_cert": "HHA", "prefers_language": "es", "location": "loc-5"},
    {"id": "pt-11", "name": "Henry Brooks", "phone": "+15550210", "age": 85, "gender": "male",
     "requires_cert": "RN", "prefers_language": "en", "location": "loc-1"},
    {"id": "pt-12", "name": "Mariana Diaz", "phone": "+15550211", "age": 71, "gender": "female",
     "requires_cert": "CNA", "prefers_language": "es", "location": "loc-2"},
    {"id": "pt-13", "name": "Samuel Green", "phone": "+15550212", "age": 90, "gender": "male",
     "requires_cert": "HHA", "prefers_language": "en", "location": "loc-3"},
    {"id": "pt-14", "name": "Adriana Flores", "phone": "+15550213", "age": 74, "gender": "female",
     "requires_cert": "RN", "prefers_language": "es", "location": "loc-4"},
    {"id": "pt-15", "name": "Charles Bennett", "phone": "+15550214", "age": 80, "gender": "male",
     "requires_cert": "CNA", "prefers_language": "en", "location": "loc-5"},
]

# Only some patients have an active medication layout — matches real life,
# and lets SW3 (Med-Log) be tested against both "has meds" and "no meds" cases.
MEDICATIONS = [
    {"patient": "pt-1", "name": "Metformin", "dose": "500mg", "schedule": "9:00 AM",
     "route": "oral", "active": True},
    {"patient": "pt-1", "name": "Lisinopril", "dose": "10mg", "schedule": "9:00 AM",
     "route": "oral", "active": True},
    {"patient": "pt-2", "name": "Atorvastatin", "dose": "20mg", "schedule": "8:00 PM",
     "route": "oral", "active": True},
    {"patient": "pt-4", "name": "Furosemide", "dose": "40mg", "schedule": "8:00 AM",
     "route": "oral", "active": True},
    {"patient": "pt-4", "name": "Insulin Glargine", "dose": "18 units", "schedule": "10:00 PM",
     "route": "injection", "active": True},
    {"patient": "pt-6", "name": "Levothyroxine", "dose": "75mcg", "schedule": "7:00 AM",
     "route": "oral", "active": True},
    {"patient": "pt-8", "name": "Amlodipine", "dose": "5mg", "schedule": "9:00 AM",
     "route": "oral", "active": True},
    {"patient": "pt-8", "name": "Ibuprofen", "dose": "200mg", "schedule": "as needed",
     "route": "oral", "active": False},
    {"patient": "pt-11", "name": "Warfarin", "dose": "5mg", "schedule": "6:00 PM",
     "route": "oral", "active": True},
]

SHIFTS = [
    {"id": "shift-1", "patient": "pt-1", "caregiver": "cg-1",
     "start": "2026-07-12T08:00:00", "end": "2026-07-12T12:00:00", "status": "FILLED"},
    {"id": "shift-2", "patient": "pt-2", "caregiver": None,
     "start": "2026-07-12T09:00:00", "end": "2026-07-12T13:00:00", "status": "OPEN"},
    {"id": "shift-3", "patient": "pt-3", "caregiver": "cg-4",
     "start": "2026-07-12T08:00:00", "end": "2026-07-12T12:00:00", "status": "FILLED"},
    {"id": "shift-4", "patient": "pt-4", "caregiver": None,
     "start": "2026-07-12T10:00:00", "end": "2026-07-12T14:00:00", "status": "OPEN"},
    {"id": "shift-5", "patient": "pt-5", "caregiver": None,
     "start": "2026-07-12T07:00:00", "end": "2026-07-12T11:00:00", "status": "OPEN"},
    {"id": "shift-6", "patient": "pt-6", "caregiver": None,
     "start": "2026-07-12T09:00:00", "end": "2026-07-12T13:00:00", "status": "SCHEDULED"},
    {"id": "shift-7", "patient": "pt-11", "caregiver": "cg-6",
     "start": "2026-07-12T08:00:00", "end": "2026-07-12T12:00:00", "status": "FILLED"},
]


def wipe(session):
    session.run("MATCH (n) DETACH DELETE n")


def seed_certifications(session):
    for cert in CERTIFICATIONS:
        session.run("MERGE (c:Certification {id: $id, name: $id})", id=cert)


def seed_languages(session):
    for code, name in LANGUAGES:
        session.run("MERGE (l:Language {code: $code, name: $name})", code=code, name=name)


def seed_locations(session):
    for loc in LOCATIONS:
        session.run("MERGE (loc:Location {id: $id, zip: $zip})", **loc)
    for a, b, minutes in LOCATION_PROXIMITY:
        session.run(
            """
            MATCH (a:Location {id: $a}), (b:Location {id: $b})
            MERGE (a)-[:NEAR {minutes: $minutes}]->(b)
            MERGE (b)-[:NEAR {minutes: $minutes}]->(a)
            """,
            a=a, b=b, minutes=minutes,
        )


def seed_caregivers(session):
    for cg in CAREGIVERS:
        session.run(
            """
            MERGE (c:Caregiver {id: $id})
            SET c.name = $name, c.phone = $phone, c.status = $status
            WITH c
            MATCH (loc:Location {id: $location})
            MERGE (c)-[:BASED_AT]->(loc)
            """,
            id=cg["id"], name=cg["name"], phone=cg["phone"], status=cg["status"],
            location=cg["location"],
        )
        for cert in cg["certs"]:
            session.run(
                """
                MATCH (c:Caregiver {id: $id}), (cert:Certification {id: $cert})
                MERGE (c)-[:HOLDS]->(cert)
                """,
                id=cg["id"], cert=cert,
            )
        for lang in cg["languages"]:
            session.run(
                """
                MATCH (c:Caregiver {id: $id}), (l:Language {code: $lang})
                MERGE (c)-[:SPEAKS]->(l)
                """,
                id=cg["id"], lang=lang,
            )


def seed_patients(session):
    for pt in PATIENTS:
        session.run(
            """
            MERGE (p:Patient {id: $id})
            SET p.name = $name, p.phone = $phone, p.age = $age, p.gender = $gender
            WITH p
            MATCH (loc:Location {id: $location}), (cert:Certification {id: $cert}),
                  (l:Language {code: $lang})
            MERGE (p)-[:LOCATED_AT]->(loc)
            MERGE (p)-[:REQUIRES]->(cert)
            MERGE (p)-[:PREFERS]->(l)
            """,
            id=pt["id"], name=pt["name"], phone=pt["phone"], age=pt["age"],
            gender=pt["gender"], location=pt["location"],
            cert=pt["requires_cert"], lang=pt["prefers_language"],
        )


def seed_medications(session):
    for med in MEDICATIONS:
        session.run(
            """
            MATCH (p:Patient {id: $patient})
            CREATE (m:Medication {
                name: $name, dose: $dose, schedule: $schedule,
                route: $route, active: $active
            })
            MERGE (p)-[:HAS_MEDICATION]->(m)
            """,
            patient=med["patient"], name=med["name"], dose=med["dose"],
            schedule=med["schedule"], route=med["route"], active=med["active"],
        )


def seed_shifts(session):
    for sh in SHIFTS:
        session.run(
            """
            MERGE (s:Shift {id: $id})
            SET s.start = $start, s.end = $end, s.status = $status
            WITH s
            MATCH (p:Patient {id: $patient})
            MERGE (p)-[:HAS_SHIFT]->(s)
            """,
            id=sh["id"], start=sh["start"], end=sh["end"], status=sh["status"],
            patient=sh["patient"],
        )
        if sh["caregiver"]:
            session.run(
                """
                MATCH (c:Caregiver {id: $caregiver}), (s:Shift {id: $id})
                MERGE (c)-[:ASSIGNED_TO]->(s)
                """,
                caregiver=sh["caregiver"], id=sh["id"],
            )


def run():
    driver = get_driver()
    with driver.session() as session:
        wipe(session)
        seed_certifications(session)
        seed_languages(session)
        seed_locations(session)
        seed_caregivers(session)
        seed_patients(session)
        seed_medications(session)
        seed_shifts(session)
    print("Seed complete: "
          f"{len(CAREGIVERS)} caregivers, {len(PATIENTS)} patients, {len(SHIFTS)} shifts.")


if __name__ == "__main__":
    run()
