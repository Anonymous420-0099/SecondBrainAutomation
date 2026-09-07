# 🧠 YouTube Second Brain (Automated Ingestion Pipeline)

An automated ingestion pipeline that transforms high-signal YouTube videos into structured knowledge cards and actionable Markdown notes.

Powered by **Gemini 2.5 Flash** and running 100% on **GitHub Actions Cloud** for **$0/month**.

---

## ⚡ How It Works

```
[ YouTube Playlist / History ]
            │ (Pulls new videos daily at 00:00 UTC)
            ▼
[ Multi-Stage Topic Filter ]
            │ (Keeps: AI, Startups, Electronics, Tech)
            │ (Discards: Gaming, Comedy, Shorts <60s)
            ▼
[ Transcript Extraction ]
            │ (Fetches English, Hindi, or Urdu subtitles)
            ▼
[ Gemini 2.5 Flash Structuring ]
            │ (Extracts: Core Insight, Frameworks, Quotes, Tags)
            ▼
[ Auto-Committed to GitHub ]
    ├── notes/YYYY/MM/YYYY-MM-DD-title.md   (Readable notes)
    ├── json/YYYY/MM/YYYY-MM-DD-title.json    (Machine-readable cards)
    └── index.json                            (Master searchable index)
```

---

## ☁️ Running on Cloud (GitHub Actions)

This pipeline runs automatically in GitHub's cloud every night at **00:00 UTC** via GitHub Actions. **Your laptop does not need to be turned on.**

### Required GitHub Secrets
In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret Name | Value | Required? |
|-------------|-------|-----------|
| `GEMINI_API_KEY` | Your free API key from [Google AI Studio](https://aistudio.google.com/apikey) | **Yes** |
| `SECOND_BRAIN_PLAYLIST_ID` | The YouTube Playlist ID of your "Second Brain Queue" (e.g. `PLxxxxxxxx`) | Recommended |
| `YOUTUBE_COOKIES` | Raw text contents of exported `cookies.txt` (for private watch history) | Optional |

---

## 💻 Manual Trigger (From Browser)
You can run this automation anytime on demand without touching code:
1. Go to the **Actions** tab on your GitHub repository.
2. Select **Daily YouTube Ingestion** on the left menu.
3. Click **Run workflow** → **Run workflow**.

---

## 📂 Repository Structure

- `notes/`: Markdown knowledge notes organized by year and month.
- `json/`: Complete structured JSON data for each processed video.
- `index.json`: Master index array of all summarized videos.
- `processed_videos.json`: Tracks processed video IDs to guarantee zero duplicates.
- `.github/workflows/daily_ingest.yml`: The GitHub Actions workflow that executes in the cloud.
