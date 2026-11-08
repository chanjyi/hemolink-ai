# Putting HemoLink online (website + phone)

HemoLink is one FastAPI app that serves both the website and the API, so any host that runs Python (or Docker) works.
The layout adapts to the screen: sidebar on laptops, a bottom tab bar on phones, and it can be **installed on a phone's
home screen** like an app (it opens full-screen with the HemoLink icon).

> Camera (live view) and GPS only work on **HTTPS** pages (or `localhost`). All options below except 1b give you HTTPS.

---

## Option 1 — Show it on your phone today (free, 5 minutes, runs on your laptop)

Uses a Cloudflare *quick tunnel*: a temporary public HTTPS link to the app running on your laptop. No account needed.

```powershell
# terminal 1 — run the app (from the hemolink folder)
conda activate hemolink
uvicorn app:app --port 8000

# terminal 2 — install once, then start the tunnel
winget install --id Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```

The tunnel prints a link like `https://something-random.trycloudflare.com`. Open it on any phone or computer.

* Your laptop must stay on and connected; the link changes every time you restart the tunnel.
* Good for judging sessions and live demos. Photo reading (OCR) works because it runs on your laptop.

### 1b — Same Wi-Fi only (no install)

```powershell
uvicorn app:app --host 0.0.0.0 --port 8000
ipconfig        # note your IPv4 address, e.g. 192.168.1.23
```

On the phone (same Wi-Fi) open `http://192.168.1.23:8000` and allow Python through the Windows firewall if asked.
Plain http: the live camera and GPS are blocked by the phone browser — use **Choose a photo** and your profile city instead.

---

## Option 2 — Permanent free link on Render

`render.yaml` is already in the project. Render's free web service has 512 MB RAM, sleeps after 15 minutes without
visitors (the next visit takes about a minute to wake it) and resets the database when it restarts — fine for a demo,
because HemoLink re-creates its demo data on start. Photo reading is switched off there (`HEMOLINK_OCR=off`) to fit in
512 MB; photos fall back to manual entry beside the image.

1. Put the `hemolink` folder in a GitHub repository (private is fine):
   ```powershell
   cd hemolink
   git init
   git add .
   git commit -m "HemoLink AI"
   # create an empty repo on github.com, then:
   git remote add origin https://github.com/<you>/hemolink-ai.git
   git push -u origin main
   ```
2. On [render.com](https://render.com): **New → Blueprint** → pick the repository → **Apply**.
3. Wait for the build (a few minutes). Your link is shown at the top, e.g. `https://hemolink-ai.onrender.com`.
4. Optional: add `ANTHROPIC_API_KEY` (or another provider key from `.env.example`) under **Environment** for AI explanations.
5. Add `HEMOLINK_DATA_KEY` (copy the text from `data_key.txt` of a local run, or generate one with
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) so encrypted report
   files stay readable. Step-by-step email / SMS / push setup: `docs/SETUP_GUIDE.md`.
6. Optional — real alerts: add the `SMTP_*` and/or `TWILIO_*` values from `.env.example`, plus `HEMOLINK_APP_URL`
   (your Render link). For push, copy `vapid_private.pem` from a local run into `VAPID_PRIVATE_KEY`, because Render's
   free disk is wiped on restart and a new key would unsubscribe every phone. Reminders only run while the service
   is awake (it sleeps after 15 idle minutes); admins can press **Run reminders now** in Notifications.

---

## Option 3 — Any Docker host with photo reading on (≥ 1 GB RAM)

```bash
docker build -t hemolink .
docker run -p 7860:7860 -e HEMOLINK_SECRET_KEY=change-me-to-a-long-random-string hemolink
# open http://localhost:7860
```

The same `Dockerfile` works on Railway, Fly.io, Google Cloud Run, Hugging Face Spaces (Docker) or your own VM.
Set `HEMOLINK_SECRET_KEY` as a secret, keep `HEMOLINK_ENV=production` (secure cookies need HTTPS), and set
`HEMOLINK_OCR=off` if the machine has less than about 1 GB of RAM.

---

## Install it on a phone

* **Android (Chrome):** open the link → ⋮ menu → **Install app** / **Add to Home screen**.
* **iPhone (Safari):** open the link → **Share** → **Add to Home Screen**.

Push alerts on phones need the HTTPS link (Option 1 tunnel or Option 2/3), then **My Profile → Alerts & language →
Enable on this device**. On iPhone this works only after **Add to Home Screen** (iOS 16.4+).

## Before sharing a public link

* The demo accounts (`donor@demo.com` / `Demo123!` …) are public on purpose — fine for judges, but don't let real
  people enter real health data or upload real blood reports on a public demo.
* With real SMTP / Twilio settings, messages go to the email and phone number in each profile — use your own
  test numbers; demo and synthetic accounts are safe (synthetic donors never get outside messages).
* “Find venue on map” uses OpenStreetMap's free Nominatim search (one request per click). For heavy use, switch to
  a paid geocoder.
* Keep the “© OpenStreetMap contributors” credit on the map. For heavy public traffic use a map tile provider
  instead of OpenStreetMap's free tile servers.
