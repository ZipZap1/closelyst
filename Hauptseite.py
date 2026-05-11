"""VoiceClip MVP. TikTok AI Voiceover Generator.

Streamlit single-page app. Text in, 1080x1920 portrait video out.
"""
import base64
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
from i18n import t, render_lang_toggle, get_lang

_ASSETS = Path(__file__).parent / "assets"

# Page title used by browser tab. Set once at config time, so we read the
# lang at module-load from query params directly (session_state isn't ready
# yet at this point).
_initial_lang = "en" if st.query_params.get("lang") == "en" else "de"
_page_title_de = "VoiceClip - TikToks ohne Gesicht in 60 Sekunden | closelyst.com"
_page_title_en = "VoiceClip - Faceless TikToks in 60 seconds | closelyst.com"
st.set_page_config(
    page_title=_page_title_de if _initial_lang == "de" else _page_title_en,
    page_icon=str(_ASSETS / "icon.png"),
    layout="centered",
    initial_sidebar_state="collapsed",
)

render_lang_toggle()

# SEO-Metadata via JavaScript in <head> injizieren. Streamlit's
# set_page_config setzt nur title/icon, fuer og:image und Description
# brauchen wir Custom-Tags. Sprache wird aus initial_lang abgeleitet.
_meta_desc = t(
    "KI-Tool für faceless TikToks. Text rein, KI-Voiceover plus passendes Stockvideo plus Untertitel raus. Fertiges 9:16-Video in unter einer Minute. Kostenlos.",
    "AI tool for faceless TikToks. Type text in, get AI voiceover plus matching stock video plus captions out. Finished 9:16 video in under a minute. Free.",
)
_meta_og_title = t(
    "VoiceClip - TikToks ohne Gesicht in 60 Sekunden",
    "VoiceClip - Faceless TikToks in 60 seconds",
)
_meta_tw_title = t(
    "VoiceClip - TikToks ohne Gesicht",
    "VoiceClip - Faceless TikToks",
)
_meta_locale = "de_DE" if get_lang() == "de" else "en_US"
st.markdown(
    f"""
    <script>
    (function() {{
      const head = document.head;
      const meta = (k, v, attr) => {{
        attr = attr || 'name';
        let existing = head.querySelector(`meta[${{attr}}="${{k}}"]`);
        if (existing) {{ existing.setAttribute('content', v); return; }}
        const m = document.createElement('meta');
        m.setAttribute(attr, k);
        m.setAttribute('content', v);
        head.appendChild(m);
      }};
      const desc = {_meta_desc!r};
      meta('description', desc);
      meta('og:title', {_meta_og_title!r}, 'property');
      meta('og:description', desc, 'property');
      meta('og:type', 'website', 'property');
      meta('og:url', 'https://closelyst.com/', 'property');
      meta('og:image', 'https://closelyst.com/~/+/media/icon.png', 'property');
      meta('og:locale', {_meta_locale!r}, 'property');
      meta('twitter:card', 'summary');
      meta('twitter:title', {_meta_tw_title!r});
      meta('twitter:description', desc);
    }})();
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

    /* Minimaler Top-Padding, damit der Pro-CTA Above-The-Fold landet */
    .main .block-container {
        padding-top: 0.25rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    @media (max-width: 640px) {
        .main .block-container {
            padding-top: 0.1rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
    /* Header bleibt mit seiner Default-Hoehe damit Sidebar-Chevron
       in seinem natuerlichen Spot sitzt (Streamlit-JS fadet ihn sonst
       weg und ist nicht via CSS oder MutationObserver zuverlaessig
       zu fixen). Above-The-Fold-Platz holen wir nur ueber kompakteres
       Hero/Logo/Social-Pills/Hero-Body. Background transparent damit
       sich der Header optisch in die Seite einfuegt. */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    /* Toolbar rechts (3-Punkte, Deploy) versteckt; entfernt Konflikt
       mit unserem Language-Toggle, der oben rechts sitzt. */
    header[data-testid="stHeader"] [data-testid="stToolbar"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar wird komplett ausgeblendet. License-Key-Eingabe lebt jetzt
# inline auf der Hauptseite als Expander. Streamlit-eigener Sidebar-
# Chevron war unzuverlaessig (verschwand nach Schliessen), Custom-
# Toggle-Button triggerte React-Handler nicht. Direkter Pfad: keine
# Sidebar = kein Toggle-Problem.
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Post-purchase Success-Banner: Polar redirected nach Zahlung mit
# ?status=success&checkout_id=... zurueck auf closelyst.com. User soll
# direkt sehen dass Kauf durchging und wo der License-Key landet.
_qs = st.query_params
if _qs.get("status") == "success":
    st.success(t(
        "**Zahlung erfolgreich.** Du bekommst gleich eine E-Mail von Polar mit "
        "deinem Lizenz-Schlüssel. Füge ihn unten unter "
        "'Pro-Schlüssel einlösen' ein und klick 'Einlösen'.",
        "**Payment successful.** You'll receive an email from Polar with your "
        "license key shortly. Paste it below under "
        "'Redeem Pro key' and click 'Redeem'.",
    ))
    _checkout_id = _qs.get("checkout_id", "")
    if _checkout_id:
        st.caption(t(
            f"Checkout-Referenz: {_checkout_id[:8]}...",
            f"Checkout reference: {_checkout_id[:8]}...",
        ))

st.image(str(_ASSETS / "logo.svg"), width=180)

# Founder-Social-Pills: TikTok + GitHub kompakt unter Logo. Kleinere
# Padding/Gap-Werte damit Above-The-Fold Platz fuer Pro-CTA bleibt.
st.markdown(
    """
    <div style="display: flex; flex-wrap: wrap; gap: 0.35em; margin: 0.1em 0 0.4em 0;">
        <a href="https://www.tiktok.com/@haciibrahimdogan" target="_blank"
           style="display: inline-flex; align-items: center; gap: 0.4em;
                  padding: 0.3em 0.7em; border-radius: 999px;
                  background: #0f172a; color: #ffffff; text-decoration: none;
                  font-weight: 600; font-size: 0.8em;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"
                 aria-hidden="true" style="flex-shrink: 0;">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
            </svg>
            @haciibrahimdogan
        </a>
        <a href="https://github.com/ZipZap1" target="_blank"
           style="display: inline-flex; align-items: center; gap: 0.4em;
                  padding: 0.3em 0.7em; border-radius: 999px;
                  background: #24292f; color: #ffffff; text-decoration: none;
                  font-weight: 600; font-size: 0.8em;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"
                 aria-hidden="true" style="flex-shrink: 0;">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            ZipZap1
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# Above-the-Fold Value-Prop. Kompakter (1.7em statt 2.2em, kurzes Body)
# damit der Pro-CTA-Button direkt darunter ohne Scrollen sichtbar ist.
_hero_headline = t(
    "TikToks ohne Gesicht. Ohne Stimme. Ohne Skills.",
    "TikToks without your face. Without your voice. Without skills.",
)
_hero_body = t(
    "Tipp deinen Text. KI macht den Rest. Fertiges Video in unter einer Minute.",
    "Type your text. AI does the rest. Finished video in under a minute.",
)
_hero_cta = t(
    "Kostenlos starten, ohne Account.",
    "Start free, no account needed.",
)
st.markdown(
    f"""
    <div style="margin-top: -0.2em; margin-bottom: 0.3em;">
        <h1 style="font-size: 1.7em; font-weight: 800; line-height: 1.15;
                   margin: 0; color: #0f172a;">
            {_hero_headline}
        </h1>
        <p style="font-size: 0.95em; line-height: 1.4; margin: 0.3em 0 0 0;
                  color: rgba(15, 23, 42, 0.72);">
            {_hero_body}
            <strong style="color: #8b5cf6;">{_hero_cta}</strong>
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


# ----- License / Pro Block: jetzt inline auf Hauptseite (war Sidebar) -----
with st.expander(t("Pro-Schlüssel einlösen", "Redeem Pro key"), expanded=False):
    license_key_input = st.text_input(
        t("Lizenz-Schlüssel", "License key"),
        type="password",
        help=t(
            "Hast du einen Lizenz-Schlüssel gekauft? Hier einfügen und Einlösen klicken.",
            "Bought a license key? Paste it here and click Redeem.",
        ),
        key="license_key_input",
    )

    # Clear stored validation if the user changes the key
    if st.session_state.get("validated_key") != license_key_input:
        st.session_state.pop("license_validation", None)
        st.session_state.pop("validated_key", None)

    if st.button(t("Einlösen", "Redeem"), disabled=not license_key_input, key="redeem_btn"):
        with st.spinner(t("Lizenz prüfen...", "Validating license...")):
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
                    st.error(t(
                        "Key gültig, aber bereits verbraucht. Kauf einen neuen oder upgrade auf Pro monatlich.",
                        "Key valid but already used. Buy a new one or upgrade to Pro monthly.",
                    ))
                elif renews_at_de:
                    st.error(t(
                        f"Pro-Limit ({limit}) erreicht. Zurücksetzung bei der nächsten Abbuchung am {renews_at_de}.",
                        f"Pro limit ({limit}) reached. Resets at next billing on {renews_at_de}.",
                    ))
                else:
                    st.error(t(
                        f"Pro-Limit ({limit}) erreicht. Zurücksetzung bei der nächsten Abrechnung.",
                        f"Pro limit ({limit}) reached. Resets at next billing.",
                    ))
            else:
                is_pro = True
                is_one_shot_key = (limit == 1)
                if is_one_shot_key:
                    st.success(t(
                        "Pro aktiv. 1 Video ohne Wasserzeichen verfügbar.",
                        "Pro active. 1 video without watermark available.",
                    ))
                elif limit is not None:
                    pro_remaining = limit - usage
                    msg = t(
                        f"Pro aktiv. {pro_remaining} von {limit} Generierungen diesen Zyklus übrig.",
                        f"Pro active. {pro_remaining} of {limit} generations left this cycle.",
                    )
                    if renews_at_de:
                        msg += t(f" Zurücksetzung am {renews_at_de}.", f" Resets on {renews_at_de}.")
                    if pro_remaining <= 10:
                        st.warning(msg)
                    else:
                        st.success(msg)
                else:
                    st.success(t(
                        "Pro aktiv. Wasserzeichen wird entfernt.",
                        "Pro active. Watermark will be removed.",
                    ))
        else:
            _reason = result.get('reason', t('unbekannt', 'unknown'))
            st.error(t(f"Ungültig: {_reason}", f"Invalid: {_reason}"))
    elif license_key_input:
        st.caption(t("Klick Einlösen um den Key zu prüfen.", "Click Redeem to validate the key."))

    st.divider()

    st.caption(t(
        "Beide Pakete entfernen das Wasserzeichen. Pro-Abo schaltet zusätzlich ElevenLabs Premium-Stimmen und Voice-Cloning frei.",
        "Both packages remove the watermark. Pro subscription additionally unlocks ElevenLabs premium voices and voice cloning.",
    ))
    if _remove_url:
        st.link_button(t("2,99 EUR: Einmalig (1 Video)", "€2.99: One-time (1 video)"), _remove_url)
    if _pro_url:
        st.link_button(t("8,99 EUR/Mo: Unlimitiert", "€8.99/mo: Unlimited"), _pro_url)
    if not _remove_url and not _pro_url:
        st.caption(t(
            "Polar-Checkout-URLs in .env eintragen, dann erscheinen die Checkout-Buttons.",
            "Set Polar checkout URLs in .env, then the checkout buttons appear.",
        ))


# Pro-CTA-Banner direkt unter dem Hero -> Above-The-Fold sichtbar
# auch auf kleinen Mobile-Screens. Border-Style fuer cleane Optik.
if not is_pro and _pro_url:
    _pro_banner_text = t(
        "<strong>Pro freischalten:</strong> Kein Wasserzeichen, Premium-Stimmen, Voice-Cloning.",
        "<strong>Unlock Pro:</strong> No watermark, premium voices, voice cloning.",
    )
    _pro_banner_cta = t("Pro-Abo 8,99 €/Mo →", "Pro subscription €8.99/mo →")
    st.markdown(
        f"""
        <div style="padding: 0.7em 0.9em; border-radius: 8px;
                    background: linear-gradient(135deg, #ede9fe 0%, #fce7f3 100%);
                    margin: 0.2em 0 0.5em 0; display: flex;
                    align-items: center; gap: 0.7em; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; font-size: 0.9em; color: #0f172a;">
                {_pro_banner_text}
            </div>
            <a href="{_pro_url}" target="_blank"
               style="padding: 0.5em 1.1em; border-radius: 999px;
                      border: 2px solid #8b5cf6; background: transparent;
                      color: #8b5cf6; font-weight: 700; font-size: 0.88em;
                      text-decoration: none; white-space: nowrap;
                      transition: all 0.15s;">
                {_pro_banner_cta}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----- Onboarding (unter Pro-CTA, damit CTA above-the-fold bleibt) -----
with st.expander(t("Wie funktioniert das?", "How does it work?"), expanded=False):
    st.markdown(t(
        """
1. Text eintippen
2. Stimme wählen (Pro: eigene klonen)
3. Hintergrund wählen
4. Generieren

Tab **Bild verbessern** ist ein Pro-Tool: Bild rein, AI macht's schärfer.
        """,
        """
1. Type text
2. Pick a voice (Pro: clone your own)
3. Pick a background
4. Generate

Tab **Enhance image** is a Pro tool: image in, AI makes it sharper.
        """,
    ))

# Optional demo-video and ProductHunt embed. Both are read from env so
# they show up only when set; nothing leaks before launch.
# Demo prefers external URL (CDN), falls back to bundled assets/demo.mp4
# wenn die im Repo liegt. So oder so: Demo erscheint sobald File / URL da ist.
_demo_url = os.environ.get("DEMO_VIDEO_URL", "").strip()
_demo_local = _ASSETS / "demo.mp4"
_demo_source = _demo_url if _demo_url else (str(_demo_local) if _demo_local.exists() else "")
_ph_url = os.environ.get("PRODUCTHUNT_URL", "").strip()


def _demo_video_html(source):
    """Autoplay-stumm + Klick-fuer-Ton (Instagram-Pattern). Browser blocken
    Autoplay mit Audio bis zur ersten User-Interaktion; muted Autoplay laeuft
    immer. Erster Klick auf das Video entmutet und zaehlt als Interaktion."""
    if source.startswith(("http://", "https://")):
        src = source
    else:
        try:
            with open(source, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            src = f"data:video/mp4;base64,{b64}"
        except OSError:
            return None
    unmute_label = t("Klick für Ton", "Tap for sound")
    return f"""
<div style="position: relative; max-width: 340px; margin: 0 auto;
            aspect-ratio: 9/16; border-radius: 12px; overflow: hidden;
            background: #000; cursor: pointer;" id="vc-demo-wrap">
    <video id="vc-demo" autoplay muted loop playsinline
           style="width: 100%; height: 100%; object-fit: cover; display: block;"
           src="{src}"></video>
    <div id="vc-unmute" style="position: absolute; inset: 0;
                                display: flex; align-items: center;
                                justify-content: center; pointer-events: none;
                                background: linear-gradient(180deg,
                                    rgba(0,0,0,0) 55%, rgba(0,0,0,0.45));
                                color: white;
                                font-family: -apple-system, BlinkMacSystemFont,
                                              'Segoe UI', sans-serif;">
        <div style="background: rgba(0,0,0,0.72); padding: 9px 16px;
                    border-radius: 999px; display: flex;
                    align-items: center; gap: 8px; font-size: 13px;
                    font-weight: 600;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM3 9v6h4l5 5V4L7 9H3z"/>
                <line x1="2" y1="2" x2="22" y2="22" stroke="white" stroke-width="2.5"/>
            </svg>
            <span>{unmute_label}</span>
        </div>
    </div>
</div>
<script>
(function() {{
    var wrap = document.getElementById('vc-demo-wrap');
    var v = document.getElementById('vc-demo');
    var overlay = document.getElementById('vc-unmute');
    if (!wrap || !v) return;
    v.play().catch(function() {{}});
    wrap.addEventListener('click', function() {{
        v.muted = !v.muted;
        if (overlay) overlay.style.display = v.muted ? 'flex' : 'none';
        v.play().catch(function() {{}});
    }});
}})();
</script>
"""


if _demo_source or _ph_url:
    cols = st.columns([3, 1])
    with cols[0]:
        if _demo_source:
            with st.expander(
                t("Demo: VoiceClip in Aktion (20 Sek)", "Demo: VoiceClip in action (20 sec)"),
                expanded=True,
            ):
                html = _demo_video_html(_demo_source)
                if html:
                    st.components.v1.html(html, height=620)
                else:
                    st.video(_demo_source, autoplay=True, muted=True, loop=True)
    with cols[1]:
        if _ph_url:
            st.link_button(t("Auf ProductHunt", "On ProductHunt"), _ph_url, use_container_width=True)


tab_video, tab_enhance = st.tabs([
    t("Video erstellen", "Create video"),
    t("Bild verbessern (Pro)", "Enhance image (Pro)"),
])

# ============================================================
# Tab 1: Video erstellen
# ============================================================
with tab_video:
    # TikTok-typische Hooks, verschiedene Formate (Tutorial, Storytelling,
    # Listicle, Contrarian, Personal). Bei jedem Klick auf "Beispiel laden"
    # zyklisch durch die Liste.
    _EXAMPLE_TEXTS_DE = [
        "Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst.",
        "Vor einer Woche hatte ich null Downloads. Heute zeige ich dir was ich gelernt habe. Erstens: niemand will deine App. Zweitens: jeder will dein Tool. Hier ist mein neuer Plan.",
        "Drei KI-Tools, die kein Mensch kennt, aber jeder Creator nutzen sollte. Tool eins macht aus Text in zehn Sekunden ein TikTok. Tool zwei findet passende Stockvideos. Tool drei erzeugt synchronisierte Untertitel.",
        "Warum 90 Prozent aller Side-Projects scheitern, und wie du in den 10 Prozent landest. Erstens: kein Markt-Test vorher. Zweitens: zu viel Feature, zu wenig Fokus. Drittens: keine Distribution.",
        "Ich habe in einem Monat 100 aktive Nutzer bekommen. Mit null Marketing-Budget. So lief das. Hook eins: jeden Tag ein TikTok. Hook zwei: 20 DMs an Micro-Creator. Hook drei: Product Hunt Launch.",
        "Die meisten Founder bauen das falsche Produkt. Sie fragen nicht ihre User. Sie schauen nicht auf Daten. Sie verlieben sich in ihre Idee. Hier sind drei Fragen, die du vor jedem Build stellen solltest.",
        "Stell dir vor du könntest in zwei Minuten ein TikTok ohne dein Gesicht zu zeigen. Text rein, fertiges Video raus. Mit KI-Stimme, Stockvideo und Untertiteln. Genau das macht VoiceClip.",
        "Drei Sachen die ich gerne vor meiner ersten App gewusst hätte. Erstens: Distribution ist wichtiger als das Produkt. Zweitens: dein erster Launch wird floppen, das ist okay. Drittens: ship oft, ship schnell.",
    ]
    _EXAMPLE_TEXTS_EN = [
        "Three tips on how to get your first users as a solo founder.",
        "A week ago I had zero downloads. Today I'll show you what I learned. First: nobody wants your app. Second: everybody wants your tool. Here is my new plan.",
        "Three AI tools nobody knows about, but every creator should use. Tool one turns text into a TikTok in ten seconds. Tool two finds matching stock videos. Tool three generates synced captions.",
        "Why 90 percent of all side projects fail, and how to land in the 10 percent. First: no market test up front. Second: too much feature, too little focus. Third: no distribution.",
        "I got 100 active users in a single month. With zero marketing budget. Here is how it went. Hook one: one TikTok every day. Hook two: 20 DMs to micro-creators. Hook three: Product Hunt launch.",
        "Most founders build the wrong product. They don't ask their users. They don't look at data. They fall in love with their idea. Here are three questions you should ask before every build.",
        "Imagine you could make a TikTok in two minutes without showing your face. Type text in, get a finished video out. With AI voice, stock video and captions. That is exactly what VoiceClip does.",
        "Three things I wish I knew before my first app. First: distribution matters more than the product. Second: your first launch will flop, that's okay. Third: ship often, ship fast.",
    ]
    _EXAMPLE_TEXTS = _EXAMPLE_TEXTS_DE if get_lang() == "de" else _EXAMPLE_TEXTS_EN

    def _load_example():
        # on_click callback runs before the next rerun, which is the
        # only safe place to mutate a widget's session_state key after
        # the widget has been instantiated.
        idx = st.session_state.get("example_idx", 0)
        st.session_state["voiceover_text"] = _EXAMPLE_TEXTS[idx % len(_EXAMPLE_TEXTS)]
        st.session_state["example_idx"] = idx + 1

    text = st.text_area(
        t("Was soll der Voiceover sagen?", "What should the voiceover say?"),
        height=130,
        placeholder=t(
            "Z.B.: Drei Tipps wie du als Solo-Founder deine ersten Nutzer kriegst.",
            "E.g.: Three tips on how to get your first users as a solo founder.",
        ),
        key="voiceover_text",
    )
    st.button(
        t("Beispiel laden", "Load example"),
        help=t(
            "Füllt das Textfeld mit einem Beispiel-Hook. Bei jedem Klick ein anderer.",
            "Fills the text field with an example hook. Different one on each click.",
        ),
        key="example_btn",
        on_click=_load_example,
    )

    # Voice-Backend-Wahl: Free-User bekommen kuratierte OpenAI-Voices,
    # Pro-User koennen zwischen ElevenLabs (Premium-Stimmen, Voice-Cloning)
    # und OpenAI (konsistenter, oft besser fuer EN) switchen.
    if is_pro:
        _eleven_label = t(
            "ElevenLabs (Premium-Stimmen, Voice-Cloning)",
            "ElevenLabs (premium voices, voice cloning)",
        )
        _openai_label = t("OpenAI (Standard, schneller)", "OpenAI (standard, faster)")
        backend_label = st.radio(
            t("Voice-Backend", "Voice backend"),
            options=[_eleven_label, _openai_label],
            index=0,
            horizontal=True,
            key="voice_backend_radio",
            help=t(
                "ElevenLabs ist expressiver und unterstützt Voice-Cloning. OpenAI ist konsistenter und für englischen Content oft genauso gut.",
                "ElevenLabs is more expressive and supports voice cloning. OpenAI is more consistent and often just as good for English content.",
            ),
        )
        voice_backend = "elevenlabs" if backend_label.startswith("ElevenLabs") else "openai_tts1hd"
    else:
        voice_backend = "openai_tts1hd"

    # Voice cloning is a Pro-only power feature, AND only meaningful when the
    # ElevenLabs backend is selected (clones live in the ElevenLabs account).
    if is_pro and voice_backend == "elevenlabs":
        with st.expander(t(
            "Pro-Einstellungen: Eigene Stimme klonen",
            "Pro settings: Clone your own voice",
        )):
            st.caption(t(
                "Audio-Sample (30+ Sek, klar gesprochen) hochladen. "
                "ElevenLabs klont die Stimme, danach erscheint sie ganz oben im Dropdown.",
                "Upload an audio sample (30+ sec, clearly spoken). "
                "ElevenLabs clones the voice, then it shows up at the top of the dropdown.",
            ))
            clone_col1, clone_col2 = st.columns([2, 1])
            with clone_col1:
                voice_sample = st.file_uploader(
                    t(
                        "Audio-Sample (.mp3 .wav, 30+ Sek)",
                        "Audio sample (.mp3 .wav, 30+ sec)",
                    ),
                    type=["mp3", "wav", "m4a"],
                    key="voice_sample_uploader",
                    accept_multiple_files=False,
                )
            with clone_col2:
                _default_clone_name = t("Meine Stimme", "My voice")
                clone_name = st.text_input(t("Name", "Name"), value=_default_clone_name, key="voice_clone_name")
            if st.button(t("Stimme klonen", "Clone voice"), disabled=not voice_sample, key="clone_btn"):
                with st.spinner(t("Stimme wird geklont (10-30s)...", "Cloning voice (10-30s)...")):
                    try:
                        prev_id = st.session_state.get("custom_voice_id")
                        if prev_id:
                            voice.delete_voice(prev_id)
                        new_id = voice.clone_voice(
                            voice_sample.getvalue(),
                            clone_name.strip() or _default_clone_name,
                            file_name=voice_sample.name,
                        )
                        st.session_state["custom_voice_id"] = new_id
                        st.session_state["custom_voice_name"] = clone_name.strip() or _default_clone_name
                        cached_voices.clear()
                        st.success(t(
                            f"Stimme '{clone_name}' geklont. Wähl sie jetzt im Dropdown.",
                            f"Voice '{clone_name}' cloned. Pick it from the dropdown now.",
                        ))
                    except Exception as exc:
                        msg = str(exc)
                        resp = getattr(exc, "response", None)
                        if resp is not None:
                            try:
                                j = resp.json()
                                msg = j.get("detail", {}).get("message") or j.get("detail") or msg
                            except Exception:
                                pass
                        st.error(t(f"Klonen fehlgeschlagen: {msg}", f"Cloning failed: {msg}"))

    # Voice picker: ElevenLabs (full list + cloned voice if any) shown to Pro
    # users. Free-Tier (OpenAI) ueberspringt den Picker und nutzt Nova als
    # Default (beste DE-Voice laut Research).
    selected_voice_id = None
    if voice_backend == "elevenlabs":
        voices_data = cached_voices()
        if isinstance(voices_data, dict) and "_error" in voices_data:
            st.warning(t(
                f"Voices nicht geladen: {voices_data['_error']}",
                f"Voices not loaded: {voices_data['_error']}",
            ))
        elif voices_data:
            voice_options = {v["name"]: v["voice_id"] for v in voices_data}
            custom_id = st.session_state.get("custom_voice_id")
            custom_name = st.session_state.get("custom_voice_name")
            if custom_id and custom_name:
                custom_label = t(f"[Eigene] {custom_name}", f"[Custom] {custom_name}")
                voice_options = {custom_label: custom_id, **voice_options}
            label = st.selectbox(t("Stimme", "Voice"), list(voice_options.keys()), key="voice_select")
            selected_voice_id = voice_options[label]
        else:
            st.info(t("Keine Stimmen verfügbar.", "No voices available."))
    else:
        # Free-Tier nutzt fix Nova (OpenAI). Kein Picker um UX schlank zu halten.
        selected_voice_id = "nova"

    # Footage source. Short labels with captions so the choice fits in one
    # glance instead of forcing users to read four long sentences.
    FOOTAGE_STOCK = t("Stock", "Stock")
    FOOTAGE_UPLOAD = t("Upload", "Upload")
    FOOTAGE_AI_IMAGE = t("AI-Bild", "AI image")
    FOOTAGE_LIPSYNC = t("Lip-Sync", "Lip-sync")
    footage_mode = st.radio(
        t("Hintergrund", "Background"),
        options=[FOOTAGE_STOCK, FOOTAGE_UPLOAD, FOOTAGE_AI_IMAGE, FOOTAGE_LIPSYNC],
        captions=[
            t("Pexels-Match aus deinem Text (gratis)", "Pexels match from your text (free)"),
            t("Eigenes Video oder Bild (gratis)", "Your own video or image (free)"),
            t("AI generiert Hintergrund aus Text (Pro)", "AI generates background from text (Pro)"),
            t("Lippen deiner Person zum Voiceover (Pro)", "Lip-sync your person to the voiceover (Pro)"),
        ],
        horizontal=True,
        key="footage_mode_radio",
    )
    uploaded_media = None
    ai_prompt_override = ""
    if footage_mode == FOOTAGE_UPLOAD:
        uploaded_media = st.file_uploader(
            t(
                "Datei (Video: .mp4 .mov / Bild: .jpg .png .webp, max 50 MB)",
                "File (video: .mp4 .mov / image: .jpg .png .webp, max 50 MB)",
            ),
            type=["mp4", "mov", "m4v", "jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            key="upload_media_uploader",
            help=t(
                "Wird auf 9:16 gecroppt. Tipp: unter 10 MB = schneller Upload. Video lokal mit ffmpeg komprimieren falls zu groß.",
                "Will be cropped to 9:16. Tip: under 10 MB = faster upload. Compress locally with ffmpeg if too large.",
            ),
        )
        if uploaded_media is not None:
            _mb = uploaded_media.size / 1_000_000
            if _mb > 15:
                st.caption(t(
                    f"Datei: {_mb:.1f} MB. Tipp: unter 10 MB = deutlich schnellerer Upload.",
                    f"File: {_mb:.1f} MB. Tip: under 10 MB = much faster upload.",
                ))
        if uploaded_media is not None and uploaded_media.name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            st.caption(t(
                "Bild erkannt, bekommt einen langsamen Zoom (Ken-Burns).",
                "Image detected, gets a slow zoom (Ken Burns).",
            ))
    elif footage_mode == FOOTAGE_AI_IMAGE:
        ai_prompt_override = st.text_input(
            t(
                "Prompt (optional, leer = AI generiert eine passende Szene aus deinem Voiceover-Text)",
                "Prompt (optional, empty = AI generates a matching scene from your voiceover text)",
            ),
            placeholder=t(
                "Z.B.: Solo-Founder programmiert nachts, Neon-Stadt im Hintergrund",
                "E.g.: Solo founder coding at night, neon city in the background",
            ),
            key="ai_prompt_input",
        )
        st.caption(t(
            "Leer lassen für automatische Szenen-Erkennung. Eigenen englischen Prompt für maximale Kontrolle eintragen.",
            "Leave empty for automatic scene detection. Enter your own English prompt for full control.",
        ))
        if not is_pro:
            st.warning(t(
                "Nur für Pro. Trag oben einen Pro-Schlüssel ein oder kauf einen.",
                "Pro only. Enter a Pro key above or buy one.",
            ))
    elif footage_mode == FOOTAGE_LIPSYNC:
        uploaded_media = st.file_uploader(
            t(
                "Portrait-Video (.mp4 .mov, 5-30 Sek, Gesicht klar sichtbar, 9:16 bevorzugt)",
                "Portrait video (.mp4 .mov, 5-30 sec, face clearly visible, 9:16 preferred)",
            ),
            type=["mp4", "mov", "m4v"],
            accept_multiple_files=False,
            key="lipsync_uploader",
            help=t(
                "Tipp: unter 10 MB = schneller Upload. Video lokal komprimieren falls zu groß.",
                "Tip: under 10 MB = faster upload. Compress the video locally if too large.",
            ),
        )
        if uploaded_media is not None:
            _mb = uploaded_media.size / 1_000_000
            if _mb > 15:
                st.caption(t(
                    f"Datei: {_mb:.1f} MB. Tipp: unter 10 MB = deutlich schnellerer Upload.",
                    f"File: {_mb:.1f} MB. Tip: under 10 MB = much faster upload.",
                ))
        st.caption(t(
            "AI synchronisiert die Lippen deiner Person mit dem AI-Voiceover. Dauert 30-90 Sekunden. Lip-Sync ist rechenintensiv und zählt 7x ins Pro-Limit (~28 Lip-Syncs pro Zyklus möglich).",
            "AI syncs your person's lips with the AI voiceover. Takes 30-90 seconds. Lip-sync is compute-heavy and counts 7x against the Pro limit (~28 lip-syncs per cycle possible).",
        ))
        if not is_pro:
            st.warning(t(
                "Nur für Pro. Trag oben einen Pro-Schlüssel ein oder kauf einen.",
                "Pro only. Enter a Pro key above or buy one.",
            ))

    # Caption-Style: TikTok-typische Defaults (gelber Text, große Box unten).
    # Free-User bekommen diese fix, Pro-User können sie anpassen.
    caption_text_color = "#fbbf24"
    caption_bg_color = "#000000"
    caption_bg_alpha = 200
    caption_font_size = 80
    caption_position = "bottom"

    if is_pro:
        with st.expander(t("Caption-Style anpassen (Pro)", "Customize caption style (Pro)")):
            cs_col1, cs_col2 = st.columns(2)
            with cs_col1:
                caption_text_color = st.color_picker(
                    t("Text-Farbe", "Text color"), value=caption_text_color, key="caption_text_color"
                )
                caption_position = st.selectbox(
                    t("Position", "Position"),
                    options=["bottom", "center", "top"],
                    index=0,
                    key="caption_position",
                )
            with cs_col2:
                caption_bg_color = st.color_picker(
                    t("Box-Farbe (Hintergrund hinter Text)", "Box color (background behind text)"),
                    value=caption_bg_color, key="caption_bg_color",
                )
                caption_font_size = st.select_slider(
                    t("Font-Größe", "Font size"),
                    options=[48, 56, 64, 72, 80, 96],
                    value=caption_font_size,
                    key="caption_font_size",
                )
            caption_bg_alpha = st.slider(
                t("Box-Deckkraft", "Box opacity"),
                min_value=0, max_value=255, value=caption_bg_alpha, key="caption_bg_alpha",
                help=t("0 = keine Box (nur Text), 255 = volle Box.", "0 = no box (text only), 255 = full box."),
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

    _default_btn = t("Video generieren", "Generate video")
    _button_label = {
        FOOTAGE_STOCK: _default_btn,
        FOOTAGE_UPLOAD: t("Video aus Upload generieren", "Generate video from upload"),
        FOOTAGE_AI_IMAGE: t("AI-Bild + Video generieren", "Generate AI image + video"),
        FOOTAGE_LIPSYNC: t("Lip-Sync + Video generieren", "Generate lip-sync + video"),
    }.get(footage_mode, _default_btn)
    generate_btn = st.button(
        _button_label,
        type="primary",
        disabled=not ready_to_generate,
        key="generate_video_btn",
    )
    if not ready_to_generate:
        _missing = []
        if not text.strip():
            _missing.append(t("Voiceover-Text eintippen", "type voiceover text"))
        if not selected_voice_id:
            _missing.append(t("Stimme wählen", "pick a voice"))
        if needs_upload and uploaded_media is None:
            _missing.append(t("Datei hochladen", "upload a file"))
        if needs_pro and not is_pro:
            _missing.append(t("Pro-Schlüssel oben einlösen", "redeem a Pro key above"))
        if _missing:
            st.caption(t("Noch nötig: ", "Still needed: ") + ", ".join(_missing))

    if not is_pro:
        @st.cache_data(ttl=30, show_spinner=False)
        def _cached_free_quota():
            return rate_limit.get_free_quota()
        _used, _rem, _lim = _cached_free_quota()
        if _rem == 0:
            st.error(t(
                f"**Tageslimit erreicht.** Du hast {_used} von {_lim} kostenlosen Videos heute "
                f"verbraucht. Komm morgen wieder oder kauf einen Pro-Schlüssel (ab 2,99 EUR) "
                f"für unbegrenzte Generierungen.",
                f"**Daily limit reached.** You used {_used} of {_lim} free videos today. "
                f"Come back tomorrow or buy a Pro key (from €2.99) for unlimited generations.",
            ))
        elif _rem <= 2:
            st.warning(t(
                f"Nur noch **{_rem} von {_lim}** kostenlosen Videos heute übrig. "
                f"Für unbegrenzt: Pro ab 2,99 EUR oben auf der Seite.",
                f"Only **{_rem} of {_lim}** free videos left today. "
                f"For unlimited: Pro from €2.99 above on the page.",
            ))
        elif _rem < _lim:
            st.info(t(
                f"Free-Tier: {_used} von {_lim} kostenlosen Videos heute verbraucht. **{_rem} übrig.**",
                f"Free tier: {_used} of {_lim} free videos used today. **{_rem} left.**",
            ))

    # ----- Generate (video flow) -----
    if generate_btn:
        # Free-tier daily limit: only relevant for non-Pro users.
        if not is_pro:
            used, remaining, free_limit = rate_limit.get_free_quota()
            if remaining <= 0:
                st.error(t(
                    f"Tageslimit von {free_limit} kostenlosen Videos erreicht. "
                    "Komm morgen wieder oder kauf einen Pro-Schlüssel für unbegrenzte Generierungen.",
                    f"Daily limit of {free_limit} free videos reached. "
                    "Come back tomorrow or buy a Pro key for unlimited generations.",
                ))
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
            progress = st.progress(0, text=t("Starte...", "Starting..."))
            try:
                strip_watermark = is_pro and not activation_blocked
                if activation_blocked:
                    st.warning(t(
                        "Schlüssel bereits verbraucht. Dieses Video bekommt Wasserzeichen.",
                        "Key already used. This video will have a watermark.",
                    ))

                if voice_backend == "elevenlabs":
                    progress.progress(10, text=t(
                        "Voiceover generieren mit ElevenLabs...",
                        "Generating voiceover with ElevenLabs...",
                    ))
                    audio_bytes, alignment = voice.generate_voiceover_with_timestamps(
                        text.strip(), selected_voice_id
                    )
                else:
                    progress.progress(10, text=t(
                        "Voiceover generieren mit OpenAI...",
                        "Generating voiceover with OpenAI...",
                    ))
                    audio_bytes = voice.generate(text.strip(), voice_backend, selected_voice_id)
                    alignment = {}
                audio_path = tmp_path / "voice.mp3"
                audio_path.write_bytes(audio_bytes)

                if footage_mode == FOOTAGE_AI_IMAGE:
                    if ai_prompt_override.strip():
                        prompt = ai_prompt_override.strip()
                    else:
                        progress.progress(30, text=t(
                            "Visuelle Szene aus Voiceover-Text ableiten...",
                            "Deriving visual scene from voiceover text...",
                        ))
                        prompt = ai_image.text_to_visual_prompt(text.strip())
                    progress.progress(40, text=t("AI-Bild wird generiert...", "Generating AI image..."))
                    video_path = tmp_path / "ai.png"
                    ai_image.generate_image(prompt, video_path, aspect_ratio="9:16")
                elif footage_mode == FOOTAGE_LIPSYNC:
                    progress.progress(35, text=t(
                        "Portrait-Video wird hochgeladen...",
                        "Uploading portrait video...",
                    ))
                    ext = Path(uploaded_media.name).suffix.lower() or ".mp4"
                    raw_path = tmp_path / f"raw{ext}"
                    raw_path.write_bytes(uploaded_media.getvalue())
                    progress.progress(50, text=t(
                        "Lippen werden synchronisiert, kann 30-90s dauern...",
                        "Syncing lips, may take 30-90s...",
                    ))
                    video_path = tmp_path / "lipsynced.mp4"
                    ai_image.lipsync_video(raw_path, audio_path, video_path)
                elif uploaded_media is not None:
                    progress.progress(40, text=t(
                        "Hochgeladenes Material wird verarbeitet...",
                        "Processing uploaded media...",
                    ))
                    ext = Path(uploaded_media.name).suffix.lower() or ".mp4"
                    video_path = tmp_path / f"upload{ext}"
                    video_path.write_bytes(uploaded_media.getvalue())
                else:
                    progress.progress(40, text=t(
                        "Stock-Footage von Pexels suchen...",
                        "Searching stock footage on Pexels...",
                    ))
                    video_path = tmp_path / "stock.mp4"
                    keywords = stock.extract_keywords(text)
                    query = " ".join(keywords) if keywords else "abstract background"
                    video_url = stock.pick_video_url(query)
                    if not video_url:
                        video_url = stock.pick_video_url("abstract background")
                    if not video_url:
                        st.error(t(
                            "Kein Stock-Video gefunden. Versuch einen anderen Text.",
                            "No stock video found. Try different text.",
                        ))
                        st.stop()
                    stock.download(video_url, video_path)

                progress.progress(70, text=t("Video wird komponiert...", "Composing video..."))
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

                progress.progress(100, text=t("Fertig.", "Done."))
                if not is_pro:
                    rate_limit.consume_free_quota()
                video_bytes = output_path.read_bytes()
                st.video(video_bytes, autoplay=False)
                st.download_button(
                    t("Video herunterladen", "Download video"),
                    video_bytes,
                    file_name="voiceclip.mp4",
                    mime="video/mp4",
                )
                if strip_watermark:
                    if consumed_one_shot:
                        st.success(t(
                            "Pro-Export ohne Wasserzeichen. Dein 1-Video-Schlüssel ist nun verbraucht.",
                            "Pro export without watermark. Your 1-video key is now used up.",
                        ))
                    else:
                        st.success(t(
                            "Pro-Export ohne Wasserzeichen.",
                            "Pro export without watermark.",
                        ))
                else:
                    st.info(t(
                        "Wasserzeichen ist im Video. Pro-Abo: kein Wasserzeichen, unlimitiert.",
                        "Watermark is in the video. Pro subscription: no watermark, unlimited.",
                    ))
                    if _pro_url:
                        _pro_cta_label = t("Pro-Abo 8,99 €/Mo →", "Pro subscription €8.99/mo →")
                        st.markdown(
                            f"""
                            <a href="{_pro_url}" target="_blank"
                               style="display: inline-block; padding: 0.6em 1.4em;
                                      border-radius: 999px; border: 2px solid #8b5cf6;
                                      background: transparent; color: #8b5cf6;
                                      font-weight: 700; font-size: 0.95em;
                                      text-decoration: none; margin-top: 0.4em;">
                                {_pro_cta_label}
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
            except Exception as exc:
                st.error(t(f"Fehler: {exc}", f"Error: {exc}"))


# ============================================================
# Tab 2: Bild verbessern (Pro)
# ============================================================
with tab_enhance:
    st.markdown(t("**AI Bild-Enhancer**", "**AI Image Enhancer**"))
    st.caption(t(
        "Lade ein Bild hoch, AI macht es schärfer und auf 2x Auflösung. "
        "Kein Voiceover, kein Video, nur das verbesserte Bild als PNG-Download.",
        "Upload an image, AI makes it sharper at 2x resolution. "
        "No voiceover, no video, just the enhanced image as a PNG download.",
    ))
    enhance_img = st.file_uploader(
        t(
            "Bild zum Verbessern (.jpg .png .webp, max 10 MB)",
            "Image to enhance (.jpg .png .webp, max 10 MB)",
        ),
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        key="enhance_uploader",
    )
    if not is_pro:
        st.warning(t(
            "Funktion nur für Pro. Trag oben einen Pro-Schlüssel ein oder kauf einen.",
            "Pro only. Enter a Pro key above or buy one.",
        ))
    enhance_btn = st.button(
        t("Bild verbessern", "Enhance image"),
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
            progress = st.progress(0, text=t("Starte...", "Starting..."))
            try:
                if activation_blocked:
                    st.warning(t(
                        "Key bereits verbraucht. Bild-Enhance trotzdem, aber kein neuer Slot konsumiert.",
                        "Key already used. Image will still be enhanced but no new slot consumed.",
                    ))
                progress.progress(20, text=t("Bild wird hochgeladen...", "Uploading image..."))
                ext = Path(enhance_img.name).suffix.lower() or ".png"
                raw_path = tmp_path / f"raw{ext}"
                raw_path.write_bytes(enhance_img.getvalue())

                progress.progress(40, text=t("Bild wird verbessert (10-30s)...", "Enhancing image (10-30s)..."))
                enhanced_path = tmp_path / "enhanced.png"
                ai_image.enhance_image(raw_path, enhanced_path, scale=2)

                progress.progress(100, text=t("Fertig.", "Done."))
                img_bytes = enhanced_path.read_bytes()
                st.image(
                    img_bytes,
                    caption=t("Verbessertes Bild (2x Auflösung)", "Enhanced image (2x resolution)"),
                    use_column_width=True,
                )
                st.download_button(
                    t("Bild herunterladen", "Download image"),
                    img_bytes,
                    file_name="enhanced.png",
                    mime="image/png",
                    key="enhance_download_btn",
                )
                if consumed_one_shot:
                    st.success(t(
                        "Bild-Enhance fertig. Dein 1-Use-Key ist nun verbraucht.",
                        "Image enhanced. Your 1-use key is now used up.",
                    ))
                else:
                    st.success(t("Bild-Enhance fertig.", "Image enhanced."))
            except Exception as exc:
                st.error(t(f"Fehler: {exc}", f"Error: {exc}"))


# ----- Footer -----
st.divider()
_footer_intro = t(
    "VoiceClip. closelyst. MVP-Version.",
    "VoiceClip. closelyst. MVP version.",
)
_footer_powered = t(
    "Powered by",
    "Powered by",
)
_footer_pro_voice = t("Pro-Voiceover, Voice-Cloning", "Pro voiceover, voice cloning")
_footer_free_voice = t("Free-Voiceover", "Free voiceover")
_footer_stock = t("Stock-Footage", "Stock footage")
_footer_and = t("und", "and")
_legal_note = t(
    "Rechtliche Hinweise nur auf Deutsch verfügbar.",
    "Legal documents available in German only.",
)
st.markdown(
    f"""
    <style>
    .footer-links a {{ text-decoration: none; color: inherit; }}
    .footer-links a:hover {{ text-decoration: underline; }}
    </style>
    <div class="footer-links" style="font-size: 0.875em; color: rgba(49, 51, 63, 0.6);">
    {_footer_intro}
    {_footer_powered} <a href="https://elevenlabs.io" target="_blank">ElevenLabs</a> ({_footer_pro_voice}),
    <a href="https://openai.com" target="_blank">OpenAI</a> ({_footer_free_voice}),
    <a href="https://www.pexels.com" target="_blank">Pexels</a> ({_footer_stock}),
    <a href="https://replicate.com" target="_blank">Replicate</a> (Flux Schnell, Clarity Upscaler, LatentSync)
    {_footer_and} <a href="https://polar.sh" target="_blank">Polar</a> (Payments).
    </div>
    <div class="footer-links" style="font-size: 0.875em; color: rgba(49, 51, 63, 0.6); margin-top: 0.5em;">
    <a href="/Impressum" target="_self">Impressum</a> |
    <a href="/Datenschutz" target="_self">Datenschutz</a> |
    <a href="/AGB" target="_self">AGB</a> |
    <a href="/Widerrufsbelehrung" target="_self">Widerrufsbelehrung</a>
    <span style="margin-left: 0.5em; opacity: 0.6;">({_legal_note})</span>
    </div>
    """,
    unsafe_allow_html=True,
)
