# Supabase Setup fuer Score-Persistenz

Brauchst du wenn du `score_voices.py` auf Streamlit Cloud deployst und Scores zwischen App-Restarts erhalten bleiben sollen.

Free Tier reicht: 500 MB Datenbank, unlimited API-Calls. Voraussichtliche Nutzung: <1 KB pro Score, also weit unter Limit.

**Du hast schon ein Supabase-Projekt fuer das Rate-Limiting der Hauptseite (`rate_limit.py`)?** Dann ueberspring Schritt 1, nutze denselben Projekt und dieselben Credentials. Die `voice_scores`-Tabelle wird einfach zusaetzlich angelegt.

## 1. Projekt anlegen (nur wenn noch keins existiert, ~3 Min)

1. Auf https://supabase.com gehen, mit GitHub einloggen (kostenlos)
2. "New Project" klicken
3. Felder:
   - **Name:** `voiceclip-scores` (oder beliebig)
   - **Database Password:** generieren lassen, in Passwortmanager speichern
   - **Region:** `Frankfurt (eu-central-1)` (DSGVO-konform fuer DE-User)
   - **Plan:** Free
4. "Create new project" klicken, ~2 Min warten

## 2. Tabelle erstellen (~1 Min)

Im Supabase-Dashboard links auf "SQL Editor" klicken, neuen Query starten und das hier ausfuehren:

```sql
CREATE TABLE voice_scores (
  tester_name TEXT NOT NULL,
  file_name TEXT NOT NULL,
  score INTEGER,
  note TEXT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (tester_name, file_name)
);

-- RLS bewusst aus, weil App auf Streamlit Cloud nur ueber privaten Link erreichbar ist
-- und kein Auth-Layer noetig ist. Falls spaeter Public-Deploy: RLS einschalten.
ALTER TABLE voice_scores DISABLE ROW LEVEL SECURITY;
```

"Run" klicken. Sollte "Success. No rows returned" zeigen.

## 3. API-Credentials holen (~1 Min)

1. Im Supabase-Dashboard links auf "Settings" -> "API"
2. Felder kopieren:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon public key:** `eyJhbGc...` (langer JWT-String)

## 4. In Streamlit Cloud eintragen

1. Auf https://share.streamlit.io zur deployed App gehen
2. Drei-Punkte-Menue rechts oben -> "Settings" -> "Secrets"
3. Eintragen (TOML-Format):

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGc..."
```

4. "Save" klicken. App restartet automatisch.

## 5. Lokal testen (optional)

In `.env` eintragen:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
```

Dann `streamlit run score_voices.py`. In der Sidebar sollte stehen: "Storage: Supabase (persistent)".

## Verifikation

Nach dem Deploy: in der App einen Test-Score setzen, dann im Supabase-Dashboard auf "Table Editor" -> "voice_scores" gehen. Da sollte eine Zeile stehen.

## Was wenn es nicht laeuft

- App zeigt "Storage: Lokales JSON-File" statt Supabase: env vars nicht angekommen, in Streamlit Cloud Secrets nochmal pruefen
- App crashed beim Score-Speichern: SQL-Schema oben ausfuehren
- Score-Save zeigt keinen Fehler aber Daten erscheinen nicht in Supabase: RLS ist an, mit obigem SQL ausschalten (oder eine Permissive-Policy schreiben)

## Backup-Strategie

Free Tier hat keine automatischen Backups. Falls die Daten kritisch werden:
- Im Supabase-Dashboard "Database" -> "Backups" gibt's Manual-Backups (auch im Free-Tier)
- Alternativ: nach Test-Ende Daten als CSV exportieren via "Table Editor" -> "Export"
