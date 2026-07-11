# SubWorkflow 1 · The 6:00 AM Shift-Backfill Cascade

_Purpose: automatically fill a called-out shift by cascading to compliant backups._
_Owner: Team · Status: Draft_

The flagship reactive flow. Turns 45 minutes of frantic manual dialing into ~5 minutes of
automated oversight, protecting **$150–$300** of billable revenue per prevented cancellation.

## 1. Trigger

The Orchestrator detects a **caregiver absence or emergency call-out** — e.g. an inbound call
where the caregiver says they can't make their shift.

## 2. Preconditions

- Caller is recognized as a caregiver via [caller-ID recognition](../02-architecture.md#personalization--intelligent-routing-engine).
- The caregiver has an assigned shift today in the [Shift Calendars](../04-data-model.md#shift-calendars).
- A roster of potential backups exists in the [Neo4j graph](../04-data-model.md#graph-relational-roster-neo4j).

## 3. Step-by-step flow

1. Confirm the specific shift being vacated (patient, time, location).
2. **Log the vacancy** — mark the shift as `OPEN` and record the reason.
3. Fire an **asynchronous database query** for available, compliant backup staff
   (matching certification, language, and proximity to the patient).
4. Trigger a **targeted outbound cascade** — SMS + voice — to the ranked backup list.
5. **Lock the shift** the moment a "YES" is received; notify remaining contacted staff it's filled.
6. Update the calendar with the new assignment and return control to the Orchestrator.

```
 Call-out ─▶ log vacancy ─▶ async query for compliant backups
                                      │
                                      ▼
                    outbound SMS + voice cascade (ranked)
                                      │
                      first "YES" ────▶ lock shift ─▶ update calendar ─▶ back to Orchestrator
```

## 4. Data read / written

- **Read:** caregiver profile, today's shift, backup roster (Neo4j), compliance status.
- **Write:** shift status (`OPEN` → `FILLED`), new assignment, cascade attempt log, audit entry.

## 5. Success & failure / edge cases

- **Success:** a compliant backup accepts; shift is re-assigned before it starts.
- **No one accepts:** exhaust the ranked list, then escalate to the human scheduler with a
  summary of who was contacted.
- **Multiple "YES" replies race:** first accepted wins; others get an "already filled" message.
- **Caller-out is not actually the assigned caregiver:** verify identity before opening the shift.
- **Backup accepts then becomes unreachable:** re-open and resume the cascade.

## 6. Integrations touched

- **Twilio Voice + SMS** — the outbound cascade. → [05 · Integrations](../05-integrations.md)
- **Neo4j** — compliant-backup query.
- **ElevenLabs** — voice for outbound calls.

## 7. Open questions

- Cascade strategy: broadcast to all backups at once, or sequential with a timeout per contact?
- How long do we wait for a reply before moving to the next backup?
- What compliance fields are hard blockers vs soft preferences in the backup query?
