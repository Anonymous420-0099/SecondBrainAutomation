# SECOND BRAIN KNOWLEDGE PROTOCOL

You are operating inside the **Second Brain Data** workspace.
This workspace contains a curated, continually updating database of structured YouTube knowledge notes, case studies, actionable frameworks, and complete transcripts.

---

## ⚡ MANDATORY RETRIEVAL WORKFLOW ON EVERY CONVERSATION

Whenever the user asks a question, makes a request, or discusses a topic:

### STEP 1: Instant Second Brain Check (Takes < 0.2s)
Before answering from general model knowledge alone, determine if the topic connects to the user's Second Brain:
- Run the local search CLI tool:
  ```powershell
  python "f:\Second Brain Data\search_brain.py" "<core concepts of user question>"
  ```
  *(Or consult `MIND_MAP.md` if reviewing cluster themes).*

### STEP 2: Evaluate Relevance
- **If matching notes are found with high relevance score (> 4.0 or exact concept match):**
  1. Open and view the corresponding note file (`f:\Second Brain Data\notes\...md`).
  2. Read the specific summary, actionable frameworks, case studies, and transcript details.
  3. Conduct your own deep synthesis/research to expand upon and verify the insights.
  4. Formulate the response incorporating the **Second Brain's exact frameworks, quotes, and case studies**, explicitly citing the source channel/video so the user knows their curated knowledge is actively driving the answer.
- **If NO matching note exists (score is 0 or query is totally unrelated):**
  1. Do NOT force a fake connection.
  2. Answer normally and thoroughly using your expert capabilities and general research.

---

## 📁 Key File Index
- Master Mind Map: `f:\Second Brain Data\MIND_MAP.md`
- Fast Search Engine: `f:\Second Brain Data\search_brain.py`
- Pre-indexed Cache: `f:\Second Brain Data\brain_cache.json`
- Raw Notes Archive: `f:\Second Brain Data\notes/`
- JSON Knowledge Cards: `f:\Second Brain Data\json/`
