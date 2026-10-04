#!/usr/bin/env python3
"""
Second Brain Instant Semantic & Keyword Search Engine
Usage:
    python search_brain.py "how to fix youtube shorts view freeze"
    python search_brain.py "claude channel clone" --top 3
    python search_brain.py "monetize faceless channel" --json
    python search_brain.py "robert greene" --show-notes
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "brain_cache.json")

STOP_WORDS = {
    "a", "an", "the", "in", "on", "of", "and", "or", "for", "with", "to", "at", "by", "from",
    "up", "about", "into", "over", "after", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "how", "what", "why", "when", "where", "who",
    "which", "this", "that", "these", "those", "can", "could", "should", "would", "my", "your",
    "our", "their", "his", "her", "its", "i", "me", "we", "you", "he", "she", "it", "they"
}

def tokenize(text: str, filter_stops: bool = False) -> List[str]:
    if not text:
        return []
    text = text.lower()
    tokens = re.findall(r'[a-z0-9_\-\+]+', text)
    if filter_stops:
        filtered = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
        return filtered if filtered else tokens
    return tokens

def compute_score(query_tokens: List[str], record: Dict[str, Any]) -> float:
    score = 0.0
    
    title_tokens = tokenize(record.get("title") or "")
    tags_tokens = tokenize(" ".join(record.get("related_topics") or []))
    cat_tokens = tokenize(record.get("category") or "")
    summary_tokens = tokenize(record.get("one_sentence_summary") or record.get("summary") or "")
    
    # Framework names
    fw_names = " ".join([fw.get("name") or "" for fw in (record.get("actionable_frameworks") or [])])
    fw_tokens = tokenize(fw_names)
    
    # Takeaways
    takeaways = " ".join(record.get("key_takeaways") or [])
    takeaways_tokens = tokenize(takeaways)
    
    # Full transcript preview tokens
    raw_transcript = record.get("transcript") or ""
    transcript_preview = tokenize(raw_transcript[:3000])

    for q in query_tokens:
        # Exact title match
        if q in title_tokens:
            score += 6.0
        elif any(q in t for t in title_tokens):
            score += 3.0
            
        # Tags / Related Topics match
        if q in tags_tokens:
            score += 5.0
            
        # Frameworks match
        if q in fw_tokens:
            score += 5.5
            
        # Summary match
        if q in summary_tokens:
            score += 3.0
            
        # Key takeaways match
        if q in takeaways_tokens:
            score += 2.0
            
        # Category match
        if q in cat_tokens:
            score += 1.5
            
        # Transcript match (only if unique token)
        if q in transcript_preview:
            score += 0.8

    # Phrase match bonus
    query_str = " ".join(query_tokens)
    full_text = f"{record.get('title', '')} {' '.join(summary_tokens)} {fw_names}".lower()
    if query_str and query_str in full_text:
        score += 12.0

    return score

def search(query: str, top_k: int = 5, min_score: float = 5.0) -> List[Dict[str, Any]]:
    if not os.path.exists(CACHE_FILE):
        print(f"Error: Cache file not found at {CACHE_FILE}. Run python build_system.py first.")
        return []

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    query_tokens = tokenize(query, filter_stops=True)
    if not query_tokens:
        return []

    scored_records = []
    for r in records:
        score = compute_score(query_tokens, r)
        if score >= min_score:
            scored_records.append((score, r))

    scored_records.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, r in scored_records[:top_k]:
        res = dict(r)
        res["search_score"] = round(score, 2)
        results.append(res)
    return results

def main():
    parser = argparse.ArgumentParser(description="Second Brain Knowledge Search")
    parser.add_argument("query", type=str, nargs="+", help="Search query keywords")
    parser.add_argument("--top", type=int, default=3, help="Number of results to return (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--show-notes", action="store_true", help="Print detailed frameworks & summary")
    args = parser.parse_args()

    query_str = " ".join(args.query)
    results = search(query_str, top_k=args.top)

    if args.json:
        # Output clean json
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    if not results:
        print(f"\n🔍 No direct Second Brain matches found for: '{query_str}'")
        print("💡 The assistant will answer normally using general expertise.\n")
        return

    print(f"\n🧠 Found {len(results)} Second Brain matches for: '{query_str}'\n" + "="*70)
    for i, r in enumerate(results, 1):
        print(f"#{i} [{r.get('category', 'Topic')}] (Score: {r['search_score']})")
        print(f"📌 Title:    {r.get('title')}")
        print(f"📺 Channel:  {r.get('channel')} | URL: {r.get('url')}")
        print(f"📄 Note:     file:///{r.get('abs_note_path')}")
        summary = r.get('one_sentence_summary') or r.get('summary', '')
        print(f"📝 Summary:  {summary}")
        
        frameworks = r.get("actionable_frameworks", [])
        if frameworks:
            print("🛠️ Frameworks:")
            for fw in frameworks:
                print(f"   • {fw.get('name')}: {fw.get('description')}")
                
        if args.show_notes:
            takeaways = r.get("key_takeaways", [])
            if takeaways:
                print("💡 Key Takeaways:")
                for tk in takeaways:
                    print(f"   - {tk}")
            quotes = r.get("memorable_quotes", [])
            if quotes:
                print(f"💬 Quote: {quotes[0]}")
        print("-" * 70)

if __name__ == "__main__":
    main()
