# Deployment auf Hostinger VPS

Migration von Streamlit Cloud zu eigenem VPS mit Docker plus Caddy plus Auto-SSL.

**Ergebnis:** closelyst.com laeuft auf deinem VPS, HTTPS via Let's Encrypt, kein Streamlit-Cloud-Account mehr noetig.

**Zeitaufwand:** ~45-60 Min, je nachdem wie schnell DNS propagiert.

---

## Voraussetzungen

- Hostinger VPS mit Root-SSH-Zugriff (Ubuntu 22.04 oder 24.04)
- Domain closelyst.com (DNS-Zugriff bei deinem Registrar)
- GitHub-Zugriff vom VPS (SSH-Key oder Personal Access Token)
- Alle API-Keys parat (ElevenLabs, OpenAI, Polar, Replicate, Supabase, Pexels)

---

## Schritt 1: VPS vorbereiten (10 Min)

SSH auf den Server:

```bash
ssh root@DEINE-VPS-IP
```

### 1.1 System updaten

```bash
apt update && apt upgrade -y
```

### 1.2 Docker installieren

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

Verify:
```bash
docker --version
docker compose version
```

### 1.3 Firewall (UFW) konfigurieren

```bash
apt install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status
```

### 1.4 Non-Root-User anlegen (Best Practice, optional aber empfohlen)

```bash
adduser closelyst
usermod -aG docker closelyst
usermod -aG sudo closelyst

# SSH-Key fuer den User kopieren
mkdir -p /home/closelyst/.ssh
cp ~/.ssh/authorized_keys /home/closelyst/.ssh/
chown -R closelyst:closelyst /home/closelyst/.ssh
chmod 700 /home/closelyst/.ssh
chmod 600 /home/closelyst/.ssh/authorized_keys
```

Ab jetzt mit `ssh closelyst@DEINE-VPS-IP` einloggen.

---

## Schritt 2: DNS aufsetzen (5 Min, dann 5-60 Min Propagation)

Bei deinem Domain-Registrar (Hostinger Domain-Panel oder wo immer closelyst.com gehostet ist):

| Type | Name | Wert | TTL |
|------|------|------|-----|
| A | @ | DEINE-VPS-IP | 300 |
| A | www | DEINE-VPS-IP | 300 |

**Pruef ob die DNS-Propagation durch ist:**

```bash
dig closelyst.com +short
# Sollte deine VPS-IP zurueckgeben
```

Falls nicht: 10-60 Min warten. Caddy kann erst SSL ausstellen wenn DNS funktioniert.

---

## Schritt 3: App auf VPS klonen (5 Min)

Als `closelyst`-User:

```bash
cd ~
git clone https://github.com/ZipZap1/closelyst.git
cd closelyst
```

Falls Repo privat ist und nicht clonen geht:
- Variante A: SSH-Key auf VPS generieren mit `ssh-keygen -t ed25519`, Pubkey auf https://github.com/settings/keys hinzufuegen, dann `git clone git@github.com:ZipZap1/closelyst.git`
- Variante B: GitHub Personal Access Token bei https://github.com/settings/tokens generieren, dann `git clone https://USERNAME:TOKEN@github.com/ZipZap1/closelyst.git`

---

## Schritt 4: Secrets eintragen (5 Min)

```bash
cp .env.example .env
nano .env  # oder vim, je nach Geschmack
```

Werte aus deinen Streamlit Cloud Secrets uebernehmen:
- `ELEVENLABS_API_KEY`
- `OPENAI_API_KEY` (frischer, gueltiger Key)
- `PEXELS_API_KEY`
- `POLAR_API_TOKEN`
- `POLAR_CHECKOUT_URL_REMOVE_WATERMARK`
- `POLAR_CHECKOUT_URL_PRO_MONTHLY`
- `REPLICATE_API_TOKEN`
- `SYNC_API_KEY` (falls genutzt)
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `MASTER_LICENSE_KEY`
- `DEMO_VIDEO_URL` (leer lassen, bundled assets/demo.mp4 wird genutzt)

Speichern: `Ctrl+O`, `Enter`, `Ctrl+X` (in nano).

---

## Schritt 5: App starten (5 Min)

```bash
docker compose up -d --build
```

Erst-Build dauert 3-5 Min (Python-Image, ffmpeg, pip-Install).

**Logs anschauen:**
```bash
docker compose logs -f streamlit
# Strg+C zum Beenden des Tail
```

Sollte "You can now view your Streamlit app in your browser" zeigen.

**Caddy-Logs (SSL-Cert-Generierung):**
```bash
docker compose logs caddy
```

Sollte "certificate obtained successfully" fuer closelyst.com zeigen.

---

## Schritt 6: Live testen (2 Min)

Browser: https://closelyst.com

- Voiceclip-Hauptseite laed
- Demo-Video oben sichtbar
- HTTPS-Padlock im Browser
- Free-Modus funktioniert (Beispiel laden plus generieren)

Falls 502 Bad Gateway: Streamlit-Container noch nicht ready, 30 Sek warten.

Falls SSL-Error: DNS noch nicht propagiert oder Caddy braucht noch ein paar Min.

---

## Updates deployen (laufender Workflow)

Wenn du Code-Aenderungen auf GitHub pushed:

```bash
cd ~/closelyst
git pull
docker compose up -d --build
```

Streamlit-Container wird neu gebaut, Caddy laeuft weiter. Downtime: ~30 Sek.

---

## Streamlit Cloud abschalten

Sobald closelyst.com auf dem VPS laeuft:

1. https://share.streamlit.io → Hauptseite-App
2. Drei Punkte → "Delete app"

Die App ist dann weg. Streamlit Cloud Free hat eh keine Kosten, also nicht zwingend.

---

## Polar-URL aktualisieren

Polar.sh -> Organization Settings -> Website-URL von `https://closelyst-app.streamlit.app/` auf `https://closelyst.com` aendern. Macht den Impressums-Link konsistent.

---

## Troubleshooting

### App startet nicht, Container crashed

```bash
docker compose logs streamlit | tail -50
```

Haeufige Ursachen:
- `.env` fehlt oder hat Tippfehler
- API-Key ungueltig (z.B. OpenAI 401 → frischen Key holen)
- Memory limit zu niedrig (Container OOM-killed) → in `docker-compose.yml` Memory-Limit hochsetzen

### SSL funktioniert nicht

```bash
docker compose logs caddy | grep -i cert
```

Caddy kann erst Cert holen wenn DNS auf den Server zeigt. `dig closelyst.com` muss die VPS-IP zeigen. Falls nicht: bei Registrar A-Record pruefen.

### Hohe Memory-Auslastung

```bash
docker stats
```

Falls Streamlit > 1 GB nutzt: Memory-Limit in docker-compose.yml anheben oder VPS-Tier upgraden.

### App ist langsam

Hostinger Entry-Tier VPS hat oft nur 1-2 CPU. Bei vielen gleichzeitigen Generierungen wird's langsam. Upgrade auf 4-CPU oder Caching der Voice-Lists in Streamlit hilft.

### Logs persistieren

Standardmaessig sind Container-Logs Docker-internal. Fuer Persistenz:

```yaml
# In docker-compose.yml unter streamlit:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Cost-Vergleich

| | Streamlit Cloud Free | Hostinger VPS (entry) |
|---|---|---|
| Kosten | 0 | 5-8 EUR/Mo |
| Bandwidth | Shared/limited | Dediziert |
| Custom-Domain | Nicht moeglich | closelyst.com direkt |
| SSL | Default | Auto via Caddy/LE |
| RAM | ~1 GB shared | 2-4 GB dediziert |
| Updates | Auto via Git-Push | `git pull && docker compose up -d --build` |

---

## Naechste Schritte nach Deploy

1. Polar-Website-URL aktualisieren
2. Hauptseite-App auf Streamlit Cloud loeschen (vermeidet Verwirrung)
3. TikTok-Bio-Link auf `https://closelyst.com` setzen
4. Falls Demo-Video extern hosten willst: `DEMO_VIDEO_URL` setzen, sonst bleibt assets/demo.mp4

---

Bei Problemen: `docker compose logs streamlit` und `docker compose logs caddy` schicken, dann diagnostiziere ich.
