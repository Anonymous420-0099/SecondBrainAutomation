"""
storage.py — File saving and GitHub push operations.

Generates Markdown notes and JSON cards from KnowledgeCard objects,
saves them to the local GitHub repo clone, maintains a master index,
and commits + pushes to GitHub via GitPython.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from git import Repo, InvalidGitRepositoryError

import config
from models import KnowledgeCard
from utils import safe_write, slugify, today_date

logger = logging.getLogger("youtube_second_brain")


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------
def generate_markdown(card: KnowledgeCard) -> str:
    """
    Generates a well-formatted Markdown note from a KnowledgeCard.

    Args:
        card: The structured knowledge card.

    Returns:
        Complete Markdown string ready to save as a .md file.
    """
    lines: list[str] = []

    # Header
    lines.append(f"# {card.title}")
    lines.append("")
    lines.append(f"- **Channel:** {card.channel}")
    lines.append(f"- **URL:** {card.url}")
    lines.append(f"- **Category:** {card.category}")
    lines.append(f"- **Processed:** {card.processed_at[:10]}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append(card.one_sentence_summary)
    lines.append("")

    # Key Takeaways
    lines.append("## Key Takeaways")
    for takeaway in card.key_takeaways:
        lines.append(f"- {takeaway}")
    lines.append("")

    # Actionable Frameworks
    if card.actionable_frameworks:
        lines.append("## Actionable Frameworks")
        for framework in card.actionable_frameworks:
            lines.append(f"### {framework.name}")
            lines.append(framework.description)
            lines.append("")

    # Memorable Quotes
    if card.memorable_quotes:
        lines.append("## Memorable Quotes")
        for quote in card.memorable_quotes:
            lines.append(f"> {quote}")
            lines.append("")

    # Tags
    lines.append("## Tags")
    tags = " ".join([f"`#{topic}`" for topic in card.related_topics])
    lines.append(tags)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File saving
# ---------------------------------------------------------------------------
def save_knowledge_card(card: KnowledgeCard) -> tuple[str, str]:
    """
    Saves a KnowledgeCard as both Markdown and JSON files.

    File structure:
        {repo}/notes/YYYY/MM/YYYY-MM-DD-slug.md
        {repo}/json/YYYY/MM/YYYY-MM-DD-slug.json

    Args:
        card: The structured knowledge card.

    Returns:
        Tuple of (markdown_path, json_path) — relative to the repo root.
    """
    repo_path = config.GITHUB_REPO_PATH
    if not repo_path:
        # Fallback: save in project directory
        repo_path = str(Path(__file__).resolve().parent / "output")
        logger.warning(f"GITHUB_REPO_PATH not set. Saving to {repo_path}")

    # Generate filename parts
    date = today_date()  # YYYY-MM-DD
    year = date[:4]
    month = date[5:7]
    slug = slugify(card.title)
    filename_base = f"{date}-{slug}"

    # Markdown file
    md_rel_path = f"notes/{year}/{month}/{filename_base}.md"
    md_abs_path = os.path.join(repo_path, md_rel_path)
    markdown_content = generate_markdown(card)
    safe_write(md_abs_path, markdown_content)
    logger.info(f"[storage] Saved Markdown: {md_rel_path}")

    # JSON file
    json_rel_path = f"json/{year}/{month}/{filename_base}.json"
    json_abs_path = os.path.join(repo_path, json_rel_path)
    json_content = card.model_dump_json(indent=2)
    safe_write(json_abs_path, json_content)
    logger.info(f"[storage] Saved JSON: {json_rel_path}")

    # Update master index
    _update_index(card, md_rel_path, repo_path)

    return md_rel_path, json_rel_path


# ---------------------------------------------------------------------------
# Master index
# ---------------------------------------------------------------------------
def _update_index(card: KnowledgeCard, md_path: str, repo_path: str) -> None:
    """
    Appends an entry to the master index.json file.

    The index provides a quick lookup of all processed videos
    without needing to scan individual files.
    """
    index_path = os.path.join(repo_path, "index.json")

    # Load existing index
    index: list[dict] = []
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.warning("Could not read index.json, starting fresh")
            index = []

    # Append new entry
    index.append({
        "video_id": card.video_id,
        "title": card.title,
        "channel": card.channel,
        "category": card.category,
        "summary": card.one_sentence_summary,
        "processed_at": card.processed_at,
        "url": card.url,
        "note_path": md_path,
    })

    # Save updated index
    safe_write(index_path, json.dumps(index, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Git operations
# ---------------------------------------------------------------------------
def git_commit_and_push(file_count: int) -> bool:
    """
    Stages all new files, commits, and pushes to GitHub.

    In CI mode (GitHub Actions), git identity is pre-configured by the workflow.
    Locally, uses your existing git config.

    Args:
        file_count: Number of new videos processed (for commit message).

    Returns:
        True if push succeeded, False otherwise.
    """
    repo_path = config.GITHUB_REPO_PATH
    if not repo_path or not Path(repo_path).is_dir():
        logger.warning("GITHUB_REPO_PATH not set or invalid. Skipping Git operations.")
        return False

    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        logger.error(
            f"'{repo_path}' is not a Git repository. "
            "Initialize it with 'git init' or clone your GitHub repo."
        )
        return False

    # In CI mode (GitHub Actions), the workflow step handles commit and push natively
    if config.CI_MODE:
        logger.info("[git] Running in CI mode — commit & push will be handled by the GitHub Actions workflow.")
        return True

    # Check if there are any changes to commit
    if not repo.is_dirty(untracked_files=True):
        logger.info("[git] No changes to commit")
        return True

    try:
        # Stage all changes
        repo.git.add("--all")

        # Commit
        date = today_date()
        commit_msg = f"📚 Daily ingest: {file_count} new video{'s' if file_count != 1 else ''} ({date})"
        repo.index.commit(commit_msg)
        logger.info(f"[git] Committed: {commit_msg}")

        # Push
        if repo.remotes:
            origin = repo.remotes.origin
            origin.push()
            logger.info("[git] ✅ Pushed to GitHub successfully")
            return True
        else:
            logger.warning("[git] No remote 'origin' configured. Commit saved locally.")
            return False

    except Exception as e:
        logger.error(
            f"[git] Push failed: {e}. "
            "Changes are committed locally and will be included in the next push."
        )
        return False
