"""Phase 1 voice-quality test runner. See voice-quality-test.md.

Generates audio files for all combinations of (script, language, backend, voice)
and writes them to test_outputs/voice-quality-test/.

Usage:
  python run_voice_test.py              # generate everything
  python run_voice_test.py --script A   # only script A
  python run_voice_test.py --skip-elevenlabs  # OpenAI only (saves ElevenLabs char quota)
"""
import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import voice

OUT_DIR = Path(__file__).parent / "test_outputs" / "voice-quality-test"

SCRIPTS = {
    "A": {
        "label": "educational",
        "de": (
            "Du dachtest, gute KI-Stimmen kosten zwanzig Euro im Monat? Falsch. "
            "Ich zeige dir drei kostenlose Tools, die genauso gut klingen. "
            "Tool Nummer eins ist OpenAI's Text-to-Speech. Klingt natuerlich, ist aber stimmlich limitiert. "
            "Tool zwei: ElevenLabs Free-Tier. Zehntausend Zeichen pro Monat reichen fuer etwa zehn TikToks. "
            "Tool drei kommt gleich."
        ),
        "en": (
            "You thought good AI voices cost twenty bucks a month? Wrong. "
            "I'll show you three free tools that sound just as good. "
            "Tool number one is OpenAI Text-to-Speech. It sounds natural but vocally limited. "
            "Tool two: ElevenLabs free tier. Ten thousand characters per month is enough for about ten TikToks. "
            "Tool three is coming up."
        ),
    },
    "B": {
        "label": "storytelling",
        "de": (
            "Vor einer Woche hatte ich null Downloads in meiner App. "
            "Ich habe alles geloescht und neu angefangen. "
            "Heute zeige ich dir, was ich gelernt habe. "
            "Erstens: niemand will deine App. Zweitens: jeder will dein Tool. "
            "Der Unterschied? Apps sind ein Versprechen. Tools sind sofortiger Nutzen. "
            "Hier ist mein neuer Plan."
        ),
        "en": (
            "One week ago I had zero downloads on my app. I deleted everything and started over. "
            "Today I'll show you what I learned. "
            "First: nobody wants your app. Second: everyone wants your tool. "
            "The difference? Apps are a promise. Tools are instant value. "
            "Here's my new plan."
        ),
    },
    "C": {
        "label": "listicle",
        "de": (
            "Drei KI-Tools, die kein Mensch kennt, aber jeder Creator nutzen sollte. "
            "Tool eins macht aus deinem Text in zehn Sekunden ein TikTok. "
            "Tool zwei findet Stockvideos die zu deinen Worten passen. "
            "Tool drei erzeugt Untertitel, die syncen. "
            "Bonus: alle drei sind kostenlos. Speichere das Video."
        ),
        "en": (
            "Three AI tools nobody knows about but every creator should use. "
            "Tool one turns your text into a TikTok in ten seconds. "
            "Tool two finds stock videos that match your words. "
            "Tool three generates captions that actually sync. "
            "Bonus: all three are free. Save this video."
        ),
    },
}

VARIANTS = [
    # ElevenLabs baseline (current default backend)
    {
        "key": "elevenlabs_adam",
        "backend": "elevenlabs",
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "label": "ElevenLabs Adam (m, warm)",
    },
    {
        "key": "elevenlabs_bella",
        "backend": "elevenlabs",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "label": "ElevenLabs Bella (f, expressive)",
    },
    # OpenAI tts-1-hd: 4 voices spanning the personality range
    {
        "key": "openai_tts1hd_onyx",
        "backend": "openai_tts1hd",
        "voice_id": "onyx",
        "label": "OpenAI tts-1-hd Onyx (m, deep, authoritative)",
    },
    {
        "key": "openai_tts1hd_echo",
        "backend": "openai_tts1hd",
        "voice_id": "echo",
        "label": "OpenAI tts-1-hd Echo (m, calm, neutral)",
    },
    {
        "key": "openai_tts1hd_nova",
        "backend": "openai_tts1hd",
        "voice_id": "nova",
        "label": "OpenAI tts-1-hd Nova (f, clear, friendly)",
    },
    {
        "key": "openai_tts1hd_shimmer",
        "backend": "openai_tts1hd",
        "voice_id": "shimmer",
        "label": "OpenAI tts-1-hd Shimmer (f, warm, soft)",
    },
    # OpenAI gpt-4o-mini-tts: same model with different style prompts
    {
        "key": "openai_4omini_alloy_excited",
        "backend": "openai_4omini",
        "voice_id": "alloy",
        "label": "OpenAI 4o-mini Alloy (styled: excited)",
        "kwargs": {"instructions": "Speak with varied tone, slight excitement, natural pauses, conversational energy."},
    },
    {
        "key": "openai_4omini_ballad_german",
        "backend": "openai_4omini",
        "voice_id": "ballad",
        "label": "OpenAI 4o-mini Ballad (styled: native German accent)",
        "kwargs": {"instructions": "Speak in German with a native German accent, no English intonation. Conversational, slightly fast-paced, like a German TikTok creator."},
    },
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--script", choices=["A", "B", "C"], help="Only run this script")
    p.add_argument("--lang", choices=["de", "en"], help="Only run this language")
    p.add_argument("--skip-elevenlabs", action="store_true", help="Skip ElevenLabs variants (saves char quota)")
    p.add_argument("--skip-openai", action="store_true", help="Skip OpenAI variants")
    return p.parse_args()


def main():
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    scripts = {args.script: SCRIPTS[args.script]} if args.script else SCRIPTS
    langs = [args.lang] if args.lang else ["de", "en"]
    variants = [
        v for v in VARIANTS
        if not (args.skip_elevenlabs and v["backend"] == "elevenlabs")
        and not (args.skip_openai and v["backend"].startswith("openai"))
    ]

    total = len(scripts) * len(langs) * len(variants)
    done = 0
    failed = []

    print(f"Generating {total} audio files into {OUT_DIR}")
    print("---")

    for script_id, script in scripts.items():
        for lang in langs:
            text = script[lang]
            for v in variants:
                done += 1
                fname = f"{script_id}_{script['label']}_{lang}_{v['key']}.mp3"
                fpath = OUT_DIR / fname
                if fpath.exists():
                    print(f"[{done}/{total}] SKIP (exists): {fname}")
                    continue
                try:
                    print(f"[{done}/{total}] {v['label']} | {script_id}/{lang} ...")
                    audio = voice.generate(
                        text, v["backend"], v["voice_id"], **v.get("kwargs", {})
                    )
                    fpath.write_bytes(audio)
                    print(f"    -> {fpath.name} ({len(audio)//1024} KB)")
                    time.sleep(0.5)
                except Exception as exc:
                    print(f"    FAIL: {exc}", file=sys.stderr)
                    failed.append((fname, str(exc)))

    print("---")
    print(f"Done. {done - len(failed)} ok, {len(failed)} failed.")
    if failed:
        print("Failed files:")
        for fname, err in failed:
            print(f"  {fname}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
