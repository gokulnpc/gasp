# 03 · SubWorkflows

_Purpose: overview of the four specialized flows and how the Orchestrator routes into them._
_Owner: Team · Status: Draft_

The [Main Orchestrator Agent](../02-architecture.md#the-main-orchestrator-agent-the-router)
detects intent on every call and hands control to exactly one SubWorkflow, returning control
to itself when the flow completes. SubWorkflow 4 is special: it is an **always-on guardrail**
that can override any active session.

## Intent-routing table

| Trigger (detected by Orchestrator) | Routes to | Spec |
|---|---|---|
| Caregiver reports an absence / emergency call-out | **SW1 · Shift-Backfill Cascade** | [01](./01-shift-backfill-cascade.md) |
| New patient / referring family starts an intake | **SW2 · Intelligent Intake & Graph Matching** | [02](./02-intake-graph-matching.md) |
| Caregiver calls in to close out a shift | **SW3 · Med-Log & Compliance Check-In** | [03](./03-medlog-compliance.md) |
| Distress keywords, severe pain, or "get me a human" (during **any** flow) | **SW4 · Interpreter & Escalation Bridge** (override) | [04](./04-interpreter-escalation.md) |

## Shared spec template

Every SubWorkflow doc follows the same shape so they're easy to scan and compare:

1. **Trigger** — what makes the Orchestrator route here.
2. **Preconditions** — what must be true / known before the flow starts.
3. **Step-by-step flow** — the conversational + system steps.
4. **Data read / written** — which [data-model](../04-data-model.md) entities are touched.
5. **Success & failure / edge cases** — happy path plus what can go wrong.
6. **Integrations touched** — Twilio / ElevenLabs / Neo4j / Video ([05](../05-integrations.md)).
7. **Open questions** — unresolved decisions.

## Cross-cutting rules

- **State returns to the Orchestrator** at the end of every flow (except an escalation that
  ends the call).
- **Barge-in and mid-call intent switches** are handled by the
  [Dual-Agent core](../02-architecture.md#the-dual-agent-core-barge-in-failsafe), not by
  individual SubWorkflows.
- **Every completed flow contributes to the post-call summary** pushed to the staff portal.
