# Documentation — The Healthcare Omni-Agent

_Purpose: the navigation hub for all product and engineering docs._
_Owner: Team · Status: Draft_

This suite breaks the product down from "why" (pitch) to "how" (engineering spec). Files
are numbered to fix reading order; every link below is relative and resolves inside this
folder.

## Index

| # | Doc | Read this if you want to know… |
|---|---|---|
| — | [Root PRD](../PRD.md) | The 30-second overview + where everything lives |
| 00 | [Executive Summary](./00-executive-summary.md) | The problem, the solution, and the business case |
| 01 | [Product Requirements](./01-product-requirements.md) | Who uses it, what it must do, and how we measure success |
| 02 | [Architecture](./02-architecture.md) | How the Orchestrator, SubWorkflows, and Dual-Agent core fit together |
| 03 | [SubWorkflows](./03-subworkflows/README.md) | The detailed spec for each of the four flows |
| 04 | [Data Model](./04-data-model.md) | The Neo4j graph, calendars, audit logs, and checklists |
| 05 | [Integrations](./05-integrations.md) | Twilio, ElevenLabs, and Neo4j wiring |
| 06 | [Non-Functional Requirements](./06-non-functional-requirements.md) | Latency, compliance, reliability, security |
| 07 | [Roadmap & Execution Plan](./07-roadmap-execution-plan.md) | What we build first and how we demo it |
| 08 | [Glossary](./08-glossary.md) | Every term and acronym in one place |

## Suggested reading paths

- **Judge / stakeholder (5 min):** [00 · Executive Summary](./00-executive-summary.md) →
  the value table → [07 · demo script](./07-roadmap-execution-plan.md#demo-script).
- **Product / design:** [01 · Product Requirements](./01-product-requirements.md) →
  [03 · SubWorkflows](./03-subworkflows/README.md).
- **Engineer building it:** [02 · Architecture](./02-architecture.md) →
  [04 · Data Model](./04-data-model.md) → [05 · Integrations](./05-integrations.md) →
  [06 · NFRs](./06-non-functional-requirements.md) → [07 · Execution Plan](./07-roadmap-execution-plan.md).

## Conventions

- Each doc opens with an H1, a one-line purpose, and an `Owner · Status` line.
- Numbered prefixes (`00-`, `01-`…) sort cleanly and define reading order.
- Cross-references use relative Markdown links.
- Diagrams are provided as both ASCII (portable) and Mermaid (renders on GitHub).
- Unresolved decisions are captured in an **Open questions** list at the bottom of the
  relevant doc, not buried in prose.
