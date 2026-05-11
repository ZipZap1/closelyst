"""Widerrufsbelehrung als eigenständige Seite (Auszug aus AGB §6)."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from i18n import render_lang_toggle, render_en_only_disclaimer_for_legal

st.set_page_config(page_title="Widerrufsbelehrung - VoiceClip", page_icon="assets/icon.png")

render_en_only_disclaimer_for_legal()

st.title("Widerrufsbelehrung")

st.markdown(
    """
## Widerrufsrecht für Verbraucher

Verbrauchern steht ein Widerrufsrecht nach folgender Maßgabe zu, wobei
Verbraucher jede natürliche Person ist, die ein Rechtsgeschäft zu
Zwecken abschließt, die überwiegend weder ihrer gewerblichen noch ihrer
selbständigen beruflichen Tätigkeit zugerechnet werden können.

## Widerrufsbelehrung

**Widerrufsrecht**

Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen
diesen Vertrag zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage
ab dem Tag des Vertragsabschlusses.

Um Ihr Widerrufsrecht auszuüben, müssen Sie uns

> Haci Ibrahim Dogan<br>
> Holunderweg 3<br>
> 44869 Bochum<br>
> E-Mail: info@pruefungscoach.tech<br>
> Telefon: +49 1551 0899025

mittels einer eindeutigen Erklärung (z.B. ein mit der Post versandter
Brief oder E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen,
informieren. Sie können dafür das unten stehende Muster-Widerrufsformular
verwenden, das jedoch nicht vorgeschrieben ist.

Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung
über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist
absenden.

**Folgen des Widerrufs**

Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die
wir von Ihnen erhalten haben, unverzüglich und spätestens binnen vierzehn
Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf
dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden
wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion
eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes
vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte
berechnet.

## Wasserzeichen entfernen (digitaler Inhalt) – vorzeitiges Erlöschen

Beim Einmalkauf "Wasserzeichen entfernen" handelt es sich um einen
digitalen Inhalt im Sinne des § 327 Abs. 2 BGB. Das Widerrufsrecht
erlischt nach § 356 Abs. 5 BGB, wenn der Anbieter mit der
Vertragsausführung begonnen hat, nachdem der Kunde

- ausdrücklich zugestimmt hat, dass der Anbieter mit der Ausführung des
  Vertrags vor Ablauf der Widerrufsfrist beginnt, **und**
- seine Kenntnis davon bestätigt hat, dass er durch seine Zustimmung mit
  Beginn der Ausführung des Vertrags sein Widerrufsrecht verliert, **und**
- der Anbieter dem Kunden eine Bestätigung des Vertrags und der erteilten
  Erklärungen in Textform zur Verfügung gestellt hat.

Mit der Bereitstellung des Lizenz-Schlüssels per E-Mail beginnt die
Vertragsausführung, und das Widerrufsrecht erlischt zu diesem Zeitpunkt.

## Pro-Abo (digitale Dienstleistung) – Wertersatz bei Nutzung

VoiceClip Pro ist eine fortlaufende digitale Dienstleistung. Das
Widerrufsrecht bleibt während der gesamten vierzehntägigen Frist
bestehen, auch wenn die Dienstleistung bereits genutzt wurde.

Hat der Kunde verlangt, dass die Dienstleistung während der
Widerrufsfrist beginnen soll, schuldet er bei Widerruf einen
zeitanteiligen Wertersatz nach § 357a Abs. 2 BGB. Beispiel: Bei
8,99 € pro Monat beträgt der tägliche Wertersatz rund 0,30 €. Bei
Widerruf nach 5 Tagen Nutzung erstattet der Anbieter rund 7,49 €.

## Muster-Widerrufsformular

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
    """,
    unsafe_allow_html=True,
)

# Sprach-Toggle fest am Seitenende, im Dokumentfluss
render_lang_toggle()
