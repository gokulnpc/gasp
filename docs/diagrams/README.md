# Architecture Diagrams

_Purpose: importable draw.io architecture diagrams for The Healthcare Omni-Agent._
_Owner: Team · Status: Draft_

Every file here is a native **draw.io / diagrams.net** file (`.drawio`, mxGraphModel XML).
Open [app.diagrams.net](https://app.diagrams.net) → **File ▸ Open From ▸ Device** (or just drag
the file onto the canvas) and it renders directly — no conversion needed. They also render
inline in VS Code with the **Draw.io Integration** extension.

The set is split so each diagram stays legible (per the "split large diagrams" ask): one master
overview plus a detailed page for the dual-agent core, each of the four SubWorkflows, and the
data layer.

## Index

| # | File | What it shows |
|---|---|---|
| 00 | [`00-system-architecture.drawio`](./00-system-architecture.drawio) | **Master.** Hub-and-spoke: Caller → Twilio → Orchestrator + Dual-Agent Core → 4 SubWorkflows → Data Layer → Staff Portal, with external services (ElevenLabs / STT / Claude), NFR band, future-scale band, rules/config, and a legend |
| 01 | [`01-dual-agent-core.drawio`](./01-dual-agent-core.drawio) | Active Agent + Passive Agent split, service wiring, and the 5-step **barge-in sequence** |
| 02 | [`02-sw1-shift-backfill.drawio`](./02-sw1-shift-backfill.drawio) | SW1 flowchart — call-out → cascade → first-YES lock, with data/integrations/edge-case panels |
| 03 | [`03-sw2-intake-matching.drawio`](./03-sw2-intake-matching.drawio) | SW2 flowchart — intake → Neo4j Cypher match → schedule, with an illustrative Cypher query |
| 04 | [`04-sw3-medlog-compliance.drawio`](./04-sw3-medlog-compliance.drawio) | SW3 flowchart — per-med questionnaire → structured JSON → append-only audit, with sample JSON |
| 05 | [`05-sw4-interpreter-escalation.drawio`](./05-sw4-interpreter-escalation.drawio) | SW4 flowchart — distress trigger → override → conference patch → two-way interpretation |
| 06 | [`06-data-layer.drawio`](./06-data-layer.drawio) | Neo4j **property graph** (nodes + relationships) alongside the Calendars / Checklists / Audit stores |

## Conventions (matches the reference style)

- **Color coding:** blue = telephony / voice, orange = orchestrator, yellow = extraction / rules,
  green = validation / success / stores, red = escalation / override, purple = data / reasoning.
- **Edges:** solid = control/data flow · red dashed = escalation/override · grey dashed = future/config.
- **Shapes:** rounded boxes with bulleted detail · numbered badges · cylinders for stores ·
  diamonds for decisions · UML actors for humans. Hand-drawn (`sketch`) style, like the reference.
- Diagrams mirror the specs in [`../03-subworkflows/`](../03-subworkflows/README.md),
  [`../02-architecture.md`](../02-architecture.md), and [`../04-data-model.md`](../04-data-model.md) —
  keep them in sync when those docs change.

## Editing tips

- To combine all pages into one multi-tab file: open the master, then **Extras ▸ Edit Diagram**,
  or use **File ▸ Import** to pull another `.drawio` in as a new page.
- Export to PNG/SVG/PDF for the pitch deck via **File ▸ Export as**.
