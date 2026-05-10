"""VoiceClip MVP. TikTok AI Voiceover Generator.

Streamlit single-page app. Text in, 1080x1920 portrait video out.
"""
import os
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

# Load .env from this directory (local dev). On Streamlit Cloud .env is absent,
# secrets come via st.secrets. Mirror st.secrets into os.environ so the rest of
# the modules can keep using os.environ.get(...) uniformly. Always overwrite,
# Streamlit Cloud's own injection may set empty values which would block us.
load_dotenv(Path(__file__).parent / ".env")
try:
    for _key in st.secrets:
        _value = st.secrets[_key]
        if _value is not None:
            _value_str = str(_value)
            if _value_str.strip():
                os.environ[_key] = _value_str
except Exception:
    pass

import voice
import stock
import compose
import license as license_mod
import ai_image
import rate_limit

_ASSETS = Path(__file__).parent / "assets"
st.set_page_config(
    page_title="VoiceClip",
    page_icon=str(_ASSETS / "icon.png"),
    layout="centered",
)

st.image(str(_ASSETS / "logo.svg"), width=260)
st.caption(
    "Text rein. TikTok-ready Video raus. AI Voiceover plus Stock-Footage in unter einer Minute."
)


# Module-level cache so it survives across tab switches and reruns
@st.cache_data(ttl=3600, show_spinner=False)
def cached_voices():
    try:
        return voice.list_voices(limit=20)
    except Exception as exc:
        return {"_error": str(exc)}


# License validation hits the LS API on every render which is slow and
# wasteful. Cache the result for 5 minutes per unique key so typing in
# any other field doesn't re-validate. The 5-minute window is short enough
# that auto-reset on a billing renewal still kicks in within a single use
# session.
@st.cache_data(ttl=300, show_spinner=False)
def cached_validate(key):
    return license_mod.validate_license_key(key)


# ----- Sidebar: license / pro -----
with st.sidebar:
    st.subheader("Pro / Wasserzeichen entfernen")
    license_key_input = st.text_input(
        "Lizenz-Schlüssel",
        type="password",
        help="Hast du einen Lizenz-Schlüssel gekauft? Hier einfügen und Einlösen klicken.",
        key="license_key_input",
    )

    # Clear stored validation if the user changes the key
    if st.session_state.get("validated_key") != license_key_input:
        st.session_state.pop("license_validation", None)
        st.session_state.pop("validated_key", None)

    if st.button("Einlösen", disabled=not license_key_input, key="redeem_btn"):
        with st.spinner("Lizenz prüfen..."):
            st.session_state["license_validation"] = cached_validate(license_key_input)
            st.session_state["validated_key"] = license_key_input

    is_pro = False
    is_one_shot_key = False
    pro_remaining = None
    result = st.session_state.get("license_validation")
    if result and license_key_input:
        if result.get("valid"):
            limit = result.get("activation_limit")
            usage = result.get("activation_usage", 0) or 0
            renews_at_iso = result.get("renews_at")
            renews_at_de = ""
            if renews_at_iso:
                try:
                    from datetime import datetime
                    renews_at_de = datetime.fromisoformat(
                        renews_at_iso.replace("Z", "+00:00")
                    ).strftime("%d.%m.%Y")
                except Exception:
                    renews_at_de = renews_at_iso[:10]
            spent = limit is not None and limit > 0 and usage >= limit
            if spent:
                if limit == 1:
                    st.error("Key gültig, aber bereits verbraucht. Kauf einen neuen oder upgrade auf Pro monatlich.")
                elif renews_at_de:
                    st.error(f"Pro-Limit ({limit}) erreicht. Zurücksetzung bei der nächsten Abbuchung am {renews_at_de}.")
                else:
                    st.error(f"Pro-Limit ({limit}) erreicht. Zurücksetzung bei der nächsten Abrechnung.")
            else:
                is_pro = True
                is_one_shot_key = (limit == 1)
                if is_one_shot_key:
                    st.success("Pro aktiv. 1 Video ohne Wasserzeichen verfügbar.")
                elif limit is not None:
                    pro_remaining = limit - usage
                    msg = f"Pro aktiv. {pro_remaining} von {limit} Generierungen diesen Zyklus übrig."
                    if renews_at_de:
                        msg += f" Zurücksetzung am {renews_at_de}."
                    if pro_remaining <= 10:
                        st.warning(msg)
                    else:
                        st.success(msg)
                else:
                    st.success("Pro aktiv. Wasserzeichen wird entfernt.")
        else:
            st.error(f"Ungültig: {result.get('reason', 'unbekannt')}")
    elif license_key_input:
        st.caption("Klick Einlösen um den Key zu prüfen.")

    st.divider()

    remove_url = license_mod.get_buy_url("POLAR_CHECKOUT_URL_REMOVE_WATERMARK")
    pro_url = license_mod.get_buy_url("POLAR_CHECKOUT_URL_PRO_MONTHLY")
    st.caption("Beide Pakete schalten alle Pro-Features frei: ElevenLabs Premium-Voices, word-synced Captions, Voice-Cloning, kein Wasserzeichen.")
    if remove_url:
        st.link_button("2,99 EUR: Einmalig (1 Video)", remove_url)
    if pro_url:
        st.link_button("8,99 EUR/Mo: Unlimitiert", pro_url)
    if not remove_url and not pro_url:
        st.caption("Polar-Checkout-URLs in .env eintragen, dann erscheinen die Checkout-Buttons.")


# ----- Onboarding -----
with st.expander("Wie funktioniert das?", expanded=False):
    st.markdown(
        """
1. Text eintippen
2. Stimme wählen (Pro: eigene klonen)
3. Hintergrund wählen
4. Generieren

Tab **Bild verbessern** ist ein Pro-Tool: Bild rein, AI macht's schärfer.
        """
    )

# Optional demo-video and ProductHunt embed. Both are read from env so
# they show up only when set; nothing leaks before launch.
_demo_url = os.environ.get("DEMO_VIDEO_URL", "").strip()
_ph_url = os.environ.get("PRODUCTHUNT_URL", "").strip()
if _demo_url or _ph_url:
    cols = st.columns([3, 1])
    with cols[0]:
        if _demo_url:
            with st.expander("Demo: VoiceClip in Aktion (1 Min)", expanded=False):
                st.video(_demo_url)
    with cols[1]:
        if _ph_url:
            st.link_button("Auf ProductHunt", _ph_url, use_container_width=True)


tab_video, tab_enhance = st.tabs(["Video erstellen", "Bild verbessern (Pro)"])

# ============================================================
# Tab 1: Video erstellen
# ============================================================
with tab_video:
    def _load_example():
        # on_click callback runs before the next rerun, which is the
        # only safe place to mutate a widget's session_state key after
        # the widget has been instantiated.
        st.session_state["voiceover_text"] = (
            "Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst."
        )

    text = st.text_area(
        "Was soll der Voiceover sagen?",
        height=130,
        placeholder="Z.B.: Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst.",
        key="voiceover_text",
    )
    st.button(
        "Beispiel laden",
        help="Füllt das Textfeld mit einem Test-Beispiel.",
        key="example_btn",
        on_click=_load_example,
    )

    # Voice-Backend-Wahl: Free-User bekommen kuratierte OpenAI-Voices,
    # Pro-User koennen zwischen ElevenLabs (Premium, synced Captions, Voice-Cloning)
    # und OpenAI (konsistenter, oft besser fuer EN) switchen.
    if is_pro:
        backend_label = st.radio(
            "Voice-Backend",
            options=["ElevenLabs (Premium, synced Captions, Voice-Cloning)", "OpenAI (Standard, schneller)"],
            index=0,
            horizontal=True,
            key="voice_backend_radio",
            help="ElevenLabs ist expressiver, hat synced Captions und Voice-Cloning. OpenAI ist konsistenter und fuer englischen Content oft genauso gut.",
        )
        voice_backend = "elevenlabs" if backend_label.startswith("ElevenLabs") else "openai_tts1hd"
    else:
        voice_backend = "openai_tts1hd"
        st.caption("Free-Modus: 3 kuratierte OpenAI-Voices. Bezahltes Paket (ab 2,99 EUR) schaltet ElevenLabs Premium-Voices, word-synced Captions und Voice-Cloning frei.")

    # Voice cloning is a Pro-only power feature, AND only meaningful when the
    # ElevenLabs backend is selected (clones live in the ElevenLabs account).
    if is_pro and voice_backend == "elevenlabs":
        with st.expander("Pro-Einstellungen: Eigene Stimme klonen"):
            st.caption(
                "Audio-Sample (30+ Sek, klar gesprochen) hochladen. "
                "ElevenLabs klont die Stimme, danach erscheint sie ganz oben im Dropdown."
            )
            clone_col1, clone_col2 = st.columns([2, 1])
            with clone_col1:
                voice_sample = st.file_uploader(
                    "Audio-Sample (.mp3 .wav, 30+ Sek)",
                    type=["mp3", "wav", "m4a"],
                    key="voice_sample_uploader",
                    accept_multiple_files=False,
                )
            with clone_col2:
                clone_name = st.text_input("Name", value="Meine Stimme", key="voice_clone_name")
            if st.button("Stimme klonen", disabled=not voice_sample, key="clone_btn"):
                with st.spinner("Stimme wird geklont (10-30s)..."):
                    try:
                        prev_id = st.session_state.get("custom_voice_id")
                        if prev_id:
                            voice.delete_voice(prev_id)
                        new_id = voice.clone_voice(
                            voice_sample.getvalue(),
                            clone_name.strip() or "Meine Stimme",
                            file_name=voice_sample.name,
                        )
                        st.session_state["custom_voice_id"] = new_id
                        st.session_state["custom_voice_name"] = clone_name.strip() or "Meine Stimme"
                        cached_voices.clear()
                        st.success(f"Stimme '{clone_name}' geklont. Wähl sie jetzt im Dropdown.")
                    except Exception as exc:
                        msg = str(exc)
                        resp = getattr(exc, "response", None)
                        if resp is not None:
                            try:
                                j = resp.json()
                                msg = j.get("detail", {}).get("message") or j.get("detail") or msg
                            except Exception:
                                pass
                        st.error(f"Klonen fehlgeschlagen: {msg}")

    # Voice picker: ElevenLabs (full list + cloned voice if any) vs OpenAI (curated 3)
    selected_voice_id = None
    if voice_backend == "elevenlabs":
        voices_data = cached_voices()
        if isinstance(voices_data, dict) and "_error" in voices_data:
            st.warning(f"Voices nicht geladen: {voices_data['_error']}")
        elif voices_data:
            voice_options = {v["name"]: v["voice_id"] for v in voices_data}
            custom_id = st.session_state.get("custom_voice_id")
            custom_name = st.session_state.get("custom_voice_name")
            if custom_id and custom_name:
                custom_label = f"[Eigene] {custom_name}"
                voice_options = {custom_label: custom_id, **voice_options}
            label = st.selectbox("Stimme", list(voice_options.keys()), key="voice_select")
            selected_voice_id = voice_options[label]
        else:
            st.info("Keine Stimmen verfügbar.")
    else:
        openai_voices = voice.list_openai_voices()
        voice_options = {f"{v['name']} ({v['category']})": v["voice_id"] for v in openai_voices}
        label = st.selectbox("Stimme", list(voice_options.keys()), key="voice_select_openai")
        selected_voice_id = voice_options[label]

    # Footage source. Short labels with captions so the choice fits in one
    # glance instead of forcing users to read four long sentences.
    FOOTAGE_STOCK = "Stock"
    FOOTAGE_UPLOAD = "Upload"
    FOOTAGE_AI_IMAGE = "AI-Bild"
    FOOTAGE_LIPSYNC = "Lip-Sync"
    footage_mode = st.radio(
        "Hintergrund",
        options=[FOOTAGE_STOCK, FOOTAGE_UPLOAD, FOOTAGE_AI_IMAGE, FOOTAGE_LIPSYNC],
        captions=[
            "Pexels-Match aus deinem Text (gratis)",
            "Eigenes Video oder Bild (gratis)",
            "AI generiert Hintergrund aus Text (Pro)",
            "Lippen deiner Person zum Voiceover (Pro)",
        ],
        horizontal=True,
        key="footage_mode_radio",
    )
    uploaded_media = None
    ai_prompt_override = ""
    if footage_mode == FOOTAGE_UPLOAD:
        uploaded_media = st.file_uploader(
            "Datei (Video: .mp4 .mov / Bild: .jpg .png .webp, max 50 MB, wird auf 9:16 gecroppt)",
            type=["mp4", "mov", "m4v", "jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            key="upload_media_uploader",
        )
        if uploaded_media is not None and uploaded_media.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            st.caption("Bild erkannt, bekommt einen langsamen Zoom (Ken-Burns).")
    elif footage_mode == FOOTAGE_AI_IMAGE:
        ai_prompt_override = st.text_input(
            "Prompt (optional, leer = AI generiert eine passende Szene aus deinem Voiceover-Text)",
            placeholder="Z.B.: Solo-Founder programmiert nachts, Neon-Stadt im Hintergrund",
            key="ai_prompt_input",
        )
        st.caption("Leer lassen für automatische Szenen-Erkennung. Eigenen englischen Prompt für maximale Kontrolle eintragen.")
        if not is_pro:
            st.warning("Nur für Pro. Trag oben einen Pro-Schlüssel ein oder kauf einen.")
    elif footage_mode == FOOTAGE_LIPSYNC:
        uploaded_media = st.file_uploader(
            "Portrait-Video (.mp4 .mov, 5-30 Sek, Gesicht klar sichtbar, 9:16 bevorzugt)",
            type=["mp4", "mov", "m4v"],
            accept_multiple_files=False,
            key="lipsync_uploader",
        )
        st.caption("AI synchronisiert die Lippen deiner Person mit dem AI-Voiceover. Dauert 30-90 Sekunden. Lip-Sync ist rechenintensiv und zählt 7x ins Pro-Limit (~28 Lip-Syncs pro Zyklus möglich).")
        if not is_pro:
            st.warning("Nur für Pro. Trag oben einen Pro-Schlüssel ein oder kauf einen.")

    # Caption-Style anpassen. Defaults sind TikTok-typisch: gelber Text,
    # größerer Font, schwarze halbtransparente Box am unteren Rand.
    with st.expander("Caption-Style anpassen (TikTok-Defaults)"):
        cs_col1, cs_col2 = st.columns(2)
        with cs_col1:
            caption_text_color = st.color_picker(
                "Text-Farbe", value="#fbbf24", key="caption_text_color"
            )
            caption_position = st.selectbox(
                "Position",
                options=["bottom", "center", "top"],
                index=0,
                key="caption_position",
            )
        with cs_col2:
            caption_bg_color = st.color_picker(
                "Box-Farbe (Hintergrund hinter Text)", value="#000000", key="caption_bg_color"
            )
            caption_font_size = st.select_slider(
                "Font-Größe",
                options=[48, 56, 64, 72, 80, 96],
                value=80,
                key="caption_font_size",
            )
        caption_bg_alpha = st.slider(
            "Box-Deckkraft", min_value=0, max_value=255, value=200, key="caption_bg_alpha",
            help="0 = keine Box (nur Text), 255 = volle Box.",
        )

    # Pre-flight: enable button only when all prereqs are met
    needs_upload = footage_mode in (FOOTAGE_UPLOAD, FOOTAGE_LIPSYNC)
    needs_pro = footage_mode in (FOOTAGE_AI_IMAGE, FOOTAGE_LIPSYNC)
    ready_to_generate = bool(
        text.strip()
        and selected_voice_id
        and (not needs_upload or uploaded_media is not None)
        and (not needs_pro or is_pro)
    )

    _button_label = {
        FOOTAGE_STOCK: "Video generieren",
        FOOTAGE_UPLOAD: "Video aus Upload generieren",
        FOOTAGE_AI_IMAGE: "AI-Bild + Video generieren",
        FOOTAGE_LIPSYNC: "Lip-Sync + Video generieren",
    }.get(footage_mode, "Video generieren")
    generate_btn = st.button(
        _button_label,
        type="primary",
        disabled=not ready_to_generate,
        key="generate_video_btn",
    )
    if not ready_to_generate:
        _missing = []
        if not text.strip():
            _missing.append("Voiceover-Text eintippen")
        if not selected_voice_id:
            _missing.append("Stimme wählen")
        if needs_upload and uploaded_media is None:
            _missing.append("Datei hochladen")
        if needs_pro and not is_pro:
            _missing.append("Pro-Schlüssel in Seitenleiste eintragen")
        if _missing:
            st.caption("Noch nötig: " + ", ".join(_missing))

    if not is_pro:
        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_free_quota():
            return rate_limit.get_free_quota()
        _used, _rem, _lim = _cached_free_quota()
        if _rem == 0:
            st.caption(f"Tageslimit erreicht ({_used}/{_lim} kostenlose Videos heute). Komm morgen wieder oder kauf einen Pro-Schlüssel.")
        elif _rem <= _lim:
            st.caption(f"Free-Tier: {_used}/{_lim} kostenlose Videos heute verbraucht. {_rem} übrig.")

    # ----- Generate (video flow) -----
    if generate_btn:
        # Free-tier daily limit: only relevant for non-Pro users.
        if not is_pro:
            used, remaining, free_limit = rate_limit.get_free_quota()
            if remaining <= 0:
                st.error(
                    f"Tageslimit von {free_limit} kostenlosen Videos erreicht. "
                    "Komm morgen wieder oder kauf einen Pro-Schlüssel für unbegrenzte Generierungen."
                )
                st.stop()

        consumed_one_shot = False
        activation_blocked = False
        # Lip-Sync calls a cost-heavy Replicate model, so it counts more
        # against the Pro cap than the cheap modes.
        usage_weight = 7 if footage_mode == FOOTAGE_LIPSYNC else 1
        if is_pro:
            instance = f"voiceclip-{uuid.uuid4().hex[:8]}"
            activation = license_mod.activate_license_key(
                license_key_input, instance, weight=usage_weight
            )
            if activation.get("activated"):
                consumed_one_shot = is_one_shot_key
            else:
                activation_blocked = True

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            progress = st.progress(0, text="Starte...")
            try:
                strip_watermark = is_pro and not activation_blocked
                if activation_blocked:
                    st.warning("Schlüssel bereits verbraucht. Dieses Video bekommt Wasserzeichen.")

                if voice_backend == "elevenlabs":
                    progress.progress(10, text="Voiceover generieren mit ElevenLabs (mit synced Captions)...")
                    audio_bytes, alignment = voice.generate_voiceover_with_timestamps(
                        text.strip(), selected_voice_id
                    )
                else:
                    progress.progress(10, text="Voiceover generieren mit OpenAI...")
                    audio_bytes = voice.generate(text.strip(), voice_backend, selected_voice_id)
                    alignment = {}
                audio_path = tmp_path / "voice.mp3"
                audio_path.write_bytes(audio_bytes)

                if footage_mode == FOOTAGE_AI_IMAGE:
                    if ai_prompt_override.strip():
                        prompt = ai_prompt_override.strip()
                    else:
                        progress.progress(30, text="Visuelle Szene aus Voiceover-Text ableiten...")
                        prompt = ai_image.text_to_visual_prompt(text.strip())
                    progress.progress(40, text="AI-Bild wird generiert...")
                    video_path = tmp_path / "ai.png"
                    ai_image.generate_image(prompt, video_path, aspect_ratio="9:16")
                elif footage_mode == FOOTAGE_LIPSYNC:
                    progress.progress(35, text="Portrait-Video wird hochgeladen...")
                    ext = Path(uploaded_media.name).suffix.lower() or ".mp4"
                    raw_path = tmp_path / f"raw{ext}"
                    raw_path.write_bytes(uploaded_media.getvalue())
                    progress.progress(50, text="Lippen werden synchronisiert, kann 30-90s dauern...")
                    video_path = tmp_path / "lipsynced.mp4"
                    ai_image.lipsync_video(raw_path, audio_path, video_path)
                elif uploaded_media is not None:
                    progress.progress(40, text="Hochgeladenes Material wird verarbeitet...")
                    ext = Path(uploaded_media.name).suffix.lower() or ".mp4"
                    video_path = tmp_path / f"upload{ext}"
                    video_path.write_bytes(uploaded_media.getvalue())
                else:
                    progress.progress(40, text="Stock-Footage von Pexels suchen...")
                    video_path = tmp_path / "stock.mp4"
                    keywords = stock.extract_keywords(text)
                    query = " ".join(keywords) if keywords else "abstract background"
                    video_url = stock.pick_video_url(query)
                    if not video_url:
                        video_url = stock.pick_video_url("abstract background")
                    if not video_url:
                        st.error("Kein Stock-Video gefunden. Versuch einen anderen Text.")
                        st.stop()
                    stock.download(video_url, video_path)

                progress.progress(70, text="Video komponieren mit FFmpeg (synced captions)...")
                output_path = tmp_path / "out.mp4"
                compose.compose(
                    audio_path=audio_path,
                    video_path=video_path,
                    output_path=output_path,
                    tmp_dir=tmp_path,
                    alignment=alignment,
                    fallback_text=text.strip(),
                    with_watermark=not strip_watermark,
                    caption_style={
                        "text_color": caption_text_color,
                        "bg_color": caption_bg_color,
                        "bg_alpha": caption_bg_alpha,
                        "font_size": caption_font_size,
                        "position": caption_position,
                    },
                    animate_image=(footage_mode != FOOTAGE_AI_IMAGE),
                )

                progress.progress(100, text="Fertig.")
                if not is_pro:
                    rate_limit.consume_free_quota()
                video_bytes = output_path.read_bytes()
                st.video(video_bytes, autoplay=True, muted=True)
                st.download_button(
                    "Video herunterladen",
                    video_bytes,
                    file_name="voiceclip.mp4",
                    mime="video/mp4",
                )
                if strip_watermark:
                    if consumed_one_shot:
                        st.success("Pro-Export ohne Wasserzeichen. Dein 1-Video-Schlüssel ist nun verbraucht.")
                    else:
                        st.success("Pro-Export ohne Wasserzeichen.")
                else:
                    st.info("Wasserzeichen ist im Video. Für 2,99 EUR entfernen siehe Seitenleiste.")
            except Exception as exc:
                st.error(f"Fehler: {exc}")


# ============================================================
# Tab 2: Bild verbessern (Pro)
# ============================================================
with tab_enhance:
    st.markdown("**AI Bild-Enhancer**")
    st.caption(
        "Lade ein Bild hoch, AI macht es schärfer und auf 2x Auflösung. "
        "Kein Voiceover, kein Video, nur das verbesserte Bild als PNG-Download."
    )
    enhance_img = st.file_uploader(
        "Bild zum Verbessern (.jpg .png .webp, max 10 MB)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        key="enhance_uploader",
    )
    if not is_pro:
        st.warning("Funktion nur für Pro. Trag oben in der Seitenleiste einen Pro-Schlüssel ein oder kauf einen.")
    enhance_btn = st.button(
        "Bild verbessern",
        type="primary",
        disabled=not (enhance_img and is_pro),
        key="enhance_btn",
    )
    if enhance_btn:
        consumed_one_shot = False
        activation_blocked = False
        if is_pro:
            instance = f"voiceclip-{uuid.uuid4().hex[:8]}"
            activation = license_mod.activate_license_key(license_key_input, instance)
            if activation.get("activated"):
                consumed_one_shot = is_one_shot_key
            else:
                activation_blocked = True

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            progress = st.progress(0, text="Starte...")
            try:
                if activation_blocked:
                    st.warning("Key bereits verbraucht. Bild-Enhance trotzdem, aber kein neuer Slot konsumiert.")
                progress.progress(20, text="Bild wird hochgeladen...")
                ext = Path(enhance_img.name).suffix.lower() or ".png"
                raw_path = tmp_path / f"raw{ext}"
                raw_path.write_bytes(enhance_img.getvalue())

                progress.progress(40, text="Bild wird verbessert (10-30s)...")
                enhanced_path = tmp_path / "enhanced.png"
                ai_image.enhance_image(raw_path, enhanced_path, scale=2)

                progress.progress(100, text="Fertig.")
                img_bytes = enhanced_path.read_bytes()
                st.image(img_bytes, caption="Verbessertes Bild (2x Auflösung)", use_column_width=True)
                st.download_button(
                    "Bild herunterladen",
                    img_bytes,
                    file_name="enhanced.png",
                    mime="image/png",
                    key="enhance_download_btn",
                )
                if consumed_one_shot:
                    st.success("Bild-Enhance fertig. Dein 1-Use-Key ist nun verbraucht.")
                else:
                    st.success("Bild-Enhance fertig.")
            except Exception as exc:
                st.error(f"Fehler: {exc}")


# ----- Footer -----
st.divider()
st.markdown(
    """
    <style>
    .footer-links a { text-decoration: none; color: inherit; }
    .footer-links a:hover { text-decoration: underline; }
    </style>
    <div class="footer-links" style="font-size: 0.875em; color: rgba(49, 51, 63, 0.6);">
    VoiceClip. closelyst. MVP-Version.
    Powered by <a href="https://elevenlabs.io" target="_blank">ElevenLabs</a> (Pro-Voiceover, Voice-Cloning),
    <a href="https://openai.com" target="_blank">OpenAI</a> (Free-Voiceover),
    <a href="https://www.pexels.com" target="_blank">Pexels</a> (Stock-Footage),
    <a href="https://replicate.com" target="_blank">Replicate</a> (Flux Schnell, Clarity Upscaler, LatentSync)
    und <a href="https://polar.sh" target="_blank">Polar</a> (Payments).
    </div>
    <div class="footer-links" style="font-size: 0.875em; color: rgba(49, 51, 63, 0.6); margin-top: 0.5em;">
    <a href="/Impressum" target="_self">Impressum</a> |
    <a href="/Datenschutz" target="_self">Datenschutz</a> |
    <a href="/AGB" target="_self">AGB</a> |
    <a href="/Widerrufsbelehrung" target="_self">Widerrufsbelehrung</a>
    </div>
    """,
    unsafe_allow_html=True,
)
