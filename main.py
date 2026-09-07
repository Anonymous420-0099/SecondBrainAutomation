"""
main.py — Pipeline orchestrator for the YouTube Second Brain.

Entry point that ties all modules together. Supports three modes:
  python main.py                     → Full pipeline run
  python main.py --dry-run           → Process but don't push to Git
  python main.py --test-url URL      → Process a single URL for testing

Each video is processed independently — if one fails, others continue.
"""

from __future__ import annotations

import argparse
import sys
import time

import config
from models import VideoMeta, ProcessingResult
from sources import fetch_all_new_videos, save_processed_id, deduplicate
from transcript import fetch_transcript, add_random_delay
from filter import classify_video
from structurer import create_gemini_client, structure_transcript
from storage import save_knowledge_card, git_commit_and_push
from utils import setup_logging, utc_now_iso


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="YouTube Second Brain — Automated Knowledge Ingestion Pipeline",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process videos but don't commit/push to Git",
    )
    parser.add_argument(
        "--test-url",
        type=str,
        default=None,
        help="Process a single YouTube URL for testing (e.g., https://youtube.com/watch?v=...)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip topic filtering (process all videos regardless of content)",
    )
    return parser.parse_args()


def extract_video_id(url: str) -> str | None:
    """
    Extracts the video ID from a YouTube URL.

    Supports:
        https://www.youtube.com/watch?v=LqY6hFLMEJw
        https://youtu.be/LqY6hFLMEJw
        LqY6hFLMEJw (raw ID)
    """
    import re

    # Pattern for youtube.com/watch?v= URLs
    match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)

    # Pattern for youtu.be/ URLs
    match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)

    # Maybe it's already a raw video ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url

    return None


def process_single_video(
    video: VideoMeta,
    gemini_client,
    skip_filter: bool = False,
) -> ProcessingResult:
    """
    Processes a single video through the full pipeline.

    Steps:
    1. Classify (filter) the video
    2. Fetch transcript
    3. Structure with Gemini
    4. Save files

    Args:
        video: Video metadata.
        gemini_client: Pre-initialized Gemini client.
        skip_filter: If True, skip topic filtering.

    Returns:
        ProcessingResult with status and details.
    """
    logger = setup_logging(config.LOG_DIR)

    # --- Step 1: Topic filtering ---
    if not skip_filter:
        decision = classify_video(
            video=video,
            transcript_preview=None,  # We'll classify by title/channel first
            gemini_client=gemini_client,
        )

        if not decision.keep:
            logger.info(
                f"⏭️  SKIPPED: '{video.title}' — {decision.reason}"
            )
            return ProcessingResult(
                video=video,
                status="skipped",
                filter_decision=decision,
            )

        logger.info(
            f"✅ KEEP: '{video.title}' — {decision.category}"
        )
    else:
        from models import FilterDecision
        decision = FilterDecision(keep=True, category="Unfiltered", reason="Filtering disabled")

    # --- Step 2: Fetch transcript ---
    logger.info(f"📝 Fetching transcript for '{video.title}'...")
    transcript_text = fetch_transcript(video.video_id)

    if not transcript_text:
        logger.warning(f"⚠️  No transcript available for '{video.title}'. Skipping.")
        return ProcessingResult(
            video=video,
            status="error",
            filter_decision=decision,
            error_message="No transcript available",
        )

    # --- Step 3: Structure with Gemini ---
    logger.info(f"🤖 Structuring '{video.title}' with Gemini...")
    try:
        card = structure_transcript(
            video=video,
            transcript_text=transcript_text,
            client=gemini_client,
        )
    except Exception as e:
        logger.error(f"❌ Gemini structuring failed for '{video.title}': {e}")
        return ProcessingResult(
            video=video,
            status="error",
            filter_decision=decision,
            error_message=f"Gemini structuring failed: {e}",
        )

    # --- Step 4: Save files ---
    try:
        md_path, json_path = save_knowledge_card(card)
        logger.info(f"💾 Saved: {md_path}")
    except Exception as e:
        logger.error(f"❌ File save failed for '{video.title}': {e}")
        return ProcessingResult(
            video=video,
            status="error",
            filter_decision=decision,
            knowledge_card=card,
            error_message=f"File save failed: {e}",
        )

    return ProcessingResult(
        video=video,
        status="success",
        filter_decision=decision,
        knowledge_card=card,
    )


def run_test_mode(test_url: str, dry_run: bool, skip_filter: bool) -> None:
    """
    Process a single video URL for testing purposes.
    """
    logger = setup_logging(config.LOG_DIR)
    logger.info(f"🧪 TEST MODE: Processing single URL: {test_url}")

    video_id = extract_video_id(test_url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {test_url}")
        sys.exit(1)

    video = VideoMeta(
        video_id=video_id,
        title=f"Test Video ({video_id})",
        channel=None,
        url=test_url if test_url.startswith("http") else f"https://www.youtube.com/watch?v={test_url}",
        duration=None,
        source="test",
    )

    # Initialize Gemini
    gemini_client = create_gemini_client()

    # Process
    result = process_single_video(video, gemini_client, skip_filter=skip_filter)

    # Report
    logger.info(f"\n{'='*60}")
    logger.info(f"Test Result: {result.status.upper()}")
    if result.knowledge_card:
        logger.info(f"Summary: {result.knowledge_card.one_sentence_summary}")
        logger.info(f"Category: {result.knowledge_card.category}")
        logger.info(f"Takeaways: {len(result.knowledge_card.key_takeaways)}")
    elif result.error_message:
        logger.info(f"Error: {result.error_message}")
    logger.info(f"{'='*60}")

    if not dry_run and result.status == "success":
        git_commit_and_push(file_count=1)
        save_processed_id(video_id, utc_now_iso())


def run_full_pipeline(dry_run: bool, skip_filter: bool) -> None:
    """
    Full pipeline: fetch all sources → filter → transcript → structure → save → push.
    """
    logger = setup_logging(config.LOG_DIR)
    logger.info("🚀 YouTube Second Brain — Starting daily pipeline")
    logger.info(f"   Dry run: {dry_run}")
    logger.info(f"   Skip filter: {skip_filter}")

    # --- Validate config ---
    errors = config.validate_config()
    if errors:
        for error in errors:
            logger.error(f"❌ Config error: {error}")
        logger.error("Fix the above errors and try again.")
        sys.exit(1)

    # --- Initialize Gemini client ---
    gemini_client = create_gemini_client()
    logger.info("✅ Gemini client initialized")

    # --- Fetch videos from all sources ---
    new_videos = fetch_all_new_videos()

    if not new_videos:
        logger.info("📭 No new videos to process. Exiting.")
        return

    # --- Process each video ---
    results: list[ProcessingResult] = []

    for i, video in enumerate(new_videos, start=1):
        logger.info(f"\n{'─'*60}")
        logger.info(f"📹 [{i}/{len(new_videos)}] Processing: '{video.title}'")
        logger.info(f"   Channel: {video.channel} | Source: {video.source}")

        result = process_single_video(video, gemini_client, skip_filter=skip_filter)
        results.append(result)

        # Mark as processed regardless of result (don't re-process failures)
        save_processed_id(video.video_id, utc_now_iso())

        # Rate limit delay between videos
        if i < len(new_videos):
            add_random_delay()
            time.sleep(config.API_DELAY_SECONDS)

    # --- Summary ---
    success_count = sum(1 for r in results if r.status == "success")
    skipped_count = sum(1 for r in results if r.status == "skipped")
    error_count = sum(1 for r in results if r.status == "error")

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Daily Summary")
    logger.info(f"   ✅ Processed: {success_count}")
    logger.info(f"   ⏭️  Skipped:   {skipped_count}")
    logger.info(f"   ❌ Errors:    {error_count}")
    logger.info(f"   📹 Total:     {len(results)}")
    logger.info(f"{'='*60}")

    # --- Git commit & push ---
    if not dry_run and success_count > 0:
        git_commit_and_push(file_count=success_count)
    elif dry_run:
        logger.info("🏜️  Dry run — skipping Git commit/push")

    logger.info("🏁 Pipeline complete!")


def main() -> None:
    """Entry point."""
    args = parse_args()

    if args.test_url:
        run_test_mode(
            test_url=args.test_url,
            dry_run=args.dry_run,
            skip_filter=args.no_filter,
        )
    else:
        run_full_pipeline(
            dry_run=args.dry_run,
            skip_filter=args.no_filter,
        )


if __name__ == "__main__":
    main()
