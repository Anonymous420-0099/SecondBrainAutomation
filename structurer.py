"""
structurer.py — Gemini LLM-powered transcript structuring.

Transforms raw video transcripts into structured KnowledgeCard objects
using the google-genai SDK with native Pydantic schema enforcement.
"""

from __future__ import annotations

import logging
import time

from google import genai
from google.genai import types

import config
from models import KnowledgeCard, VideoExtractionSchema, VideoMeta
from transcript import truncate_transcript
from utils import retry, utc_now_iso

logger = logging.getLogger("youtube_second_brain")

# ---------------------------------------------------------------------------
# System prompt for knowledge extraction
# ---------------------------------------------------------------------------
STRUCTURING_SYSTEM_PROMPT = """\
You are a knowledge extraction assistant for a BSEE (Electrical Engineering) \
student who is interested in AI, technology, startups, engineering, electronics, \
programming, and career growth.

Given a YouTube video transcript, extract a structured knowledge card.

Rules:
- video_id, title, channel, url, processed_at: Copy these exactly from the \
provided metadata — do NOT infer or modify them.
- category: One of [AI Systems, Programming, Startups & Business, \
Electrical Engineering, Electronics, Career & Skills, Research, Other]
- one_sentence_summary: A crisp single sentence capturing the CORE insight \
of the video. Not a generic description — capture what makes this video unique.
- key_takeaways: 3-7 bullet points of the most ACTIONABLE insights. \
Each should be a standalone piece of knowledge someone can apply immediately.
- actionable_frameworks: Named frameworks, mental models, or methodologies \
explicitly mentioned in the video. Include a brief description of each. \
Empty list if none mentioned.
- memorable_quotes: Direct, word-for-word quotes from the video that are \
insightful or impactful. Max 3. Empty list if none stand out.
- related_topics: 3-5 lowercase topic tags for cross-referencing \
(e.g., "ai", "agents", "automation", "startups").

Focus on ACTIONABLE knowledge, not surface-level summaries.
Skip filler, sponsor segments, self-promotion, and "like and subscribe" content.
If the transcript is in Hindi/Urdu, still output ALL fields in English.\
"""


# ---------------------------------------------------------------------------
# Gemini client initialization
# ---------------------------------------------------------------------------
def create_gemini_client() -> genai.Client:
    """
    Creates and returns a Gemini API client.

    The API key is loaded from config (which reads it from .env).
    """
    if not config.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Get a free key at https://aistudio.google.com/apikey"
        )

    return genai.Client(api_key=config.GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# Main structuring function
# ---------------------------------------------------------------------------
@retry(max_retries=3, delay=10.0, backoff=2.0)
def structure_transcript(
    video: VideoMeta,
    transcript_text: str | None,
    client: genai.Client,
) -> KnowledgeCard:
    """
    Sends a transcript or direct YouTube URL to Gemini and returns a structured KnowledgeCard.

    Uses Pydantic response_schema for guaranteed structured JSON output.
    If transcript_text is None (e.g. blocked by YouTube in cloud environments),
    falls back to Gemini's native multimodal YouTube video analysis.

    Args:
        video: Video metadata.
        transcript_text: Full transcript text, or None to use direct video understanding.
        client: Pre-initialized Gemini client.

    Returns:
        KnowledgeCard Pydantic object with all extracted knowledge.

    Raises:
        Exception: If Gemini fails after all retries.
    """
    if transcript_text:
        prompt_transcript = truncate_transcript(transcript_text, config.MAX_TRANSCRIPT_WORDS)
        user_prompt = (
            f"Video Metadata:\n"
            f"- video_id: {video.video_id}\n"
            f"- title: {video.title}\n"
            f"- channel: {video.channel or 'Unknown'}\n"
            f"- url: {video.url}\n"
            f"- processed_at: {utc_now_iso()}\n\n"
            f"--- TRANSCRIPT START ---\n"
            f"{prompt_transcript}\n"
            f"--- TRANSCRIPT END ---"
        )
        contents = user_prompt
        logger.info(
            f"[structurer] Sending transcript to Gemini: '{video.title}' "
            f"({len(prompt_transcript.split())} words in prompt, "
            f"{len(transcript_text.split())} words total)"
        )
    else:
        user_prompt = (
            f"Video Metadata:\n"
            f"- video_id: {video.video_id}\n"
            f"- title: {video.title}\n"
            f"- channel: {video.channel or 'Unknown'}\n"
            f"- url: {video.url}\n"
            f"- processed_at: {utc_now_iso()}\n\n"
            f"Please analyze the attached YouTube video and extract the structured knowledge card."
        )
        contents = [
            types.Part.from_uri(
                file_uri=video.url,
                mime_type="video/*",
            ),
            user_prompt,
        ]
        logger.info(
            f"[structurer] Sending direct YouTube URL to Gemini (multimodal analysis): '{video.title}'"
        )

    models_to_try = [config.GEMINI_MODEL]
    for fallback in ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    response = None
    last_err = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=STRUCTURING_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=VideoExtractionSchema,
                    temperature=config.GEMINI_TEMPERATURE,
                    max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
                ),
            )
            break
        except Exception as e:
            last_err = e
            logger.warning(
                f"[structurer] Model '{model_name}' failed for '{video.title}': {e}. "
                "Trying next model candidate..."
            )

    if response is None:
        raise last_err

    # Parse response into dictionary
    if response.parsed:
        raw_card = response.parsed
        card_data = raw_card.model_dump()
    else:
        import json
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        card_data = json.loads(cleaned)

    # Attach full transcript to KnowledgeCard
    card_data["transcript"] = transcript_text
    card = KnowledgeCard(**card_data)

    logger.info(
        f"[structurer] ✅ Structured '{video.title}' → "
        f"{len(card.key_takeaways)} takeaways, "
        f"{len(card.actionable_frameworks)} frameworks"
    )

    return card

