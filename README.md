# HemoLink AI v6.1

**See the blood shortage before it happens, and alert the donors most likely to come.**
Hackathon prototype for DSH Hacks V2 (AI × Healthcare) · Python FastAPI + SQLite + scikit-learn + responsive HTML/CSS/JavaScript

v6.1 = eligibility rules checked against **Pusat Darah Negara**, **security & PDPA** (rate limits, login lock, encrypted report files, consent records, download / delete my data) and a step-by-step **setup guide** (`docs/SETUP_GUIDE.md`).

v6 = **real-data model training** (per-blood-type model selection, rolling cross-validation, fairness checks, saved models + report), an **optional AI key with a connection test**, **real email / SMS / phone push alerts** with reminders, **Bahasa Malaysia** (EN | BM switch everywhere) and **“pick location on map”** for organizers — see section 12.

v5.1 = donor welcome banner restored, **phone layout with a bottom tab bar**, installable on phones (home-screen app), and **ready to host online** — see **DEPLOY.md** (phone demo in 5 minutes with a free HTTPS tunnel, or a permanent free link on Render).

v5 = **new crimson & cream design** (split login with role tiles, donor dashboard with milestones mascot, outlined cards) and a **campaign map with GPS distances** (section 7).

v4 = **HemoCare** (Medical Knowledge + Medication History + Donation Preparation) and a **camera / photo option** in HemoScan (see sections 5–6).

v3.1 = clearer roles (donor · drive organizer · blood bank admin), a tidier donor menu, and urgent requests inside Notifications.

v3 = v2 **plus HemoScan AI** — a private blood test (FBC/CBC) report reader for donors (see section 5).

v2 = the v1 HemoLink app (accounts, campaigns, bookings, official MOH data, Random Forest forecast) **plus** AI features from HemoSync: shortage outlook, smart donor matching for urgent requests, eligibility check, donor return prediction, campaign planner, reports and an AI assistant with safety rules.

| Role | Who | Menu |
|---|---|---|
| Donor | Members of the public (everyone signs up as a donor) | Dashboard · Find Campaigns · My Appointments · Eligibility Check · **HemoScan AI** · **HemoCare** · Notifications (**urgent requests are answered here**) · Health Assistant |
| Drive Organizer | Community groups — universities, companies, NGOs — approved by the blood bank | Dashboard · My Campaigns · **Bookings & Check-in** (donated / no-show) · **Insights & Planner** (turnout, ratings, donors to re-invite, where/when to hold the next drive) · Notifications · Help Assistant |
| Blood Bank Admin | Blood bank staff (e.g. a Pusat Darah Negara centre) | Dashboard · **Blood Stock** (stock + 7-day shortage outlook + edit levels) · **Urgent Requests** (AI donor matching, alerts, mark donated) · Donation Trends (MOH data) · **Users & Organizers** (approve organizers) · AI Models · Notifications · Help Assistant |

Organizers cannot see stock levels, urgent requests or anyone's HemoScan reports; admins cannot see HemoScan reports either.

## 1. Quick start — Windows / Anaconda / VS Code

Run from the **`hemolink`** folder:

```powershell
conda create -n hemolink python=3.11 -y
conda activate hemolink
pip install -r requirements.txt
uvicorn app:app --reload
```

Or with a virtual environment:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000** · API docs at **http://127.0.0.1:8000/api/docs**. No Node.js needed.

### Demo accounts

One-click buttons on the login screen, or sign in with password `Demo123!`:

| Role | Login | Notes |
|---|---|---|
| Donor | `donor@demo.com` | Amira Hassan · **O−** · Cyberjaya · eligible to donate |
| Drive Organizer | `organizer@demo.com` | Daniel Lim · runs community drives around Kuala Lumpur |
| Blood Bank Admin | `admin@demo.com` | Dr. Sara Tan (Demo) · HemoLink Centre Kuala Lumpur |

The database file is now **`hemolink_v2.db`** (separate from v1's `hemolink.db`). Delete it while the server is stopped to reset everything. On first run it also creates **300 synthetic donors** (`sim###@donors.hemolink.test`, cannot log in), 180 days of simulated stock movements and past alert replies, so the AI features have data to learn from.

### Optional: real AI explanations

Create a `.env` file next to `app.py`:

```
LLM_PROVIDER=anthropic          # anthropic | openai | gemini
ANTHROPIC_API_KEY=...
```

Without a key the eligibility explanations and the assistant use built-in template / FAQ answers, so the demo never breaks. All optional settings (AI key, email, SMS, push, app URL) are listed in **`.env.example`**; copy it to `.env`. Admin → **AI Models** → **Test AI connection** checks the key without showing it.

## 2. Demo script (about 3 minutes)

Use two browser windows: admin (normal) and donor (incognito).

0. **Donor → Find Campaigns**: click **Use my location** → distances, ≤10 km filter, **Map** → pin popup → **Directions**.
1. **Admin → Dashboard**: banner says *O− is already below the safe level*. Open **Blood Stock** to show the 7-day projection and model error.
2. Click **Mobilise O− donors → Find matching donors**. The AI ranks compatible, eligible donors with reasons and picks just enough to alert. Click **Send alerts**.
3. **Donor window** (within 15 s, or refresh): the dashboard shows *A blood bank needs your help* → **Reply in Notifications** → **I can come**.
4. **Admin**: **Simulate donor replies (demo)** → **Mark donated** → stock goes up; open Blood Stock again.
5. **Organizer → Insights & Planner**: donors to re-invite (return prediction) and the campaign planner → **Create this campaign**. **Bookings & Check-in** → mark donated / no-show.
6. **Donor → Eligibility Check**: Amira now has to wait 90 days — the rules engine explains why.
7. **Admin → Users & Organizers** (approve a new donor as organizer), **AI Models** and **Donation Trends**.
8. **Donor → HemoScan AI**: try **Take a photo** with the *Phone photo* sample (or your webcam), or download the *Latest FBC* sample → upload it → check the highlighted values → **Confirm and analyse**. Show the microcytic pattern, the Hb drop vs the two earlier reports, the donation note, the assistant (*“Does this mean I have anaemia?”*) and **Summary for my doctor**. Then try the *SI units* and *Scanned* samples.

## 3. Load real Malaysian donation records (recommended)

Same as v1 — powers the admin **Donation Trends** page:

```powershell
python scripts/download_data.py      # already included in v6: data/donations_state.csv
# or: python scripts/download_data.py --local "C:\path\to\blood_donations_state.csv"
python scripts/train_models.py       # ~2 min: trains every region × blood group, writes models/ + docs/MODEL_REPORT.md
python scripts/train_models.py --quick   # national series only (~15 s)
```

**Source:** [Ministry of Health Malaysia / National Blood Centre, Daily Blood Donations by Blood Group & State](https://data.moh.gov.my/data-catalogue/blood_donations_state), **CC BY 4.0**. It reports donations collected only — not hospital usage or stock — so the Blood Stock outlook uses simulated stock movements.

## 4. AI features

| # | Feature | How it works | File |
|---|---|---|---|
| 1 | **Shortage outlook** | Per blood type, three methods compete (same weekday last week · 4-week weekday average · Random Forest) under rolling-origin cross-validation; the lowest error wins (simpler wins ties). Stock is projected 7 days ahead against the safe level | `ai/stock.py`, `forecast.py` |
| 2 | **Smart donor matching** | Compatibility + eligibility filter → score (distance, past reply rate, exact type, regular donor, alert fatigue, no-shows) → alerts enough donors to cover units × 1.5 | `ai/matching.py` |
| 3 | **Eligibility check** | Rules engine decides; the LLM only explains. Medical questions are blocked before reaching the LLM | `ai/eligibility.py`, `ai/assistant.py`, `ai/llm.py` |
| 4 | **Donor return prediction** | scikit-learn logistic regression on donation history; 5-fold cross-validated AUC, Brier score, calibration and results by age band / area | `ai/churn.py`, `ai/evaluation.py` |
| + | **Campaign planner** | Where (most eligible compatible donors) and which weekday (best collection day) to hold a drive | `ai_routes.py` |
| v1 | **Donation trends** | Same model selection on official MOH data (all states, 3 years); saved models are loaded when they match the data file | `forecast.py`, `scripts/train_models.py` |
| v6 | **Fairness check** | Matching is simulated for every centre × blood type; selection rates by age band / area / distance are compared with the four-fifths rule and explained | `ai/evaluation.py` |

## 5. HemoScan AI (new in v3)

A private report viewer for donors: **upload → check → analyse → explain → history**.

| Step | What happens | File |
|---|---|---|
| 1. PDF upload & extraction | PyMuPDF reads each word with its position, rebuilds table rows, matches ~20 biomarker names (Hb, MCV, PLT, differential…), units, H/L flags and lab reference ranges. Converts SI units (g/L → g/dL, L/L → %, x10³/µL → x10⁹/L). **Scanned PDFs and photos (v4) are read with OCR but every value is marked “Check” and must be confirmed** — without OCR the app asks for manual entry. Limits: 10 MB, 10 pages (OCR: first 3), no passwords | `ai/hemoscan/extract.py`, `biomarkers.py` |
| 2. Editable results | Page image of the original report with boxes where each value was read (hover a row to find it). Confidence per value (high / check / low); missing units, missing ranges, implausible values and not-found core tests are highlighted. User must tick *“I have checked these values”* before analysis; server re-validates units and plausible ranges | `static/hemoscan.js`, `hemoscan_routes.py` |
| 3. Rules-based patterns | 17 transparent rules separate from the language model, e.g. low Hb + low MCV (microcytic pattern), RDW hint, Mentzer index, macrocytic, low platelets + low WBC (dengue pattern), pancytopenia, neutrophilia… Each finding shows **why it fired**, possible associations, usual next steps and references. Urgent placeholder thresholds (e.g. Hb < 7) are shown first. Status: *pending clinician review* | `ai/hemoscan/rules.py` |
| 4. AI explanation & assistant | The LLM only explains rule findings from confirmed values (never raw PDF text). Without a key → template explanation + curated FAQ. Guardrails block diagnosis (“Do I have…?”) and treatment/dose questions | `ai/hemoscan/interpret.py` |
| 5. Private history | Reports + structured results saved per donor; trend chart per biomarker with the lab range band; “since your previous report” changes (Hb drop ≥ 1 g/dL, platelets −30 %, MCV falling); CSV export; printable **summary for my doctor** (Print → Save as PDF); edit, reopen, delete | `hemoscan_routes.py` |

**Extras added:** donation advice (Hb vs a placeholder 12.5 g/dL minimum + frequent-donor iron note using the donor's own donation count), HemoScan Hb shown on the Eligibility page (advice only, never changes the verdict), questions to ask your doctor, 3 fictional sample PDFs (table layout, SI units, scanned), demo donor seeded with 2 earlier reports for the trend chart.

**Privacy:** donor-only and owner-only (other users get 404; organizers/admins 403). PDFs are stored with random names in `hemoscan_reports/` next to the database (set `HEMOLINK_REPORT_DIR` to change), served with `no-store`; delete removes the file and results. Only the PDF view endpoint may be framed (same origin).

**Before real use:** every rule, threshold and reference in `ai/hemoscan/rules.py` must be reviewed and signed off by a clinician (fill `REVIEW`), and ranges should come from the lab whenever possible.

## 6. HemoCare + camera (new in v4)

| Part | What it does | File |
|---|---|---|
| **Take a photo** (HemoScan) | Live camera (laptop webcam / phone) or choose a photo. The photo is shrunk in the browser, stored as a one-page PDF, then read with OCR (**RapidOCR**, pip-only — no extra software). Tilt is corrected, common unit misreads fixed, unreadable units flagged. **Every OCR value is marked “Check” (never high confidence) and must be confirmed.** Scanned PDFs use the same OCR. If no OCR is installed → manual entry beside the photo | `ai/hemoscan/ocr.py`, `static/hemoscan.js` |
| **Medical Knowledge** | 9 plain-language guides: anaemia, iron deficiency, thalassaemia, platelet disorders, dengue, B12 & folate, white cells, blood pressure, medicines & donating. Each: what it is, signs, causes, tests, *what doctors may consider* (no doses), **what it means for donating**, **when to get urgent care**, references. HemoScan findings link straight to the matching guides | `ai/hemocare/knowledge.py` |
| **Medication History** | Private medicine list (name, type auto-detected, what for, label text, start / last dose). Each medicine is checked against example waiting periods (antibiotics, isotretinoin, finasteride, dutasteride, blood thinners …). A waiting period **defers the Eligibility Check and removes the donor from urgent-alert matching** until it ends | `ai/hemocare/meds.py`, `hemocare_routes.py` |
| **Donation Preparation** | Eligibility, latest HemoScan Hb, medicines to mention (current + last 90 days), checklist, printable screening summary | `hemocare_routes.py` |

**Before real use:** the medicine waiting periods are examples from US blood-service lists plus HemoLink's 7-day antibiotic placeholder — confirm every one with Pusat Darah Negara. Knowledge guides are pending clinician review.

**OCR install note:** `rapidocr_onnxruntime` (in `requirements.txt`) pulls in onnxruntime and OpenCV (~60 MB). If it fails to install on your computer, delete that line — everything else works and photos fall back to manual entry. The live camera needs `localhost` or HTTPS; on a phone over plain HTTP use **Choose a photo** (it still opens the phone camera).

## 7. New design + campaign map (v5)

| Part | What it does |
|---|---|
| Login | Crimson brand panel (“Every drop. Every connection. Every life.”) + cream sign-in panel with icon fields and **Role selection** demo tiles |
| Donor dashboard | “Good afternoon, Amira 👋” + outlined cards with heart badges: **Donor Milestones** (original blood-drop mascot, progress to next milestone), **Next Eligibility Date**, **Upcoming Campaigns** (with distance), My Blood Health, Blood Needed Now, Latest Updates |
| Find Campaigns | **Leaflet map** (OpenStreetMap tiles) with a pin per campaign, **Use my location** (browser GPS; falls back to your profile city), distance + rough drive time on every card, **≤10/25/50 km filters**, nearest/soonest sort, **Directions** (opens Google Maps), “Map” button flies to the pin |
| Whole app | Crimson/cream tokens, pill buttons, solid-red active menu item; organizer/admin pages get the same theme |

Notes: campaign locations are approximate (known demo venues, otherwise the city centre plus a small offset; new campaigns get the same). GPS needs `localhost` or HTTPS and the user's permission. Distances are straight-line; drive time assumes ~35 km/h with a 1.3× road factor. Map tiles need internet. Leaflet 1.9.4 is bundled in `static/vendor/leaflet` (BSD-2-Clause); map data © OpenStreetMap contributors — keep the attribution and follow the OSM tile usage policy (for a public deployment use a tile provider or your own tiles).

## 8. Folder structure

```text
hemolink/
├── app.py            # v1 FastAPI app: accounts, campaigns, bookings, inventory, notifications (+ new tables)
├── ai_routes.py      # v2 endpoints: outlook, urgent requests, alerts, eligibility, feedback, reports, models
├── ai/               # AI modules: stock, matching, eligibility, churn, assistant, llm, schemas
│   ├── hemoscan/     # v3: biomarkers, extract (PyMuPDF), ocr (v4), rules, interpret, samples
│   └── hemocare/     # v4: knowledge (guides), meds (waiting periods)
├── hemoscan_routes.py # v3: HemoScan upload/photo/review/confirm/history/export/summary/assistant API
├── hemocare_routes.py # v4: HemoCare knowledge, medication history, donation preparation API
├── forecast.py       # Random Forest (shared by donation trends and shortage outlook)
├── seed.py           # synthetic donors, stock history, reply history (demo only)
├── notifier.py       # v6: email / SMS / web-push delivery + bilingual message templates + outbox log
├── notify_routes.py  # v6: alert settings, push subscribe, delivery log, scheduled reminders, /sw.js
├── scripts/          # download_data.py, train_models.py (v6)
├── models/           # v6: saved forecast models + metrics.json (joblib files are rebuilt by train_models.py)
├── docs/MODEL_REPORT.md
├── static/           # index.html, app.js, hemoscan.js, hemocare.js, alerts.js + i18n.js (v6), sw.js, style.css, vendor/leaflet
└── tests/            # test_app.py (7) + test_ai.py (10) + test_hemoscan.py (13) + test_hemocare.py (4)
```

## 9. API summary (v2 – v5)

- Outlook: `GET /api/outlook`
- HemoScan photo: `POST /api/hemoscan/reports/photo` (multipart: file = JPG/PNG/WebP, consent); samples include `photo`
- HemoCare (donor only, own data): `GET /api/hemocare/overview`, `GET /api/hemocare/articles/{id}`, `GET|POST /api/hemocare/meds`, `PUT|DELETE /api/hemocare/meds/{id}`, `POST /api/hemocare/meds/{id}/stop`, `GET /api/hemocare/prep`, `GET /api/hemocare/prep/summary` (printable)
- Campaigns now include `lat`/`lng`; `POST /api/campaigns` accepts optional `lat`/`lng` (else venue/city location)
- Users (admin): `GET /api/admin/users?q=&role=`, `PATCH /api/admin/users/{id}/role` (`donor` ↔ `organizer`)
- Urgent requests (admin): `GET/POST /api/requests`, `GET /api/requests/{id}`, `POST /api/requests/{id}/alerts|simulate|close`
- Alerts: `GET /api/my-alerts`, `POST /api/alerts/{id}/respond` (donor), `POST /api/alerts/{id}/donated` (admin)
- Eligibility: `GET /api/eligibility`, `POST /api/eligibility/check`
- Feedback & check-in: `POST /api/feedback`, `POST /api/organizer/bookings/{id}/status`
- Reports & models: `GET /api/reports` (organizer), `GET /api/models` (admin)
- Assistant: `POST /api/assistant` (guardrails → LLM if configured → FAQ)
- HemoScan (donor only, own reports): `GET /api/hemoscan/catalog`, `GET /api/hemoscan/samples/{latest|dengue|scanned}`, `POST /api/hemoscan/reports/upload` (multipart: file, consent), `POST /api/hemoscan/reports/manual`, `GET /api/hemoscan/reports`, `GET|DELETE /api/hemoscan/reports/{id}`, `GET /api/hemoscan/reports/{id}/file`, `GET /api/hemoscan/reports/{id}/page/{n}` (PNG), `POST /api/hemoscan/reports/{id}/confirm|reopen|ask`, `GET /api/hemoscan/reports/{id}/summary`, `GET /api/hemoscan/history`, `GET /api/hemoscan/export.csv`

All v1 endpoints, role checks, the `X-HemoLink-Request` header check and signed cookies are unchanged.

## 10. Safety, privacy and limitations

- **Student prototype, not a medical device.** Screening staff make every final decision.
- **Eligibility rules follow Pusat Darah Negara (checked 8 Nov 2026, sources in `ai/eligibility.py` and on the Eligibility page):** age 17 (parent's written consent) to 65, first-time donors up to 60, regular donors 66–70 with a yearly check-up; weight ≥ 45 kg; Hb ≥ 12.5 g/dL on the day; men every 3 months, women every 4; 15 questions from the PDN donor form (antibiotics 2 weeks, dental 24 h, tattoo / piercing / bekam / acupuncture 6 months, dengue 6 months, surgery or transfusion 6 months, vaccine 4 weeks → staff, period, pregnancy / breastfeeding / birth 6 months). It is a guide — the doctor at the drive decides. Medicine waiting periods other than antibiotics are not published by PDN and remain examples.
- Stock movements, synthetic donors, centres ("HemoLink Centre …") and alert replies are **fictional**. "Simulate donor replies" only touches synthetic donors.
- **HemoScan is educational, not a diagnosis.** It shows possible associations; rules and urgent/donation thresholds are placeholders pending clinician review. OCR values (photos / scanned PDFs) are never trusted without the donor's confirmation. Health data is sensitive — for a hosted demo use only the fictional sample PDFs, and add encryption at rest, retention limits and a consent record (PDPA 2010) before real users.
- **HemoCare is educational.** No doses or treatment instructions; medicine waiting periods are placeholders and staff decide. Medicine lists are private to the donor (organizers/admins get 403; other donors 404).
- Alerts reach donors in the app and, when configured, by email (SMTP), SMS (Twilio) and web push. Without settings they run in **demo mode**: nothing leaves the server and every attempt is listed in the admin's delivery log. Synthetic donors never get outside messages. Phone numbers and emails are masked in the log.
- Bahasa Malaysia covers the app's menus, buttons, forms and messages. Names, campaign titles/descriptions, HemoCare medical guides and HemoScan findings stay in English (a note says so); AI answers follow the chosen language when an AI key is set.
- **Security & PDPA (v6.1):** rate limits (300 API calls/min per IP, 20 sign-ins/min, 20 AI questions/min, 10 uploads/10 min), a 15-minute lock after 5 wrong passwords, Content-Security-Policy + HSTS (production) + Permissions-Policy headers, **uploaded report files encrypted at rest** (Fernet; key in `HEMOLINK_DATA_KEY` or `data_key.txt` — back it up), privacy-notice consent at sign-up and for every HemoScan upload (recorded with version and time), **Download my data** (JSON) and **Delete my account** in My Profile, original report files deleted after 12 months and the delivery log after 90 days. Privacy notice: `static/privacy.html`.
- Still to do before real patients: SQLite → a managed database with backups, encrypting the database itself, an audit log of staff access, a data protection officer and a reviewed privacy notice. Set `HEMOLINK_SECRET_KEY` and `HEMOLINK_ENV=production` for any hosted demo.

## 11. Automated checks

```powershell
python -m pytest -q
```

54 tests (v6.1 adds `tests/test_security.py` and PDN rule tests; v6 adds `tests/test_ml.py` — model selection, wide MOH layout, evaluation/fairness — and `tests/test_notify.py` — alert settings, Malay messages, booking alerts, reminders run once, map pin + location edit, push subscription, AI language). Earlier: 7 original v1 tests, 10 for the AI features and roles, 13 for HemoScan (incl. photo OCR) and 4 for HemoCare (waiting periods, eligibility + matching deferral, privacy, guides) (table + SI-unit extraction, scanned → manual, missing-unit confidence, microcytic rule, urgent ordering, typical ranges, assistant guardrails, full upload → confirm → trend → export → summary loop, unit/plausibility validation, PDF-only + consent, owner-only privacy).

## 12. What's new in v6

### Machine learning
| Part | What changed |
|---|---|
| Real data | `data/donations_state.csv` (MOH, 2006 → Oct 2026, all states) is included and read in its wide layout |
| Per-type model choice | Each region × blood group picks its own method; e.g. O− collections use “same weekday last week” because the Random Forest was worse there |
| Validation | Rolling-origin cross-validation (4–8 cut points × 7 days) instead of one 80/20 split; MAE ± spread shown on the Trends and AI Models pages |
| Training script | `scripts/train_models.py` saves models + `models/metrics.json` and writes `docs/MODEL_REPORT.md` |
| Fairness | Return prediction and donor matching are checked by age band and area (four-fifths rule). Current finding: donors 45+ are selected a little less often (ratio 0.75–0.79), mainly because of distance and fewer past donations — shown with that explanation on AI Models |

### Alerts (email · SMS · push) and reminders
| Who | Gets |
|---|---|
| Donor | Urgent request (email + SMS + push) · booking confirmed / cancelled · reminder the day before · “you can donate again” · new drive within 25 km · donation recorded |
| Organizer | Donor booked / cancelled (with slots filled) · donor feedback · role approved |
| Admin | Donor replied “I can come” to an urgent request · delivery log with **Run reminders now** and **Send me a test** |

Everyone sets language, email, SMS (with phone number), push (“Enable on this device”) and nearby-drive alerts in **My Profile → Alerts & language**. Push needs HTTPS or `localhost`; on iPhone add HemoLink to the Home Screen first.

### Bahasa Malaysia
EN | BM switch on the login page and the top bar (also in the profile). The choice is saved to the account, so emails / SMS / push and in-app messages arrive in the same language. Dates switch to Malay (e.g. *Ahd, 8 November 2026*).

### Pick location on map (organizers)
**Create campaign** has a map: **Find venue on map** (OpenStreetMap search), **Use my location**, or click / drag the pin. Each campaign card has **Edit location**. Points outside Malaysia are refused. Creating a drive tells nearby donors who opted in.

New API: `PATCH /api/me/lang` · `GET|PUT /api/notify/settings` · `POST|DELETE /api/push/subscribe` · `POST /api/notify/test` · `GET /api/admin/outbox` · `POST /api/admin/jobs/run` · `PATCH /api/campaigns/{id}/location` · `POST /api/admin/llm/test` · `GET /sw.js`

## 13. v6.1 — official rules, security and setup guide

| Area | What changed |
|---|---|
| Eligibility | Rules rebuilt from PDN's donor registration form and FAQ (see section 10); new optional **Sex** field sets the 3- / 4-month gap; sources listed on the Eligibility page |
| Security | Rate limits, login lock, strict security headers, encrypted report files |
| Privacy (PDPA) | Consent records, privacy notice, Download my data, Delete my account, automatic retention |
| Setup | `docs/SETUP_GUIDE.md`: model training, Gmail / Twilio, push on a real phone |

Tests: 54 (adds `tests/test_security.py` and the PDN rule tests).

## License and data usage

HemoLink AI is licensed under the **GNU AGPL-3.0-or-later** (`LICENSE`, credits in `NOTICE.md`). If you host a changed
version, set `HEMOLINK_SOURCE_URL` to your public repository — the app's **Source code** links (sign-in page and My
Profile) send people there, as AGPL section 13 requires. Official KKMNOW data is **CC BY 4.0** and must be attributed.

**PyMuPDF** (used by HemoScan) is dual-licensed: **AGPL-3.0** or a commercial licence from Artifex — that is why HemoLink is AGPL. To relicense HemoLink under MIT later, swap the extractor (e.g. `pdfplumber` + `pypdfium2`) in `ai/hemoscan/extract.py` or buy a commercial PyMuPDF licence.
