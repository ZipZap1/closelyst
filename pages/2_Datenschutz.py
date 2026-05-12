"""Datenschutzerklärung. Required under DSGVO Art. 13/14.

Placeholder content. Replace with output from a generator like
e-recht24.de or datenschutz-generator.de before going public.
The list of third-party services below is the actual VoiceClip stack
and should be carried over to the generator output.
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from i18n import render_lang_toggle, render_en_only_disclaimer_for_legal

st.set_page_config(page_title="Datenschutz - VoiceClip", page_icon="assets/icon.png")

render_en_only_disclaimer_for_legal()

st.title("Datenschutzerklärung")

st.markdown(
    """
**Stand:** 10.05.2026

## 1. Verantwortlicher

Haci Ibrahim Dogan<br>
Holunderweg 3<br>
44869 Bochum<br>
E-Mail: info@pruefungscoach.tech

## 2. Allgemeine Hinweise

Diese Datenschutzerklärung informiert dich darüber, wie wir personenbezogene
Daten verarbeiten, wenn du VoiceClip nutzt. VoiceClip ist eine Web-App zum
Erstellen von TikTok-Voiceover-Videos.

## 3. Hosting

Die App läuft auf **Streamlit Community Cloud** (Snowflake Inc., USA). Beim
Aufruf werden technisch notwendige Verbindungsdaten (IP-Adresse, Browser,
Zugriffszeit) verarbeitet. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO
(berechtigtes Interesse am Betrieb der App).

## 4. Eingesetzte Dienste

Wenn du VoiceClip nutzt, werden je nach Funktion Daten an folgende
Dienstleister übertragen:

- **ElevenLabs Inc., USA** (Sprachsynthese und Voice-Cloning, Pro-Tier):
  dein eingegebener Text, optional dein Voice-Sample beim Cloning
- **OpenAI, L.L.C., USA** (Sprachsynthese im Free-Tier über tts-1-hd und
  gpt-4o-mini-tts): dein eingegebener Text wird an OpenAI übermittelt und
  in Audio umgewandelt. OpenAI speichert API-Inputs laut eigener
  API-Datenrichtlinie maximal 30 Tage und nutzt sie nicht zum Training.
- **Pexels GmbH, Deutschland** (Stock-Footage-Suche): die Suchwörter
- **Replicate Inc., USA** (KI-Bildgenerierung, Bild-Verbesserung, Lip-Sync):
  dein Prompt, ggf. hochgeladenes Bild oder Video, ggf. Audio-Datei
- **Polar Software, Inc., USA** (Zahlungsabwicklung als
  Merchant of Record): Email, Rechnungs- und Zahlungsdaten
- **Supabase Inc., USA** (Datenbank für Free-Tier-Rate-Limiting):
  ein Hash aus IP-Adresse und Browser-User-Agent, sowie Datum und
  Anzahl deiner Free-Tier-Generierungen. Die rohe IP wird nicht
  gespeichert; sie wird vor dem Speichern via SHA-256 zu einem
  pseudonymen Fingerprint reduziert. Rechtsgrundlage: Art. 6 Abs. 1
  lit. f DSGVO (berechtigtes Interesse an Missbrauchsschutz und
  Kostenkontrolle). Aufbewahrung: 30 Tage rollierend.
- **Umami Software, Inc., USA** (Web-Analyse via Umami Cloud,
  cloud.umami.is): aggregierte Nutzungsdaten zum Verständnis,
  welche Seiten besucht werden. Erfasst werden: besuchte URL,
  Referrer, Browser-Typ, Geräteklasse, ungefähre Region anhand der
  IP-Adresse. Umami setzt **keine Cookies**, speichert **keine
  IP-Adressen oder personenbezogenen Daten** und verwendet kein
  Fingerprinting. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO
  (berechtigtes Interesse an Reichweitenmessung und Verbesserung
  des Angebots). Da keine personenbezogenen Daten erhoben werden,
  ist keine Einwilligung nach § 25 TDDDG erforderlich. Aufbewahrung
  gemäß Umami-Cloud-Richtlinien.

Übertragungen in die USA basieren auf Standardvertragsklauseln nach
Art. 46 DSGVO.

## 5. Lizenz-Schlüssel-Verarbeitung

Wenn du einen Lizenz-Schlüssel eingibst, wird dieser an Polar zur
Validierung übertragen. Wir speichern den Key während deiner Session im
Browser-Speicher von Streamlit. Es findet keine dauerhafte Speicherung
auf unserer Seite statt.

## 6. Hochgeladene Dateien

Audio, Bilder und Videos, die du hochlädst, werden zur Verarbeitung
temporär an Replicate übertragen und nach Abschluss der Generierung
auf deren Servern gemäß deren Aufbewahrungsrichtlinien gelöscht. Wir
selbst speichern deine Uploads nicht dauerhaft.

## 7. Cookies

VoiceClip setzt nur technisch notwendige Session-Cookies, die für den
Betrieb der App erforderlich sind. Es findet keine Werbe- oder Analyse-
Tracking statt. Eine Einwilligung nach § 25 TDDDG ist daher nicht
erforderlich.

## 8. Deine Rechte

Du hast das Recht auf Auskunft (Art. 15), Berichtigung (Art. 16), Löschung
(Art. 17), Einschränkung (Art. 18), Datenübertragbarkeit (Art. 20),
Widerspruch (Art. 21) und Beschwerde bei einer Aufsichtsbehörde (Art. 77 DSGVO).

Zuständige Aufsichtsbehörde:<br>
Landesbeauftragte für Datenschutz und Informationsfreiheit Nordrhein-Westfalen<br>
https://www.ldi.nrw.de

## 9. Änderungen

Wir behalten uns vor, diese Datenschutzerklärung anzupassen, um sie an
geänderte Rechtslage oder Funktionen anzupassen.

---

*Hinweis: Dies ist ein Platzhalter-Text auf Basis des aktuellen Tech-Stacks.
Vor Veröffentlichung über einen Generator wie [datenschutz-generator.de](https://datenschutz-generator.de)
oder [eRecht24](https://www.e-recht24.de/datenschutzerklaerung-muster.html) prüfen
und ergänzen lassen.*
    """,
    unsafe_allow_html=True,
)

# Sprach-Toggle fest am Seitenende, im Dokumentfluss
render_lang_toggle()
