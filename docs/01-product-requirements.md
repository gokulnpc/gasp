# 01 · Product Requirements

_Purpose: who uses the product, what it must do, and how we judge success._
_Owner: Team · Status: Draft_

## Personas

| Persona | Role | Primary needs |
|---|---|---|
| **Agency Scheduler / Admin** | Runs day-to-day staffing from the central office | Fewer manual calls, filled shifts, a clean audit trail, visibility into every interaction |
| **Caregiver** | Field staff delivering in-home care | Fast call-outs, quick shift confirmations, effortless end-of-shift med logging in their own language |
| **Patient / Referring Family** | New or existing care recipient | Easy intake, a well-matched caregiver, a reliable way to reach a human in a crisis |
| **Triage Coordinator** | Human escalation target for emergencies | To be looped in only when it matters, with real-time interpretation across the language barrier |

## Functional requirements

The system is a phone-first (Twilio Voice + SMS) conversational agent. Full behavior is
specified per flow in [03 · SubWorkflows](./03-subworkflows/README.md); the requirements
below are the product-level "musts."

- **FR-1 · Universal answer & routing.** Answer every inbound call, recognize the caller by
  phone number, greet them by name, establish language natively, and detect intent to route
  into the correct SubWorkflow. → [Architecture](./02-architecture.md)
- **FR-2 · Persistent state.** Hold global conversation context so a mid-call intent switch
  closes one SubWorkflow and opens another **without dropping the call**.
- **FR-3 · Barge-in tolerance.** When a caller interrupts mid-sentence, stop playback, drop
  in-flight generation, and adapt to the new direction without losing prior inputs.
- **FR-4 · Shift back-fill.** Detect a call-out, log the vacancy, and fire an outbound
  SMS/voice cascade to compliant backups; lock the shift on the first "YES."
- **FR-5 · Intelligent intake & matching.** Capture a structured patient profile and match
  against the caregiver roster on language, certifications, and proximity; write the proposed
  schedule to the calendar.
- **FR-6 · Med-log & compliance.** Run a strict verbal questionnaire to confirm administered
  doses against the patient's daily layout; append structured JSON to audit-ready logs.
- **FR-7 · Escalation & interpretation.** On distress keywords, severe pain, or an explicit
  request for a human, override the session, hot-dial the triage coordinator, patch the lines,
  and act as a real-time two-way interpreter.
- **FR-8 · Inline calendar changes.** Let users conversationally accept, confirm, or
  reschedule visit slots during any call.
- **FR-9 · Transparency summaries.** On call end, generate a structured summary and push it to
  the agency staff portal.
- **FR-10 · Visual validation (optional).** When a check-in needs visual confirmation, text a
  Twilio Video link connecting field staff to a remote supervisor.

## User stories

- As a **caregiver**, when I call out at 6 AM, I want the agent to find my replacement so I
  don't have to make calls while sick.
- As a **scheduler**, I want vacancies filled automatically so I only step in when the cascade
  can't find anyone.
- As a **referring family member**, I want to describe a patient's needs once and get a matched
  caregiver and a proposed schedule on the same call.
- As a **caregiver**, I want to confirm the meds I gave by voice at end of shift instead of
  filling out forms.
- As a **patient in distress**, I want to be connected to a human immediately, in my language.
- As an **admin**, I want a written summary of every call in the portal so nothing is lost.

## Scope

### In scope (hackathon MVP)
- Inbound call answering, caller-ID recognition, and intent routing.
- SubWorkflow 1 (Shift-Backfill Cascade) and SubWorkflow 3 (Med-Log) as the primary demos.
- Dual-Agent state with barge-in handling.
- Post-call structured summary.
- See [07 · Roadmap & Execution Plan](./07-roadmap-execution-plan.md) for the exact build order.

### Out of scope (for the hackathon)
- Production EHR integration and real PHI.
- Full multi-tenant agency management / billing.
- Native mobile apps (phone + SMS + a web portal view only).
- Automated caregiver credential verification against external registries.

## Success metrics

| Metric | Target |
|---|---|
| Time to fill a called-out shift | 45 min → **≤ 5 min** |
| Unstaffed shifts avoided (revenue protected) | **$150–$300** per prevented cancellation |
| Med-log entries captured as structured JSON | **100%** of completed check-ins |
| Voice response latency (perceived) | Feels real-time (see [06 · NFRs](./06-non-functional-requirements.md)) |
| Calls handled without a dropped/lost-state failure | **≥ 95%** in the demo |

## Open questions

- Which languages must the interpreter bridge support at minimum for the demo?
- Is a lightweight web staff-portal view in scope, or do summaries go somewhere simpler (e.g. a channel)?
- Do we need consent/recording disclosure prompts for the demo jurisdiction?
