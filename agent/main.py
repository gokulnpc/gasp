"""GASP Healthcare Omni-Agent - LiveKit entry point (Person 2: Orchestrator & State).

Run it:
  python main.py console        voice agent (Mac mic — no phone)
  python main.py dev            LIVE: call +1 (929) 730-7867 lands here via SIP
  python worker.py              dispatch worker (second terminal)
"""

import logging
import uuid

from livekit.agents import (AgentServer, AgentSession, JobContext,
                            RoomInputOptions, cli, inference)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import summary as summary_mod
from config import (AGENT_NAME, CONSOLE_CALLER_PHONE, LLM_MODEL,
                    STT_MODEL, TTS_MODEL, startup_report)
from orchestrator import OrchestratorAgent
from passive import wire_passive
from state import CallState

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("main")

server = AgentServer()


async def _caller_phone(ctx: JobContext) -> str:
    """SIP attribute on real calls; env fallback for console."""
    try:
        participant = await ctx.wait_for_participant()
        phone = participant.attributes.get("sip.phoneNumber")
        if isinstance(phone, str) and phone:
            log.info("SIP caller: %s", phone)
            return phone
    except Exception:
        pass
    for participant in ctx.room.remote_participants.values():
        phone = participant.attributes.get("sip.phoneNumber")
        if isinstance(phone, str) and phone:
            return phone
    return CONSOLE_CALLER_PHONE


def _is_sip_call(room_name: str) -> bool:
    return room_name.startswith("call")


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    room_name = ctx.room.name if isinstance(ctx.room.name, str) else "console"
    sip = _is_sip_call(room_name)

    caller = await _caller_phone(ctx) if sip else CONSOLE_CALLER_PHONE
    state = CallState(
        call_id=room_name if sip else f"call-{uuid.uuid4().hex[:8]}",
        caller_phone=caller,
        room_name=room_name,
    )
    log.info("call starting: %s from %s (sip=%s)", state.call_id, state.caller_phone, sip)

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
