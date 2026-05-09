"""ElevenLabs API wrapper. Voice listing and TTS."""
import os
import requests

API_BASE = "https://api.elevenlabs.io/v1"


def _headers():
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key or key == "your_elevenlabs_key_here":
        raise RuntimeError(
            "ELEVENLABS_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    return {"xi-api-key": key}


def list_voices(limit=20):
    """Return up to `limit` voices as list of dicts."""
    r = requests.get(f"{API_BASE}/voices", headers=_headers(), timeout=15)
    r.raise_for_status()
    voices = r.json().get("voices", [])
    return [
        {
            "voice_id": v["voice_id"],
            "name": v["name"],
            "category": v.get("category", ""),
            "labels": v.get("labels", {}),
        }
        for v in voices[:limit]
    ]


def generate_voiceover(text, voice_id, model_id="eleven_multilingual_v2"):
    """Generate audio bytes (mp3) from text using the given voice."""
    url = f"{API_BASE}/text-to-speech/{voice_id}"
    headers = {**_headers(), "Content-Type": "application/json", "Accept": "audio/mpeg"}
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content


def generate_voiceover_with_timestamps(text, voice_id, model_id="eleven_multilingual_v2"):
    """Generate audio plus character-level timestamps.

    Returns tuple (audio_bytes, alignment_dict) where alignment_dict has keys:
      - characters: list of single-character strings
      - character_start_times_seconds: list of floats
      - character_end_times_seconds: list of floats
    """
    import base64
    url = f"{API_BASE}/text-to-speech/{voice_id}/with-timestamps"
    headers = {**_headers(), "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    audio = base64.b64decode(data["audio_base64"])
    alignment = data.get("alignment") or data.get("normalized_alignment") or {}
    return audio, alignment
