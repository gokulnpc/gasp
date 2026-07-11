"""Person 1's core deliverable (M0 + voice half of M1): the LiveKit voice
agent that handles a live call's audio — ElevenLabs STT/TTS, the recording
disclosure, and barge-in signaling.

Deliberately has NO LLM and no business logic: the "brain" is Person 2's
Orchestrator, which listens to events on the EventBus and drives speech with
`speak` commands. Until Person 2 wires in, run with GASP_ECHO_MODE=1 for a
self-contained test loop (agent acknowledges each utterance).

Run (after `lk`/setup_livekit_sip.py has created the inbound trunk +
dispatch rule, and the Twilio Origination URI points at LiveKit):

    python -m telephony.voice_agent dev
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, JobContext
from livekit.plugins import elevenlabs, silero

from .contracts import EventEnvelope
from .event_bus import EventBus

load_dotenv()

logger = logging.getLogger("telephony.voice-agent")

# Shared bus instance: Person 2's code imports this and subscribes/sends
# commands against it (in-process transport, per team decision).
bus = EventBus()

RECORDING_DISCLOSURE = {
    "en": "This call may be recorded for quality and training purposes.",
    "es": "Esta llamada puede ser grabada con fines de calidad y capacitacion.",
}

GREETING = {
    "en": "Hello, you've reached the care coordination line. How can I help you today?",
    "es": "Hola, se ha comunicado con la linea de coordinacion de cuidado. Como puedo ayudarle hoy?",
}

ECHO_MODE = os.getenv("GASP_ECHO_MODE", "0") == "1"


def _tts_for(language: str) -> elevenlabs.TTS:
    voice_id = os.getenv(
        f"ELEVEN_VOICE_ID_{language.upper()}",
        os.getenv("ELEVEN_VOICE_ID_EN", ""),
    )
    kwargs: dict = {"model": "eleven_flash_v2_5", "language": language}
    if voice_id:
        kwargs["voice_id"] = voice_id
    return elevenlabs.TTS(**kwargs)


class VoiceIOAgent(Agent):
    """Transport-only agent: no LLM, no tools. Person 2 drives replies."""

    def __init__(self) -> None:
        super().__init__(instructions="(unused — no LLM attached; speech is command-driven)")


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    call_id = ctx.room.name  # convention: "call-..." from the SIP dispatch rule

    # The SIP participant (the PSTN caller) — wait for them to land in the room.
    participant = await ctx.wait_for_participant()
    caller_number = participant.attributes.get("sip.phoneNumber", "unknown")
    logger.info("call %s from %s (echo_mode=%s)", call_id, caller_number, ECHO_MODE)

    # Language: default English. Detection mechanism (DTMF vs profile lookup)
    # is still an open team decision; Spanish voice/STT is ready when it lands.
    language = "en"

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=elevenlabs.STT(language_code=language),
        tts=_tts_for(language),
        allow_interruptions=True,
    )

    # ---- events out (Person 1 -> Person 2) --------------------------------

    bus.emit(EventEnvelope("participant.joined", call_id, {
        "caller_number": caller_number,
        "room_name": ctx.room.name,
    }))

    @session.on("user_input_transcribed")
    def _on_transcript(ev) -> None:
        bus.emit(EventEnvelope(
            "transcript.final" if ev.is_final else "transcript.partial",
            call_id,
            {"text": ev.transcript, "language": getattr(ev, "language", None)},
        ))
        if ECHO_MODE and ev.is_final and ev.transcript.strip():
            try:
                logger.info("echo: saying back %r", ev.transcript)
                # allow_interruptions=False so a noisy line can't instantly
                # kill the echo before any audio is heard (echo-mode only).
                session.say(f"I heard you say: {ev.transcript}", allow_interruptions=False)
            except Exception:
                logger.exception("echo say failed")

    @session.on("speech_created")
    def _on_speech_created(ev) -> None:
        logger.info("speech created (source=%s)", getattr(ev, "source", "?"))

    # Barge-in: the caller starts speaking while the agent is mid-utterance.
    # AgentSession already halts TTS playback itself; our contract obligation
    # is to emit `barge_in` promptly so Person 2's Passive Agent can snapshot.
    @session.on("user_state_changed")
    def _on_user_state(ev) -> None:
        if ev.new_state == "speaking" and session.agent_state == "speaking":
            bus.emit(EventEnvelope("barge_in", call_id, {}))

    @ctx.room.on("sip_dtmf_received")
    def _on_dtmf(dtmf: rtc.SipDTMF) -> None:
        bus.emit(EventEnvelope("dtmf", call_id, {"digit": dtmf.digit}))

    @ctx.room.on("participant_disconnected")
    def _on_disconnect(p: rtc.RemoteParticipant) -> None:
        if p.identity == participant.identity:
            bus.emit(EventEnvelope("call.ended", call_id, {"reason": "caller_hangup"}))

    # ---- commands in (Person 2/4 -> Person 1) -----------------------------

    @bus.on_command("speak")
    def _on_speak(command: dict) -> None:
        if command.get("call_id") != call_id:
            return
        session.say(
            command["text"],
            allow_interruptions=command.get("allow_interruptions", True),
        )

    @bus.on_command("stop_speaking")
    def _on_stop(command: dict) -> None:
        if command.get("call_id") != call_id:
            return
        session.interrupt()

    # ---- go live -----------------------------------------------------------

    await session.start(agent=VoiceIOAgent(), room=ctx.room)

    # Compliance: disclosure first, not interruptible, then greet.
    await session.say(RECORDING_DISCLOSURE[language], allow_interruptions=False)
    await session.say(GREETING[language], allow_interruptions=True)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
