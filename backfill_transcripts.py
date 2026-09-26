"""
backfill_transcripts.py — Backfill missing transcripts for previously processed videos in-place.

Iterates through all JSON cards in json/, finds any that are missing a transcript,
fetches the transcript via transcript.fetch_transcript(), updates the KnowledgeCard,
and rewrites the EXACT existing Markdown note and JSON file with the full transcript.
Requires zero LLM API calls ($0 cost).
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import sys
import time

import config
from models import KnowledgeCard
from storage import generate_markdown, git_commit_and_push
from transcript import fetch_transcript
from utils import safe_write

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("backfill")


def backfill_all(dry_run: bool = False, push: bool = False) -> None:
    json_pattern = os.path.join(config.GITHUB_REPO_PATH, "json", "**", "*.json")
    all_json_files = glob.glob(json_pattern, recursive=True)

    targets: list[tuple[str, str, str]] = []
    for jf in sorted(all_json_files):
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("transcript"):
                targets.append((jf, data.get("video_id", ""), data.get("title", "")))
        except Exception as e:
            logger.warning(f"Could not read {jf}: {e}")

    logger.info(f"Found {len(targets)} previous videos missing transcripts out of {len(all_json_files)} total.")

    if not targets:
        logger.info("All videos already have transcripts! Nothing to do.")
        return

    success_count = 0
    fail_count = 0

    for idx, (json_path, video_id, title) in enumerate(targets, 1):
        if not video_id:
            logger.warning(f"[{idx}/{len(targets)}] No video_id found in {json_path}. Skipping.")
            continue

        clean_title = title.encode("ascii", "replace").decode("ascii")
        logger.info(f"[{idx}/{len(targets)}] Fetching transcript for '{clean_title}' ({video_id})...")
        try:
            transcript = fetch_transcript(video_id)
            if not transcript:
                logger.warning(f"[{idx}/{len(targets)}] No transcript available for {video_id}.")
                fail_count += 1
                continue

            word_count = len(transcript.split())
            logger.info(f"[{idx}/{len(targets)}] [OK] Extracted {word_count:,} words for '{clean_title}'.")

            if not dry_run:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                card = KnowledgeCard.model_validate(data)
                card.transcript = transcript

                from pathlib import Path
                p = Path(json_path)
                parts = list(p.parts)
                for i, part in enumerate(parts):
                    if part == "json":
                        parts[i] = "notes"
                        break
                md_path = str(Path(*parts).with_suffix(".md"))
                markdown_content = generate_markdown(card)
                safe_write(md_path, markdown_content)
                safe_write(json_path, card.model_dump_json(indent=2))
                logger.info(f"[{idx}/{len(targets)}] Saved in-place: {os.path.basename(md_path)}")
                success_count += 1
            else:
                logger.info(f"[dry-run] Would save transcript to {json_path}")
                success_count += 1

        except Exception as e:
            logger.error(f"[{idx}/{len(targets)}] Error backfilling {video_id}: {e}")
            fail_count += 1

        # Gentle delay to prevent rate limits
        time.sleep(1.0)

    logger.info("=" * 60)
    logger.info(f"Backfill Complete: {success_count} updated, {fail_count} failed or unavailable.")
    logger.info("=" * 60)

    if push and not dry_run and success_count > 0:
        logger.info("Pushing updated notes and JSON cards to GitHub...")
        git_commit_and_push(success_count)


def main():
    parser = argparse.ArgumentParser(description="Backfill transcripts for existing Second Brain notes.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and verify without saving to disk")
    parser.add_argument("--push", action="store_true", help="Commit and push changes to GitHub when done")
    args = parser.parse_args()

    backfill_all(dry_run=args.dry_run, push=args.push)


if __name__ == "__main__":
    main()
