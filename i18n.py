"""Lightweight i18n: query-param + session-state language switching.

Usage:
    from i18n import t, render_lang_toggle, get_lang

    render_lang_toggle()  # top of every page
    st.write(t("Hallo", "Hello"))

DE is the default. EN-toggle is forward-looking for international TikTok
reach. Legal pages stay DE-only with an EN disclaimer banner.
"""
import streamlit as st

LANGUAGES = ("de", "en")
DEFAULT_LANG = "de"


def get_lang():
    """Resolve current language. Query param wins (shareable URLs), falls back
    to session state, then DEFAULT_LANG."""
    try:
        qp = st.query_params.get("lang")
    except Exception:
        qp = None
    if qp in LANGUAGES:
        st.session_state["lang"] = qp
        return qp
    return st.session_state.get("lang", DEFAULT_LANG)


def t(de, en):
    """Inline translation helper. Pass both strings, returns the active one.

    Keeps source and target text next to each other in code, no central dict
    to keep in sync. Trade-off: harder to extract for pro translation later.
    Acceptable for a solo dev with a small surface area.
    """
    return de if get_lang() == "de" else en


def render_lang_toggle():
    """Fixed top-right DE/EN pill. Uses anchor links to set ?lang=X which
    Streamlit reads on rerun. Persists via session state across page nav."""
    current = get_lang()
    de_active = "active" if current == "de" else ""
    en_active = "active" if current == "en" else ""
    st.markdown(
        f"""
<style>
/* Streamlit's eigenes 3-Punkte-Menue sitzt oben rechts und faengt
   sonst die Taps auf Mobile ab. Aus und Toggle ownt den Platz. */
[data-testid="stMainMenu"] {{ display: none !important; }}

.vc-lang {{
    position: fixed; top: 0.6rem; right: 0.8rem;
    /* Max-Int z-index, sicher ueber jedem Streamlit-Layer */
    z-index: 2147483647;
    display: flex; gap: 2px;
    background: rgba(255,255,255,0.96);
    padding: 4px; border-radius: 999px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.18);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    /* Verhindert, dass iOS Long-Press-Selektion den Tap killt */
    -webkit-user-select: none; user-select: none;
    -webkit-tap-highlight-color: rgba(139, 92, 246, 0.25);
}}
.vc-lang a {{
    /* Apple HIG: min 44px Touch-Target. 13px Font + Padding kommt hin. */
    min-width: 44px; min-height: 32px;
    display: inline-flex; align-items: center; justify-content: center;
    padding: 6px 14px; border-radius: 999px;
    text-decoration: none !important; color: #64748b;
    font-size: 13px; font-weight: 700;
    letter-spacing: 0.04em;
    transition: all 0.12s;
    cursor: pointer;
    pointer-events: auto;
    touch-action: manipulation;
}}
.vc-lang a:hover {{ color: #0f172a; }}
.vc-lang a:active {{ transform: scale(0.95); }}
.vc-lang a.active {{
    background: #8b5cf6; color: white !important;
}}
@media (prefers-color-scheme: dark) {{
    .vc-lang {{ background: rgba(30,30,30,0.92); }}
    .vc-lang a {{ color: #cbd5e1; }}
    .vc-lang a:hover {{ color: white; }}
}}
@media (max-width: 640px) {{
    /* Auf Mobile etwas tiefer, damit kein Konflikt mit Streamlit-Header */
    .vc-lang {{ top: 0.5rem; right: 0.5rem; }}
    .vc-lang a {{ min-width: 48px; min-height: 36px; padding: 7px 16px; font-size: 14px; }}
}}
</style>
<div class="vc-lang">
    <a href="?lang=de" class="{de_active}" target="_self" rel="nofollow">DE</a>
    <a href="?lang=en" class="{en_active}" target="_self" rel="nofollow">EN</a>
</div>
""",
        unsafe_allow_html=True,
    )


def render_en_only_disclaimer_for_legal():
    """Banner shown on legal pages when EN is selected. Legal docs stay DE
    because German law applies; this just tells EN visitors why."""
    if get_lang() != "en":
        return
    st.info(
        "This legal document is only available in German. The German "
        "version is the authoritative legal text under German law."
    )
