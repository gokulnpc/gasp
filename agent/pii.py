"""Bare PII/PHI scrubbing before text reaches the LLM.

Regex-based ingestion gate (docs/diagrams/07-guardrail-flow): strips common
identifiers from user turns and prior user messages in the chat context sent to
the model. Does not touch tool outputs or telephony matching — only LLM-facing
transcript text.

Production would swap this for Presidio + a PHI vault; this is the hackathon
minimum viable guardrail.
"""

from __future__ import annotations

import re
from typing import Iterable

from livekit.agents import llm

# Order matters: more specific patterns first.
_REDACTIONS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (
        re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
            r"\.[A-Za-z]{2,}\b"
        ),
        "[EMAIL]",
    ),
    (re.compile(r"\b\+1\d{10}\b"), "[PHONE]"),
    (
        re.compile(
            r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "[PHONE]",
    ),
    (
        re.compile(
            r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)?\d{2}\b"
        ),
        "[DOB]",
    ),
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[CARD]"),
    (
        re.compile(
            r"\b(?:MRN|mrn|medical record)\s*[#:]?\s*\d+\b",
            re.IGNORECASE,
        ),
        "[MRN]",
    ),
    (
        re.compile(
            r"\b\d{1,5}\s+(?:[A-Za-z]+\s+){0,3}"
            r"(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court)\b\.?",
            re.IGNORECASE,
        ),
        "[ADDRESS]",
    ),
]


def redact_text(text: str) -> tuple[str, list[str]]:
    """Return scrubbed text and labels for categories that matched."""
    if not text:
        return text, []

    out = text
    hits: list[str] = []
    for pattern, repl in _REDACTIONS:
        if pattern.search(out):
            hits.append(repl.strip("[]"))
            out = pattern.sub(repl, out)
    return out, hits


def _redact_message(msg: llm.ChatMessage) -> list[str]:
    hits: list[str] = []
    new_content: list = []
    for chunk in msg.content:
        if isinstance(chunk, str):
            scrubbed, found = redact_text(chunk)
            new_content.append(scrubbed)
            hits.extend(found)
        else:
            new_content.append(chunk)
    msg.content = new_content
    return hits


def scrub_for_llm(
    turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
) -> list[str]:
    """Scrub the incoming user turn and prior user messages in turn_ctx."""
    all_hits: list[str] = []
    all_hits.extend(_redact_message(new_message))
    for item in turn_ctx.items:
        if isinstance(item, llm.ChatMessage) and item.role == "user":
            all_hits.extend(_redact_message(item))
    # de-dupe while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for label in all_hits:
        if label not in seen:
            seen.add(label)
            ordered.append(label)
    return ordered
