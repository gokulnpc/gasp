"""matchCaregivers (SW2 intake) and findBackups (SW1 cascade).

Hard filters (must match, no exceptions): certification, language, availability.
Weighted/ranked factor: proximity (minutes) — closer is better, sorted ascending.
"""

from db import get_driver


def match_caregivers(patient_id: str) -> list[dict]:
    """Ranked list of available caregivers who hold the patient's required
    certification, speak the patient's preferred language, and are
    reachable via a NEAR path. Closest first.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Patient {id: $patientId})-[:REQUIRES]->(cert:Certification),
                  (p)-[:PREFERS]->(lang:Language),
                  (p)-[:LOCATED_AT]->(loc:Location)
            MATCH (cg:Caregiver {status: 'available'})-[:HOLDS]->(cert),
                  (cg)-[:SPEAKS]->(lang),
                  (cg)-[:BASED_AT]->(cgLoc:Location)-[near:NEAR]->(loc)
            RETURN cg, near.minutes AS proximity
            ORDER BY proximity ASC
            """,
            patientId=patient_id,
        )
        return [
            {**dict(record["cg"]), "proximity_minutes": record["proximity"]}
            for record in result
        ]


def find_backups(shift_id: str) -> list[dict]:
    """Ranked list of available caregivers who can cover a shift's patient —
    same hard filters as match_caregivers, but starting from a Shift.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Shift {id: $shiftId})<-[:HAS_SHIFT]-(p:Patient),
                  (p)-[:REQUIRES]->(cert:Certification),
                  (p)-[:PREFERS]->(lang:Language),
                  (p)-[:LOCATED_AT]->(loc:Location)
            MATCH (cg:Caregiver {status: 'available'})-[:HOLDS]->(cert),
                  (cg)-[:SPEAKS]->(lang),
                  (cg)-[:BASED_AT]->(cgLoc:Location)-[near:NEAR]->(loc)
            WHERE NOT (cg)-[:ASSIGNED_TO]->(s)
            RETURN cg, near.minutes AS proximity
            ORDER BY proximity ASC
            """,
            shiftId=shift_id,
        )
        return [
            {**dict(record["cg"]), "proximity_minutes": record["proximity"]}
            for record in result
        ]
