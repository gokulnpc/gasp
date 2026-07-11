# 08 · Glossary

_Purpose: one definition per term and acronym used across the docs._
_Owner: Team · Status: Draft_

## Core concepts

- **Main Orchestrator Agent** — The universal gateway that answers every call, recognizes the
  caller, detects intent, holds global state, and routes into a SubWorkflow. → [02](./02-architecture.md#the-main-orchestrator-agent-the-router)
- **SubWorkflow** — A specialized conversational flow the Orchestrator routes into. There are
  four; SubWorkflow 4 can override the others. → [03](./03-subworkflows/README.md)
- **Dual-Agent core** — The pairing of an Active Agent and a Passive Agent that keeps the system
  fast while never losing state. → [02](./02-architecture.md#the-dual-agent-core-barge-in-failsafe)
- **Active Agent (Voice I/O)** — Handles the real-time audio stream with a lightweight context
  window; powered by ElevenLabs.
- **Passive Agent (Context Ledger)** — Listens in the background, updates the database, and
  maintains global conversation state; generates the post-call summary.
- **Barge-in** — A caller interrupting the AI mid-sentence; Twilio halts playback, the Active
  Agent drops generation and adapts using the Passive Agent's state snapshot.
- **Cascade** — The ranked outbound SMS/voice sequence to backup caregivers in the
  [Shift-Backfill](./03-subworkflows/01-shift-backfill-cascade.md) flow.
- **Graph-Relational Occupational Intelligence Platform** — The Neo4j-backed roster used to
  match patients to caregivers by language, certification, and proximity.
- **Hub-and-spoke** — The architecture pattern: one Orchestrator (hub) routing into
  SubWorkflows (spokes).
- **Caller-ID recognition** — Using the inbound phone number to identify the caller and pull
  their profile, shifts, or compliance records.
- **Post-call summary** — The structured recap the Passive Agent pushes to the staff portal at
  call end.

## Personas

- **Agency Scheduler / Admin** — Runs staffing from the central office.
- **Caregiver** — Field staff delivering in-home care.
- **Patient / Referring Family** — The care recipient or their advocate.
- **Triage Coordinator** — The human escalation target for emergencies. → [01](./01-product-requirements.md#personas)

## Technology

- **Twilio** — Programmable Voice, SMS, and Video; the telephony backbone. → [05](./05-integrations.md#twilio-voice-sms-video)
- **ElevenLabs** — Ultra-low-latency, natural voice synthesis for the Active Agent.
- **Neo4j** — Graph database backing the roster and matching queries.
- **Cypher** — Neo4j's query language, used for the matching/backfill queries. → [04](./04-data-model.md)
- **Media Streams** — Twilio's WebSocket audio streaming feature.
- **TTS / STT** — Text-to-Speech / Speech-to-Text.

## Domain & compliance

- **PHI** — Protected Health Information; patient data subject to privacy rules.
- **HIPAA** — US law governing PHI handling. → [06](./06-non-functional-requirements.md#compliance--phi-hipaa-aware)
- **Med-Log** — The verbal medication-administration record captured at shift close-out. → [03](./03-subworkflows/03-medlog-compliance.md)
- **PRN** — "Pro re nata" — medication given as needed rather than on a fixed schedule.
- **Audit log** — Append-only, compliance-grade record of what happened.
- **Billable shift** — A staffed visit the agency can bill for; the revenue at risk in a call-out.
