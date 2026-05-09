"""Pexels Video API wrapper. Keyword-to-stock-video matching."""
import os
import re
import requests

API_BASE = "https://api.pexels.com/videos"

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on", "and",
    "or", "but", "for", "with", "as", "at", "by", "this", "that", "it", "be",
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "wenn", "ist",
    "sind", "war", "waren", "von", "auf", "an", "zu", "im", "in", "mit", "fuer",
    "fur", "wie", "was", "wer", "wo", "wann", "warum", "ich", "du", "er", "sie",
    "es", "wir", "ihr", "sie", "den", "dem", "des",
}


def _headers():
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key or key == "your_pexels_key_here":
        raise RuntimeError(
            "PEXELS_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    return {"Authorization": key}


def extract_keywords(text, max_keywords=3):
    """Naive keyword extraction. Pick longest non-stopword tokens."""
    words = re.findall(r"\b[a-zA-ZäöüÄÖÜß]{4,}\b", text.lower())
    keywords = [w for w in words if w not in STOPWORDS]
    seen = set()
    unique = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    unique.sort(key=len, reverse=True)
    return unique[:max_keywords]


def search_videos(query, per_page=10):
    """Search Pexels videos. Prefer portrait orientation for TikTok."""
    r = requests.get(
        f"{API_BASE}/search",
        headers=_headers(),
        params={"query": query, "per_page": per_page, "orientation": "portrait"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("videos", [])


def pick_video_url(query):
    """Pick a small mp4 URL from the first matching video. Returns None if nothing found."""
    videos = search_videos(query, per_page=10)
    if not videos:
        return None
    for v in videos:
        files = v.get("video_files", [])
        mp4_files = [f for f in files if f.get("file_type") == "video/mp4"]
        if not mp4_files:
            continue
        # Prefer SD (smaller download)
        mp4_files.sort(key=lambda f: f.get("width") or 999999)
        for f in mp4_files:
            if f.get("width") and 480 <= f["width"] <= 1080:
                return f["link"]
        return mp4_files[0]["link"]
    return None


def download(url, out_path):
    """Stream-download a URL to local path."""
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return out_path
