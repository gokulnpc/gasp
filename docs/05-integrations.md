# 05 · Integrations

_Purpose: the external services the platform depends on and how they wire in._
_Owner: Team · Status: Draft_

Three primary integrations power the product. This doc is the single place to track keys,
webhooks, and responsibilities; specific usage is cross-linked from each SubWorkflow.

## Twilio (Voice, SMS, Video)

The telephony backbone — every interaction starts here.

| Capability | Used for |
|---|---|
| **Programmable Voice** | Inbound call answering; outbound cascade calls; conferencing/patching for [escalation](./03-subworkflows/04-interpreter-escalation.md) |
| **Barge-in / playback control** | Halting audio when a caller interrupts → [Dual-Agent core](./02-architecture.md#the-dual-agent-core-barge-in-failsafe) |
| **SMS** | Outbound backup cascade in [SW1](./03-subworkflows/01-shift-backfill-cascade.md); Video links |
| **Media Streams (WebSocket)** | Streaming call audio to the Active Agent and tokens to the Passive Agent |
| **Video** | Secure field-staff ↔ supervisor channel for [visual validation](./02-architecture.md#video-api-integration-layer) |

**Wiring:** Twilio webhooks hit the app's call/SMS handlers; Media Streams open a WebSocket to
the Dual-Agent core. Caller-ID from the inbound number drives
[recognition & routing](./02-architecture.md#personalization--intelligent-routing-engine).

## ElevenLabs (Voice I/O)

Powers the **Active Agent** with ultra-low-latency, natural voice delivery.

- Streaming TTS so speech starts before the full response is generated.
- Must support fast interruption (stop-on-barge-in) to pair with Twilio playback control.
- Voice output for outbound cascade calls and the interpreter bridge.

→ See latency targets in [06 · NFRs](./06-non-functional-requirements.md).

## Neo4j (Graph-Relational Roster)

The **Graph-Relational Occupational Intelligence Platform** behind matching and backfill.

- Stores caregivers, patients, certifications, languages, and proximity — see the
  [data model](./04-data-model.md#graph-relational-roster-neo4j).
- Serves the ranked-candidate query for [intake matching](./03-subworkflows/02-intake-graph-matching.md)
  and the compliant-backup query for the [cascade](./03-subworkflows/01-shift-backfill-cascade.md).

## Supporting services

- **Speech-to-text / translation pipeline** — real-time two-way interpretation for
  [SW4](./03-subworkflows/04-interpreter-escalation.md).
- **Staff portal** — destination for post-call structured summaries.
- **Calendar store** — read/write of [shift slots](./04-data-model.md#shift-calendars).

## Secrets & configuration (to be filled in)

| Service | Needed | Where |
|---|---|---|
| Twilio | Account SID, Auth Token, phone number(s), webhook URLs | env / secrets manager |
| ElevenLabs | API key, voice ID | env / secrets manager |
| Neo4j | URI, user, password | env / secrets manager |

> Do not commit secrets. Use environment variables or a secrets manager; see
> [06 · NFRs — Security](./06-non-functional-requirements.md#security--auth).

## Open questions

- Which STT + translation provider backs the interpreter bridge?
- Managed Neo4j (Aura) or self-hosted for the hackathon?
- Do we need a separate outbound-caller-ID number for the cascade?
