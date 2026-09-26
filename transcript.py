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


def format_transcript_paragraphs(text: str, words_per_paragraph: int = 90) -> str:
    """
    Groups raw transcript text into clean, readable paragraphs.
    Ensures natural paragraph breaks at sentence endings where possible.
    """
    if not text:
        return ""
    words = text.split()
    paragraphs: list[str] = []
    current_para: list[str] = []

    for word in words:
        current_para.append(word)
        if len(current_para) >= words_per_paragraph:
            if word.endswith((".", "?", "!")) or len(current_para) >= words_per_paragraph + 35:
                paragraphs.append(" ".join(current_para))
                current_para = []

    if current_para:
        paragraphs.append(" ".join(current_para))

    return "\n\n".join(paragraphs)


def _parse_vtt_text(raw_text: str) -> str:
    """Parses WEBVTT subtitle text into a single clean string."""
    import re
    clean_lines: list[str] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if (
            not line
            or "-->" in line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or line.startswith("NOTE")
        ):
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line and (not clean_lines or clean_lines[-1] != line):
            clean_lines.append(line)
    return " ".join(clean_lines)


def _parse_json3_text(json_data: dict) -> str:
    """Parses YouTube json3 format captions into a single clean string."""
    words: list[str] = []
    for ev in json_data.get("events", []):
        for seg in ev.get("segs", []):
            txt = seg.get("utf8", "").strip()
            if txt and txt != "\n":
                words.append(txt)
    return " ".join(words)


def fetch_transcript(video_id: str) -> str | None:
    """
    Fetches the full text transcript for a YouTube video.

    Tries languages in priority order (EN regional variants → HI → UR),
    with fallback to native tracks, translation, and yt-dlp extraction.

    Args:
        video_id: The YouTube video ID (e.g., 'LqY6hFLMEJw').

    Returns:
        Full transcript formatted into clean paragraphs, or None if unavailable.
    """
    ytt_api = _get_transcript_api()

    # --- Attempt 1: Direct fetch with preferred languages ---
    try:
        fetched = ytt_api.fetch(
            video_id,
            languages=config.TRANSCRIPT_LANGUAGES,
        )
        full_text = " ".join([snippet.text for snippet in fetched])
        formatted = format_transcript_paragraphs(full_text)
        logger.info(
            f"[transcript] Fetched full transcript for {video_id} via API "
            f"({len(formatted.split())} words)"
        )
        return formatted

    except TranscriptsDisabled:
        logger.warning(
            f"[transcript] Captions disabled by creator for {video_id}. Trying yt-dlp..."
        )

    except VideoUnavailable:
        logger.warning(
            f"[transcript] Video {video_id} is unavailable (deleted/private). Skipping."
        )
        return None

    except NoTranscriptFound:
        logger.info(
            f"[transcript] No exact match in {config.TRANSCRIPT_LANGUAGES} "
            f"for {video_id}. Checking available tracks..."
        )

    except Exception as e:
        logger.warning(
            f"[transcript] Direct fetch error for {video_id}: {e}. "
            "Checking track list and yt-dlp fallback..."
        )

    # --- Attempt 2: Find any available track in list ---
    try:
        transcript_list = ytt_api.list(video_id)

        # 2a. Check if any track is already an English or preferred variant (fetch directly, DO NOT translate!)
        for track in transcript_list:
            code = track.language_code.lower()
            if any(code == lang.lower() or code.startswith(f"{lang.lower()}-") for lang in ["en", "hi", "ur"]):
                logger.info(
                    f"[transcript] Fetching native preferred track '{track.language_code}' for {video_id}"
                )
                fetched = track.fetch()
                full_text = " ".join([snippet.text for snippet in fetched])
                formatted = format_transcript_paragraphs(full_text)
                return formatted

        # 2b. If only foreign tracks exist, translate to English
        for track in transcript_list:
            if track.is_translatable:
                target_lang = "en"
                logger.info(
                    f"[transcript] Translating foreign track {track.language_code} → "
                    f"{target_lang} for {video_id}"
                )
                try:
                    translated = track.translate(target_lang)
                    fetched = translated.fetch()
                    full_text = " ".join([snippet.text for snippet in fetched])
                    formatted = format_transcript_paragraphs(full_text)
                    return formatted
                except Exception as te:
                    logger.warning(
                        f"[transcript] Translation failed for {track.language_code}: {te}"
                    )

        # 2c. Fallback: fetch whatever first track is available
        for track in transcript_list:
            logger.info(
                f"[transcript] Using fallback language track "
                f"'{track.language_code}' for {video_id}"
            )
            fetched = track.fetch()
            full_text = " ".join([snippet.text for snippet in fetched])
            formatted = format_transcript_paragraphs(full_text)
            return formatted

    except Exception as e:
        logger.warning(f"[transcript] youtube-transcript-api track listing failed for {video_id}: {e}")

    # --- Attempt 3: yt-dlp subtitle extraction (handles cloud IP blocks and regional tracks) ---
    logger.info(f"[transcript] Trying yt-dlp subtitle extraction for {video_id}...")
    ytdlp_text = _fetch_transcript_via_ytdlp(video_id)
    if ytdlp_text:
        return ytdlp_text

    return None


def _fetch_transcript_via_ytdlp(video_id: str) -> str | None:
    """
    Robust subtitle extraction using yt-dlp.
    1. First tries direct timedtext URL retrieval (vtt / json3), which bypasses
       most downloader-level HTTP 429 blocks.
    2. Falls back to downloading VTT subtitles to a temporary directory.
    """
    import glob
    import json
    import os
    import tempfile
    import requests
    import yt_dlp

    cookie_path = Path(config.COOKIE_FILE_PATH)
    ydl_opts: dict = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en.*", "hi.*", "ur.*", "en", "en-US", "en-GB", "en-CA", "en-orig", "hi", "ur", "all"],
        "subtitlesformat": "vtt",
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 2,
    }
    if cookie_path.is_file():
        ydl_opts["cookiefile"] = str(cookie_path)

    # Strategy A: Direct timedtext URL fetch via extract_info (avoids downloader 429)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        subs = info.get("subtitles") or {}
        auto = info.get("automatic_captions") or {}

        # Collect candidate tracks in priority order: manual subtitles first, then auto captions
        candidates: list[tuple[str, list[dict]]] = []
        for source in (subs, auto):
            for lang in ["en", "hi", "ur"]:
                for k, track in source.items():
                    k_lower = k.lower()
                    if k_lower == lang or k_lower.startswith(f"{lang}-") or k_lower.startswith(f"{lang}_"):
                        if (k, track) not in candidates:
                            candidates.append((k, track))

        if candidates:
            session = requests.Session()
            session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            })
            if cookie_path.is_file():
                try:
                    import http.cookiejar
                    cj = http.cookiejar.MozillaCookieJar(str(cookie_path))
                    cj.load(ignore_discard=True, ignore_expires=True)
                    session.cookies = cj
                except Exception:
                    pass

            for k, track in candidates:
                # 1. Try VTT format
                vtt_entry = next((e for e in track if e.get("ext") == "vtt"), None)
                if vtt_entry and vtt_entry.get("url"):
                    try:
                        r = session.get(vtt_entry["url"], timeout=20)
                        if r.status_code == 200 and r.text:
                            parsed = _parse_vtt_text(r.text)
                            if len(parsed.split()) >= 30:
                                formatted = format_transcript_paragraphs(parsed)
                                logger.info(
                                    f"[transcript] Successfully extracted via yt-dlp timedtext VTT ({k}) for {video_id} "
                                    f"({len(formatted.split())} words)"
                                )
                                return formatted
                    except Exception:
                        pass

                # 2. Try JSON3 format
                json3_entry = next((e for e in track if e.get("ext") == "json3"), None)
                if json3_entry and json3_entry.get("url"):
                    try:
                        r = session.get(json3_entry["url"], timeout=20)
                        if r.status_code == 200:
                            parsed = _parse_json3_text(r.json())
                            if len(parsed.split()) >= 30:
                                formatted = format_transcript_paragraphs(parsed)
                                logger.info(
                                    f"[transcript] Successfully extracted via yt-dlp timedtext JSON3 ({k}) for {video_id} "
                                    f"({len(formatted.split())} words)"
                                )
                                return formatted
                    except Exception:
                        pass
    except Exception as e:
        logger.debug(f"[transcript] Direct timedtext extraction attempt failed for {video_id}: {e}")

    # Strategy B: Download to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts["outtmpl"] = os.path.join(tmpdir, "%(id)s.%(ext)s")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

            vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
            if not vtt_files:
                logger.warning(f"[transcript] yt-dlp found no subtitles for {video_id}")
                return None

            # Prefer English, Hindi, Urdu in order
            target_file = vtt_files[0]
            for lang in ["en", "hi", "ur"]:
                matched = [
                    f for f in vtt_files
                    if f".{lang}." in os.path.basename(f).lower()
                    or f".{lang}-" in os.path.basename(f).lower()
                    or f".{lang}_" in os.path.basename(f).lower()
                ]
                if matched:
                    target_file = matched[0]
                    break

            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            parsed = _parse_vtt_text(content)
            if parsed and len(parsed.split()) >= 30:
                formatted = format_transcript_paragraphs(parsed)
                logger.info(
                    f"[transcript] Successfully extracted via yt-dlp VTT file for {video_id} "
                    f"({len(formatted.split())} words)"
                )
                return formatted

        except Exception as e:
            logger.warning(f"[transcript] yt-dlp subtitle download failed for {video_id}: {e}")

    return None


def truncate_transcript(text: str, max_words: int | None = None) -> str:
    """
    Truncates transcript to max_words (defaults to config.MAX_TRANSCRIPT_WORDS)
    if it exceeds the limit. Used when preparing prompt content for LLM calls.
    """
    limit = max_words or config.MAX_TRANSCRIPT_WORDS
    words = text.split()
    if len(words) > limit:
        logger.info(
            f"[transcript] Truncating from {len(words)} to "
            f"{limit} words for LLM context"
        )
        return " ".join(words[:limit])
    return text


def add_random_delay() -> None:
    """
    Adds a random delay between transcript fetches to avoid
    triggering YouTube's anti-bot detection.
    """
    delay = 2.0 + random.random() * 2.0  # 2-4 seconds
    time.sleep(delay)
