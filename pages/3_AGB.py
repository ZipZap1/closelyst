"""Allgemeine Geschäftsbedingungen für VoiceClip Pro-Käufe."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from i18n import render_lang_toggle, render_en_only_disclaimer_for_legal

st.set_page_config(page_title="AGB - VoiceClip", page_icon="assets/icon.png")

render_en_only_disclaimer_for_legal()

st.title("Allgemeine Geschäftsbedingungen")

st.markdown(
    """
**Stand:** 10.05.2026

## 1. Geltungsbereich, Vertragssprache, Speicherung des Vertragstextes

### 1.1 Geltungsbereich

Diese AGB gelten für alle Verträge zwischen Haci Ibrahim Dogan, Holunderweg 3,
44869 Bochum (im Folgenden "Anbieter") und dem Nutzer (im Folgenden "Kunde")
über die Nutzung der Web-App **VoiceClip**. Maßgeblich ist die zum Zeitpunkt
des Vertragsschlusses gültige Fassung.

### 1.2 Vertragssprache

Vertragssprache ist ausschließlich Deutsch. Übersetzungen dieser AGB in
andere Sprachen dienen nur der Information; im Zweifel ist die deutsche
Fassung maßgeblich.

### 1.3 Speicherung des Vertragstextes

Der Vertragstext (diese AGB sowie die Bestelldaten) wird vom Anbieter
nicht gespeichert und ist nach Abschluss des Bestellvorgangs nicht mehr
über den Anbieter abrufbar. Der Kunde kann diese AGB jederzeit auf
dieser Webseite einsehen, herunterladen und ausdrucken. Die Bestelldaten
werden dem Kunden zudem per E-Mail durch Polar als
Auftragsverarbeiter zugesandt.

## 2. Vertragsgegenstand

VoiceClip ist eine Web-Anwendung zur Erstellung von TikTok-tauglichen
Voiceover-Videos. Die Grundfunktionen sind kostenlos. Optional können
folgende kostenpflichtige Leistungen erworben werden:

- **Wasserzeichen entfernen** (Einmalkauf): Entfernt das Wasserzeichen aus
  einem einzelnen Export
- **VoiceClip Pro (Monatsabo)**: Entfernt das Wasserzeichen dauerhaft
  und schaltet erweiterte Funktionen frei (Voice-Cloning, KI-Bilder,
  Bild-Verbesserung, Lip-Sync) im Rahmen monatlicher Nutzungs-Limits

## 3. Vertragsschluss

Der Kauf eines kostenpflichtigen Produkts erfolgt über die Checkout-Seite
des Zahlungsdienstleisters Polar. Der Vertrag kommt zustande, wenn
der Kunde

1. das gewünschte Produkt auswählt,
2. diese AGB durch Setzen der vorgesehenen Bestätigung (Checkbox oder
   gleichwertige Erklärung) annimmt,
3. die für die Bereitstellung digitaler Inhalte erforderliche ausdrückliche
   Zustimmung erteilt (siehe § 6),
4. den Bestellvorgang durch Klick auf den Bestellbutton abschließt.

Der Kunde erhält im Anschluss eine Bestätigungs-E-Mail mit Lizenz-Schlüssel.
Diese E-Mail enthält zugleich die Bestätigung des Vertrags in Textform
gemäß § 312f BGB.

## 4. Zahlungsabwicklung über Polar

Die Zahlungsabwicklung erfolgt ausschließlich über **Polar Software, Inc.
(USA)** als Merchant of Record. Polar ist der formale Verkäufer gegenüber
dem Kunden, übernimmt Steuerabführung, USt und Rechnungsstellung. Die AGB
und Datenschutzbestimmungen von Polar (https://polar.sh/legal) ergänzen
diese AGB für den Zahlungsvorgang. Die Datenübermittlung in die USA
erfolgt auf Basis der Standardvertragsklauseln nach Art. 46 DSGVO.

## 5. Preise

Die jeweils aktuellen Preise werden auf der Polar-Checkout-Seite
angezeigt. Alle Preise sind Bruttopreise inklusive eventuell anfallender
Umsatzsteuer.

## 6. Widerrufsrecht für Verbraucher

### 6.1 Widerrufsbelehrung

Verbrauchern steht grundsätzlich ein Widerrufsrecht zu.

**Widerrufsrecht:** Sie haben das Recht, binnen vierzehn Tagen ohne Angabe
von Gründen diesen Vertrag zu widerrufen. Die Widerrufsfrist beträgt
vierzehn Tage ab dem Tag des Vertragsabschlusses.

Um Ihr Widerrufsrecht auszuüben, müssen Sie uns

> Haci Ibrahim Dogan, Holunderweg 3, 44869 Bochum,
> E-Mail: info@pruefungscoach.tech, Telefon: +49 1551 0899025

mittels einer eindeutigen Erklärung (z.B. ein mit der Post versandter
Brief oder E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen,
informieren. Sie können dafür das beigefügte Muster-Widerrufsformular
verwenden, das jedoch nicht vorgeschrieben ist.

Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung
über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist
absenden.

**Folgen des Widerrufs:** Wenn Sie diesen Vertrag widerrufen, haben wir
Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, unverzüglich und
spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die
Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist.

### 6.2 Wasserzeichen entfernen (digitaler Inhalt) – vorzeitiges Erlöschen

Beim Einmalkauf "Wasserzeichen entfernen" handelt es sich um einen
digitalen Inhalt im Sinne des § 327 Abs. 2 BGB, der dem Kunden mit
einem Lizenz-Schlüssel bereitgestellt wird. Das Widerrufsrecht erlischt
nach § 356 Abs. 5 BGB vorzeitig, wenn der Anbieter mit der
Vertragsausführung begonnen hat, nachdem der Kunde

- ausdrücklich zugestimmt hat, dass der Anbieter mit der Ausführung des
  Vertrags vor Ablauf der Widerrufsfrist beginnt, **und**
- seine Kenntnis davon bestätigt hat, dass er durch seine Zustimmung mit
  Beginn der Ausführung des Vertrags sein Widerrufsrecht verliert, **und**
- der Anbieter dem Kunden eine Bestätigung des Vertrags und der erteilten
  Erklärungen in Textform zur Verfügung gestellt hat.

Der Kunde erteilt diese Zustimmung und Kenntnisbestätigung durch das
Setzen der entsprechenden Checkbox auf der Checkout-Seite. Mit der
Bereitstellung des Lizenz-Schlüssels per E-Mail beginnt die Vertragsausführung,
und das Widerrufsrecht erlischt zu diesem Zeitpunkt.

### 6.3 Pro-Abo (digitale Dienstleistung) – Widerrufsrecht und Wertersatz

VoiceClip Pro stellt eine fortlaufende digitale Dienstleistung im Sinne
des § 327 Abs. 3 BGB dar. Das Widerrufsrecht erlischt hier nicht durch
die bloße Bereitstellung des Lizenz-Schlüssels, sondern besteht innerhalb
der vollen vierzehntägigen Frist auch dann fort, wenn der Kunde die
Dienstleistung in dieser Zeit bereits genutzt hat.

Hat der Kunde verlangt, dass die Dienstleistung während der
Widerrufsfrist beginnen soll, schuldet er dem Anbieter im Falle des
Widerrufs einen anteiligen Wertersatz für die bis zum Widerruf
erbrachte Leistung gemäß § 357a Abs. 2 BGB. Der Wertersatz wird auf
Grundlage des vereinbarten Gesamtpreises zeitanteilig berechnet.

Beispiel: Bei einer Pro-Abo-Gebühr von 8,99 € pro Monat (30 Tage)
beträgt der tägliche Wertersatz rund 0,30 €. Hat der Kunde die
Dienstleistung 5 Tage genutzt und widerruft am 6. Tag, beträgt der
Wertersatz rund 1,50 €; der Anbieter erstattet die Differenz von
rund 7,49 €.

Eine Wertersatzpflicht besteht nur, wenn der Anbieter den Kunden
ordnungsgemäß über das Widerrufsrecht und die Wertersatzpflicht
belehrt und der Kunde ausdrücklich zugestimmt hat, dass die Ausführung
vor Ablauf der Widerrufsfrist beginnt. Beides erfolgt durch das Setzen
der vorgesehenen Checkboxen auf der Checkout-Seite.

### 6.4 Muster-Widerrufsformular

Wenn Sie den Vertrag widerrufen wollen, können Sie dieses Formular
ausfüllen und an uns zurücksenden:

> An Haci Ibrahim Dogan, Holunderweg 3, 44869 Bochum,
> E-Mail: info@pruefungscoach.tech
>
> Hiermit widerrufe(n) ich/wir (\\*) den von mir/uns (\\*) abgeschlossenen
> Vertrag über den Kauf der folgenden Waren (\\*) / die Erbringung der
> folgenden Dienstleistung (\\*)
>
> Bestellt am (\\*) / erhalten am (\\*)
>
> Name des/der Verbraucher(s)
>
> Anschrift des/der Verbraucher(s)
>
> E-Mail-Adresse, mit der bestellt wurde
>
> Lizenz-Schlüssel (zur schnelleren Bearbeitung; siehe Bestätigungs-E-Mail)
>
> Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier)
>
> Datum
>
> (\\*) Unzutreffendes streichen.

Die Angabe von E-Mail-Adresse und Lizenz-Schlüssel ist nicht zwingend
erforderlich, beschleunigt aber die Bearbeitung Ihres Widerrufs
erheblich.

### 6.5 Widerrufsbutton (ab 19.06.2026)

Ab dem 19.06.2026 stellt der Anbieter zur Ausübung des Widerrufsrechts
gemäß § 356a BGB eine elektronische Widerrufsfunktion bereit. Diese ist
auf der Checkout-Seite sowie in der Bestätigungs-E-Mail klar erkennbar
verlinkt.

## 7. Leistungsumfang und Verfügbarkeit

Der Anbieter stellt die App auf **Streamlit Community Cloud** bereit.
Eine bestimmte Verfügbarkeit oder Reaktionszeit wird nicht garantiert.
Für Funktionen, die externe APIs nutzen (ElevenLabs, OpenAI, Pexels, Replicate),
gelten zusätzlich deren Limits und Verfügbarkeiten.

Pro-Limits werden monatlich beim Abrechnungs-Stichtag zurückgesetzt.

## 8. Gewährleistung und Mängelrechte

Es gelten die gesetzlichen Mängelhaftungsrechte. Bei digitalen Produkten
und digitalen Dienstleistungen finden insbesondere die §§ 327 ff. BGB
Anwendung. Der Anbieter ist verpflichtet, dem Kunden die vereinbarte
Leistung mangelfrei bereitzustellen und für deren Aktualisierung im
gesetzlich vorgesehenen Zeitraum zu sorgen.

Mängel sind dem Anbieter unverzüglich nach Entdeckung anzuzeigen.

## 9. Haftung

Der Anbieter haftet uneingeschränkt für Vorsatz und grobe Fahrlässigkeit
sowie für Schäden aus Verletzung des Lebens, des Körpers oder der
Gesundheit. Bei einfacher Fahrlässigkeit haftet der Anbieter nur bei
Verletzung wesentlicher Vertragspflichten (Kardinalpflichten) und
begrenzt auf den vertragstypisch vorhersehbaren Schaden. Wesentliche
Vertragspflichten sind solche, deren Erfüllung die ordnungsgemäße
Durchführung des Vertrags überhaupt erst ermöglicht und auf deren
Einhaltung der Kunde regelmäßig vertraut und vertrauen darf.

Für Inhalte, die der Kunde mit VoiceClip erstellt, ist der Kunde selbst
verantwortlich. Insbesondere muss der Kunde sicherstellen, dass er
nötige Rechte an verwendeten Stimmen, Bildern und Videos besitzt und
die Erstellung keine Rechte Dritter (insbesondere Persönlichkeits- oder
Urheberrechte) verletzt.

## 10. Nutzungsrechte an erstellten Videos

Der Kunde erhält ein einfaches, nicht-ausschließliches Nutzungsrecht
an den mit VoiceClip erstellten Videos. Stock-Footage von Pexels
unterliegt der [Pexels-Lizenz](https://www.pexels.com/license/). Bei
Voice-Cloning versichert der Kunde, dass er die erforderlichen Rechte
an den hochgeladenen Sprachproben besitzt.

## 11. Kündigung Pro-Abo

Das Pro-Abo wird auf unbestimmte Zeit geschlossen. Der Kunde kann
jederzeit zum Ende der laufenden Abrechnungsperiode kündigen. Die
Kündigung erfolgt über das Kundenportal von Polar. Der
Kündigungslink befindet sich in jeder Bestätigungs-E-Mail.

Eine Kündigungsfrist gibt es nicht. Bereits gezahlte Beträge für die
laufende Periode werden nicht anteilig erstattet.

## 12. Änderungen der AGB

Der Anbieter kann diese AGB mit Wirkung für die Zukunft ändern, soweit
die Änderung sachlich gerechtfertigt ist (z.B. Anpassung an geänderte
Rechtslage, neue Funktionen). Der Kunde wird über Änderungen mindestens
sechs Wochen vor Inkrafttreten per E-Mail informiert. Widerspricht der
Kunde nicht innerhalb dieser Frist in Textform, gelten die geänderten
AGB als angenommen. Auf das Widerspruchsrecht und die Folgen wird in
der Mitteilung gesondert hingewiesen.

## 13. Schlussbestimmungen

### 13.1 Anwendbares Recht

Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des
UN-Kaufrechts. Bei Verbrauchern gilt diese Rechtswahl nur, soweit
hierdurch nicht zwingende Schutzvorschriften des Rechts ihres
Aufenthaltsstaats ausgehöhlt werden.

### 13.2 Erfüllungsort

Erfüllungsort für sämtliche Leistungen aus den mit dem Anbieter
bestehenden Geschäftsbeziehungen sowie der Gerichtsstand ist der Sitz
des Anbieters in Bochum, soweit der Kunde nicht Verbraucher, sondern
Kaufmann, juristische Person des öffentlichen Rechts oder
öffentlich-rechtliches Sondervermögen ist. Dasselbe gilt, wenn der Kunde
keinen allgemeinen Gerichtsstand in Deutschland oder der EU hat oder der
Wohnsitz oder gewöhnliche Aufenthalt im Zeitpunkt der Klageerhebung nicht
bekannt ist.

### 13.3 Salvatorische Klausel

Sollten einzelne Bestimmungen dieses Vertrages unwirksam oder
undurchführbar sein oder nach Vertragsschluss unwirksam oder
undurchführbar werden, bleibt davon die Wirksamkeit des Vertrages im
Übrigen unberührt. An die Stelle der unwirksamen oder undurchführbaren
Bestimmung soll diejenige wirksame und durchführbare Regelung treten,
deren Wirkungen der wirtschaftlichen Zielsetzung am nächsten kommen,
die die Vertragsparteien mit der unwirksamen bzw. undurchführbaren
Bestimmung verfolgt haben. Die vorstehenden Bestimmungen gelten
entsprechend für den Fall, dass sich der Vertrag als lückenhaft erweist.

## 14. Online-Streitbeilegung

Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung
bereit: https://ec.europa.eu/consumers/odr/

Der Anbieter ist nicht bereit oder verpflichtet, an Streitbeilegungsverfahren
vor einer Verbraucherschlichtungsstelle teilzunehmen.

---

**Kontakt:**<br>
Haci Ibrahim Dogan<br>
Holunderweg 3<br>
44869 Bochum<br>
E-Mail: info@pruefungscoach.tech<br>
Telefon: +49 1551 0899025
    """,
    unsafe_allow_html=True,
)

# Sprach-Toggle fest am Seitenende, im Dokumentfluss
render_lang_toggle()
