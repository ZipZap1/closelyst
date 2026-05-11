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
.vc-lang {{
    position: fixed; top: 0.6rem; right: 0.8rem; z-index: 9999;
    display: flex; gap: 2px;
    background: rgba(255,255,255,0.96);
    padding: 3px; border-radius: 999px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.vc-lang a {{
    padding: 4px 11px; border-radius: 999px;
    text-decoration: none !important; color: #64748b;
    font-size: 12px; font-weight: 700;
    letter-spacing: 0.02em;
    transition: all 0.12s;
}}
.vc-lang a:hover {{ color: #0f172a; }}
.vc-lang a.active {{
    background: #8b5cf6; color: white !important;
}}
@media (prefers-color-scheme: dark) {{
    .vc-lang {{ background: rgba(30,30,30,0.92); }}
    .vc-lang a {{ color: #cbd5e1; }}
    .vc-lang a:hover {{ color: white; }}
}}
</style>
<div class="vc-lang">
    <a href="?lang=de" class="{de_active}" target="_self">DE</a>
    <a href="?lang=en" class="{en_active}" target="_self">EN</a>
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
