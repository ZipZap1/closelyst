"""Impressum page. Required under § 5 DDG."""
import sys
from pathlib import Path

import streamlit as st

# Parent-dir auf sys.path damit i18n.py importierbar ist (Streamlit pages
# laufen in pages/ aber das Modul liegt ein Verzeichnis darueber).
sys.path.insert(0, str(Path(__file__).parent.parent))
from i18n import render_lang_toggle, render_en_only_disclaimer_for_legal

st.set_page_config(page_title="Impressum - VoiceClip", page_icon="assets/icon.png")

render_en_only_disclaimer_for_legal()

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

**Umsatzsteuer-Identifikationsnummer**

Eine Umsatzsteuer-Identifikationsnummer wird nicht geführt. Der Anbieter
ist Kleinunternehmer im Sinne des § 19 UStG und weist daher keine
Umsatzsteuer aus.

**Redaktionell verantwortlich (§ 18 Abs. 2 MStV)**

Haci Ibrahim Dogan<br>
Holunderweg 3<br>
44869 Bochum

**EU-Streitschlichtung**

Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
https://ec.europa.eu/consumers/odr/

Der Anbieter ist nicht bereit oder verpflichtet, an Streitbeilegungsverfahren
vor einer Verbraucherschlichtungsstelle teilzunehmen.

---

## Haftungsausschluss

**Haftung für Inhalte**

Die Inhalte dieser Seiten wurden mit größtmöglicher Sorgfalt erstellt.
Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte kann
jedoch keine Gewähr übernommen werden. Als Diensteanbieter ist der
Anbieter gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach
den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG ist der
Anbieter als Diensteanbieter jedoch nicht verpflichtet, übermittelte
oder gespeicherte fremde Informationen zu überwachen oder nach Umständen
zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.

Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen
nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine
diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis
einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden entsprechender
Rechtsverletzungen wird der Anbieter diese Inhalte umgehend entfernen.

**Haftung für Links**

Diese Seiten enthalten gegebenenfalls Links zu externen Websites Dritter,
auf deren Inhalte der Anbieter keinen Einfluss hat. Deshalb kann für
diese fremden Inhalte auch keine Gewähr übernommen werden. Für die
Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder
Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum
Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft.
Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar.

Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch
ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht zumutbar. Bei
Bekanntwerden von Rechtsverletzungen werden derartige Links umgehend
entfernt.

**Urheberrecht**

Die durch den Anbieter erstellten Inhalte und Werke auf diesen Seiten
unterliegen dem deutschen Urheberrecht. Die Vervielfältigung,
Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der
Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des
jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite
sind nur für den privaten, nicht kommerziellen Gebrauch gestattet.

Soweit die Inhalte auf dieser Seite nicht vom Anbieter erstellt wurden,
werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte
Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine
Urheberrechtsverletzung aufmerksam werden, wird um einen entsprechenden
Hinweis gebeten. Bei Bekanntwerden von Rechtsverletzungen werden
derartige Inhalte umgehend entfernt.
    """,
    unsafe_allow_html=True,
)

# Sprach-Toggle fest am Seitenende, im Dokumentfluss
render_lang_toggle()
