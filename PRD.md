# The Healthcare Omni-Agent

**Workforce & Caregiver Logistics Engine** · Target event: **Healthcare Hack NYC**

> A single conversational voice AI that answers the phone for a home-health agency and
> handles the four jobs that eat scheduler time: back-filling call-outs, intaking &
> matching new patients, logging medication compliance, and bridging language + crisis
> escalations — all while holding perfect state across interruptions.

This file is the entry point. The full product and engineering documentation lives in
[`docs/`](./docs/).

---

## Documentation map

| Doc | What's inside |
|---|---|
| [docs/README.md](./docs/README.md) | Navigation hub + suggested reading paths |
| [00 · Executive Summary](./docs/00-executive-summary.md) | Problem, solution, value proposition, business metrics |
| [01 · Product Requirements](./docs/01-product-requirements.md) | Personas, user stories, functional requirements, scope, success metrics |
| [02 · Architecture](./docs/02-architecture.md) | Orchestrator + SubWorkflows, Dual-Agent core, barge-in, diagrams |
| [03 · SubWorkflows](./docs/03-subworkflows/README.md) | The four specialized flows (one spec each) |
| [04 · Data Model](./docs/04-data-model.md) | Neo4j graph schema, calendars, audit logs, checklists |
| [05 · Integrations](./docs/05-integrations.md) | Twilio Voice/SMS/Video, ElevenLabs, Neo4j |
| [06 · Non-Functional Requirements](./docs/06-non-functional-requirements.md) | Latency, HIPAA, reliability, security, i18n, observability |
| [07 · Roadmap & Execution Plan](./docs/07-roadmap-execution-plan.md) | Hackathon build order, milestones, demo script |
| [08 · Glossary](./docs/08-glossary.md) | Terms, personas, acronyms |

## The one-paragraph pitch

Home-health agencies spend ~27% of their operating budget on non-clinical admin labor —
mostly manual phone coordination. When a caregiver calls out at 6:00 AM, a human scheduler
burns 45 minutes dialing backups while billable shifts go unstaffed. The Healthcare
Omni-Agent replaces that scramble: a **Main Orchestrator Agent** answers every Twilio call,
recognizes the caller, detects intent, and routes into one of four **SubWorkflows**. A
**Dual-Agent core** (an Active voice agent + a Passive context ledger) keeps conversation
state flawless even when callers interrupt or switch topics mid-call.

## Status

`Draft` — hackathon build. See [07 · Roadmap & Execution Plan](./docs/07-roadmap-execution-plan.md)
for current scope and build order.
