"""getCallerByPhone — used by the Orchestrator to recognize who's calling."""

from db import get_driver


def get_caller_by_phone(phone: str) -> dict | None:
    """Looks up a Caregiver or Patient by phone number.

    Returns a dict like {"type": "caregiver"|"patient", **node_properties},
    or None if the number isn't in the graph.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (c:Caregiver {phone: $phone}) RETURN c AS node", phone=phone
        ).single()
        if result:
            return {"type": "caregiver", **dict(result["node"])}

        result = session.run(
            "MATCH (p:Patient {phone: $phone}) RETURN p AS node", phone=phone
        ).single()
        if result:
            return {"type": "patient", **dict(result["node"])}

    return None
