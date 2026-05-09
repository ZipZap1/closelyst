"""Impressum page. Required under § 5 DDG."""
import streamlit as st

st.set_page_config(page_title="Impressum - VoiceClip", page_icon="assets/icon.png")

st.title("Impressum")

st.markdown(
    """
**Angaben gemäß § 5 DDG**

Haci Ibrahim Dogan
Holunderweg 3
44869 Bochum
Deutschland

**Kontakt**

Telefon: +49 1551 0899025
E-Mail: info@pruefungscoach.tech

**Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV**

Haci Ibrahim Dogan
(Anschrift wie oben)

**EU-Streitschlichtung**

Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
https://ec.europa.eu/consumers/odr/

Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
Verbraucherschlichtungsstelle teilzunehmen.
    """
)
