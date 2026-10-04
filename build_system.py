#!/usr/bin/env python3
"""
Builds the Mind Map and Search Engine for Second Brain Data.
Scans index.json and all json/ files, generates:
1. brain_cache.json (ultra-fast indexed lookup)
2. search_brain.py (CLI and programmatic search script)
3. MIND_MAP.md (comprehensive structured knowledge mind map)
4. GEMINI.md (automatic workspace rule for Antigravity)
"""

import os
import re
import json
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, "json")
NOTES_DIR = os.path.join(BASE_DIR, "notes")
INDEX_PATH = os.path.join(BASE_DIR, "index.json")

def load_all_records():
    records = []
    seen_ids = set()

    # Load from json directory
    json_files = glob.glob(os.path.join(JSON_DIR, "**", "*.json"), recursive=True)
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                d = json.load(f)
            vid = d.get("video_id")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                rel_json = os.path.relpath(jf, BASE_DIR).replace("\\", "/")
                # derive relative note path
                rel_note = rel_json.replace("json/", "notes/").replace(".json", ".md")
                d["rel_json_path"] = rel_json
                d["rel_note_path"] = rel_note
                d["abs_note_path"] = os.path.join(BASE_DIR, rel_note).replace("\\", "/")
                records.append(d)
        except Exception as e:
            print(f"Error loading {jf}: {e}")

    # Cross-reference with index.json if needed
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                idx = json.load(f)
            for item in idx:
                vid = item.get("video_id")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    note_p = item.get("note_path", "")
                    if note_p.endswith(".notes"):
                        note_p = note_p[:-6] + ".md"
                    item["rel_note_path"] = note_p
                    item["abs_note_path"] = os.path.join(BASE_DIR, note_p).replace("\\", "/")
                    item["one_sentence_summary"] = item.get("summary", "")
                    item["actionable_frameworks"] = []
                    item["key_takeaways"] = []
                    item["related_topics"] = []
                    records.append(item)
        except Exception as e:
            print(f"Error reading index.json: {e}")

    return records

def categorize_and_cluster(records):
    clusters = {
        "AI Systems & Automation": {
            "icon": "🤖",
            "desc": "Autonomous workflows, LLM prompt architectures, video generation models, agent pipelines, and channel cloning techniques.",
            "records": []
        },
        "YouTube Growth & Viral Mechanics": {
            "icon": "🚀",
            "desc": "Retention hacking, Script Bending, Jenny Hoyos retention curves, escaping viewbombs, 9-video rule, and high-CTR thumbnail psychology.",
            "records": []
        },
        "Faceless Niches & Monetization": {
            "icon": "💰",
            "desc": "High-RPM faceless niches, 30-day monetization case studies, turning channels into sellable assets, TikTok Shop scale, and affiliate funnels.",
            "records": []
        },
        "Video Editing & Production Craft": {
            "icon": "🎬",
            "desc": "CapCut documentary editing workflows, motion control, sound design, visual pacing, and bulk visual production.",
            "records": []
        },
        "Engineering, Infrastructure & Hardware": {
            "icon": "⚡",
            "desc": "Power grid black start protocols, electrical cranking paths, free cloud GPU servers, and decentralized open-source infrastructure.",
            "records": []
        },
        "Psychology, Communication & Influence": {
            "icon": "🧠",
            "desc": "Robert Greene's Laws of Seduction & Influence, persuasive storytelling, Pulitzer Prize writing workflows, and communication mastery.",
            "records": []
        }
    }

    for r in records:
        title = r.get("title", "").lower()
        cat = r.get("category", "")
        topics = [t.lower() for t in r.get("related_topics", [])]
        combined = f"{title} {' '.join(topics)} {r.get('one_sentence_summary', '').lower()}"

        if any(k in combined for k in ["blackout", "power grid", "cranking path", "gpu server", "open-source internet", "open source internet"]):
            clusters["Engineering, Infrastructure & Hardware"]["records"].append(r)
        elif any(k in combined for k in ["robert greene", "seduction", "pulitzer", "writing process", "communication", "richard powers"]):
            clusters["Psychology, Communication & Influence"]["records"].append(r)
        elif any(k in combined for k in ["capcut", "editing", "motion control", "documentary editing"]):
            clusters["Video Editing & Production Craft"]["records"].append(r)
        elif any(k in combined for k in ["script bending", "viewbomb", "261 billion", "jenny hoyos", "thumbnail", "9-video rule", "9 video rule", "algorithm", "0 subs", "seo"]):
            clusters["YouTube Growth & Viral Mechanics"]["records"].append(r)
        elif any(k in combined for k in ["niche", "faceless", "monetiz", "$47,000", "20k/month", "300k", "tiktok shop", "photo automation", "sell anything", "money"]):
            clusters["Faceless Niches & Monetization"]["records"].append(r)
        elif cat == "AI Systems" or any(k in combined for k in ["claude", "gpt", "agent", "google flow", "veo", "antigravity", "transformer", "karpathy", "higgsfield", "ai"]):
            clusters["AI Systems & Automation"]["records"].append(r)
        else:
            clusters["Faceless Niches & Monetization"]["records"].append(r)

    return clusters

def generate_search_script():
    script_content = '''#!/usr/bin/env python3
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "brain_cache.json")

def tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    return re.findall(r'[a-z0-9_\\-\\+]+', text)

def compute_score(query_tokens: List[str], record: Dict[str, Any]) -> float:
    score = 0.0
    
    title_tokens = tokenize(record.get("title", ""))
    tags_tokens = tokenize(" ".join(record.get("related_topics", [])))
    cat_tokens = tokenize(record.get("category", ""))
    summary_tokens = tokenize(record.get("one_sentence_summary", "") or record.get("summary", ""))
    
    # Framework names
    fw_names = " ".join([fw.get("name", "") for fw in record.get("actionable_frameworks", [])])
    fw_tokens = tokenize(fw_names)
    
    # Takeaways
    takeaways = " ".join(record.get("key_takeaways", []))
    takeaways_tokens = tokenize(takeaways)
    
    # Full transcript preview tokens
    transcript_preview = tokenize(record.get("transcript", "")[:3000])

    for q in query_tokens:
        # Exact title match
        if q in title_tokens:
            score += 6.0
        elif any(q in t for t in title_tokens):
            score += 3.0
            
        # Tags / Related Topics match
        if q in tags_tokens:
            score += 4.5
            
        # Frameworks match
        if q in fw_tokens:
            score += 5.0
            
        # Summary match
        if q in summary_tokens:
            score += 3.0
            
        # Key takeaways match
        if q in takeaways_tokens:
            score += 2.0
            
        # Category match
        if q in cat_tokens:
            score += 1.5
            
        # Transcript match
        if q in transcript_preview:
            score += 1.0

    # Phrase match bonus
    query_str = " ".join(query_tokens)
    full_text = f"{record.get('title', '')} {summary_tokens} {fw_names}".lower()
    if query_str and query_str in full_text:
        score += 10.0

    return score

def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    if not os.path.exists(CACHE_FILE):
        print(f"Error: Cache file not found at {CACHE_FILE}. Run python build_system.py first.")
        return []

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    scored_records = []
    for r in records:
        score = compute_score(query_tokens, r)
        if score > 0:
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
        print(f"\\n🔍 No direct Second Brain matches found for: '{query_str}'")
        print("💡 The assistant will answer normally using general expertise.\\n")
        return

    print(f"\\n🧠 Found {len(results)} Second Brain matches for: '{query_str}'\\n" + "="*70)
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
'''
    with open(os.path.join(BASE_DIR, "search_brain.py"), "w", encoding="utf-8") as f:
        f.write(script_content)
    print("Created search_brain.py")

def generate_mind_map_markdown(clusters, total_records):
    md = []
    md.append("# 🧠 Second Brain Master Knowledge Mind Map & Fast Retrieval Map\n")
    md.append(f"> **Database Scope:** {total_records} structured knowledge cards, video transcripts, frameworks, and actionable notes.")
    md.append("> **Automated Cloud Sync:** Synced live with GitHub Actions repository `SecondBrainAutomation`.\n")
    md.append("---\n")
    md.append("## 🧭 High-Level Architecture Diagram\n")
    md.append("```mermaid")
    md.append("graph TD")
    md.append("    SB[🧠 Second Brain Knowledge Hub] --> AI[🤖 AI Systems & Automation]")
    md.append("    SB --> YT[🚀 YouTube Growth & Virality]")
    md.append("    SB --> BIZ[💰 Faceless Niches & Monetization]")
    md.append("    SB --> EDIT[🎬 Video Editing & Production Craft]")
    md.append("    SB --> ENG[⚡ Engineering & Infrastructure]")
    md.append("    SB --> PSY[🧠 Psychology & Influence]")
    md.append("```\n")
    md.append("---\n")
    md.append("## ⚡ Instant Retrieval Protocol for Antigravity\n")
    md.append("Whenever a question is asked:\n")
    md.append("1. **Find Matching Node:** Scan the domain clusters below or run `python search_brain.py \"<user query>\"`.")
    md.append("2. **Inspect the Target Note:** Open the linked note file directly: `file:///f:/Second Brain Data/notes/...md`.")
    md.append("3. **Extract Exact Facts:** Pull the specific case study numbers, framework steps, tool names, or transcript quotes.")
    md.append("4. **Synthesize & Cite:** Combine the Second Brain insights with fresh research and cite the specific video/channel.\n")
    md.append("---\n")

    for cat_name, cat_data in clusters.items():
        records = cat_data["records"]
        icon = cat_data["icon"]
        desc = cat_data["desc"]
        md.append(f"## {icon} {cat_name} ({len(records)} Videos)")
        md.append(f"*{desc}*\n")
        
        # Table of contents for this category
        md.append("| Video / Topic | Channel | Key Frameworks & Keywords | Note Link |")
        md.append("| :--- | :--- | :--- | :--- |")
        
        for r in records:
            title = r.get("title", "").replace("|", "-")
            channel = r.get("channel", "Unknown")
            fws = [fw.get("name", "") for fw in r.get("actionable_frameworks", [])]
            topics = r.get("related_topics", [])
            tag_str = ", ".join(fws[:2] + topics[:2]) if (fws or topics) else "Knowledge Note"
            rel_note = r.get("rel_note_path", "")
            abs_note = r.get("abs_note_path", "")
            md.append(f"| **{title}** | {channel} | `{tag_str}` | [Read Note](file:///{abs_note}) |")
        
        md.append("\n### Detailed Topic Breakdowns & Retrieval Triggers\n")
        
        for r in records:
            title = r.get("title", "")
            channel = r.get("channel", "Unknown")
            abs_note = r.get("abs_note_path", "")
            summary = r.get("one_sentence_summary") or r.get("summary", "")
            fws = r.get("actionable_frameworks", [])
            takeaways = r.get("key_takeaways", [])
            topics = r.get("related_topics", [])
            url = r.get("url", "")
            
            md.append(f"#### 📌 [{title}](file:///{abs_note})")
            md.append(f"- **Channel & Source:** {channel} | [YouTube Link]({url})")
            md.append(f"- **Trigger Keywords:** `{'`, `'.join(topics)}`" if topics else "- **Trigger Keywords:** N/A")
            md.append(f"- **Executive Summary:** {summary}")
            
            if fws:
                md.append("- **Core Actionable Frameworks:**")
                for fw in fws:
                    md.append(f"  * **{fw.get('name')}:** {fw.get('description')}")
            
            if takeaways:
                md.append("- **Key Strategic Takeaways:**")
                for tk in takeaways[:3]:
                    md.append(f"  * {tk}")
            md.append("")
        
        md.append("---\n")

    content = "\n".join(md)
    with open(os.path.join(BASE_DIR, "MIND_MAP.md"), "w", encoding="utf-8") as f:
        f.write(content)
    print("Created MIND_MAP.md")

def generate_gemini_rule():
    rule_content = """# SECOND BRAIN KNOWLEDGE PROTOCOL

You are operating inside the **Second Brain Data** workspace.
This workspace contains a curated, continually updating database of structured YouTube knowledge notes, case studies, actionable frameworks, and complete transcripts.

---

## ⚡ MANDATORY RETRIEVAL WORKFLOW ON EVERY CONVERSATION

Whenever the user asks a question, makes a request, or discusses a topic:

### STEP 1: Instant Second Brain Check (Takes < 0.2s)
Before answering from general model knowledge alone, determine if the topic connects to the user's Second Brain:
- Run the local search CLI tool:
  ```powershell
  python "f:\\Second Brain Data\\search_brain.py" "<core concepts of user question>"
  ```
  *(Or consult `MIND_MAP.md` if reviewing cluster themes).*

### STEP 2: Evaluate Relevance
- **If matching notes are found with high relevance score (> 4.0 or exact concept match):**
  1. Open and view the corresponding note file (`f:\\Second Brain Data\\notes\\...md`).
  2. Read the specific summary, actionable frameworks, case studies, and transcript details.
  3. Conduct your own deep synthesis/research to expand upon and verify the insights.
  4. Formulate the response incorporating the **Second Brain's exact frameworks, quotes, and case studies**, explicitly citing the source channel/video so the user knows their curated knowledge is actively driving the answer.
- **If NO matching note exists (score is 0 or query is totally unrelated):**
  1. Do NOT force a fake connection.
  2. Answer normally and thoroughly using your expert capabilities and general research.

---

## 📁 Key File Index
- Master Mind Map: `f:\\Second Brain Data\\MIND_MAP.md`
- Fast Search Engine: `f:\\Second Brain Data\\search_brain.py`
- Pre-indexed Cache: `f:\\Second Brain Data\\brain_cache.json`
- Raw Notes Archive: `f:\\Second Brain Data\\notes/`
- JSON Knowledge Cards: `f:\\Second Brain Data\\json/`
"""
    with open(os.path.join(BASE_DIR, "GEMINI.md"), "w", encoding="utf-8") as f:
        f.write(rule_content)
    print("Created GEMINI.md")

def main():
    print("Loading all Second Brain records...")
    records = load_all_records()
    print(f"Loaded {len(records)} records.")

    # Save brain_cache.json for microsecond search
    cache_path = os.path.join(BASE_DIR, "brain_cache.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Saved {cache_path}")

    # Categorize and cluster
    clusters = categorize_and_cluster(records)

    # Generate search script
    generate_search_script()

    # Generate MIND_MAP.md
    generate_mind_map_markdown(clusters, len(records))

    # Generate GEMINI.md
    generate_gemini_rule()

    print("✅ All Second Brain mind map and search components built successfully!")

if __name__ == "__main__":
    main()
