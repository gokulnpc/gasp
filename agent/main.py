"""GASP Healthcare Omni-Agent - LiveKit entry point (Person 2: Orchestrator & State).

One Orchestrator answers the call, recognizes the caller, and routes into
SubWorkflows (SW1 backfill / SW2 intake / SW3 med-log / SW4 escalation).
A Passive ledger watches every turn off the voice path; telephony side
effects and the data layer are simulated - no Twilio needed yet.

Run it:
  python main.py console        voice agent (mic)
  python worker.py              dispatch worker (second terminal)
  python main.py dev            LiveKit Cloud (SIP later)

Demo happy path (console):
  "I can't make my ten A M shift, I have a fever"     -> SW1 + live cascade
  "also let me close out yesterday's shift meds"      -> intent switch to SW3
  "I fell, I'm bleeding badly"                        -> SW4 override any time
  Ctrl+C / hang up                                    -> post-call summary banner
"""

import logging
import uuid

from livekit.agents import (AgentServer, AgentSession, JobContext,
                            RoomInputOptions, cli, inference)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import summary as summary_mod
from config import (AGENT_NAME, CONSOLE_CALLER_PHONE, LLM_MODEL, STT_MODEL,
                    TTS_MODEL, startup_report)
from orchestrator import OrchestratorAgent
from passive import wire_passive
from state import CallState

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)  # hide REST call noise
log = logging.getLogger("main")

server = AgentServer()


def _caller_phone(ctx: JobContext) -> str:
    """Phone of the human in the room: SIP attribute on real calls, env in console.

    Console mode hands us a mock room, so only trust real string values.
    """
    try:
        for participant in ctx.room.remote_participants.values():
            phone = participant.attributes.get("sip.phoneNumber")
            if isinstance(phone, str) and phone:
                return phone
    except Exception:
        pass
    return CONSOLE_CALLER_PHONE


def _room_name(ctx: JobContext) -> str:
    name = ctx.room.name
    return name if isinstance(name, str) else "console"


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    state = CallState(
        call_id=f"call-{uuid.uuid4().hex[:8]}",
        caller_phone=_caller_phone(ctx),
        room_name=_room_name(ctx),
    )
    log.info("call starting: %s from %s", state.call_id, state.caller_phone)

    # Same snappy config as the Livekit-agents project: local turn detector,
    # preemptive generation, and short endpointing so replies come fast and
    # barge-in stays responsive (the remote TurnDetector added a ~2.5s delay).
    session = AgentSession(
        userdata=state,
        vad=silero.VAD.load(),
        stt=inference.STT(STT_MODEL, language="multi"),
        llm=inference.LLM(LLM_MODEL),
        tts=inference.TTS(TTS_MODEL),
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
        min_endpointing_delay=0.35,
        max_endpointing_delay=1.8,
    )

    wire_passive(session, state)
    ctx.add_shutdown_callback(lambda: summary_mod.emit(state, reason="job shutdown"))

    await session.start(
        agent=OrchestratorAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    print("GASP omni-agent - orchestrator & dual-agent core\n" + startup_report())
    cli.run_app(server)
