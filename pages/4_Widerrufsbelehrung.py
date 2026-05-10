"""Widerrufsbelehrung als eigenständige Seite (Auszug aus AGB §6)."""
import streamlit as st

st.set_page_config(page_title="Widerrufsbelehrung - VoiceClip", page_icon="assets/icon.png")

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

## Vorzeitiges Erlöschen des Widerrufsrechts (§ 356 Abs. 5 BGB)

Bei einem Vertrag über die Bereitstellung nicht auf einem körperlichen
Datenträger befindlicher digitaler Inhalte erlischt das Widerrufsrecht
auch dann, wenn der Anbieter mit der Vertragsausführung begonnen hat,
nachdem der Kunde

- ausdrücklich zugestimmt hat, dass der Anbieter mit der Ausführung des
  Vertrags vor Ablauf der Widerrufsfrist beginnt, **und**
- seine Kenntnis davon bestätigt hat, dass er durch seine Zustimmung mit
  Beginn der Ausführung des Vertrags sein Widerrufsrecht verliert, **und**
- der Anbieter dem Kunden eine Bestätigung des Vertrags und der erteilten
  Erklärungen in Textform zur Verfügung gestellt hat.

Der Kunde erteilt diese Zustimmung und Kenntnisbestätigung durch das
Setzen der entsprechenden Checkbox auf der Checkout-Seite. Mit der
Bereitstellung des License-Keys per E-Mail beginnt die Vertragsausführung,
und das Widerrufsrecht erlischt zu diesem Zeitpunkt.

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
> Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier)
>
> Datum
>
> (\\*) Unzutreffendes streichen.
    """,
    unsafe_allow_html=True,
)
