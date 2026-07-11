# SubWorkflow 3 · Caregiver Med-Log & Compliance Check-In

_Purpose: verbally confirm administered doses and append audit-ready structured logs._
_Owner: Team · Status: Draft_

Removes end-of-day compliance paperwork for field staff and produces error-free, audit-ready
data that prevents regulatory fines.

## 1. Trigger

A **caregiver calls in to close out their shift**.

## 2. Preconditions

- Caller recognized as a caregiver with an active/just-ended shift.
- The patient's **active daily medication layout** exists in the
  [Task Checklists](../04-data-model.md#task-checklists).

## 3. Step-by-step flow

1. Identify the shift and patient being closed out.
2. Execute a **strict questionnaire** — walk the patient's active daily layout and verbally
   confirm each administered dose (drug, dose, time).
3. Handle exceptions conversationally (missed dose, refused dose, PRN given).
4. **Translate verbal confirmations into structured JSON.**
5. **Append** the record to the agency's audit-ready compliance logs and return control to
   the Orchestrator.

```
 Close-out ─▶ strict per-med questionnaire ─▶ capture confirmations + exceptions
                                                       │
                                                       ▼
                                verbal → structured JSON ─▶ append to audit log
```

Example structured output (illustrative):

```json
{
  "shift_id": "shift_20260711_am",
  "caregiver_id": "cg_014",
  "patient_id": "pt_209",
  "administered": [
    { "medication": "Metformin", "dose": "500mg", "time": "08:05", "status": "given" },
    { "medication": "Lisinopril", "dose": "10mg", "time": "08:05", "status": "given" },
    { "medication": "Atorvastatin", "dose": "20mg", "time": "20:00", "status": "not_given", "reason": "patient refused" }
  ],
  "confirmed_by": "voice",
  "logged_at": "2026-07-11T20:15:00Z"
}
```

## 4. Data read / written

- **Read:** patient's active daily med layout / task checklist, shift assignment.
- **Write:** structured med-log JSON appended to the append-only
  [Operational Audit Logs](../04-data-model.md#operational-audit-logs).

## 5. Success & failure / edge cases

- **Success:** every scheduled med is confirmed or exception-noted; JSON appended.
- **Missed / refused dose:** record status + reason rather than skipping the entry.
- **Med not on the layout was given:** capture as an ad-hoc/PRN entry flagged for review.
- **Caregiver unsure of exact time:** capture a best-estimate flag for later reconciliation.
- **Call drops mid-log:** partial log is preserved; resume on callback via caller-ID.

## 6. Integrations touched

- **Twilio Voice** + **ElevenLabs** — the questionnaire conversation. → [05 · Integrations](../05-integrations.md)
- **Audit log store** — append-only compliance records.

## 7. Open questions

- What is the exact JSON schema and which fields are mandatory for audit compliance?
- Do we require read-back confirmation ("you gave 500mg Metformin at 8:05, correct?") on every med?
- How are corrections handled — new appended entry vs amendment with provenance?
