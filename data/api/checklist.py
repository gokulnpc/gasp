"""getMedLayout — a patient's active daily medication/care checklist,
walked by the SW3 med-log questionnaire.
"""

from db import get_driver


def get_med_layout(patient_id: str) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Patient {id: $patientId})-[:HAS_MEDICATION]->(m:Medication {active: true})
            RETURN m
            """,
            patientId=patient_id,
        )
        return [dict(record["m"]) for record in result]
