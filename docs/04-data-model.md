# 04 · Data Model

_Purpose: the entities the platform reads and writes — graph, calendars, logs, checklists._
_Owner: Team · Status: Draft_

The [backend data layer](./02-architecture.md#backend-data-layer-modular-api-core) is a
modular API core over four stores. Everything below is a working model for the hackathon; the
exact schemas are open questions to be firmed up during the build.

## Graph-Relational Roster (Neo4j)

The heart of [intake & matching](./03-subworkflows/02-intake-graph-matching.md) and the
[backfill cascade](./03-subworkflows/01-shift-backfill-cascade.md). Modeled as a property
graph so "find a compliant, nearby, language-matched caregiver" is a traversal, not a join.

### Nodes (proposed)

| Node | Key properties |
|---|---|
| `Caregiver` | `id`, `name`, `phone`, `status`, `availability` |
| `Patient` | `id`, `name`, `phone`, `care_needs`, `address` |
| `Certification` | `id`, `name` (e.g. CNA, HHA, RN) |
| `Language` | `code`, `name` |
| `Location` | `id`, `zip`, `geo` (for proximity) |
| `Shift` | `id`, `start`, `end`, `status` |

### Relationships (proposed)

```
(Caregiver)-[:HOLDS]->(Certification)
(Caregiver)-[:SPEAKS]->(Language)
(Caregiver)-[:BASED_AT]->(Location)
(Caregiver)-[:ASSIGNED_TO]->(Shift)
(Patient)-[:REQUIRES]->(Certification)
(Patient)-[:PREFERS]->(Language)
(Patient)-[:LOCATED_AT]->(Location)
(Patient)-[:HAS_SHIFT]->(Shift)
(Location)-[:NEAR {minutes}]->(Location)
```

### Matching query (illustrative Cypher)

```cypher
MATCH (p:Patient {id: $patientId})-[:REQUIRES]->(c:Certification),
      (p)-[:PREFERS]->(l:Language),
      (p)-[:LOCATED_AT]->(loc:Location)
MATCH (cg:Caregiver {status: 'available'})-[:HOLDS]->(c),
      (cg)-[:SPEAKS]->(l),
      (cg)-[:BASED_AT]->(cgLoc:Location)-[near:NEAR]->(loc)
RETURN cg, near.minutes AS proximity
ORDER BY proximity ASC
```

## Shift Calendars

Visit slots and their assignments; the target of inline
[calendar modification](./02-architecture.md#personalization--intelligent-routing-engine).

| Field | Notes |
|---|---|
| `shift_id` | Unique slot id |
| `patient_id` / `caregiver_id` | Assignment (caregiver nullable when `OPEN`) |
| `start` / `end` | Visit window |
| `status` | `SCHEDULED` · `OPEN` · `FILLED` · `CANCELLED` |
| `location` | Visit address / location node |

State transitions: `SCHEDULED → OPEN` (call-out) `→ FILLED` (cascade accept) — see
[SW1](./03-subworkflows/01-shift-backfill-cascade.md).

## Operational Audit Logs

**Append-only**, compliance-grade records — the output of the
[med-log flow](./03-subworkflows/03-medlog-compliance.md) and every escalation.

- Med-log entries as structured JSON (schema illustrated in the SW3 spec).
- Escalation events with transcript summaries.
- Cascade attempt history (who was contacted, when, outcome).
- Corrections handled as new appended entries with provenance, not in-place edits.

## Task Checklists

Per-patient **active daily medication / care layout** that the med-log questionnaire walks.

| Field | Notes |
|---|---|
| `patient_id` | Owner |
| `medication` | Name |
| `dose` | e.g. `500mg` |
| `schedule` | Time(s) of day / frequency |
| `route` | e.g. oral |
| `active` | Whether currently prescribed |

## Post-call summary (derived)

Not a store of its own — the [Passive Agent](./02-architecture.md#the-dual-agent-core-barge-in-failsafe)
generates a structured summary at call end and pushes it to the staff portal, referencing the
entities above.

## Open questions

- Neo4j only, or Neo4j (graph) + a relational/document store for calendars & logs?
- Where do live conversation-state snapshots live (fast cache vs graph)?
- Exact, audit-approved JSON schema for med-log entries.
- How is PHI segregated and access-controlled? → [06 · NFRs](./06-non-functional-requirements.md)
