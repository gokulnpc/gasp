# SubWorkflow 2 · Intelligent Intake & Graph-Relational Matching

_Purpose: intake a new patient and match them to the optimal caregiver using the graph._
_Owner: Team · Status: Draft_

Replaces manual cross-referencing of patient needs against the roster. Accelerates
time-to-first-staffing — capturing revenue faster and shrinking waitlists.

## 1. Trigger

A **new patient or referring family member** initiates an intake process.

## 2. Preconditions

- Access to the [Graph-Relational Roster (Neo4j)](../04-data-model.md#graph-relational-roster-neo4j)
  with caregiver certifications, languages, and location/proximity nodes.
- Write access to the [Shift Calendars](../04-data-model.md#shift-calendars).

## 3. Step-by-step flow

1. Guide the caller through **structured profile capture** — care needs, required certifications,
   language, location, schedule constraints.
2. Query the **Graph-Relational Occupational Intelligence Platform (Neo4j)** to map the
   patient's specific care requirements against the caregiver roster.
3. Match on **language, certifications, and proximity nodes** to rank candidate caregivers.
4. Propose the **optimal schedule** to the caller and confirm inline.
5. **Write the schedule directly to the calendar** and return control to the Orchestrator.

```
 Intake ─▶ structured profile capture ─▶ Neo4j graph match (language + certs + proximity)
                                                   │
                                                   ▼
                         propose optimal schedule ─▶ confirm ─▶ write to calendar
```

## 4. Data read / written

- **Read:** caregiver roster, certifications, languages, proximity/location nodes, availability.
- **Write:** new patient profile, care requirements, proposed/confirmed schedule, audit entry.

## 5. Success & failure / edge cases

- **Success:** a well-matched caregiver is proposed and the schedule is written.
- **No exact match:** relax non-critical constraints (e.g. proximity) and re-rank; surface trade-offs.
- **Partial availability:** propose a split schedule across multiple caregivers.
- **Ambiguous care needs:** ask clarifying questions before matching rather than guessing.
- **Duplicate patient:** detect an existing profile via caller-ID and update instead of creating.

## 6. Integrations touched

- **Neo4j** — the core matching query. → [05 · Integrations](../05-integrations.md)
- **Twilio Voice** + **ElevenLabs** — the intake conversation.
- **Shift Calendars API** — writing the proposed schedule.

## 7. Open questions

- Which matching factors are hard filters vs weighted scores, and what are the weights?
- How is "proximity" modeled — travel time, zip-code adjacency, or graph distance?
- Do we confirm the match with the caregiver before writing, or write provisionally and notify?
