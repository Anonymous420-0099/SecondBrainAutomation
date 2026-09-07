"""
config.py — Central configuration for the YouTube Second Brain pipeline.

All tunable parameters live here. Secrets are loaded from .env file.
No magic strings scattered across modules.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file (must be in the same directory as this script)
# ---------------------------------------------------------------------------
_project_dir = Path(__file__).resolve().parent
load_dotenv(_project_dir / ".env")

# ---------------------------------------------------------------------------
# Environment Detection
# ---------------------------------------------------------------------------
# True when running inside GitHub Actions (or any CI environment)
CI_MODE: bool = os.getenv("CI", "").lower() == "true" or os.getenv("GITHUB_ACTIONS", "") == "true"

# ---------------------------------------------------------------------------
# Secrets (from .env or GitHub Actions secrets via environment variables)
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
# In CI mode, GITHUB_REPO_PATH defaults to the current workspace (the repo itself)
GITHUB_REPO_PATH: str = os.getenv(
    "GITHUB_REPO_PATH",
    os.getenv("GITHUB_WORKSPACE", str(_project_dir)) if CI_MODE else "",
)
SECOND_BRAIN_PLAYLIST_ID: str = os.getenv("SECOND_BRAIN_PLAYLIST_ID", "")
COOKIE_FILE_PATH: str = os.getenv("COOKIE_FILE_PATH", str(_project_dir / "cookies.txt"))

# ---------------------------------------------------------------------------
# Gemini API Settings
# ---------------------------------------------------------------------------
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_TEMPERATURE: float = 0.3  # Low temp for factual extraction
GEMINI_MAX_OUTPUT_TOKENS: int = 2000
API_DELAY_SECONDS: float = 4.0  # Delay between Gemini calls (free tier: 10-15 RPM)

# ---------------------------------------------------------------------------
# YouTube Source Settings
# ---------------------------------------------------------------------------
# Browser for cookie fallback (only used if cookies.txt doesn't exist)
# Options: "chrome", "firefox", "brave", "edge", None
BROWSER_FALLBACK: str | None = None

# YouTube's fixed Watch Later playlist ID
WATCH_LATER_PLAYLIST_ID: str = "WL"

# Maximum number of recent history items to fetch per run
HISTORY_LIMIT: int = 50

# Minimum video duration in seconds (skip YouTube Shorts and very short clips)
MIN_DURATION_SECONDS: int = 60

# ---------------------------------------------------------------------------
# Transcript Settings
# ---------------------------------------------------------------------------
# Language priority for transcript fetching
# Manual captions are tried first for each language, then auto-generated
TRANSCRIPT_LANGUAGES: list[str] = ["en", "hi", "ur"]

# Maximum transcript length in words (for very long videos 3h+)
MAX_TRANSCRIPT_WORDS: int = 50_000

# ---------------------------------------------------------------------------
# Topic Filtering — Whitelist & Blacklist
# ---------------------------------------------------------------------------
# Videos matching ANY whitelist keyword (case-insensitive) in title/channel → KEEP
WHITELIST_KEYWORDS: list[str] = [
    # AI & Machine Learning
    "AI", "artificial intelligence", "machine learning", "deep learning",
    "LLM", "GPT", "neural network", "transformer", "NLP",
    "computer vision", "reinforcement learning", "generative AI",
    "prompt engineering", "RAG", "fine-tuning", "agentic",
    # Programming & Software
    "programming", "software", "python", "javascript", "typescript",
    "react", "backend", "frontend", "fullstack", "API", "database",
    "DevOps", "docker", "kubernetes", "cloud computing", "AWS", "GCP",
    "coding", "developer", "web development", "app development",
    "system design", "data structures", "algorithm",
    # Electrical Engineering & Electronics
    "electronics", "FPGA", "embedded", "circuit", "PCB",
    "microcontroller", "arduino", "raspberry pi", "IoT",
    "VLSI", "semiconductor", "signal processing", "power electronics",
    "electrical engineering", "EE", "BSEE",
    # Robotics & Hardware
    "robotics", "robot", "3D printing", "CAD", "hardware",
    "drone", "autonomous", "sensor", "actuator",
    # Startups & Business
    "startup", "entrepreneur", "business", "SaaS", "venture capital",
    "product management", "marketing", "growth hacking",
    "freelancing", "side hustle", "passive income",
    # Tech & Career
    "tech", "technology", "career", "interview prep",
    "productivity", "automation", "no-code", "low-code",
    # Science & Research
    "research", "science", "physics", "mathematics", "data science",
    "statistics", "quantum computing",
]

# Videos matching ANY blacklist keyword (case-insensitive) in title/channel → SKIP
BLACKLIST_KEYWORDS: list[str] = [
    # Entertainment
    "gaming", "gameplay", "game walkthrough", "let's play",
    "funny", "comedy", "stand-up", "memes", "meme compilation",
    "movie recap", "movie review", "film review", "trailer",
    "music video", "song", "lyrics", "remix", "mashup",
    "vlog", "daily vlog", "travel vlog",
    "unboxing", "haul",
    "asmr",
    "netflix", "web series", "episode",
    "reaction video", "reaction",
    "prank", "challenge",
    "tiktok compilation",
    # Sports
    "cricket", "football highlights", "match highlights",
    "IPL", "world cup highlights",
    # Drama & Shows
    "drama", "cartoon", "anime episode", "anime",
    # Misc noise
    "satisfying", "oddly satisfying", "relaxing",
    "mukbang", "cooking recipe",
    "gossip", "celebrity",
]

# ---------------------------------------------------------------------------
# Output Settings
# ---------------------------------------------------------------------------
PROCESSED_VIDEOS_FILE: str = str(_project_dir / "processed_videos.json")
LOG_DIR: str = str(_project_dir / "logs")

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_config() -> list[str]:
    """
    Validates critical configuration. Returns list of error messages.
    Empty list means all good.
    """
    errors: list[str] = []

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        errors.append(
            "GEMINI_API_KEY is not set. "
            "Get a free key at https://aistudio.google.com/apikey "
            "and add it to your .env file (or GitHub Actions secret)."
        )

    if not GITHUB_REPO_PATH:
        errors.append(
            "GITHUB_REPO_PATH is not set. "
            "Clone your GitHub repo and set the local path in .env."
        )
    elif not Path(GITHUB_REPO_PATH).is_dir():
        errors.append(
            f"GITHUB_REPO_PATH '{GITHUB_REPO_PATH}' does not exist or is not a directory."
        )

    # Cookies are optional — without them, only playlist sources work
    cookie_path = Path(COOKIE_FILE_PATH)
    if not cookie_path.is_file() and BROWSER_FALLBACK is None:
        import logging
        logger = logging.getLogger("youtube_second_brain")
        if CI_MODE:
            logger.info(
                "No cookies.txt found (expected in CI mode). "
                "Only playlist-based sources will work. "
                "To enable watch history, add YOUTUBE_COOKIES secret."
            )
        elif not SECOND_BRAIN_PLAYLIST_ID:
            errors.append(
                f"Cookie file '{COOKIE_FILE_PATH}' not found, no BROWSER_FALLBACK set, "
                "and no SECOND_BRAIN_PLAYLIST_ID configured. "
                "At least one video source must be available."
            )

    return errors
