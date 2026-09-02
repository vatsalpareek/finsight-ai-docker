from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # backend/
DATA_DIR = ROOT / "seed"
DB_PATH = Path(os.getenv("RESEARCH_DB", str(ROOT / "research_memory.db")))

# LLM is optional — without a key, templates take over (no fabrication, no failure)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
LLM_ENABLED = bool(ANTHROPIC_API_KEY)
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "25"))

# Data provider: always "live" in FinSight — we use yfinance
PROVIDER = "live"

DESK_WEIGHTS = {
    "technical": 0.22,
    "fundamental": 0.34,
    "market": 0.22,
    "sentiment": 0.22,
}
