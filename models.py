"""
models.py — Pydantic data models for the YouTube Second Brain pipeline.

Defines strict typed models for every stage of the pipeline:
- VideoMeta: raw video metadata from YouTube
- FilterDecision: keep/skip classification result
- KnowledgeCard: the structured output from Gemini (also used as response_schema)
- ProcessingResult: final result for each video
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VideoMeta(BaseModel):
    """Raw video metadata extracted from YouTube via yt-dlp."""

    video_id: str = Field(description="YouTube video ID")
    title: str = Field(description="Video title")
    channel: str | None = Field(default=None, description="Channel/uploader name")
    url: str = Field(description="Full YouTube URL")
    duration: int | None = Field(default=None, description="Video duration in seconds")
    source: str = Field(
        default="history",
        description="Where this video was discovered: 'history', 'playlist', or 'watch_later'",
    )


class FilterDecision(BaseModel):
    """Result of the topic classification filter."""

    keep: bool = Field(description="Whether to keep (True) or skip (False) this video")
    category: str = Field(description="Detected category, e.g. 'AI Systems', 'Entertainment'")
    reason: str = Field(description="Brief explanation of why the video was kept or skipped")


class ActionableFramework(BaseModel):
    """A named framework or mental model mentioned in the video."""

    name: str = Field(description="Name of the framework or mental model")
    description: str = Field(description="Brief description of how it works")


class KnowledgeCard(BaseModel):
    """
    Structured knowledge card extracted from a video transcript by Gemini.

    This model is ALSO passed as Gemini's response_schema to enforce
    structured JSON output via the google-genai SDK.
    """

    video_id: str = Field(description="YouTube video ID")
    title: str = Field(description="Video title")
    channel: str = Field(description="Channel name")
    url: str = Field(description="Full YouTube URL")
    processed_at: str = Field(description="ISO 8601 timestamp of when this was processed")
    category: str = Field(
        description=(
            "One of: AI Systems, Programming, Startups & Business, "
            "Electrical Engineering, Electronics, Career & Skills, Research, Other"
        )
    )
    one_sentence_summary: str = Field(
        description="A crisp single sentence capturing the core insight of the video"
    )
    key_takeaways: list[str] = Field(
        description="3-7 bullet points of the most actionable insights"
    )
    actionable_frameworks: list[ActionableFramework] = Field(
        default_factory=list,
        description="Named frameworks or mental models mentioned (empty list if none)",
    )
    memorable_quotes: list[str] = Field(
        default_factory=list,
        description="Direct quotes worth remembering, max 3 (empty list if none)",
    )
    related_topics: list[str] = Field(
        description="3-5 topic tags for cross-referencing, e.g. ['ai', 'agents', 'automation']"
    )


class ProcessingResult(BaseModel):
    """Final result of processing a single video."""

    video: VideoMeta
    status: str = Field(description="'success', 'skipped', 'error'")
    filter_decision: FilterDecision | None = None
    knowledge_card: KnowledgeCard | None = None
    error_message: str | None = None
