# 09 · Work Split (4-Person Build)

_Purpose: how the hackathon build is divided across four people, with a copy-pasteable prompt each._
_Owner: Team · Status: Draft_

The critical path (telephony → core → workflows) is inherently sequential, so this split is
built around **contract-first parallelism**: agree three seams in hour 0, then everyone builds
against mocks and integrates later. Streams map to the milestones in
[07 · Roadmap & Execution Plan](./07-roadmap-execution-plan.md).

## Division of labor

| Person | Owns | Milestones | Primary docs |
|---|---|---|---|
| **1 · Telephony & Voice I/O** | Twilio transport + ElevenLabs/STT + barge-in playback | M0, voice half of M1, M8 | [05](./05-integrations.md), [02](./02-architecture.md) (barge-in), [06](./06-non-functional-requirements.md) |
| **2 · Orchestrator & State core** | Router + Passive Agent + state + post-call summary | M1 (agent), M2, M5 | [02](./02-architecture.md), [03/README](./03-subworkflows/README.md), [01](./01-product-requirements.md) |
| **3 · Data & Graph** | Neo4j + Cypher + calendars + audit logs | data for M3/M4/M6 | [04](./04-data-model.md), [05](./05-integrations.md) (Neo4j) |
| **4 · SubWorkflows & Demo** | The four flows + integration + demo | M3, M4, M6, M7, demo | [03/*](./03-subworkflows/README.md), [07](./07-roadmap-execution-plan.md), [01](./01-product-requirements.md) |

## Hour 0 — lock these together before splitting (~30 min)

These are the seams. Agree them up front and nobody blocks anyone:

1. **Stack & repo layout** — language (Node vs Python), one repo, branch-per-person, agreed folder boundaries.
2. **Telephony event contract** (Person 1 ⇄ 2) — events *out*: `call.started{callerNumber}`,
   `user.utterance{text}`, `barge_in`, `dtmf`, `call.ended`; commands *in*: `speak(text)`,
   `stop_speaking()`, `dial(number)`, `send_sms(to,body)`, `start_conference(legs)`.
3. **SubWorkflow contract** (Person 2 ⇄ 4) — each flow implements `enter(ctx)`,
   `handleTurn(utterance, ctx)`, `exit()` over a shared state object; Orchestrator owns
   routing + override.
4. **Data API shape** (Person 3 ⇄ 2,4) — `getCallerByPhone`, `findBackups(shiftId)`,
   `matchCaregivers(patientProfile)`, `getShift/updateShift`, `getMedLayout(patientId)`,
   `appendAuditLog(entry)`.
5. **Synthetic seed data** — Person 3 publishes a small fake graph + patients so everyone can
   test without real PHI.

## Assumptions

- SW4's escalation is a **shared effort** between Person 1 (conferencing) and Person 4
  (trigger + interpret).
- The **stack/language is a team decision** for hour 0, not pre-picked here.
- **Person 4 is the most dependency-heavy** stream — the mock-first approach is what keeps
  them unblocked.

---

## The four prompts

### 👤 Person 1 — Telephony & Voice I/O

```
You own the telephony spine and voice I/O for The Healthcare Omni-Agent — the shared
foundation every other stream builds on. Read CLAUDE.md, then docs/05-integrations.md,
the barge-in section of docs/02-architecture.md, and the latency section of
docs/06-non-functional-requirements.md.

Build (milestones M0 + voice-half of M1, plus M8 stretch):
- Twilio inbound call answering + Media Streams WebSocket for live audio.
- ElevenLabs streaming TTS (start speaking before the full response is ready) and a
  streaming STT path for user utterances.
- Barge-in: when the caller speaks over playback, stop Twilio audio immediately and emit
  a `barge_in` event.
- Outbound transport for the cascade: place voice calls and send SMS.
- Conferencing/line-patching for escalation (used by SW4).
- (Stretch M8) SMS a Twilio Video link for visual validation.

Expose the agreed telephony event contract: emit call.started{callerNumber},
user.utterance{text}, barge_in, dtmf, call.ended; accept speak(text), stop_speaking(),
dial(number), send_sms(to,body), start_conference(legs).

Deliver on day 0 a MOCK event emitter that replays a scripted call, so Persons 2 and 4
can build without a live phone. Validate Twilio webhook signatures; keep all keys in env
vars. Definition of done: a real inbound call is answered, transcribed, spoken back to,
and cleanly interrupted — measured against the latency budget in doc 06.
```

### 👤 Person 2 — Orchestrator & Dual-Agent State

```
You own the brain: the Main Orchestrator Agent and the Passive Agent (context ledger).
Read CLAUDE.md, then docs/02-architecture.md in full, docs/03-subworkflows/README.md
(routing table), and FR-1/2/3 and FR-9 in docs/01-product-requirements.md.

Build (milestones M1 agent-side + M2 + M5):
- Orchestrator: caller-ID recognition (via Person 3's getCallerByPhone), intent detection,
  and routing into the correct SubWorkflow using the intent-routing table.
- Mid-call intent switching: cleanly close one SubWorkflow and open another without
  dropping the call.
- Passive Agent: maintain global conversation state, take state snapshots, and do DB
  writes OFF the critical path so the Active Agent stays fast. On barge_in, hand the latest
  snapshot back so the flow resumes with context intact.
- SubWorkflow 4 override handling: let escalation interrupt any active session and restore
  the prior flow afterward.
- Post-call summary (M5): on call.ended, generate a structured summary and push it to the
  staff portal.

You OWN the SubWorkflow contract (enter/handleTurn/exit + shared state) — publish it hour 0
so Person 4 can build against it. Consume Person 1's telephony events and Person 3's data
API; build against their mocks until integration. Definition of done: a mock call routes to
the right stub SubWorkflow, survives an intent switch and a barge-in without losing state,
and emits a summary.
```

### 👤 Person 3 — Data & Graph

```
You own the entire backend data layer. Read CLAUDE.md, then docs/04-data-model.md in full,
the Neo4j section of docs/05-integrations.md, and skim the SW1/SW2/SW3 specs to see which
queries they need.

Build (data behind M3/M4/M6):
- Neo4j: implement the node/relationship schema from doc 04 and SEED a small synthetic
  graph (caregivers, patients, certifications, languages, proximity edges) — publish it
  hour 0 so everyone can test without real PHI.
- Cypher queries: the ranked caregiver-match query (for SW2 intake) and the compliant-backup
  query (for SW1 cascade). Decide which factors are hard filters vs weighted scores.
- Shift calendar store + API with the status transitions SCHEDULED → OPEN → FILLED, plus
  race-safe shift locking (first-YES-wins, no double-booking).
- Append-only audit log store for med-log JSON, escalation events, and cascade history —
  corrections as new appended entries with provenance, never in-place edits.
- Task-checklist store for each patient's active daily medication layout.

Expose the agreed data API: getCallerByPhone, findBackups(shiftId),
matchCaregivers(profile), getShift/updateShift, getMedLayout(patientId), appendAuditLog.
Persons 2 and 4 depend on this shape — agree it hour 0, then build independently. Keep
credentials in env vars. Definition of done: each API function returns correct results
against the seeded graph, and shift locking is proven safe under concurrent accepts.
```

### 👤 Person 4 — SubWorkflows & Product Integration

```
You own the four SubWorkflows — the product surface — and the demo. Read CLAUDE.md, then
every file in docs/03-subworkflows/, the demo script in docs/07-roadmap-execution-plan.md,
and the user stories in docs/01-product-requirements.md.

Build each flow against Person 2's SubWorkflow contract (enter/handleTurn/exit) and Person
3's data API, in this priority order:
- SW1 · Shift-Backfill Cascade (M3): call-out → log vacancy → findBackups → fire cascade
  via Person 1's SMS/voice → first "YES" locks the shift (use Person 3's race-safe lock).
- SW3 · Med-Log (M4): run the strict per-med questionnaire → translate voice confirmations
  into the structured JSON schema in the SW3 spec → appendAuditLog. Handle missed/refused/PRN.
- SW2 · Intake & Matching (M6): structured profile capture → matchCaregivers → propose
  schedule → write to calendar.
- SW4 · Interpreter & Escalation (M7): detect distress/human-request, trigger the override,
  and drive Person 1's conferencing to patch in a human + interpret two-way. Pair with
  Person 1 on the telephony bits.
- Inline calendar modification during any flow.

Build against Persons 2 and 3's mocks first; integrate as their real pieces land. You also
own rehearsing the demo script in doc 07 end-to-end. Definition of done: SW1 and SW3 run
fully against real telephony + data, with a barge-in/intent-switch shown live and a
structured summary produced.
```

## Open questions

- Node or Python for the shared stack?
- Who owns the staff-portal summary view — Person 2 (produces it) or Person 4 (surfaces it)?
- Do we integrate continuously from hour 1, or hold a dedicated integration block near the end?
