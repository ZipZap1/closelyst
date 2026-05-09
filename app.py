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
    st.subheader("Pro / Watermark entfernen")
    license_key_input = st.text_input(
        "License Key",
        type="password",
        help="Hast du einen Key gekauft? Hier einfügen, um diese Session ohne Watermark zu exportieren.",
    )
    is_pro = False
    is_one_shot_key = False
    pro_remaining = None
    if license_key_input:
        with st.spinner("License prüfen..."):
            result = cached_validate(license_key_input)
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
                        st.error(f"Pro-Limit ({limit}) erreicht. Reset beim nächsten Bankabzug am {renews_at_de}.")
                    else:
                        st.error(f"Pro-Limit ({limit}) erreicht. Reset beim nächsten Billing.")
                else:
                    is_pro = True
                    is_one_shot_key = (limit == 1)
                    if is_one_shot_key:
                        st.success("Pro aktiv. 1 Video ohne Watermark verfügbar.")
                    elif limit is not None:
                        pro_remaining = limit - usage
                        msg = f"Pro aktiv. {pro_remaining} von {limit} Generations diesen Zyklus übrig."
                        if renews_at_de:
                            msg += f" Reset am {renews_at_de}."
                        if pro_remaining <= 10:
                            st.warning(msg)
                        else:
                            st.success(msg)
                    else:
                        st.success("Pro aktiv. Unlimited Generations.")
            else:
                st.error(f"Ungültig: {result.get('reason', 'unbekannt')}")

    st.divider()

    @st.cache_data(ttl=3600, show_spinner=False)
    def _cached_buy_url(product_id):
        return license_mod.get_buy_url(product_id)

    remove_url = _cached_buy_url(
        os.environ.get("LEMONSQUEEZY_PRODUCT_REMOVE_WATERMARK", "")
    )
    pro_url = _cached_buy_url(
        os.environ.get("LEMONSQUEEZY_PRODUCT_PRO_MONTHLY", "")
    )
    if remove_url:
        st.link_button("2,99 EUR: Watermark entfernen", remove_url)
    if pro_url:
        st.link_button("8,99 EUR/Mo: Pro werden", pro_url)
    if not remove_url and not pro_url:
        st.caption("Lemon-Squeezy-Produkt-IDs in .env eintragen, dann erscheinen die Checkout-Buttons.")

    # Generation history (in-session, max 5)
    _history = st.session_state.get("history", [])
    if _history:
        st.divider()
        st.subheader("Letzte Generations")
        for i, item in enumerate(_history):
            kind_emoji = "Video" if item["kind"] == "video" else "Bild"
            st.caption(f"{item['ts']} - {kind_emoji} - {item['label']}")
            st.download_button(
                "Erneut herunterladen",
                item["bytes"],
                file_name=item["filename"],
                mime=item["mime"],
                key=f"hist_dl_{i}",
            )


# ----- Onboarding: how it works -----
with st.expander("Wie funktioniert das?", expanded=False):
    st.markdown(
        """
1. **Voiceover-Text eintippen** den die AI vorlesen soll
2. **Stimme wählen** aus dem Dropdown (oder mit Pro deine eigene klonen)
3. **Hintergrund wählen**: Stock-Video automatisch, eigenes Material, AI-Bild oder Lip-Sync (Pro)
4. **Video generieren** klicken, fertig in 30-90 Sekunden

Tab **Bild verbessern** ist ein eigener Pro-Tool: Bild rein, AI macht's schärfer und größer.
        """
    )


tab_video, tab_enhance = st.tabs(["Video erstellen", "Bild verbessern (Pro)"])

# ============================================================
# Tab 1: Video erstellen
# ============================================================
with tab_video:
    text = st.text_area(
        "Was soll der Voiceover sagen?",
        height=130,
        placeholder="Z.B.: Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst.",
        key="voiceover_text",
    )
    if st.button(
        "Beispiel laden",
        help="Füllt das Textfeld mit einem Test-Beispiel.",
        key="example_btn",
    ):
        st.session_state["voiceover_text"] = (
            "Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst."
        )
        st.rerun()

    # Pro-only: clone your own voice from an audio sample
    with st.expander("Pro: Eigene Stimme klonen (Voice Cloning)"):
        if not is_pro:
            st.caption("Pro-only Feature. Trag oben einen Pro-Key ein um deine Stimme zu klonen.")
        else:
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

    voices_data = cached_voices()
    selected_voice_id = None
    if isinstance(voices_data, dict) and "_error" in voices_data:
        st.warning(f"Voices nicht geladen: {voices_data['_error']}")
    elif voices_data:
        voice_options = {f"{v['name']} ({v['category']})": v["voice_id"] for v in voices_data}
        custom_id = st.session_state.get("custom_voice_id")
        custom_name = st.session_state.get("custom_voice_name")
        if custom_id and custom_name:
            custom_label = f"[Eigene] {custom_name}"
            voice_options = {custom_label: custom_id, **voice_options}
        label = st.selectbox("Stimme", list(voice_options.keys()), key="voice_select")
        selected_voice_id = voice_options[label]
    else:
        st.info("Keine Stimmen verfügbar.")

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
            "Prompt (optional, leer = nutzt deinen Voiceover-Text als Prompt)",
            placeholder="Z.B.: Solo-Founder programmiert nachts, Neon-Stadt im Hintergrund",
            key="ai_prompt_input",
        )
        st.caption("Tipp: englische Prompts liefern oft schärfere Ergebnisse, weil das Modell auf englischen Beschreibungen trainiert ist.")
        if not is_pro:
            st.warning("Pro-only. Trag oben einen Pro-Key ein oder kauf einen.")
    elif footage_mode == FOOTAGE_LIPSYNC:
        uploaded_media = st.file_uploader(
            "Portrait-Video (.mp4 .mov, 5-30 Sek, Gesicht klar sichtbar, 9:16 bevorzugt)",
            type=["mp4", "mov", "m4v"],
            accept_multiple_files=False,
            key="lipsync_uploader",
        )
        st.caption("AI synchronisiert die Lippen deiner Person mit dem AI-Voiceover. Dauert 30-90 Sekunden.")
        if not is_pro:
            st.warning("Pro-only. Trag oben einen Pro-Key ein oder kauf einen.")

    # Caption-Style anpassen (TikTok-Branding)
    with st.expander("Caption-Style anpassen"):
        cs_col1, cs_col2 = st.columns(2)
        with cs_col1:
            caption_text_color = st.color_picker(
                "Text-Farbe", value="#ffffff", key="caption_text_color"
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
                value=64,
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
            _missing.append("Pro-Key in Sidebar eintragen")
        if _missing:
            st.caption("Noch nötig: " + ", ".join(_missing))

    # ----- Generate (video flow) -----
    if generate_btn:
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
                strip_watermark = is_pro and not activation_blocked
                if activation_blocked:
                    st.warning("Key bereits verbraucht. Dieses Video bekommt Watermark.")

                progress.progress(10, text="Voiceover generieren mit ElevenLabs (mit Timestamps)...")
                audio_bytes, alignment = voice.generate_voiceover_with_timestamps(
                    text.strip(), selected_voice_id
                )
                audio_path = tmp_path / "voice.mp3"
                audio_path.write_bytes(audio_bytes)

                if footage_mode == FOOTAGE_AI_IMAGE:
                    progress.progress(40, text="AI-Bild wird generiert...")
                    prompt = ai_prompt_override.strip() or text.strip()
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
                )

                progress.progress(100, text="Fertig.")
                video_bytes = output_path.read_bytes()
                st.video(video_bytes, autoplay=True, muted=True)
                st.download_button(
                    "Video herunterladen",
                    video_bytes,
                    file_name="voiceclip.mp4",
                    mime="video/mp4",
                )
                # Save in session history (last 5)
                history = st.session_state.setdefault("history", [])
                from datetime import datetime as _dt
                history.insert(0, {
                    "kind": "video",
                    "label": (text.strip()[:50] + ("..." if len(text.strip()) > 50 else "")) or "Video",
                    "ts": _dt.now().strftime("%H:%M:%S"),
                    "bytes": video_bytes,
                    "filename": "voiceclip.mp4",
                    "mime": "video/mp4",
                })
                st.session_state["history"] = history[:5]
                if strip_watermark:
                    if consumed_one_shot:
                        st.success("Pro-Export ohne Watermark. Dein 1-Video-Key ist nun verbraucht.")
                    else:
                        st.success("Pro-Export ohne Watermark.")
                else:
                    st.info("Watermark ist im Video. Für 2,99 EUR entfernen siehe Sidebar.")
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
        st.warning("Pro-only Feature. Trag oben in der Sidebar einen Pro-Key ein oder kauf einen.")
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
                # Save in session history (last 5)
                history = st.session_state.setdefault("history", [])
                from datetime import datetime as _dt
                history.insert(0, {
                    "kind": "image",
                    "label": enhance_img.name,
                    "ts": _dt.now().strftime("%H:%M:%S"),
                    "bytes": img_bytes,
                    "filename": "enhanced.png",
                    "mime": "image/png",
                })
                st.session_state["history"] = history[:5]
                if consumed_one_shot:
                    st.success("Bild-Enhance fertig. Dein 1-Use-Key ist nun verbraucht.")
                else:
                    st.success("Bild-Enhance fertig.")
            except Exception as exc:
                st.error(f"Fehler: {exc}")


# ----- Footer -----
st.divider()
st.caption("VoiceClip. closelyst. MVP-Version. Stock-Footage von [Pexels](https://www.pexels.com).")
