# Voice-Quality Test Protocol

**Aktueller Stand (2026-05-10):** Hybrid-Setup ist bereits live in der App (Free=OpenAI, Pro=ElevenLabs). Pro-User koennen im UI zwischen beiden Backends switchen. Test ist jetzt **Validierung**, nicht Entscheidungsfindung.

**Hypothesen aus Research** (siehe `references/research/2026-05-10-openai-tts-voice-differentiation.md`):
- Nova und Fable sind die einzigen OpenAI-Voices mit akzeptabler deutscher Aussprache. Test soll das bestaetigen oder widerlegen.
- Andere Voices (Onyx, Shimmer, Echo, Alloy) haben deutlich englischen Akzent in DE. Test soll quantifizieren wie schlimm.
- gpt-4o-mini-tts mit "native German accent"-Instruction ist Wildcard. Wenn das funktioniert, ersetzt es tts-1-hd als DE-Default.

**Zweck:**
1. Validieren dass die OpenAI-Voices im Free-Tier "gut genug" sind, um Free-User nicht abzuschrecken
2. Curated-Set finden: welche der 6 OpenAI-Voices fliegen aus dem Picker, welche bleiben
3. Top-Voices für Pro-Tier identifizieren (welche ElevenLabs-Voices als Default vorschlagen)
4. Critical-Check: Ist der Deutsch-Akzent von OpenAI ein Dealbreaker für den DE-Markt?

**Wann ausführen:** Pre-Exam-Phase (08.-22.05.2026), parallel zu TikTok-Account-Setup. Kostet ~2-3h verteilt über mehrere Tage.

**Hard deadline:** Resultat vor 23.05.2026 (Build-Start), damit das Free-Voice-Picker-Set in `voice.py` final ist.

---

## Setup (einmalig, ~30 Min)

### Accounts und API-Keys
- ElevenLabs: Free-Tier reicht (10k Chars), API-Key aus dem Dashboard
- OpenAI: API-Key bereits in `.env` (sonst anlegen)
- TikTok: Test-Account (laut Pre-Exam-Plan ohnehin auf der Liste)

### Test-Voices (8 Variants)
| Backend | Voice | Begründung |
|---|---|---|
| ElevenLabs | "Adam" (pNInz6obpgDQGcFmaJgB) | Männlich, warm, viral-erprobt |
| ElevenLabs | "Bella" (EXAVITQu4vr4xnSDxMaL) | Weiblich, expressiv |
| OpenAI tts-1-hd | "onyx" | Männlich, tief, autoritär |
| OpenAI tts-1-hd | "echo" | Männlich, ruhig, neutral |
| OpenAI tts-1-hd | "nova" | Weiblich, klar, freundlich |
| OpenAI tts-1-hd | "shimmer" | Weiblich, warm, soft |
| OpenAI gpt-4o-mini-tts | "alloy" + Excited-Style | Mit Emotion-Steering |
| OpenAI gpt-4o-mini-tts | "ballad" + Native-German-Style | Test ob Style-Prompt DE-Akzent fixt |

---

## Test-Scripts (3 Varianten, je ~25-30 Sek)

Alle Scripts in deutscher und englischer Version generieren, weil VoiceClip beide Märkte bedienen soll.

### Script A: Educational Hook (Tech/AI-Tutorial-Style)

**DE:**
> Du dachtest, gute KI-Stimmen kosten zwanzig Euro im Monat? Falsch. Ich zeige dir drei kostenlose Tools, die genauso gut klingen. Tool Nummer eins ist OpenAI's Text-to-Speech. Klingt natürlich, ist aber stimmlich limitiert. Tool zwei: ElevenLabs Free-Tier. Zehntausend Zeichen pro Monat reichen für etwa zehn TikToks. Tool drei kommt gleich.

**EN:**
> You thought good AI voices cost twenty bucks a month? Wrong. I'll show you three free tools that sound just as good. Tool number one is OpenAI Text-to-Speech. It sounds natural but vocally limited. Tool two: ElevenLabs free tier. Ten thousand characters per month is enough for about ten TikToks. Tool three is coming up.

### Script B: Storytelling Hook (Solo-Founder-Style)

**DE:**
> Vor einer Woche hatte ich null Downloads in meiner App. Ich habe alles gelöscht und neu angefangen. Heute zeige ich dir, was ich gelernt habe. Erstens: niemand will deine App. Zweitens: jeder will dein Tool. Der Unterschied? Apps sind ein Versprechen. Tools sind sofortiger Nutzen. Hier ist mein neuer Plan.

**EN:**
> One week ago I had zero downloads on my app. I deleted everything and started over. Today I'll show you what I learned. First: nobody wants your app. Second: everyone wants your tool. The difference? Apps are a promise. Tools are instant value. Here's my new plan.

### Script C: Punchy Listicle (High-Energy)

**DE:**
> Drei KI-Tools, die kein Mensch kennt, aber jeder Creator nutzen sollte. Tool eins macht aus deinem Text in zehn Sekunden ein TikTok. Tool zwei findet Stockvideos die zu deinen Worten passen. Tool drei erzeugt Untertitel, die syncen. Bonus: alle drei sind kostenlos. Speichere das Video.

**EN:**
> Three AI tools nobody knows about but every creator should use. Tool one turns your text into a TikTok in ten seconds. Tool two finds stock videos that match your words. Tool three generates captions that actually sync. Bonus: all three are free. Save this video.

---

## Test-Protokoll

### Phase 1: Internal A/B (Tag 1-2, ~1.5h)

1. Generate jeden Script mit allen 8 Voice-Variants in 2 Sprachen (48 Audio-Files total)
2. Blind-Listening-Test mit 3 Personen (Familie/Freunde, ohne Kontext)
3. Frage pro File: "Klingt das wie ein echter Mensch oder wie ein Roboter?" (1-10 Skala)
4. Frage final: "Welches der 8 Files würdest du in einem TikTok hören wollen?"
5. Optional Pre-Filter: Du selbst hörst die 48 Files vor dem Familien-Test, wirfst die offensichtlich schlechtesten 3-4 raus, gehst nur mit Top 4-5 in den Blind-Test

**Ergebnis dokumentieren:** Score-Tabelle in dieser Datei am Ende anhängen.

### Phase 2: TikTok A/B-Test (Tag 3-7, ~2h)

**Setup:**
- Pick die 2 besten Voices aus Phase 1 (vermutlich 1x ElevenLabs, 1x OpenAI)
- Pick den besten Script aus Phase 1
- Erstelle 2 identische Videos: gleicher Hook, gleicher Cut, gleiche Stock-Footage, NUR Voice unterschiedlich
- Optional: 3. Video als "Kontrolle" mit deiner eigenen Stimme

**Posting-Schedule:**
- Tag 3 (Mittwoch): Video A (ElevenLabs) um 18:00
- Tag 4 (Donnerstag): Video B (OpenAI) um 18:00
- Optional Tag 5: Video C (eigene Stimme) um 18:00

**Wichtig:** Captions, Cover-Image, Hashtags identisch halten. Nur die Voice variieren.

### Phase 3: Daten sammeln (Tag 8-12)

Nach 5 Tagen Reife:
- Watch-Time-% (TikTok Analytics)
- Comments und Sentiment (manuell durchscrollen)
- Saves und Shares
- Follower-Growth pro Video

---

## Decision-Matrix (Hybrid bereits live, hier nur Anpassungen)

| Resultat | Aktion |
|---|---|
| Alle 6 OpenAI-Voices Score >= 6/10 | **Keep all 6** im Free-Picker, nur Reihenfolge optimieren |
| 1-3 OpenAI-Voices Score < 5/10 | **Drop them** aus `_OPENAI_VOICES` in voice.py, Picker zeigt nur Top-Voices |
| 4+ OpenAI-Voices Score < 5/10 | **Hybrid revisiten:** OpenAI ist nicht gut genug. Optionen: (a) ElevenLabs auch im Free mit Char-Limit, (b) Free komplett kostenpflichtig machen |
| DE-Voices durchgängig schlechter als EN | **Free-Tier auf EN-only** im DE-Markt klar kommunizieren ("für deutschsprachige Videos: Pro empfohlen") |
| ballad+German-Style schlägt tts-1-hd in DE | **gpt-4o-mini-tts als DE-Default** statt tts-1-hd, voice.py Patch |
| TikTok-Watch-Time OpenAI-Video < 50% von ElevenLabs-Video | **Free-Tier-Strategie überdenken**: Free-Watermark-Distribution killt sich selbst wenn Voice nicht teilbar ist |

---

## Resultate

### Phase 1 Blind-Test Scores
_Auszufüllen nach Tag 2. Tabelle:_

| Voice | Sprache | Mensch-Score (1-10, avg of 3) | Top-Pick-Wahl (Anzahl von 3) | Notes |
|---|---|---|---|---|
| ElevenLabs Adam | DE / EN | / | / | |
| ElevenLabs Bella | DE / EN | / | / | |
| OpenAI Onyx | DE / EN | / | / | |
| OpenAI Echo | DE / EN | / | / | |
| OpenAI Nova | DE / EN | / | / | |
| OpenAI Shimmer | DE / EN | / | / | |
| OpenAI Alloy (excited) | DE / EN | / | / | |
| OpenAI Ballad (German-style) | DE / EN | / | / | |

### Phase 2 TikTok Performance
_Auszufüllen nach Tag 12. Top-OpenAI-Voice vs Top-ElevenLabs-Voice, je 1 Video, gleicher Script und Cut._

| Metric | Video A (ElevenLabs) | Video B (OpenAI) | Diff |
|---|---|---|---|
| Watch-Time-% | | | |
| Avg View Duration | | | |
| Saves | | | |
| Shares | | | |
| Comments (Sentiment) | | | |
| Follower-Growth | | | |

### Final Decision (vor 22.05.2026 setzen)

**Free-Picker-Voices (final set):**
_z.B. "Nova, Shimmer, Onyx" (3 Top-Voices) statt aller 6_

**Pro-Picker-Default-Voice:**
_z.B. "Adam für männlich, Bella für weiblich"_

**DE-Markt-Strategie:**
_z.B. "OpenAI im Free reicht für DE" oder "Free-Tier-Captions in DE empfehlen Pro"_

**Code-Änderungen nötig?**
_Liste der voice.py / app.py Änderungen, falls relevant_

**Decision-Log-Eintrag in `decisions/log.md`:**
_Datum, Entscheidung, Reasoning_
