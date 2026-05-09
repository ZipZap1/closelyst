"""Impressum page. Required under § 5 DDG."""
import streamlit as st

st.set_page_config(page_title="Impressum - VoiceClip", page_icon="assets/icon.png")

st.title("Impressum")

st.markdown(
    """
**Angaben gemäß § 5 DDG**

Haci Ibrahim Dogan<br>
Holunderweg 3<br>
44869 Bochum<br>
Deutschland

**Kontakt**

Telefon: +49 1551 0899025<br>
E-Mail: info@pruefungscoach.tech

**Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV**

Haci Ibrahim Dogan<br>
(Anschrift wie oben)

**EU-Streitschlichtung**

Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
https://ec.europa.eu/consumers/odr/

Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
Verbraucherschlichtungsstelle teilzunehmen.
    """,
    unsafe_allow_html=True,
)
