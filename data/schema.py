"""Creates uniqueness constraints for the graph. Run once before seed.py.

A constraint on a property also creates an index on it, so lookups by
id/phone stay fast even in a hackathon-sized graph.
"""

from db import get_driver

CONSTRAINTS = [
    "CREATE CONSTRAINT caregiver_id IF NOT EXISTS FOR (c:Caregiver) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT caregiver_phone IF NOT EXISTS FOR (c:Caregiver) REQUIRE c.phone IS UNIQUE",
    "CREATE CONSTRAINT patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT patient_phone IF NOT EXISTS FOR (p:Patient) REQUIRE p.phone IS UNIQUE",
    "CREATE CONSTRAINT certification_id IF NOT EXISTS FOR (c:Certification) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT language_code IF NOT EXISTS FOR (l:Language) REQUIRE l.code IS UNIQUE",
    "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (loc:Location) REQUIRE loc.id IS UNIQUE",
    "CREATE CONSTRAINT shift_id IF NOT EXISTS FOR (s:Shift) REQUIRE s.id IS UNIQUE",
]


def apply_schema():
    driver = get_driver()
    with driver.session() as session:
        for statement in CONSTRAINTS:
            session.run(statement)
    print(f"Applied {len(CONSTRAINTS)} constraints.")


if __name__ == "__main__":
    apply_schema()
