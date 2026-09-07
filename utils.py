"""
utils.py — Shared utilities for the YouTube Second Brain pipeline.

Provides:
- Structured logging (console + daily log file)
- Retry decorator with exponential backoff
- Filename slug generator
- Atomic file writer
"""

from __future__ import annotations

import functools
import logging
import os
import re
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------
def setup_logging(log_dir: str, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger that writes to both console and a daily log file.

    Log file: {log_dir}/run_YYYY-MM-DD.log
    Format:   [2026-09-07 00:05:23] [INFO] message

    Args:
        log_dir: Directory to store log files.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("youtube_second_brain")
    logger.setLevel(level)

    # Prevent duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (reconfigure to utf-8 if supported to prevent emoji errors on Windows)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (daily log)
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"run_{today}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------
def retry(
    max_retries: int = 3,
    delay: float = 5.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to catch and retry on.

    Example:
        @retry(max_retries=3, delay=5, backoff=2)
        def call_api():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger("youtube_second_brain")
            current_delay = delay

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"[{func.__name__}] Failed after {max_retries} attempts: {e}"
                        )
                        raise
                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt}/{max_retries} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Slug Generator
# ---------------------------------------------------------------------------
def slugify(text: str, max_length: int = 80) -> str:
    """
    Converts a title into a URL/filename-safe slug.

    Examples:
        "How AI Makes Him Crores!!" → "how-ai-makes-him-crores"
        "What is FPGA? (2026 Guide)" → "what-is-fpga-2026-guide"

    Args:
        text: The title or text to slugify.
        max_length: Maximum character length for the slug.

    Returns:
        A lowercase kebab-case string safe for filenames.
    """
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    # Convert to ASCII, ignoring non-ASCII chars
    text = text.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    text = text.lower()
    # Replace any non-alphanumeric character with a hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)
    # Truncate to max_length (don't cut in middle of a word)
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text


# ---------------------------------------------------------------------------
# Atomic File Writer
# ---------------------------------------------------------------------------
def safe_write(path: str, content: str) -> None:
    """
    Writes content to a file atomically to prevent corruption.

    Writes to a temporary file first, then renames it to the target path.
    Creates parent directories if they don't exist.

    Args:
        path: Target file path.
        content: String content to write.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory (ensures same filesystem for rename)
    fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        # Atomic rename (on Windows, target must not exist for os.rename)
        if target.exists():
            target.unlink()
        os.rename(tmp_path, str(target))
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# Timestamp Helper
# ---------------------------------------------------------------------------
def utc_now_iso() -> str:
    """Returns the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_date() -> str:
    """Returns today's date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
