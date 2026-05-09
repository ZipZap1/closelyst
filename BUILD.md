# VoiceClip MVP: Setup und Run

## Voraussetzungen

- Python 3.10 oder neuer
- FFmpeg auf PATH installiert
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg` oder `sudo dnf install ffmpeg`
  - Windows: ffmpeg.org Download, ffmpeg-Ordner zur PATH hinzufuegen

## Lokale Installation

```bash
cd projects/voiceclip
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## API Keys eintragen

```bash
cp .env.example .env
# .env oeffnen und Werte eintragen:
# - ELEVENLABS_API_KEY (Account: elevenlabs.io)
# - PEXELS_API_KEY (Account: pexels.com/api)
# - LEMONSQUEEZY_API_KEY und Produkt-IDs (kannst du leer lassen bis Tag 6)
```

## Lokal starten

```bash
streamlit run app.py
```

Browser oeffnet sich auf http://localhost:8501.

## Erste Tests

1. Kein License Key eingeben, Text "Drei Tipps fuer Solo-Founder" eintippen, Voice waehlen, Generate
2. Watermark sollte am Ende des Videos erscheinen
3. Lemon-Squeezy-Test-Key eintragen (siehe Lemon-Squeezy-Dashboard "Test Mode"), Watermark verschwindet

## Deployment auf Streamlit Cloud

1. Code ins Git pushen (Repo: closelyst/voiceclip oder eigene Repo). Falls VoiceClip allein im Subordner unter closelyst-Repo liegt, separates Repo erstellen oder Streamlit Cloud-Pfad-Setting nutzen
2. share.streamlit.io oeffnen, "New app", Repo auswaehlen, `app.py` als entry
3. Secrets eintragen (gleicher Inhalt wie .env, im UI unter "Advanced settings")
4. Deploy

Streamlit Cloud installiert FFmpeg nicht automatisch. Workaround: `packages.txt` im Repo-Root anlegen mit:

```
ffmpeg
```

Streamlit Cloud installiert dann ffmpeg auf der VM beim Build.

## Bekannte Limits / TODOs (Post-MVP)

- Captions sind aktuell static text, nicht wort-synchron. Iteration nach 100 Nutzern via ElevenLabs-Timestamps oder Whisper-API
- Stock-Video-Matching ist naive Keyword-Extraktion. Spaeter: LLM-basierte Query-Generierung
- Keine User-Accounts. License Keys gelten nur fuer die Session. Spaeter: Account plus persistierte Pro-State
- Logging und Analytics fehlen. Spaeter: simple `requests.post` zu Plausible oder Umami fuer Generation-Counts
- Watermark ist Text-Overlay last 1.5s. Spaeter: dediziertes Outro-Frame oder kleines Logo bottom-right durchgehend

## Struktur

```
projects/voiceclip/
├── README.md             # Strategie / Plan / Roadmap
├── BUILD.md              # Diese Datei (Setup, Run, Deploy)
├── app.py                # Streamlit UI, Glue-Code
├── voice.py              # ElevenLabs Wrapper
├── stock.py              # Pexels Wrapper plus Keyword-Extraktion
├── compose.py            # FFmpeg Compose plus Watermark
├── license.py            # Lemon Squeezy License-Validation
├── requirements.txt      # Python deps
└── .env.example          # Vorlage fuer .env (git-ignored)
```
