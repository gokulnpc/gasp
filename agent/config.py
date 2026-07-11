"""Central configuration for the GASP omni-agent.

Key lookup order - reuses secrets you already have in sibling projects:
  1. your shell environment
  2. gasp/agent/.env                        (this project)
  3. ../../livekit-dispatch/.env            (SIM_MODE, demo knobs)
  4. ../../Livekit-agents/.env              (LIVEKIT_URL / API_KEY / API_SECRET)
  5. ../../caretaker-dispatch/.env          (Twilio + Supabase + OpenAI)
  6. ../../s2s-experiment/.env              (OPENAI_API_KEY)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).parent
ROOT = HERE.parent.parent  # "Voice agent- for health care/"
for env_file in (
    HERE / ".env",
    ROOT / "livekit-dispatch" / ".env",
    ROOT / "Livekit-agents" / ".env",
    ROOT / "caretaker-dispatch" / ".env",
    ROOT / "s2s-experiment" / ".env",
):
    load_dotenv(env_file)

# --- LiveKit Cloud ---
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
AGENT_NAME = os.getenv("GASP_AGENT_NAME", "gasp-agent")  # SIP dispatch rule targets this later

# --- Voice pipeline models (ride on LiveKit Inference - one LIVEKIT key covers them) ---
STT_MODEL = os.getenv("STT_MODEL", "deepgram/nova-3")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4.1-mini")
TTS_MODEL = os.getenv("TTS_MODEL", "cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc")

# --- Supabase (REST) ---
SUPABASE_URL = (os.getenv("SUPABASE_URL", "")).rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

# --- Demo knobs ---
CONSOLE_CALLER_PHONE = os.getenv("CONSOLE_CALLER_PHONE", "+15550001")  # Maria in seed data
COORDINATOR_PHONE = os.getenv("COORDINATOR_PHONE", "+15559990000")
DEMO_FAST = os.getenv("DEMO_FAST", "true").lower() == "true"  # compress cascade waits

# Everything phone-shaped is simulated in this build (no Twilio yet).
SIM_LOG = HERE / "simulation_log.txt"
PORTAL_LOG = HERE / "portal_summaries.jsonl"


def startup_report() -> str:
    """One honest line per subsystem so you instantly see what's real."""
    return "\n".join([
        f"  livekit    : {LIVEKIT_URL or 'MISSING - console mode only'}",
        f"  supabase   : {SUPABASE_URL if SUPABASE_URL and SUPABASE_KEY else 'MISSING - using in-memory seed'}",
        f"  voice      : {STT_MODEL} / {LLM_MODEL}",
        f"  telephony  : SIMULATED (sms -> {SIM_LOG.name})",
        f"  demo_fast  : {DEMO_FAST}",
    ])
