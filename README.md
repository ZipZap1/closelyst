# VoiceClip

**Live:** https://closelyst.com

TikTok-ready AI Voiceover Generator. Type text, get a 1080x1920 portrait video with synced captions and stock footage in under a minute.

Built with Python, Streamlit, ElevenLabs, OpenAI TTS, Pexels, and FFmpeg. Solo project by [closelyst](https://github.com/ZipZap1).

## Features

- AI voiceover: ElevenLabs (Pro, 20+ voices, multilingual) or OpenAI (Free, Nova default)
- Auto-matched stock video from Pexels
- Word-synced captions (Pro) or static captions (Free)
- AI-generated background images (Pro, Replicate)
- Lip-sync video generation (Pro)
- Voice cloning (Pro, via ElevenLabs Instant-Voice-Clone)
- Watermark on free exports, removable via Polar license key
- One-click download as TikTok-ready mp4

## Run locally

Requires Python 3.10+ and FFmpeg on PATH.

```bash
git clone https://github.com/ZipZap1/closelyst.git
cd closelyst
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in API keys in .env (siehe Kommentare im File)
streamlit run Hauptseite.py
```

## Deployment

Self-hosted auf Hostinger VPS mit Docker plus Caddy als Reverse-Proxy plus
Auto-SSL via Let's Encrypt. Domain: closelyst.com.

Setup-Anleitung: siehe [DEPLOY.md](./DEPLOY.md)

Update-Workflow:
```bash
ssh root@VPS-IP
cd ~/closelyst && git pull && docker compose up -d --build
```

## Tech stack

- **Frontend:** Streamlit
- **Voiceover Pro:** ElevenLabs API (`with-timestamps` endpoint for synced captions)
- **Voiceover Free:** OpenAI TTS (tts-1-hd model, Nova voice)
- **Stock video:** Pexels API
- **AI Image:** Replicate (Flux Schnell)
- **Lip-Sync:** Replicate (LatentSync) oder sync.so (lipsync-2)
- **Caption rendering:** Pillow (PNG overlays)
- **Video composition:** FFmpeg (overlay filter, zoompan fuer Ken-Burns)
- **Payments:** Polar als Merchant of Record
- **Rate-Limit Storage:** Supabase Postgres
- **Reverse-Proxy:** Caddy (Auto-SSL via Let's Encrypt)
- **Hosting:** Hostinger VPS

## License

All rights reserved. This is a closed-source MVP for closelyst.

## Status

Live auf https://closelyst.com seit Mai 2026.
