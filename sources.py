"""
sources.py — Video discovery from multiple YouTube sources.

Fetches video metadata from three sources:
1. Watch History (via yt-dlp + cookies.txt)
2. "Second Brain Queue" playlist (via yt-dlp)
3. "Watch Later" playlist (via yt-dlp + cookies.txt)

Then deduplicates against previously processed videos.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import yt_dlp

import config
from models import VideoMeta

logger = logging.getLogger("youtube_second_brain")


# ---------------------------------------------------------------------------
# Core yt-dlp extraction helpers
# ---------------------------------------------------------------------------
def _get_ydl_opts(limit: int | None = None) -> dict[str, Any]:
    """
    Builds the base yt-dlp options dict with cookie authentication.

    Uses cookies.txt file if available, falls back to browser cookie
    extraction if BROWSER_FALLBACK is configured.
    """
    opts: dict[str, Any] = {
        "extract_flat": "in_playlist",  # Fast: metadata only, no stream resolution
        "skip_download": True,
        "ignoreerrors": True,  # Skip deleted/private/geo-blocked videos
        "quiet": True,
        "no_warnings": True,
    }

    if limit:
        opts["playlist_items"] = f"1:{limit}"

    # Authentication: prefer cookies.txt, fall back to browser
    cookie_path = Path(config.COOKIE_FILE_PATH)
    if cookie_path.is_file():
        opts["cookiefile"] = str(cookie_path)
    elif config.BROWSER_FALLBACK:
        # Must be a tuple! ('chrome',) not 'chrome'
        opts["cookiesfrombrowser"] = (config.BROWSER_FALLBACK,)
    else:
        logger.warning(
            "No cookies.txt found and no BROWSER_FALLBACK set. "
            "Private sources (history, Watch Later) will fail."
        )

    return opts


def _extract_videos(url: str, source_label: str, limit: int | None = None) -> list[VideoMeta]:
    """
    Extracts video metadata from a YouTube URL using yt-dlp.

    Args:
        url: YouTube URL (history feed, playlist URL, or yt-dlp shortcut).
        source_label: Label for the source ('history', 'playlist', 'watch_later').
        limit: Maximum number of videos to extract.

    Returns:
        List of VideoMeta objects.
    """
    opts = _get_ydl_opts(limit=limit)
    videos: list[VideoMeta] = []

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                logger.warning(f"[{source_label}] No data returned from {url}")
                return videos

            # CRITICAL: entries is a generator, must iterate carefully
            raw_entries = info.get("entries") or []
            for entry in raw_entries:
                # Deleted/private videos appear as None
                if not entry:
                    continue

                video_id = entry.get("id")
                if not video_id:
                    continue

                videos.append(
                    VideoMeta(
                        video_id=video_id,
                        title=entry.get("title") or "Untitled",
                        channel=entry.get("uploader") or entry.get("channel"),
                        url=entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                        duration=entry.get("duration"),
                        source=source_label,
                    )
                )

        logger.info(f"[{source_label}] Fetched {len(videos)} videos")

    except Exception as e:
        logger.error(f"[{source_label}] Failed to extract from {url}: {e}")

    return videos


def _has_auth() -> bool:
    """Checks if any authentication mechanism (cookie file or browser) is available."""
    cookie_path = Path(config.COOKIE_FILE_PATH)
    return cookie_path.is_file() or bool(config.BROWSER_FALLBACK)


# ---------------------------------------------------------------------------
# Source fetchers
# ---------------------------------------------------------------------------
def fetch_watch_history() -> list[VideoMeta]:
    """Fetches recent videos from YouTube watch history."""
    if not _has_auth():
        logger.info("[history] No cookie file found. Skipping watch history extraction.")
        return []

    logger.info("Fetching watch history...")
    return _extract_videos(
        url=":ythistory",
        source_label="history",
        limit=config.HISTORY_LIMIT,
    )


def fetch_second_brain_playlist() -> list[VideoMeta]:
    """Fetches videos from the 'Second Brain Queue' playlist."""
    playlist_id = config.SECOND_BRAIN_PLAYLIST_ID
    if not playlist_id:
        logger.info("[playlist] No SECOND_BRAIN_PLAYLIST_ID configured, skipping.")
        return []

    logger.info(f"Fetching 'Second Brain Queue' playlist ({playlist_id})...")
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    return _extract_videos(url=url, source_label="playlist")


def fetch_watch_later() -> list[VideoMeta]:
    """Fetches videos from the 'Watch Later' playlist."""
    if not _has_auth():
        logger.info("[watch_later] No cookie file found. Skipping Watch Later extraction.")
        return []

    logger.info("Fetching 'Watch Later' playlist...")
    url = f"https://www.youtube.com/playlist?list={config.WATCH_LATER_PLAYLIST_ID}"
    return _extract_videos(url=url, source_label="watch_later")


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------
def load_processed_ids() -> dict[str, str]:
    """
    Loads the set of already-processed video IDs from disk.

    Returns:
        Dict mapping video_id → ISO timestamp of when it was processed.
    """
    path = config.PROCESSED_VIDEOS_FILE
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read processed_videos.json: {e}. Starting fresh.")
        return {}


def save_processed_id(video_id: str, timestamp: str) -> None:
    """
    Marks a video ID as processed by appending it to the persistent file.

    Args:
        video_id: The YouTube video ID.
        timestamp: ISO 8601 timestamp of processing.
    """
    processed = load_processed_ids()
    processed[video_id] = timestamp

    path = config.PROCESSED_VIDEOS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)


def deduplicate(videos: list[VideoMeta]) -> list[VideoMeta]:
    """
    Removes already-processed videos and deduplicates by video_id.

    Args:
        videos: List of VideoMeta from all sources (may have duplicates).

    Returns:
        List of new, unprocessed VideoMeta objects (unique by video_id).
    """
    processed_ids = load_processed_ids()
    seen: set[str] = set()
    unique: list[VideoMeta] = []

    for video in videos:
        vid = video.video_id
        if vid in processed_ids:
            continue  # Already processed in a previous run
        if vid in seen:
            continue  # Duplicate within this run (appeared in multiple sources)
        seen.add(vid)
        unique.append(video)

    skipped = len(videos) - len(unique)
    if skipped > 0:
        logger.info(f"Dedup: {skipped} videos skipped (already processed or duplicate)")

    return unique


# ---------------------------------------------------------------------------
# Main entry point for sources
# ---------------------------------------------------------------------------
def fetch_all_new_videos() -> list[VideoMeta]:
    """
    Fetches videos from all configured sources, merges, and deduplicates.

    Returns:
        List of new, unprocessed VideoMeta objects ready for the pipeline.
    """
    all_videos: list[VideoMeta] = []

    # Source A: Watch History
    all_videos.extend(fetch_watch_history())

    # Source B: Second Brain Queue playlist
    all_videos.extend(fetch_second_brain_playlist())

    # Source C: Watch Later
    all_videos.extend(fetch_watch_later())

    logger.info(f"Total videos fetched from all sources: {len(all_videos)}")

    # Remove duplicates and already-processed videos
    new_videos = deduplicate(all_videos)
    logger.info(f"New videos to process: {len(new_videos)}")

    return new_videos
