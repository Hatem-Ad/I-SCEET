"""
================================================================================
 I-SCEET — Central Configuration
 File: config.py
================================================================================
 Edit this file to configure your I-SCEET installation.
 Never commit .env to GitHub — use .env.example as template.
================================================================================
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# ── PATHS ─────────────────────────────────────────────────────────────────────
ROOT_DIR    = Path(__file__).parent
DB_PATH     = ROOT_DIR / "isceet.db"
UPLOAD_DIR  = ROOT_DIR / "data" / "uploads"
OUTPUT_DIR  = ROOT_DIR / "outputs"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── COLAB CONNECTION ──────────────────────────────────────────────────────────
# Paste your ngrok URL here OR set COLAB_URL in .env
COLAB_URL = os.getenv("COLAB_URL", "")

# ── SYSTEM PROMPTS ────────────────────────────────────────────────────────────
PROMPTS_DIR = ROOT_DIR / "models" / "system_prompts"

def get_system_prompt(module: str) -> str:
    """Load system prompt for a module."""
    path = PROMPTS_DIR / f"{module}_system_prompt.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        f"You are {module}, a specialized DO-178C engineering AI. "
        f"Be precise, structured, and follow all DO-178C standards."
    )

# ── GENERATION SETTINGS ───────────────────────────────────────────────────────
GEN_CONFIG = {
    "temperature": 0.2,   # Low = deterministic (DO-178C compliant)
    "max_tokens":  8192,
    "top_p":       0.8,
    "top_k":       40,
}

# ── PROJECT SETTINGS ──────────────────────────────────────────────────────────
APP_TITLE   = "I-SCEET"
APP_VERSION = "1.0.0"
DAL_LEVELS  = ["A", "B", "C", "D"]
