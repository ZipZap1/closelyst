"""Datenschutzerklärung. Required under DSGVO Art. 13/14.

Placeholder content. Replace with output from a generator like
e-recht24.de or datenschutz-generator.de before going public.
The list of third-party services below is the actual VoiceClip stack
and should be carried over to the generator output.
"""
import streamlit as st

st.set_page_config(page_title="Datenschutz - VoiceClip", page_icon="assets/icon.png")

st.title("Datenschutzerklärung")

st.markdown(
    """
**Stand:** 09.05.2026

## 1. Verantwortlicher

Haci Ibrahim Dogan
Holunderweg 3
44869 Bochum
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

- **ElevenLabs Inc., USA** (Sprachsynthese und Voice-Cloning): dein eingegebener
  Text, optional dein Voice-Sample beim Cloning
- **Pexels GmbH, Deutschland** (Stock-Footage-Suche): die Suchwörter
- **Replicate Inc., USA** (KI-Bildgenerierung, Bild-Verbesserung, Lip-Sync):
  dein Prompt, ggf. hochgeladenes Bild oder Video, ggf. Audio-Datei
- **Lemon Squeezy (UAB Squeezy, Litauen / USA)** (Zahlungsabwicklung als
  Merchant of Record): Email, Rechnungs- und Zahlungsdaten

Übertragungen in die USA basieren auf Standardvertragsklauseln nach
Art. 46 DSGVO.

## 5. License-Key-Verarbeitung

Wenn du einen License-Key eingibst, wird dieser an Lemon Squeezy zur
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

Zuständige Aufsichtsbehörde:
Landesbeauftragte für Datenschutz und Informationsfreiheit Nordrhein-Westfalen
https://www.ldi.nrw.de

## 9. Änderungen

Wir behalten uns vor, diese Datenschutzerklärung anzupassen, um sie an
geänderte Rechtslage oder Funktionen anzupassen.

---

*Hinweis: Dies ist ein Platzhalter-Text auf Basis des aktuellen Tech-Stacks.
Vor Veröffentlichung über einen Generator wie [datenschutz-generator.de](https://datenschutz-generator.de)
oder [eRecht24](https://www.e-recht24.de/datenschutzerklaerung-muster.html) prüfen
und ergänzen lassen.*
    """
)
