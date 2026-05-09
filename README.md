# VoiceClip

TikTok-ready AI Voiceover Generator. Type text, get a 1080x1920 portrait video with synced captions and stock footage in under a minute.

Built with Python, Streamlit, ElevenLabs, Pexels, and FFmpeg. Solo project by [closelyst](https://github.com/ZipZap1).

## Features

- AI voiceover via ElevenLabs (20+ voices, multilingual)
- Auto-matched stock video from Pexels
- Word-synced captions (max 3 words per phrase, ~1.6s each)
- Watermark on free exports, removable via license key
- One-click download as TikTok-ready mp4

## Run locally

Requires Python 3.10+ and FFmpeg on PATH.

```bash
git clone https://github.com/ZipZap1/closelyst.git
cd voiceclip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in ELEVENLABS_API_KEY and PEXELS_API_KEY in .env
streamlit run app.py
```

## Deployment

This repo is set up for Streamlit Community Cloud:

1. `packages.txt` installs FFmpeg on the deploy VM
2. `.env` values are set as Streamlit secrets in the Cloud UI
3. Push to `main` triggers redeploy

## Tech stack

- **Frontend:** Streamlit
- **Voiceover:** ElevenLabs API (`with-timestamps` endpoint)
- **Stock video:** Pexels API
- **Caption rendering:** Pillow (PNG overlays)
- **Video composition:** FFmpeg (overlay filter)
- **Payments:** Lemon Squeezy as merchant of record

## License

All rights reserved. This is a closed-source MVP for closelyst.

## Status

MVP. Pre-launch as of May 2026.
