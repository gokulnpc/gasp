"""appendAuditLog — append-only store for med-log entries, escalation
events, and cascade history. Never edit an existing entry; corrections are
new entries that reference the one they correct.
"""

import uuid
from datetime import datetime, timezone

from db import get_driver


def append_audit_log(entry: dict) -> dict:
    """entry must include "type" (e.g. "med_log" | "escalation" | "cascade")
    and "payload" (the structured data for that type). Adds an id and
    timestamp automatically; entry itself is stored as-is, never mutated
    later.
    """
    record = {
        "id": str(uuid.uuid4()),
        "type": entry["type"],
        "payload": entry["payload"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    driver = get_driver()
    with driver.session() as session:
        session.run(
            """
            CREATE (a:AuditLogEntry {
                id: $id, type: $type, payload: $payload, created_at: $created_at
            })
            """,
            id=record["id"],
            type=record["type"],
            payload=str(record["payload"]),
            created_at=record["created_at"],
        )
    return record
