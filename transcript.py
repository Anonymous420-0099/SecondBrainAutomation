"""
transcript.py — YouTube transcript extraction with multi-language fallbacks.

Uses the youtube-transcript-api v1.0+ OOP API (NOT the deprecated get_transcript()).
Supports English, Hindi, and Urdu with automatic fallback and translation.
"""

from __future__ import annotations

import logging
import random
import time

import http.cookiejar
from pathlib import Path
import requests
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

import config

logger = logging.getLogger("youtube_second_brain")


def _get_transcript_api() -> YouTubeTranscriptApi:
    """Creates a YouTubeTranscriptApi instance, with session cookies if available."""
    cookie_path = Path(config.COOKIE_FILE_PATH)
    if cookie_path.is_file():
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            })
            cj = http.cookiejar.MozillaCookieJar(str(cookie_path))
            cj.load(ignore_discard=True, ignore_expires=True)
            session.cookies = cj
            return YouTubeTranscriptApi(http_client=session)
        except Exception as e:
            logger.warning(f"[transcript] Could not load cookies for transcript API: {e}")
    return YouTubeTranscriptApi()


def fetch_transcript(video_id: str) -> str | None:
    """
    Fetches the text transcript for a YouTube video.

    Tries languages in priority order (EN → HI → UR), with fallback
    to any available track and translation if needed.

    Args:
        video_id: The YouTube video ID (e.g., 'LqY6hFLMEJw').

    Returns:
        Full transcript as a single string, or None if unavailable.
    """
    ytt_api = _get_transcript_api()

    # --- Attempt 1: Direct fetch with preferred languages ---
    try:
        fetched = ytt_api.fetch(
            video_id,
            languages=config.TRANSCRIPT_LANGUAGES,
        )
        full_text = " ".join([snippet.text for snippet in fetched])
        logger.info(
            f"[transcript] Fetched transcript for {video_id} "
            f"({len(full_text.split())} words)"
        )
        return _truncate_if_needed(full_text)

    except TranscriptsDisabled:
        logger.warning(
            f"[transcript] Captions disabled by creator for {video_id}. Skipping."
        )
        return None

    except VideoUnavailable:
        logger.warning(
            f"[transcript] Video {video_id} is unavailable (deleted/private). Skipping."
        )
        return None

    except NoTranscriptFound:
        logger.info(
            f"[transcript] No transcript in {config.TRANSCRIPT_LANGUAGES} "
            f"for {video_id}. Trying translation fallback..."
        )

    except Exception as e:
        logger.warning(
            f"[transcript] Unexpected error fetching {video_id}: {e}. "
            "Trying fallback..."
        )

    # --- Attempt 2: Find any available track and translate ---
    try:
        transcript_list = ytt_api.list(video_id)

        for track in transcript_list:
            if track.is_translatable:
                # Translate to English (first preferred language)
                target_lang = config.TRANSCRIPT_LANGUAGES[0]  # "en"
                logger.info(
                    f"[transcript] Translating {track.language_code} → "
                    f"{target_lang} for {video_id}"
                )
                translated = track.translate(target_lang)
                fetched = translated.fetch()
                full_text = " ".join([snippet.text for snippet in fetched])
                return _truncate_if_needed(full_text)

        # No translatable tracks found — try fetching whatever is available
        for track in transcript_list:
            logger.info(
                f"[transcript] Using non-preferred language "
                f"'{track.language_code}' for {video_id}"
            )
            fetched = track.fetch()
            full_text = " ".join([snippet.text for snippet in fetched])
            return _truncate_if_needed(full_text)

        logger.warning(f"[transcript] No transcript tracks available via API for {video_id}")

    except Exception as e:
        logger.warning(f"[transcript] youtube-transcript-api failed for {video_id}: {e}")

    # --- Attempt 3: yt-dlp subtitle extraction fallback (bypasses datacenter IP bans) ---
    logger.info(f"[transcript] Trying yt-dlp subtitle extraction fallback for {video_id}...")
    ytdlp_text = _fetch_transcript_via_ytdlp(video_id)
    if ytdlp_text:
        return ytdlp_text

    return None


def _fetch_transcript_via_ytdlp(video_id: str) -> str | None:
    """
    Fallback subtitle extraction using yt-dlp.
    Downloads auto-generated or manual VTT subtitles to a temporary directory
    and parses the plain text. Works reliably in cloud environments where
    direct youtube-transcript-api requests are throttled or IP-blocked.
    """
    import glob
    import os
    import re
    import tempfile
    import yt_dlp

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts: dict = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(config.TRANSCRIPT_LANGUAGES) + ["en", "hi", "ur"],
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 8,
            "retries": 1,
            "extractor_retries": 0,
        }

        cookie_path = Path(config.COOKIE_FILE_PATH)
        if cookie_path.is_file():
            ydl_opts["cookiefile"] = str(cookie_path)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

            vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
            if not vtt_files:
                logger.warning(f"[transcript] yt-dlp found no subtitles for {video_id}")
                return None

            # Prefer preferred languages
            target_file = vtt_files[0]
            for lang in config.TRANSCRIPT_LANGUAGES:
                matched = [f for f in vtt_files if f".{lang}." in f]
                if matched:
                    target_file = matched[0]
                    break

            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            clean_lines: list[str] = []
            for line in lines:
                line = line.strip()
                if (
                    not line
                    or "-->" in line
                    or line.startswith("WEBVTT")
                    or line.startswith("Kind:")
                    or line.startswith("Language:")
                ):
                    continue
                # Strip inline HTML-like timestamps/tags
                line = re.sub(r"<[^>]+>", "", line).strip()
                if line and (not clean_lines or clean_lines[-1] != line):
                    clean_lines.append(line)

            full_text = " ".join(clean_lines)
            if full_text:
                logger.info(
                    f"[transcript] Successfully extracted via yt-dlp for {video_id} "
                    f"({len(full_text.split())} words)"
                )
                return _truncate_if_needed(full_text)

        except Exception as e:
            logger.warning(f"[transcript] yt-dlp subtitle extraction failed for {video_id}: {e}")

    return None


def _truncate_if_needed(text: str) -> str:
    """
    Truncates transcript to MAX_TRANSCRIPT_WORDS if it exceeds the limit.
    This prevents sending extremely long transcripts to Gemini for 3h+ videos.
    """
    words = text.split()
    if len(words) > config.MAX_TRANSCRIPT_WORDS:
        logger.info(
            f"[transcript] Truncating from {len(words)} to "
            f"{config.MAX_TRANSCRIPT_WORDS} words"
        )
        return " ".join(words[: config.MAX_TRANSCRIPT_WORDS])
    return text


def add_random_delay() -> None:
    """
    Adds a random delay between transcript fetches to avoid
    triggering YouTube's anti-bot detection.
    """
    delay = 2.0 + random.random() * 2.0  # 2-4 seconds
    time.sleep(delay)
