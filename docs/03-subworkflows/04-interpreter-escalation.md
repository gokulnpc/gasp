# SubWorkflow 4 · The Interpreter & Escalation Bridge (Always-On Guardrail)

_Purpose: override any session to connect a human and interpret in real time during a crisis._
_Owner: Team · Status: Draft_

The high-priority guardrail. Lets an English-only central office coordinate with multilingual
caregivers and patients, displacing external medical translation services billing
**$0.80–$5.00+/minute**.

## 1. Trigger

The Orchestrator detects, **during any other SubWorkflow**:
- Distress keywords,
- Severe pain reports, or
- An explicit request for a human.

Because it can fire mid-flow, this SubWorkflow is an **override**, not a normal route.

## 2. Preconditions

- A human **triage coordinator** contact is configured and reachable.
- Twilio can conference/patch multiple legs together.
- The agent has established the caller's language.

## 3. Step-by-step flow

1. **Override the active session** — pause/close the in-progress SubWorkflow while preserving
   its state via the [Passive Agent](../02-architecture.md#the-dual-agent-core-barge-in-failsafe).
2. **Hot-dial** the agency's human triage coordinator.
3. **Patch the lines together** via Twilio into a single conference.
4. Transform the Main Agent into a **real-time, two-way language interpreter** between the
   caller and the coordinator.
5. Stay on as interpreter until the crisis is resolved; log the escalation.

```
 Distress / "get me a human" detected
        │  (override — preserve prior state)
        ▼
 hot-dial triage coordinator ─▶ Twilio patches lines ─▶ Main Agent interprets both ways
                                                              │
                                                              ▼
                                                    crisis resolved ─▶ log escalation
```

## 4. Data read / written

- **Read:** caller profile & language, triage coordinator contact, prior SubWorkflow state.
- **Write:** escalation event + transcript summary to the
  [Operational Audit Logs](../04-data-model.md#operational-audit-logs); post-call summary to the portal.

## 5. Success & failure / edge cases

- **Success:** coordinator joins, interpretation flows both ways, crisis resolved.
- **Coordinator unreachable:** fall back to a secondary contact / on-call number.
- **False-positive trigger:** offer to return to the prior SubWorkflow rather than forcing escalation.
- **Language not supported:** surface the limitation and connect to the human immediately anyway.
- **Original flow must resume after resolution:** restore preserved state and hand back to the Orchestrator.

## 6. Integrations touched

- **Twilio Voice** — conferencing / patching multiple legs. → [05 · Integrations](../05-integrations.md)
- **ElevenLabs** — interpreter voice output.
- **Speech/translation pipeline** — real-time two-way interpretation.

## 7. Open questions

- What exactly counts as a "distress keyword," and how do we tune sensitivity to avoid false alarms?
- Which languages are supported for live interpretation at demo time?
- Is the interpretation consecutive (turn-taking) or simultaneous, and what latency is acceptable?
