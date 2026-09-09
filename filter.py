"""
filter.py — Two-stage topic classification and noise filtering.

Stage 1 (free): Rule-based keyword matching against title + channel name.
Stage 2 (cheap): Gemini classification for ambiguous videos (~100 tokens each).

Keeps: AI, tech, engineering, startups, electronics, programming content.
Skips: Gaming, comedy, entertainment, sports, vlogs.
"""

from __future__ import annotations

import logging

from google import genai
from google.genai import types

import config
from models import FilterDecision, VideoMeta

logger = logging.getLogger("youtube_second_brain")


def classify_video(
    video: VideoMeta,
    transcript_preview: str | None = None,
    gemini_client: genai.Client | None = None,
) -> FilterDecision:
    """
    Classifies a video as KEEP or SKIP using a two-stage approach.

    Stage 1: Fast rule-based filter (free, no API call).
    Stage 2: Gemini classification for ambiguous videos.

    Args:
        video: The video metadata to classify.
        transcript_preview: First ~200 words of transcript (for Stage 2).
        gemini_client: Pre-initialized Gemini client (for Stage 2).

    Returns:
        FilterDecision with keep, category, and reason fields.
    """
    # --- Stage 1: Rule-based pre-filter ---
    decision = _rule_based_filter(video)
    if decision is not None:
        return decision

    # --- Stage 2: Gemini classification (ambiguous videos only) ---
    if gemini_client is not None:
        return _gemini_classify(video, transcript_preview, gemini_client)

    # If no Gemini client available, default to KEEP for ambiguous videos
    logger.info(
        f"[filter] Ambiguous video '{video.title}' — no Gemini client, defaulting to KEEP"
    )
    return FilterDecision(
        keep=True,
        category="Uncategorized",
        reason="Ambiguous title, no Gemini client for classification — defaulting to keep",
    )


def _rule_based_filter(video: VideoMeta) -> FilterDecision | None:
    """
    Stage 1: Fast keyword-based classification.

    Returns:
        FilterDecision if a clear match is found, None if ambiguous.
    """
    # Combine title and channel for matching
    searchable = f"{video.title} {video.channel or ''}".lower()

    # Check 1: Skip shorts (< MIN_DURATION_SECONDS)
    if video.duration is not None and video.duration < config.MIN_DURATION_SECONDS:
        return FilterDecision(
            keep=False,
            category="Short",
            reason=f"Duration {video.duration}s < {config.MIN_DURATION_SECONDS}s minimum",
        )

    # Check 2: Blacklist match → SKIP
    for keyword in config.BLACKLIST_KEYWORDS:
        if keyword.lower() in searchable:
            return FilterDecision(
                keep=False,
                category="Entertainment",
                reason=f"Blacklisted keyword match: '{keyword}'",
            )

    # Check 3: Whitelist match → KEEP
    for keyword in config.WHITELIST_KEYWORDS:
        if keyword.lower() in searchable:
            # Infer category from the keyword
            category = _infer_category_from_keyword(keyword)
            return FilterDecision(
                keep=True,
                category=category,
                reason=f"Whitelisted keyword match: '{keyword}'",
            )

    # No clear match — ambiguous
    return None


def _infer_category_from_keyword(keyword: str) -> str:
    """Maps a whitelist keyword to a broad category."""
    kw = keyword.lower()

    ai_keywords = {
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "llm", "gpt", "neural network", "transformer", "nlp",
        "computer vision", "reinforcement learning", "generative ai",
        "prompt engineering", "rag", "fine-tuning", "agentic",
    }
    programming_keywords = {
        "programming", "software", "python", "javascript", "typescript",
        "react", "backend", "frontend", "fullstack", "api", "database",
        "devops", "docker", "kubernetes", "cloud computing", "aws", "gcp",
        "coding", "developer", "web development", "app development",
        "system design", "data structures", "algorithm",
    }
    ee_keywords = {
        "electronics", "fpga", "embedded", "circuit", "pcb",
        "microcontroller", "arduino", "raspberry pi", "iot",
        "vlsi", "semiconductor", "signal processing", "power electronics",
        "electrical engineering", "ee", "bsee",
    }
    robotics_keywords = {
        "robotics", "robot", "3d printing", "cad", "hardware",
        "drone", "autonomous", "sensor", "actuator",
    }
    business_keywords = {
        "startup", "entrepreneur", "business", "saas", "venture capital",
        "product management", "marketing", "growth hacking",
        "freelancing", "side hustle", "passive income",
    }

    if kw in ai_keywords:
        return "AI Systems"
    elif kw in programming_keywords:
        return "Programming"
    elif kw in ee_keywords:
        return "Electrical Engineering"
    elif kw in robotics_keywords:
        return "Electronics"
    elif kw in business_keywords:
        return "Startups & Business"
    else:
        return "Career & Skills"


def _gemini_classify(
    video: VideoMeta,
    transcript_preview: str | None,
    client: genai.Client,
) -> FilterDecision:
    """
    Stage 2: Uses Gemini to classify ambiguous videos.
    Costs ~100-150 tokens per call — very cheap.
    """
    # Build classification prompt
    content_parts = [
        f"Title: {video.title}",
        f"Channel: {video.channel or 'Unknown'}",
    ]
    if transcript_preview:
        # Use first 200 words of transcript for context
        words = transcript_preview.split()[:200]
        content_parts.append(f"Transcript preview: {' '.join(words)}")

    user_prompt = "\n".join(content_parts)

    system_prompt = (
        "You are a content classifier for a BSEE (Electrical Engineering) student "
        "who is interested in AI, technology, startups, engineering, electronics, "
        "programming, and career growth.\n\n"
        "Classify the following YouTube video as either KEEP or SKIP.\n"
        "KEEP: The video contains valuable educational, technical, or career content.\n"
        "SKIP: The video is entertainment, gaming, comedy, sports, or lifestyle content.\n\n"
        "When in doubt, KEEP the video."
    )

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=FilterDecision,
                temperature=0.1,  # Very low temp for consistent classification
                max_output_tokens=500,
            ),
        )

        if response.parsed:
            decision: FilterDecision = response.parsed
        else:
            import json
            cleaned = response.text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(cleaned)
            decision = FilterDecision(**data)

        logger.info(
            f"[filter] Gemini classified '{video.title}' → "
            f"{'KEEP' if decision.keep else 'SKIP'} ({decision.category}: {decision.reason})"
        )
        return decision

    except Exception as e:
        logger.warning(
            f"[filter] Gemini classification failed for '{video.title}': {e}. "
            "Defaulting to KEEP."
        )
        return FilterDecision(
            keep=True,
            category="Uncategorized",
            reason=f"Gemini classification error: {e} — defaulting to keep",
        )
