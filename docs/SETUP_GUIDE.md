# HemoLink — finishing setup on your own computer

Three things that have to happen on your machine and phone. About 30 minutes in total.
All settings go in the `.env` file next to `app.py` (copy `.env.example` if you haven't). **Restart the server after every `.env` change.**

---

## A. Train the forecasting models (≈ 2 minutes)

```powershell
cd hemolink
conda activate hemolink
pip install -r requirements.txt          # v6 added pywebpush
python scripts/train_models.py           # all states × blood groups
```

You should see `70 series … Random Forest 57 …` and two new things: the `models/forecast/` folder and `docs/MODEL_REPORT.md`.
Check: Admin → **AI Models** → "Training run" card shows today's date.

Short on time? `python scripts/train_models.py --quick` (national series only, ~15 s).

---

## B. Real email and SMS (≈ 15 minutes)

### Email with Gmail (free)
1. Your Google account needs **2-Step Verification** on: myaccount.google.com → Security.
2. Create an **app password**: myaccount.google.com/apppasswords → name it "HemoLink" → copy the 16 letters.
3. Add to `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=yourname@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   SMTP_FROM=HemoLink <yourname@gmail.com>
   ```
4. Restart → log in as a donor whose email you can read (sign up with your own email) → **My Profile → Send me a test alert**.
5. Check: Admin → Notifications → "Message delivery": Email shows **Live**, the row says **sent**.

Gmail allows about 500 emails a day — plenty for a demo. Never use your normal Google password here.

### SMS with Twilio (free trial credit)
1. Sign up at twilio.com → verify **your own** phone number (trial accounts can only text verified numbers).
2. Console → copy **Account SID** and **Auth Token** → **Get a phone number**.
3. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_FROM=+1xxxxxxxxxx
   ```
4. Restart → My Profile → turn **SMS** on, enter your number (e.g. `012-345 6789`) → **Save** → **Send me a test alert**.

Trial texts start with "Sent from your Twilio trial account". If a text to a Malaysian number doesn't arrive (some carriers
filter overseas numbers), use the **WhatsApp sandbox** instead: Twilio Console → Messaging → Try WhatsApp → send the join
code from your phone, then set `TWILIO_FROM=whatsapp:+14155238886`.

Also set `HEMOLINK_APP_URL=https://your-link` so the "Open HemoLink" button in emails points to the right place.

---

## C. Push alerts on a real phone (≈ 10 minutes)

Push needs **HTTPS**, so use the free tunnel from DEPLOY.md Option 1:

```powershell
# terminal 1
uvicorn app:app --port 8000
# terminal 2
cloudflared tunnel --url http://localhost:8000
```

1. Open the `https://….trycloudflare.com` link on your phone.
   * **Android (Chrome):** works straight away.
   * **iPhone (iOS 16.4+):** Share → **Add to Home Screen**, then open HemoLink from the home-screen icon (push only works there).
2. Log in → **My Profile → Alerts & language → Enable on this device** → allow notifications.
3. Tap **Send me a test alert** → a pop-up should appear within a few seconds, even with the browser in the background.
4. Real demo: as admin (on your laptop) post an **Urgent request** for the phone user's blood type → **Send alerts** → the phone buzzes.

Keep `vapid_private.pem` (created next to the database). If it is deleted, phones must press "Enable on this device" again.

---

## D. Data protection settings (optional)

| Setting | Default | What it does |
|---|---|---|
| `HEMOLINK_DATA_KEY` | auto (`data_key.txt` next to the database) | Key that encrypts uploaded blood test files. **Back it up** — without it, stored files can't be opened |
| `HEMOLINK_REPORT_FILE_DAYS` | 365 | Original report files are deleted after this many days; confirmed values stay |
| `HEMOLINK_RATE_LIMIT` | on | `off` only for automated tests |

On Render (files wiped on restart) set `HEMOLINK_DATA_KEY` and `VAPID_PRIVATE_KEY` as environment variables.

## Troubleshooting

| You see | Fix |
|---|---|
| Email row shows **failed** with code 535 (username / password not accepted) | Use the 16-letter **app password**, not your Google password |
| SMS row shows **failed** with code 21608 | Trial account: verify that phone number in Twilio first |
| "Push isn't available here" | You're on `http://` — use the https tunnel link |
| iPhone has no "Enable on this device" effect | Open HemoLink from the **home-screen icon**, not Safari |
| Email / SMS still "Demo mode" | `.env` typo or the server wasn't restarted |
