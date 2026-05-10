"""Streamlit-Helper zum Hoeren und Bewerten der 48 Voice-Test-Files.

Multi-Tester-Mode: Jeder Tester gibt am Anfang seinen Namen ein, Scores
werden pro Name getrennt persistiert. Storage-Backend ist Supabase wenn
SUPABASE_URL und SUPABASE_KEY gesetzt sind, sonst lokales JSON-File.

Usage:
  streamlit run score_voices.py

Deploy:
  Auf Streamlit Cloud, share.streamlit.io. Entry-File: projects/voiceclip/score_voices.py
  Secrets: SUPABASE_URL, SUPABASE_KEY in der Streamlit-UI eintragen.
  Setup-Doku: SUPABASE_SETUP.md
"""
import re
from collections import defaultdict
from pathlib import Path

import streamlit as st

import storage

ROOT = Path(__file__).parent
TEST_DIR = ROOT / "test_outputs" / "voice-quality-test"

VARIANT_LABELS = {
    "elevenlabs_adam": "ElevenLabs Adam",
    "elevenlabs_bella": "ElevenLabs Bella",
    "openai_tts1hd_onyx": "OpenAI Onyx",
    "openai_tts1hd_echo": "OpenAI Echo",
    "openai_tts1hd_nova": "OpenAI Nova",
    "openai_tts1hd_shimmer": "OpenAI Shimmer",
    "openai_4omini_alloy_excited": "OpenAI Alloy (excited)",
    "openai_4omini_ballad_german": "OpenAI Ballad (DE-style)",
}

SCRIPT_LABELS = {
    "A": "A: Educational",
    "B": "B: Storytelling",
    "C": "C: Listicle",
}

LANG_LABELS = {"de": "Deutsch", "en": "English"}


def parse_filename(fname: str):
    m = re.match(r"^([ABC])_([a-z]+)_(de|en)_(.+)\.mp3$", fname)
    if not m:
        return None
    script_id, _label, lang, variant = m.groups()
    return {"script": script_id, "lang": lang, "variant": variant, "fname": fname}




def aggregate_per_tester(scores_for_tester, files):
    agg = defaultdict(lambda: {"de": [], "en": []})
    for f in files:
        key = f["fname"]
        if key not in scores_for_tester:
            continue
        s = scores_for_tester[key].get("score")
        if s is None:
            continue
        agg[f["variant"]][f["lang"]].append(s)
    rows = []
    for variant, by_lang in agg.items():
        de = by_lang["de"]
        en = by_lang["en"]
        rows.append({
            "Voice": VARIANT_LABELS.get(variant, variant),
            "DE Avg": round(sum(de) / len(de), 1) if de else None,
            "EN Avg": round(sum(en) / len(en), 1) if en else None,
            "Total Avg": round(sum(de + en) / max(1, len(de + en)), 1) if (de + en) else None,
        })
    rows.sort(key=lambda r: (r["Total Avg"] or 0), reverse=True)
    return rows


def aggregate_across_testers(all_scores, files):
    """Avg across all testers per voice."""
    agg = defaultdict(lambda: {"de": [], "en": []})
    for tester, scores in all_scores.items():
        for f in files:
            s = scores.get(f["fname"], {}).get("score")
            if s is None:
                continue
            agg[f["variant"]][f["lang"]].append(s)
    rows = []
    for variant, by_lang in agg.items():
        de = by_lang["de"]
        en = by_lang["en"]
        rows.append({
            "Voice": VARIANT_LABELS.get(variant, variant),
            "DE Avg": round(sum(de) / len(de), 1) if de else None,
            "DE n": len(de),
            "EN Avg": round(sum(en) / len(en), 1) if en else None,
            "EN n": len(en),
            "Total Avg": round(sum(de + en) / max(1, len(de + en)), 1) if (de + en) else None,
        })
    rows.sort(key=lambda r: (r["Total Avg"] or 0), reverse=True)
    return rows


def main():
    st.set_page_config(page_title="Voice-Score", layout="wide")
    st.title("VoiceClip - Voice-Quality Test")
    st.caption(
        "Hoer dir jedes File an und gib eine Bewertung von 1 (klingt roboterhaft) bis 10 (klingt wie ein echter Mensch)."
        " Scores werden auto-gespeichert."
    )

    if not TEST_DIR.exists():
        st.error(f"Test-Ordner nicht gefunden: {TEST_DIR}")
        st.stop()

    files = []
    for p in sorted(TEST_DIR.glob("*.mp3")):
        if p.name.startswith("_"):
            continue
        parsed = parse_filename(p.name)
        if parsed:
            parsed["path"] = p
            files.append(parsed)

    if not files:
        st.warning("Keine Test-Files gefunden. Erst `python run_voice_test.py` laufen lassen.")
        st.stop()

    # ---- Tester-Identifikation ----
    all_scores = storage.load_all_scores()
    existing_testers = sorted(all_scores.keys())

    with st.sidebar:
        st.caption("Storage: " + ("Supabase (persistent)" if storage.is_supabase() else "Lokales JSON-File"))
        st.subheader("Wer bist du?")
        if existing_testers:
            choice = st.radio(
                "Bestehender Tester oder neu?",
                options=["Bestehend"] + ["Neu"],
                horizontal=True,
            )
            if choice == "Bestehend":
                tester = st.selectbox("Name", options=existing_testers)
            else:
                tester = st.text_input("Dein Name", placeholder="z.B. Mama, Papa, Ibrahim")
        else:
            tester = st.text_input("Dein Name", placeholder="z.B. Mama, Papa, Ibrahim")

        st.divider()
        if all_scores:
            st.caption(f"{len(all_scores)} Tester insgesamt:")
            for t in existing_testers:
                n = sum(1 for v in all_scores[t].values() if v.get("score") is not None)
                st.caption(f"  - {t}: {n} / {len(files)}")

    if not tester or not tester.strip():
        st.info("Bitte links Name eingeben um zu starten.")
        st.stop()

    tester = tester.strip()
    if tester not in all_scores:
        all_scores[tester] = {}
    scores = all_scores[tester]

    scored_count = sum(1 for f in files if scores.get(f["fname"], {}).get("score") is not None)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Files total", len(files))
    col_b.metric(f"{tester}: bewertet", f"{scored_count} / {len(files)}")
    col_c.metric("Ausstehend", len(files) - scored_count)

    if scored_count > 0:
        with st.expander(f"Aggregat fuer {tester}", expanded=False):
            rows = aggregate_per_tester(scores, files)
            st.dataframe(rows, use_container_width=True, hide_index=True)

    if len(all_scores) > 1:
        with st.expander("Aggregat ueber alle Tester", expanded=True):
            rows = aggregate_across_testers(all_scores, files)
            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.divider()

    # ---- Filters ----
    col1, col2 = st.columns(2)
    selected_script = col1.selectbox("Script-Filter", options=["Alle"] + list(SCRIPT_LABELS.values()))
    selected_lang = col2.selectbox("Sprache", options=["Alle", "Deutsch", "English"])
    only_unscored = st.checkbox("Nur unbewertete zeigen", value=False)

    filtered = []
    for f in files:
        if selected_script != "Alle" and SCRIPT_LABELS[f["script"]] != selected_script:
            continue
        if selected_lang != "Alle" and LANG_LABELS[f["lang"]] != selected_lang:
            continue
        if only_unscored and scores.get(f["fname"], {}).get("score") is not None:
            continue
        filtered.append(f)

    st.caption(f"{len(filtered)} Files gefiltert.")

    grouped = defaultdict(list)
    for f in filtered:
        grouped[(f["script"], f["lang"])].append(f)

    for (script_id, lang), group_files in sorted(grouped.items()):
        st.subheader(f"{SCRIPT_LABELS[script_id]} - {LANG_LABELS[lang]}")
        for f in group_files:
            existing = scores.get(f["fname"], {})
            existing_score = existing.get("score")
            existing_note = existing.get("note", "")

            cols = st.columns([3, 4, 1, 3])
            voice_label = VARIANT_LABELS.get(f["variant"], f["variant"])
            cols[0].markdown(f"**{voice_label}**")
            cols[1].audio(str(f["path"]))

            score_options = [None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            try:
                idx = score_options.index(existing_score)
            except ValueError:
                idx = 0
            new_score = cols[2].selectbox(
                "Score",
                options=score_options,
                index=idx,
                key=f"score_{tester}_{f['fname']}",
                format_func=lambda x: "-" if x is None else str(x),
                label_visibility="collapsed",
            )
            new_note = cols[3].text_input(
                "Notiz",
                value=existing_note,
                key=f"note_{tester}_{f['fname']}",
                placeholder="Notiz (optional)",
                label_visibility="collapsed",
            )

            if new_score != existing_score or new_note != existing_note:
                scores[f["fname"]] = {"score": new_score, "note": new_note}
                all_scores[tester] = scores
                storage.upsert_score(tester, f["fname"], new_score, new_note)

    st.divider()

    if scored_count == len(files) and len(files) > 0:
        st.success(f"{tester}: alle Files bewertet. Danke!")

    if st.button("Markdown-Export (alle Tester aggregiert)"):
        rows = aggregate_across_testers(all_scores, files)
        md = "| Voice | DE Avg | DE n | EN Avg | EN n | Total Avg |\n|---|---|---|---|---|---|\n"
        for r in rows:
            md += f"| {r['Voice']} | {r['DE Avg'] or '-'} | {r['DE n']} | {r['EN Avg'] or '-'} | {r['EN n']} | {r['Total Avg'] or '-'} |\n"
        st.code(md, language="markdown")


if __name__ == "__main__":
    main()
