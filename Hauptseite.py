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
    page_title="VoiceClip - TikToks ohne Gesicht in 60 Sekunden | closelyst.com",
    page_icon=str(_ASSETS / "icon.png"),
    layout="centered",
    initial_sidebar_state="expanded",
)

# SEO-Metadata via JavaScript in <head> injizieren. Streamlit's
# set_page_config setzt nur title/icon, fuer og:image und Description
# brauchen wir Custom-Tags.
st.markdown(
    """
    <script>
    (function() {
      const head = document.head;
      const meta = (k, v, attr) => {
        attr = attr || 'name';
        let existing = head.querySelector(`meta[${attr}="${k}"]`);
        if (existing) { existing.setAttribute('content', v); return; }
        const m = document.createElement('meta');
        m.setAttribute(attr, k);
        m.setAttribute('content', v);
        head.appendChild(m);
      };
      const desc = "KI-Tool für faceless TikToks. Text rein, KI-Voiceover plus passendes Stockvideo plus Untertitel raus. Fertiges 9:16-Video in unter einer Minute. Kostenlos.";
      meta('description', desc);
      meta('og:title', 'VoiceClip - TikToks ohne Gesicht in 60 Sekunden', 'property');
      meta('og:description', desc, 'property');
      meta('og:type', 'website', 'property');
      meta('og:url', 'https://closelyst.com/', 'property');
      meta('og:image', 'https://closelyst.com/~/+/media/icon.png', 'property');
      meta('og:locale', 'de_DE', 'property');
      meta('twitter:card', 'summary');
      meta('twitter:title', 'VoiceClip - TikToks ohne Gesicht');
      meta('twitter:description', desc);
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# iOS Safari fullscreent HTML5-Videos beim ersten User-Tap, wenn das
# playsinline-Attribut fehlt. st.video() setzt es nicht, also patchen
# wir alle <video>-Elemente per MutationObserver. Greift fuer Demo-
# Video und Post-Generation-Preview gleichzeitig.
st.markdown(
    """
    <script>
    (function() {
      const patch = () => {
        document.querySelectorAll('video').forEach(v => {
          if (!v.hasAttribute('playsinline')) {
            v.setAttribute('playsinline', '');
            v.setAttribute('webkit-playsinline', '');
          }
        });
      };
      patch();
      const obs = new MutationObserver(patch);
      obs.observe(document.body, {childList: true, subtree: true});
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# Minimaler Polish: Footer (Made with Streamlit) und Deploy-Button verstecken.
# Das 3-Punkte-Menue bleibt sichtbar - Streamlit-Default, kein UI-Krieg.
# Padding-Top fuer Atemraum oben.
st.markdown(
    """
    <style>
    /* "Made with Streamlit" Footer und Deploy-Button raus */
    footer,
    [data-testid="stFooter"],
    a[href*="streamlit.io"],
    [data-testid="stDeployButton"] {
        display: none !important;
    }

    /* Atemraum oben vor dem Logo, links nah an der Sidebar */
    .main .block-container {
        padding-top: 1rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    @media (max-width: 640px) {
        .main .block-container {
            padding-top: 0.5rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Post-purchase Success-Banner: Polar redirected nach Zahlung mit
# ?status=success&checkout_id=... zurueck auf closelyst.com. User soll
# direkt sehen dass Kauf durchging und wo der License-Key landet.
_qs = st.query_params
if _qs.get("status") == "success":
    st.success(
        "**Zahlung erfolgreich.** Du bekommst gleich eine E-Mail von Polar mit "
        "deinem Lizenz-Schlüssel. Füge ihn links in der Sidebar unter "
        "'Lizenz-Schlüssel' ein und klick 'Einlösen'."
    )
    _checkout_id = _qs.get("checkout_id", "")
    if _checkout_id:
        st.caption(f"Checkout-Referenz: {_checkout_id[:8]}...")

st.image(str(_ASSETS / "logo.svg"), width=260)

# Founder-Social-Pills: TikTok + GitHub direkt unter Logo, auch auf
# Mobile sichtbar (ohne Sidebar zu oeffnen). Cross-Channel-Traffic.
st.markdown(
    """
    <div style="display: flex; flex-wrap: wrap; gap: 0.5em; margin-bottom: 0.8em;">
        <a href="https://www.tiktok.com/@haciibrahimdogan" target="_blank"
           style="display: inline-flex; align-items: center; gap: 0.5em;
                  padding: 0.5em 0.9em; border-radius: 999px;
                  background: #0f172a; color: #ffffff; text-decoration: none;
                  font-weight: 600; font-size: 0.9em;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"
                 aria-hidden="true" style="flex-shrink: 0;">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
            </svg>
            @haciibrahimdogan
        </a>
        <a href="https://github.com/ZipZap1" target="_blank"
           style="display: inline-flex; align-items: center; gap: 0.5em;
                  padding: 0.5em 0.9em; border-radius: 999px;
                  background: #24292f; color: #ffffff; text-decoration: none;
                  font-weight: 600; font-size: 0.9em;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"
                 aria-hidden="true" style="flex-shrink: 0;">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            ZipZap1
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# Above-the-Fold Value-Prop. Sichtbar bevor User scrollt oder das Form sieht.
st.markdown(
    """
    <div style="margin-top: -0.5em; margin-bottom: 0.5em;">
        <h1 style="font-size: 2.2em; font-weight: 800; line-height: 1.15;
                   margin: 0; color: #0f172a;">
            TikToks ohne Gesicht. Ohne Stimme. Ohne Skills.
        </h1>
        <p style="font-size: 1.05em; line-height: 1.5; margin-top: 0.6em;
                  color: rgba(15, 23, 42, 0.7);">
            Tipp deinen Text. KI generiert Voiceover, sucht passende Stockvideos,
            synct Untertitel. Fertiges Video in unter einer Minute.
            <strong style="color: #8b5cf6;">Kostenlos starten, ohne Account.</strong>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
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


# Polar-Checkout-URLs auf Modul-Level: gleicher Wert wird in Sidebar
# UND in Main-Content (Pro-CTA-Block) genutzt.
_remove_url = license_mod.get_buy_url("POLAR_CHECKOUT_URL_REMOVE_WATERMARK")
_pro_url = license_mod.get_buy_url("POLAR_CHECKOUT_URL_PRO_MONTHLY")


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

    st.caption("Beide Pakete entfernen das Wasserzeichen. Pro-Abo schaltet zusätzlich ElevenLabs Premium-Stimmen und Voice-Cloning frei.")
    if _remove_url:
        st.link_button("2,99 EUR: Einmalig (1 Video)", _remove_url)
    if _pro_url:
        st.link_button("8,99 EUR/Mo: Unlimitiert", _pro_url)
    if not _remove_url and not _pro_url:
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


# Pro-CTA-Banner mit direktem Link zum Polar-Abo-Checkout (8,99/Mo).
# Border-Style fuer cleane Outline-Optik.
if not is_pro and _pro_url:
    st.markdown(
        f"""
        <div style="padding: 0.9em 1em; border-radius: 8px;
                    background: linear-gradient(135deg, #ede9fe 0%, #fce7f3 100%);
                    margin: 0.5em 0 0.8em 0; display: flex;
                    align-items: center; gap: 0.8em; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; font-size: 0.95em; color: #0f172a;">
                <strong>Pro freischalten:</strong> Kein Wasserzeichen, Premium-Stimmen, Voice-Cloning.
            </div>
            <a href="{_pro_url}" target="_blank"
               style="padding: 0.55em 1.2em; border-radius: 999px;
                      border: 2px solid #8b5cf6; background: transparent;
                      color: #8b5cf6; font-weight: 700; font-size: 0.9em;
                      text-decoration: none; white-space: nowrap;
                      transition: all 0.15s;">
                Pro-Abo 8,99 €/Mo →
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Optional demo-video and ProductHunt embed. Both are read from env so
# they show up only when set; nothing leaks before launch.
# Demo prefers external URL (CDN), falls back to bundled assets/demo.mp4
# wenn die im Repo liegt. So oder so: Demo erscheint sobald File / URL da ist.
_demo_url = os.environ.get("DEMO_VIDEO_URL", "").strip()
_demo_local = _ASSETS / "demo.mp4"
_demo_source = _demo_url if _demo_url else (str(_demo_local) if _demo_local.exists() else "")
_ph_url = os.environ.get("PRODUCTHUNT_URL", "").strip()
if _demo_source or _ph_url:
    cols = st.columns([3, 1])
    with cols[0]:
        if _demo_source:
            with st.expander("Demo: VoiceClip in Aktion (20 Sek)", expanded=True):
                st.video(_demo_source, autoplay=True, muted=False, loop=True)
    with cols[1]:
        if _ph_url:
            st.link_button("Auf ProductHunt", _ph_url, use_container_width=True)


tab_video, tab_enhance = st.tabs(["Video erstellen", "Bild verbessern (Pro)"])

# ============================================================
# Tab 1: Video erstellen
# ============================================================
with tab_video:
    # TikTok-typische Hooks, verschiedene Formate (Tutorial, Storytelling,
    # Listicle, Contrarian, Personal). Bei jedem Klick auf "Beispiel laden"
    # zyklisch durch die Liste.
    _EXAMPLE_TEXTS = [
        "Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst.",
        "Vor einer Woche hatte ich null Downloads. Heute zeige ich dir was ich gelernt habe. Erstens: niemand will deine App. Zweitens: jeder will dein Tool. Hier ist mein neuer Plan.",
        "Drei KI-Tools, die kein Mensch kennt, aber jeder Creator nutzen sollte. Tool eins macht aus Text in zehn Sekunden ein TikTok. Tool zwei findet passende Stockvideos. Tool drei erzeugt synchronisierte Untertitel.",
        "Warum 90 Prozent aller Side-Projects scheitern, und wie du in den 10 Prozent landest. Erstens: kein Markt-Test vorher. Zweitens: zu viel Feature, zu wenig Fokus. Drittens: keine Distribution.",
        "Ich habe in einem Monat 100 aktive Nutzer bekommen. Mit null Marketing-Budget. So lief das. Hook eins: jeden Tag ein TikTok. Hook zwei: 20 DMs an Micro-Creator. Hook drei: Product Hunt Launch.",
        "Die meisten Founder bauen das falsche Produkt. Sie fragen nicht ihre User. Sie schauen nicht auf Daten. Sie verlieben sich in ihre Idee. Hier sind drei Fragen, die du vor jedem Build stellen solltest.",
        "Stell dir vor du könntest in zwei Minuten ein TikTok ohne dein Gesicht zu zeigen. Text rein, fertiges Video raus. Mit KI-Stimme, Stockvideo und Untertiteln. Genau das macht VoiceClip.",
        "Drei Sachen die ich gerne vor meiner ersten App gewusst hätte. Erstens: Distribution ist wichtiger als das Produkt. Zweitens: dein erster Launch wird floppen, das ist okay. Drittens: ship oft, ship schnell.",
    ]

    def _load_example():
        # on_click callback runs before the next rerun, which is the
        # only safe place to mutate a widget's session_state key after
        # the widget has been instantiated.
        idx = st.session_state.get("example_idx", 0)
        st.session_state["voiceover_text"] = _EXAMPLE_TEXTS[idx % len(_EXAMPLE_TEXTS)]
        st.session_state["example_idx"] = idx + 1

    text = st.text_area(
        "Was soll der Voiceover sagen?",
        height=130,
        placeholder="Z.B.: Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst.",
        key="voiceover_text",
    )
    st.button(
        "Beispiel laden",
        help="Füllt das Textfeld mit einem Beispiel-Hook. Bei jedem Klick ein anderer.",
        key="example_btn",
        on_click=_load_example,
    )

    # Voice-Backend-Wahl: Free-User bekommen kuratierte OpenAI-Voices,
    # Pro-User koennen zwischen ElevenLabs (Premium-Stimmen, Voice-Cloning)
    # und OpenAI (konsistenter, oft besser fuer EN) switchen.
    if is_pro:
        backend_label = st.radio(
            "Voice-Backend",
            options=["ElevenLabs (Premium-Stimmen, Voice-Cloning)", "OpenAI (Standard, schneller)"],
            index=0,
            horizontal=True,
            key="voice_backend_radio",
            help="ElevenLabs ist expressiver und unterstützt Voice-Cloning. OpenAI ist konsistenter und für englischen Content oft genauso gut.",
        )
        voice_backend = "elevenlabs" if backend_label.startswith("ElevenLabs") else "openai_tts1hd"
    else:
        voice_backend = "openai_tts1hd"

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

    # Voice picker: ElevenLabs (full list + cloned voice if any) shown to Pro
    # users. Free-Tier (OpenAI) ueberspringt den Picker und nutzt Nova als
    # Default (beste DE-Voice laut Research).
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
        # Free-Tier nutzt fix Nova (OpenAI). Kein Picker um UX schlank zu halten.
        selected_voice_id = "nova"

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
            "Datei (Video: .mp4 .mov / Bild: .jpg .png .webp, max 50 MB)",
            type=["mp4", "mov", "m4v", "jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            key="upload_media_uploader",
            help="Wird auf 9:16 gecroppt. Tipp: unter 10 MB = schneller Upload. Video lokal mit ffmpeg komprimieren falls zu groß.",
        )
        if uploaded_media is not None:
            _mb = uploaded_media.size / 1_000_000
            if _mb > 15:
                st.caption(f"Datei: {_mb:.1f} MB. Tipp: unter 10 MB = deutlich schnellerer Upload.")
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
            help="Tipp: unter 10 MB = schneller Upload. Video lokal komprimieren falls zu groß.",
        )
        if uploaded_media is not None:
            _mb = uploaded_media.size / 1_000_000
            if _mb > 15:
                st.caption(f"Datei: {_mb:.1f} MB. Tipp: unter 10 MB = deutlich schnellerer Upload.")
        st.caption("AI synchronisiert die Lippen deiner Person mit dem AI-Voiceover. Dauert 30-90 Sekunden. Lip-Sync ist rechenintensiv und zählt 7x ins Pro-Limit (~28 Lip-Syncs pro Zyklus möglich).")
        if not is_pro:
            st.warning("Nur für Pro. Trag oben einen Pro-Schlüssel ein oder kauf einen.")

    # Caption-Style: TikTok-typische Defaults (gelber Text, große Box unten).
    # Free-User bekommen diese fix, Pro-User können sie anpassen.
    caption_text_color = "#fbbf24"
    caption_bg_color = "#000000"
    caption_bg_alpha = 200
    caption_font_size = 80
    caption_position = "bottom"

    if is_pro:
        with st.expander("Caption-Style anpassen (Pro)"):
            cs_col1, cs_col2 = st.columns(2)
            with cs_col1:
                caption_text_color = st.color_picker(
                    "Text-Farbe", value=caption_text_color, key="caption_text_color"
                )
                caption_position = st.selectbox(
                    "Position",
                    options=["bottom", "center", "top"],
                    index=0,
                    key="caption_position",
                )
            with cs_col2:
                caption_bg_color = st.color_picker(
                    "Box-Farbe (Hintergrund hinter Text)", value=caption_bg_color, key="caption_bg_color"
                )
                caption_font_size = st.select_slider(
                    "Font-Größe",
                    options=[48, 56, 64, 72, 80, 96],
                    value=caption_font_size,
                    key="caption_font_size",
                )
            caption_bg_alpha = st.slider(
                "Box-Deckkraft", min_value=0, max_value=255, value=caption_bg_alpha, key="caption_bg_alpha",
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
            st.error(
                f"**Tageslimit erreicht.** Du hast {_used} von {_lim} kostenlosen Videos heute "
                f"verbraucht. Komm morgen wieder oder kauf einen Pro-Schlüssel (ab 2,99 EUR) "
                f"für unbegrenzte Generierungen."
            )
        elif _rem <= 2:
            st.warning(
                f"Nur noch **{_rem} von {_lim}** kostenlosen Videos heute übrig. "
                f"Für unbegrenzt: Pro ab 2,99 EUR (siehe Sidebar)."
            )
        elif _rem < _lim:
            st.info(
                f"Free-Tier: {_used} von {_lim} kostenlosen Videos heute verbraucht. **{_rem} übrig.**"
            )

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
                    progress.progress(10, text="Voiceover generieren mit ElevenLabs...")
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

                progress.progress(70, text="Video wird komponiert...")
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
                    animate_image=True,
                )

                progress.progress(100, text="Fertig.")
                if not is_pro:
                    rate_limit.consume_free_quota()
                video_bytes = output_path.read_bytes()
                st.video(video_bytes, autoplay=False)
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
                    st.info("Wasserzeichen ist im Video. Pro-Abo: kein Wasserzeichen, unlimitiert.")
                    if _pro_url:
                        st.markdown(
                            f"""
                            <a href="{_pro_url}" target="_blank"
                               style="display: inline-block; padding: 0.6em 1.4em;
                                      border-radius: 999px; border: 2px solid #8b5cf6;
                                      background: transparent; color: #8b5cf6;
                                      font-weight: 700; font-size: 0.95em;
                                      text-decoration: none; margin-top: 0.4em;">
                                Pro-Abo 8,99 €/Mo →
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
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
