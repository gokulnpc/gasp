# 07 · Roadmap & Execution Plan

_Purpose: what we build, in what order, and how we demo it at Healthcare Hack NYC._
_Owner: Team · Status: Draft_

The goal for the event is a **believable live demo** of the Orchestrator answering a call,
routing intelligently, and completing at least one full SubWorkflow — with barge-in and a
post-call summary to prove the Dual-Agent core works.

## Build order (thin vertical slices)

Build the spine first, then hang SubWorkflows off it. Each milestone is demoable on its own.

| # | Milestone | Deliverable | Depends on |
|---|---|---|---|
| M0 | **Telephony spine** | Twilio answers a call, streams audio, ElevenLabs speaks back | [05](./05-integrations.md) |
| M1 | **Dual-Agent core + barge-in** | Active/Passive split; interrupt stops playback and adapts with state intact | M0, [02](./02-architecture.md) |
| M2 | **Orchestrator routing** | Caller-ID recognition + intent detection routes into a stub SubWorkflow | M1 |
| M3 | **SW1 · Shift-Backfill Cascade** | Call-out → Neo4j backup query → SMS/voice cascade → first-YES locks shift | M2, [04](./04-data-model.md) |
| M4 | **SW3 · Med-Log** | Verbal questionnaire → structured JSON → append to audit log | M2 |
| M5 | **Post-call summary** | Passive Agent emits a structured summary to the portal | M1 |
| M6 | **SW2 · Intake & Graph Matching** | Structured intake → Cypher match → write schedule | M2, M3 |
| M7 | **SW4 · Interpreter & Escalation** | Distress trigger → hot-dial + patch → two-way interpretation | M2 |
| M8 | **Video validation (stretch)** | SMS a Twilio Video link → field ↔ supervisor channel | M0 |

### Priority for the hackathon
**Must-have to demo:** M0–M5 (spine + SW1 + SW3 + summary).
**High-value if time allows:** M6, M7.
**Stretch:** M8.

## Milestones → SubWorkflow specs

- M3 → [SW1](./03-subworkflows/01-shift-backfill-cascade.md)
- M4 → [SW3](./03-subworkflows/03-medlog-compliance.md)
- M6 → [SW2](./03-subworkflows/02-intake-graph-matching.md)
- M7 → [SW4](./03-subworkflows/04-interpreter-escalation.md)

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Voice latency feels sluggish | Stream STT/TTS; keep Active-Agent context tiny; DB writes on Passive Agent → [06](./06-non-functional-requirements.md#latency-the-make-or-break) |
| Barge-in loses state | Snapshot in Passive Agent; test interrupt paths early (M1) |
| Neo4j matching too complex for the time box | Seed a small synthetic graph; hard-code proximity edges |
| Cascade race conditions | First-YES-wins lock, tested with concurrent replies |
| Real PHI / compliance exposure | Use synthetic patients → [06](./06-non-functional-requirements.md#compliance--phi-hipaa-aware) |

## Demo script

A ~4-minute run that shows the spine, one reactive flow, and the state guarantee:

1. **The 6:00 AM call-out.** A "caregiver" calls in and says they can't make their shift.
   The Orchestrator recognizes them by number and greets them by name.
2. **Cascade fires.** Show the SMS/voice cascade going out to backups; a backup replies "YES";
   the shift locks live. (SW1)
3. **Barge-in moment.** Mid-sentence, the caller interrupts to change something — the agent
   stops, adapts, and keeps prior context. (Dual-Agent core)
4. **Intent switch.** Same call pivots to closing out a shift; the agent runs the med-log
   questionnaire and reads back the structured JSON. (SW3)
5. **Escalation (optional).** Trigger a distress phrase; the agent hot-dials a human and
   interprets across languages. (SW4)
6. **The receipt.** Show the structured post-call summary landing in the staff portal.

## Definition of done (for the event)

- A live inbound call completes SW1 **and** SW3 end-to-end.
- At least one barge-in / intent-switch is demonstrated without losing state.
- A structured post-call summary is produced.
- The pitch ties each moment back to the [value metrics](./00-executive-summary.md#value-proposition--business-metrics).

## Open questions

- Team size and who owns which milestone?
- Which SubWorkflow is the "wow" moment we rehearse most?
- Do we pre-seed the Neo4j graph or build it live during intake?
