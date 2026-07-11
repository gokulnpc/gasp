# 06 · Non-Functional Requirements

_Purpose: the qualities the system must have beyond features — latency, compliance, reliability._
_Owner: Team · Status: Draft_

## Latency (the make-or-break)

A voice agent lives or dies on perceived responsiveness. The
[Dual-Agent core](./02-architecture.md#the-dual-agent-core-barge-in-failsafe) exists to keep
the Active Agent fast while the Passive Agent does the heavy bookkeeping.

| Budget | Target |
|---|---|
| Time-to-first-audio after user stops speaking | Feels immediate (aim ≲ 1s) |
| Barge-in stop → adapt | Near-instant; no talking over the user |
| Streaming TTS start | Begin speaking before the full response is generated |

Levers: streaming STT/TTS, a lightweight Active-Agent context window, and doing DB writes on
the Passive Agent off the critical path.

## Compliance & PHI (HIPAA-aware)

The product handles patient data and medication records; treat it as PHI-adjacent even for the
demo.

- **Minimize real PHI** in the hackathon — use synthetic patients where possible.
- **Audit logs are append-only** with provenance for corrections → [04 · Data Model](./04-data-model.md#operational-audit-logs).
- Med-log output must be **structured, complete, and audit-ready** → [SW3](./03-subworkflows/03-medlog-compliance.md).
- Consider call-recording disclosure/consent prompts depending on jurisdiction (open question in [01](./01-product-requirements.md#open-questions)).

## Reliability & call recovery

- **No dropped state on interruption** — mid-call intent switches and barge-in must not lose prior inputs (FR-2/FR-3 in [01](./01-product-requirements.md)).
- **Resume after a dropped call** — partial med-logs and in-progress cascades survive and resume via caller-ID.
- **Cascade race safety** — first "YES" wins; no double-booking a shift.
- **Graceful human fallback** — if automation can't resolve, escalate to a human with full context.

## Security & auth

- Secrets in environment variables / a secrets manager — never committed. → [05 · Integrations](./05-integrations.md#secrets--configuration-to-be-filled-in)
- Validate Twilio webhook signatures on inbound requests.
- Least-privilege access to the roster, calendars, and audit logs.

## Internationalization

- Establish caller language natively at answer time and conduct the whole call in it.
- Interpreter bridge does real-time two-way translation for [escalations](./03-subworkflows/04-interpreter-escalation.md).
- Confirm the minimum supported language set for the demo.

## Observability

- Every call produces a **structured post-call summary** to the staff portal.
- Log cascade attempts, escalations, and match decisions for debugging and audit.
- Capture latency metrics per turn to protect the responsiveness budget above.

## Open questions

- What's the acceptable p95 turn latency for the demo, and how do we measure it live?
- What is the minimum viable HIPAA posture for a hackathon demo vs a real deployment?
- Do we persist full call transcripts, or only summaries + structured records?
