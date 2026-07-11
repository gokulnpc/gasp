# 00 · Executive Summary

_Purpose: the problem, the solution, and the business case in one place — the pitch._
_Owner: Team · Status: Draft_

## Problem scenario

Home-health agencies spend roughly **27% of their operating budget on non-clinical
administrative labor** — primarily manual coordination, shift scheduling, and tracking
caregiver compliance.

- **The 6:00 AM call-out.** When a caregiver calls out sick, a human scheduler loses ~45
  minutes manually dialing backups. The result is unstaffed shifts and forfeited billable
  hours.
- **The intake bottleneck.** Taking patient intakes by hand and cross-referencing them
  against caregiver rosters to find the right match is slow, error-prone, and delays
  time-to-first-staffing.
- **The compliance grind.** End-of-day medication logging is manual paperwork that
  introduces errors and regulatory exposure.
- **The language gap.** An English-only central office struggles to coordinate with
  multilingual caregivers and patients, and pays external medical translation services by
  the minute.

## The solution

A single conversational AI engine built on a modular **Main Agent + SubWorkflows
architecture** with a **Dual-Agent processing core** (Active Responder + Passive Context
Manager). It optimizes workforce logistics by:

1. Automating reactive **shift back-fills**,
2. Dynamically **intaking and matching** patients using graph-relational intelligence,
3. Handling daily caregiver **medication logging**, and
4. Managing **crisis escalation and live interpretation** —

all while maintaining flawless state across call interruptions and mid-call intent
switches. See [02 · Architecture](./02-architecture.md) for how it works and
[03 · SubWorkflows](./03-subworkflows/README.md) for each flow.

## Value proposition & business metrics

| Feature / SubWorkflow | Operational value | Revenue / cost metric |
|---|---|---|
| [Shift-Backfill Cascade](./03-subworkflows/01-shift-backfill-cascade.md) | Cuts frantic manual phone coordination from **45 min → ~5 min** of automated oversight | Prevents unstaffed shifts, protecting **$150–$300** in lost billable revenue per cancellation |
| [Intake & Graph Matching](./03-subworkflows/02-intake-graph-matching.md) | Eliminates manual cross-referencing for patient↔caregiver alignment | Accelerates time-to-first-staffing — captures revenue faster, shrinks waitlists |
| [Med-Log Validation](./03-subworkflows/03-medlog-compliance.md) | Removes end-of-day compliance paperwork for field staff | Produces error-free, audit-ready compliance data — prevents regulatory fines |
| [Interpreter Bridge](./03-subworkflows/04-interpreter-escalation.md) | Lets an English-only office coordinate with multilingual caregivers & patients | Displaces external medical translation billing **$0.80–$5.00+/min** |

## Why now

Ultra-low-latency voice synthesis (ElevenLabs), programmable telephony with barge-in
(Twilio), and graph databases (Neo4j) are now cheap and composable enough to replace an
entire category of manual scheduler labor with one always-available agent.

## Related

- [01 · Product Requirements](./01-product-requirements.md) — personas, scope, success metrics.
- [07 · Roadmap & Execution Plan](./07-roadmap-execution-plan.md) — how we build and demo this.
