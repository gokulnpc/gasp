"""getShift / updateShift, including the race-safe first-YES-wins lock
used when the SW1 cascade gets multiple simultaneous accepts.
"""

from db import get_driver


def get_shift(shift_id: str) -> dict | None:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (s:Shift {id: $id}) RETURN s AS node", id=shift_id
        ).single()
        return dict(result["node"]) if result else None


def update_shift(shift_id: str, **fields) -> dict:
    """Plain field update — no locking. Use accept_shift() for the
    caregiver-claims-an-OPEN-shift path, since that needs the lock.
    """
    driver = get_driver()
    with driver.session() as session:
        set_clause = ", ".join(f"s.{key} = ${key}" for key in fields)
        result = session.run(
            f"MATCH (s:Shift {{id: $id}}) SET {set_clause} RETURN s AS node",
            id=shift_id,
            **fields,
        ).single()
        return dict(result["node"])


def accept_shift(shift_id: str, caregiver_id: str) -> bool:
    """First-YES-wins claim. Only flips status OPEN -> FILLED if it is
    still OPEN at the moment this query runs, inside one transaction, so two
    caregivers accepting at the same instant can't both win.

    Returns True if this caregiver won the shift, False if someone else
    already had it (or the shift didn't exist / wasn't OPEN).
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.execute_write(_try_claim, shift_id, caregiver_id)
        return result


def _try_claim(tx, shift_id: str, caregiver_id: str) -> bool:
    record = tx.run(
        """
        MATCH (s:Shift {id: $shiftId, status: 'OPEN'})
        MATCH (cg:Caregiver {id: $caregiverId})
        SET s.status = 'FILLED'
        MERGE (cg)-[:ASSIGNED_TO]->(s)
        RETURN s
        """,
        shiftId=shift_id,
        caregiverId=caregiver_id,
    ).single()
    return record is not None
