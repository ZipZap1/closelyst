"""Score-Storage fuer score_voices.py.

Zwei Backends:
- Supabase (wenn SUPABASE_URL und SUPABASE_KEY gesetzt sind, persistent in Cloud)
- JSON-File-Fallback (lokal, wenn keine Supabase-Credentials)

Schema im Supabase:
  CREATE TABLE voice_scores (
    tester_name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    score INTEGER,
    note TEXT,
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tester_name, file_name)
  );

Setup-Doku: SUPABASE_SETUP.md im selben Ordner.
"""
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Optional

JSON_FILE = Path(__file__).parent / "test_outputs" / "voice-quality-test" / "scores.json"
TABLE = "voice_scores"


def _get_supabase_creds():
    """Returns (url, key) or (None, None). Looks in env first, then Streamlit secrets."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if url and key:
        return url, key
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "").strip()
        key = st.secrets.get("SUPABASE_KEY", "").strip()
        if url and key:
            return url, key
    except Exception:
        pass
    return None, None


def _get_client():
    url, key = _get_supabase_creds()
    if not (url and key):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def is_supabase() -> bool:
    return _get_client() is not None


def load_all_scores() -> dict:
    """Returns {tester_name: {file_name: {score, note}}}."""
    client = _get_client()
    if client:
        try:
            res = client.table(TABLE).select("*").execute()
            data = defaultdict(dict)
            for row in (res.data or []):
                data[row["tester_name"]][row["file_name"]] = {
                    "score": row.get("score"),
                    "note": row.get("note", "") or "",
                }
            return dict(data)
        except Exception:
            # Fallback to JSON if Supabase call fails
            pass
    return _load_json()


def upsert_score(tester_name: str, file_name: str, score: Optional[int], note: str = ""):
    client = _get_client()
    if client:
        try:
            client.table(TABLE).upsert({
                "tester_name": tester_name,
                "file_name": file_name,
                "score": score,
                "note": note or "",
            }).execute()
            return
        except Exception:
            pass
    _save_json_one(tester_name, file_name, score, note)


def _load_json() -> dict:
    if JSON_FILE.exists():
        try:
            data = json.loads(JSON_FILE.read_text())
            if isinstance(data, dict):
                # Migrate flat-format if needed
                if data and all(isinstance(v, dict) and "score" in v for v in data.values()):
                    return {"legacy": data}
                return data
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def _save_json_one(tester_name: str, file_name: str, score: Optional[int], note: str):
    all_scores = _load_json()
    all_scores.setdefault(tester_name, {})
    all_scores[tester_name][file_name] = {"score": score, "note": note or ""}
    JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
    JSON_FILE.write_text(json.dumps(all_scores, indent=2, sort_keys=True))
