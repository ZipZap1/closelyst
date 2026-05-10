"""TTS wrapper. ElevenLabs (default) plus OpenAI as alternative backend.

Public surface used by Hauptseite.py and score_voices.py / run_voice_test.py:
- list_voices(limit): ElevenLabs voices for the voice picker
- list_openai_voices(): curated OpenAI voices for free-tier picker / scoring tool
- clone_voice / delete_voice: Instant-Voice-Clone via ElevenLabs
- generate_voiceover / generate_voiceover_with_timestamps: ElevenLabs TTS
- generate(text, backend, voice_id, **kwargs): backend-agnostic TTS for tests
"""
import os
import requests

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
OPENAI_BASE = "https://api.openai.com/v1"


def _elevenlabs_headers():
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key or key == "your_elevenlabs_key_here":
        raise RuntimeError(
            "ELEVENLABS_API_KEY not set. Copy .env.example to .env and fill it in."
        )
    return {"xi-api-key": key}


def _openai_headers():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key or key == "your_openai_key_here":
        raise RuntimeError(
            "OPENAI_API_KEY not set. Add it to .env to use OpenAI TTS backend."
        )
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def list_voices(limit=20):
    """Return up to `limit` ElevenLabs voices as list of dicts."""
    r = requests.get(f"{ELEVENLABS_BASE}/voices", headers=_elevenlabs_headers(), timeout=15)
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


# Curated OpenAI voice catalog. Nur die 3 besten Voices die in DE und EN
# funktionieren. Source: references/research voice-quality-test research.
_OPENAI_VOICES = [
    {
        "voice_id": "nova",
        "name": "Nova",
        "category": "Weiblich, klar - DE und EN, Listicles, High-Energy",
    },
    {
        "voice_id": "fable",
        "name": "Fable",
        "category": "Maennlich, britisch-warm - DE und EN, Storytelling, Tutorials",
    },
    {
        "voice_id": "onyx",
        "name": "Onyx",
        "category": "Maennlich, tief, autoritaer - vor allem EN, News-Style, Trust-Hooks",
    },
]


def list_openai_voices():
    """Return curated OpenAI tts-1-hd voices for the free tier picker."""
    return list(_OPENAI_VOICES)


def clone_voice(audio_bytes, voice_name, file_name="sample.mp3"):
    """Upload an audio sample to ElevenLabs and create an Instant-Voice-Clone.

    Returns the new voice_id. Voice clones live on the API-key holder's
    ElevenLabs account, not per app user; slot count is bounded by the
    ElevenLabs subscription plan (Free has 0, Starter $5/mo has 10).
    """
    url = f"{ELEVENLABS_BASE}/voices/add"
    headers = _elevenlabs_headers().copy()
    # multipart upload, let requests set Content-Type with the boundary
    headers.pop("Content-Type", None)
    files = {
        "name": (None, voice_name),
        "files": (file_name, audio_bytes, "audio/mpeg"),
    }
    r = requests.post(url, headers=headers, files=files, timeout=120)
    r.raise_for_status()
    return r.json().get("voice_id")


def delete_voice(voice_id):
    """Free the ElevenLabs slot occupied by a previously cloned voice.

    Best-effort. Failures are swallowed because a leftover slot only
    wastes one slot until cleaned manually in the dashboard.
    """
    try:
        r = requests.delete(
            f"{ELEVENLABS_BASE}/voices/{voice_id}",
            headers=_elevenlabs_headers(),
            timeout=30,
        )
        return r.status_code == 200
    except requests.RequestException:
        return False


def generate_voiceover(text, voice_id, model_id="eleven_v3"):
    """Generate audio bytes (mp3) from text using ElevenLabs."""
    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"
    headers = {**_elevenlabs_headers(), "Content-Type": "application/json", "Accept": "audio/mpeg"}
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content


def generate_voiceover_with_timestamps(text, voice_id, model_id="eleven_v3"):
    """Generate audio plus character-level timestamps via ElevenLabs.

    Returns tuple (audio_bytes, alignment_dict) where alignment_dict has keys:
      - characters: list of single-character strings
      - character_start_times_seconds: list of floats
      - character_end_times_seconds: list of floats
    """
    import base64
    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}/with-timestamps"
    headers = {**_elevenlabs_headers(), "Content-Type": "application/json"}
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


def _generate_openai_tts(text, voice_id, model="tts-1-hd", instructions=None):
    """Generate mp3 bytes via OpenAI TTS.

    voice_id options for tts-1 / tts-1-hd: alloy, echo, fable, onyx, nova, shimmer
    voice_id options for gpt-4o-mini-tts: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer
    `instructions` only honored by gpt-4o-mini-tts (e.g. "speak excitedly with varied tone").
    """
    url = f"{OPENAI_BASE}/audio/speech"
    payload = {
        "model": model,
        "voice": voice_id,
        "input": text,
        "response_format": "mp3",
    }
    if instructions and model == "gpt-4o-mini-tts":
        payload["instructions"] = instructions
    r = requests.post(url, headers=_openai_headers(), json=payload, timeout=60)
    r.raise_for_status()
    return r.content


def generate(text, backend, voice_id, **kwargs):
    """Backend-agnostic TTS for the voice-quality test runner.

    backend: "elevenlabs" | "openai_tts1hd" | "openai_4omini"
    voice_id: ElevenLabs voice_id OR OpenAI voice name (alloy, onyx, nova, ...)
    kwargs:
      - instructions: style prompt for openai_4omini only
      - model_id: ElevenLabs model override

    Returns mp3 bytes.
    """
    if backend == "elevenlabs":
        return generate_voiceover(text, voice_id, model_id=kwargs.get("model_id", "eleven_v3"))
    if backend == "openai_tts1hd":
        return _generate_openai_tts(text, voice_id, model="tts-1-hd")
    if backend == "openai_4omini":
        return _generate_openai_4omini_tts(
            text, voice_id,
            instructions=kwargs.get("instructions"),
        )
    raise ValueError(f"Unknown backend: {backend}")


def _generate_openai_4omini_tts(text, voice_id, instructions=None):
    return _generate_openai_tts(text, voice_id, model="gpt-4o-mini-tts", instructions=instructions)
