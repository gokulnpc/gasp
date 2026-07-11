# CLAUDE.md

Project context for **The Healthcare Omni-Agent** (Workforce & Caregiver Logistics Engine) —
a phone-first conversational voice AI for home-health agencies. Target event: **Healthcare
Hack NYC**. Status: **hackathon build (Draft)**.

This file is the map. **Read the linked doc before working in its area** — the docs hold the
authoritative detail; this file just keeps the context wired together.

## What this product is

A single voice AI that answers every inbound call. A **Main Orchestrator Agent** recognizes
the caller, detects intent, holds global state, and routes into one of four **SubWorkflows**.
A **Dual-Agent core** (Active voice agent + Passive context ledger) keeps responses fast and
state flawless across interruptions (barge-in) and mid-call intent switches.

## Documentation map — read the relevant doc before editing

Start here → [`docs/README.md`](./docs/README.md) (navigation hub + reading paths).

| Topic | Doc | Read when you're working on… |
|---|---|---|
| Overview / entry point | [`PRD.md`](./PRD.md) | The 30-second pitch + where everything lives |
| Problem & business case | [`docs/00-executive-summary.md`](./docs/00-executive-summary.md) | Pitch, value proposition, revenue metrics |
| Product requirements | [`docs/01-product-requirements.md`](./docs/01-product-requirements.md) | Personas, user stories, scope, success metrics |
| Architecture | [`docs/02-architecture.md`](./docs/02-architecture.md) | Orchestrator, Dual-Agent core, barge-in, diagrams |
| SubWorkflows (overview) | [`docs/03-subworkflows/README.md`](./docs/03-subworkflows/README.md) | Intent-routing table + shared spec template |
| SW1 · Shift-Backfill | [`docs/03-subworkflows/01-shift-backfill-cascade.md`](./docs/03-subworkflows/01-shift-backfill-cascade.md) | The 6 AM call-out cascade |
| SW2 · Intake & Matching | [`docs/03-subworkflows/02-intake-graph-matching.md`](./docs/03-subworkflows/02-intake-graph-matching.md) | New-patient intake + Neo4j matching |
| SW3 · Med-Log | [`docs/03-subworkflows/03-medlog-compliance.md`](./docs/03-subworkflows/03-medlog-compliance.md) | End-of-shift medication logging |
| SW4 · Interpreter/Escalation | [`docs/03-subworkflows/04-interpreter-escalation.md`](./docs/03-subworkflows/04-interpreter-escalation.md) | Crisis escalation + live interpretation |
| Data model | [`docs/04-data-model.md`](./docs/04-data-model.md) | Neo4j graph/Cypher, calendars, audit logs, checklists |
| Integrations | [`docs/05-integrations.md`](./docs/05-integrations.md) | Twilio, ElevenLabs, Neo4j wiring + secrets |
| Non-functional reqs | [`docs/06-non-functional-requirements.md`](./docs/06-non-functional-requirements.md) | Latency, HIPAA/PHI, reliability, security, i18n |
| Roadmap & execution | [`docs/07-roadmap-execution-plan.md`](./docs/07-roadmap-execution-plan.md) | Build order (M0–M8), risks, demo script |
| Glossary | [`docs/08-glossary.md`](./docs/08-glossary.md) | Any unfamiliar term or acronym |

## Key facts to keep in context

- **Architecture:** hub-and-spoke — one Orchestrator (hub) routes into four SubWorkflows
  (spokes). SubWorkflow 4 (escalation) is an always-on override that can interrupt any flow.
- **Dual-Agent core:** the **Active Agent** (ElevenLabs voice I/O, lightweight context) stays
  fast; the **Passive Agent** (context ledger) does DB writes and holds global state. On
  barge-in, the Active Agent drops generation and pulls the Passive Agent's state snapshot.
- **Tech stack:** Twilio (Voice/SMS/Video + Media Streams), ElevenLabs (TTS), Neo4j (roster +
  Cypher matching). Details in [`docs/05-integrations.md`](./docs/05-integrations.md).
- **Build priority:** M0–M5 are must-have for the demo (telephony spine → Dual-Agent core →
  Orchestrator → SW1 + SW3 → post-call summary). See
  [`docs/07-roadmap-execution-plan.md`](./docs/07-roadmap-execution-plan.md).

## Working conventions

- **Docs are the source of truth.** When behavior changes, update the relevant `docs/*.md` in
  the same change — don't let this file or the docs drift.
- **Doc structure:** numbered filename prefixes fix reading order; each doc opens with an H1,
  a one-line purpose, and an `Owner · Status` line; cross-references use relative Markdown
  links; diagrams are provided as both ASCII and Mermaid.
- **Open questions** live at the bottom of each doc — check and update them; resolve rather
  than duplicate.
- **Secrets:** never commit keys. Twilio/ElevenLabs/Neo4j credentials go in env vars / a
  secrets manager — see [`docs/05-integrations.md`](./docs/05-integrations.md#secrets--configuration-to-be-filled-in).
- **PHI:** prefer synthetic patient data; audit logs are append-only. See
  [`docs/06-non-functional-requirements.md`](./docs/06-non-functional-requirements.md#compliance--phi-hipaa-aware).

## Repo layout

```
gasp/
├── CLAUDE.md   ← you are here (project context + doc map)
├── PRD.md      ← overview + documentation map
└── docs/       ← full product & engineering docs (see table above)
```
