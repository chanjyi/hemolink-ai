"""HemoLink AI hackathon prototype (v2: v1 + AI features). Local SQLite, no hospital integrations."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
import hashlib
import hmac
import os
import re
import secrets
import sqlite3

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from typing import Literal, Optional

from dotenv import load_dotenv

from pydantic import BaseModel, Field
from forecast import get_forecast, REGIONS, GROUPS
from ai import llm
import security
from fastapi.responses import JSONResponse
from seed import coords, seed_demo, venue_coords

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")  # optional: LLM key, secret key
DB_PATH = Path(os.environ.get("HEMOLINK_DB_PATH", str(ROOT / "hemolink_v2.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
SECRET = os.getenv("HEMOLINK_SECRET_KEY") or secrets.token_urlsafe(32)
SESSION = URLSafeTimedSerializer(SECRET, salt="hemolink-demo-v1")
COOKIE = "hemolink_session"
APP_ENV = os.getenv("HEMOLINK_ENV", "development")
app = FastAPI(title="HemoLink AI Prototype", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@contextmanager
def connect():
    db = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 15000")
    try:
        yield db
    finally:
        db.close()


def record_consent(db, user_id: int, kind: str) -> None:
    """PDPA: keep a record of what the person agreed to, and which version of the notice."""
    db.execute("INSERT INTO consents(user_id,kind,version) VALUES(?,?,?)", (user_id, kind, security.PRIVACY_VERSION))


def rows(result):
    return [dict(x) for x in result.fetchall()]


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 310_000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password, stored):
    try:
        salt, digest = stored.split(":")
        return hmac.compare_digest(hash_password(password, salt), stored)
    except (ValueError, TypeError):
        return False


def initialize():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('donor','organizer','admin')),
          blood_type TEXT DEFAULT 'Unknown', city TEXT DEFAULT '',
          lat REAL, lng REAL, birth_year INTEGER, weight_kg REAL,
          no_shows INTEGER NOT NULL DEFAULT 0, centre_id TEXT,
          is_synthetic INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS campaigns (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
          venue TEXT NOT NULL, city TEXT NOT NULL, event_date TEXT NOT NULL,
          description TEXT NOT NULL, organizer_id INTEGER NOT NULL REFERENCES users(id),
          status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS slots (
          id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
          start_time TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 1000)
        );
        CREATE TABLE IF NOT EXISTS appointments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, donor_id INTEGER NOT NULL REFERENCES users(id),
          slot_id INTEGER NOT NULL REFERENCES slots(id),
          status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled','donated','no_show')) DEFAULT 'confirmed',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(donor_id, slot_id)
        );
        CREATE TABLE IF NOT EXISTS inventory (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          blood_type TEXT NOT NULL, component TEXT NOT NULL DEFAULT 'Red blood cells',
          units INTEGER NOT NULL CHECK(units >= 0),
          threshold INTEGER NOT NULL CHECK(threshold >= 0),
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(blood_type, component)
        );
        CREATE TABLE IF NOT EXISTS notifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
          title TEXT NOT NULL, body TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS centres (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL, lat REAL NOT NULL, lng REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS donations (
          id INTEGER PRIMARY KEY AUTOINCREMENT, donor_id INTEGER NOT NULL REFERENCES users(id),
          donated_on TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'history'
        );
        CREATE TABLE IF NOT EXISTS stock_history (
          date TEXT NOT NULL, blood_type TEXT NOT NULL,
          collected INTEGER NOT NULL, used INTEGER NOT NULL, PRIMARY KEY(date, blood_type)
        );
        CREATE TABLE IF NOT EXISTS urgent_requests (
          id INTEGER PRIMARY KEY AUTOINCREMENT, centre_id TEXT NOT NULL REFERENCES centres(id),
          blood_type TEXT NOT NULL, units INTEGER NOT NULL CHECK(units BETWEEN 1 AND 100),
          needed_by TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','fulfilled','closed')),
          created_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS alerts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER NOT NULL REFERENCES urgent_requests(id),
          donor_id INTEGER NOT NULL REFERENCES users(id), score REAL NOT NULL DEFAULT 0,
          reasons TEXT NOT NULL DEFAULT '[]', sent_at TEXT NOT NULL,
          response TEXT CHECK(response IN ('yes','no')), responded_at TEXT,
          donated INTEGER NOT NULL DEFAULT 0, UNIQUE(request_id, donor_id)
        );
        CREATE TABLE IF NOT EXISTS feedback (
          id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
          donor_id INTEGER NOT NULL REFERENCES users(id), rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
          comment TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(campaign_id, donor_id)
        );
        CREATE TABLE IF NOT EXISTS hemo_reports (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
          source TEXT NOT NULL CHECK(source IN ('pdf','manual')), original_name TEXT, stored_name TEXT,
          page_count INTEGER NOT NULL DEFAULT 0, report_date TEXT, lab_name TEXT NOT NULL DEFAULT '',
          sex TEXT CHECK(sex IN ('female','male')),
          status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','confirmed')),
          extraction TEXT, analysis TEXT, explanation TEXT, used_llm INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, confirmed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS hemo_results (
          id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL REFERENCES hemo_reports(id) ON DELETE CASCADE,
          biomarker TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL, ref_low REAL, ref_high REAL,
          ref_source TEXT NOT NULL DEFAULT 'lab', flag TEXT NOT NULL DEFAULT 'normal', edited INTEGER NOT NULL DEFAULT 0,
          confidence REAL, UNIQUE(report_id, biomarker)
        );
        CREATE INDEX IF NOT EXISTS idx_hemo_reports_user ON hemo_reports(user_id, report_date);
        CREATE TABLE IF NOT EXISTS hemo_meds (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
          name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'auto', reason TEXT NOT NULL DEFAULT '',
          dose_note TEXT NOT NULL DEFAULT '', start_date TEXT, end_date TEXT, notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_hemo_meds_user ON hemo_meds(user_id);
        CREATE INDEX IF NOT EXISTS idx_donations_donor ON donations(donor_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_donor ON alerts(donor_id);
        CREATE INDEX IF NOT EXISTS idx_bookings_slot_status ON appointments(slot_id,status);
        CREATE INDEX IF NOT EXISTS idx_slots_campaign ON slots(campaign_id);
        """)
        demo_users = [
            ("Amira Hassan", "donor@demo.com", "donor", "O+", "Cyberjaya"),
            ("Daniel Lim", "organizer@demo.com", "organizer", "Unknown", "Kuala Lumpur"),
            ("Dr. Sara Tan (Demo)", "admin@demo.com", "admin", "Unknown", "Putrajaya"),
        ]
        for name,email,role,blood,city in demo_users:
            db.execute("INSERT OR IGNORE INTO users(name,email,password_hash,role,blood_type,city) VALUES(?,?,?,?,?,?)",
                       (name,email,hash_password("Demo123!"),role,blood,city))
        organizer = db.execute("SELECT id FROM users WHERE email='organizer@demo.com'").fetchone()["id"]
        count = db.execute("SELECT COUNT(*) AS n FROM campaigns").fetchone()["n"]
        if not count:
            examples = [
                ("Community Blood Drive", "MMU Cyberjaya Campus", "Cyberjaya", 3, "Join our community blood donation initiative with our healthcare partners.", [("09:00",15),("10:30",12),("13:30",18)]),
                ("Give Hope, Give Blood", "Sunway Pyramid Convention Centre", "Subang Jaya", 6, "A weekend donation campaign to support community blood collection.", [("10:00",20),("12:00",18),("15:00",16)]),
                ("Campus Heroes Donation Day", "Universiti Malaya", "Kuala Lumpur", 10, "Students and staff come together for a meaningful donation day.", [("09:30",20),("11:30",15)]),
                ("Putrajaya Health Week", "Presint 3 Community Hall", "Putrajaya", 15, "Support local blood donation and health awareness activities.", [("09:00",25),("14:00",25)]),
            ]
            for title,venue,city,delta,description,slots in examples:
                cid = db.execute("INSERT INTO campaigns(title,venue,city,event_date,description,organizer_id) VALUES(?,?,?,?,?,?)",
                    (title,venue,city,(date.today()+timedelta(days=delta)).isoformat(),description,organizer)).lastrowid
                for st,cap in slots:
                    db.execute("INSERT INTO slots(campaign_id,start_time,capacity) VALUES(?,?,?)",(cid,st,cap))
        for blood,units,threshold in [("A+",42,25),("A-",12,15),("B+",38,25),("B-",9,12),("AB+",18,12),("AB-",7,10),("O+",54,35),("O-",14,22)]:
            db.execute("INSERT OR IGNORE INTO inventory(blood_type,units,threshold) VALUES(?,?,?)",(blood,units,threshold))
        donor = db.execute("SELECT id FROM users WHERE email='donor@demo.com'").fetchone()["id"]
        if not db.execute("SELECT 1 FROM notifications WHERE user_id=?",(donor,)).fetchone():
            db.execute("INSERT INTO notifications(user_id,title,body) VALUES(?,?,?)",
                (donor,"Welcome to HemoLink AI","Find donation campaigns near you and book your first appointment."))
        seed_demo(db)  # synthetic donors, stock history and reply history for the AI features
        # v6: notification preferences, delivery log, push devices, reminders
        ucols = {r[1] for r in db.execute("PRAGMA table_info(users)")}
        for col, ddl in [("phone", "TEXT"), ("notify_email", "INTEGER NOT NULL DEFAULT 1"),
                         ("notify_sms", "INTEGER NOT NULL DEFAULT 0"), ("notify_push", "INTEGER NOT NULL DEFAULT 1"),
                         ("notify_nearby", "INTEGER NOT NULL DEFAULT 1"), ("lang", "TEXT NOT NULL DEFAULT 'en'"),
                         ("eligible_notice_for", "TEXT"), ("sex", "TEXT")]:
            if col not in ucols:
                db.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
        if "reminded_at" not in {r[1] for r in db.execute("PRAGMA table_info(appointments)")}:
            db.execute("ALTER TABLE appointments ADD COLUMN reminded_at TEXT")
        db.executescript("""
          CREATE TABLE IF NOT EXISTS consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            kind TEXT NOT NULL, version TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
          CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event TEXT NOT NULL, channel TEXT NOT NULL,
            to_addr TEXT, subject TEXT, status TEXT NOT NULL, error TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
          CREATE TABLE IF NOT EXISTS push_subs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), endpoint TEXT NOT NULL UNIQUE,
            p256dh TEXT NOT NULL, auth TEXT NOT NULL, user_agent TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
          CREATE INDEX IF NOT EXISTS idx_outbox_time ON outbox(created_at);
        """)
        # v5: campaign locations for the map (older databases get the columns added)
        cols = {r[1] for r in db.execute("PRAGMA table_info(campaigns)")}
        if "lat" not in cols:
            db.execute("ALTER TABLE campaigns ADD COLUMN lat REAL")
            db.execute("ALTER TABLE campaigns ADD COLUMN lng REAL")
        for c in db.execute("SELECT id, venue, city FROM campaigns WHERE lat IS NULL OR lng IS NULL").fetchall():
            db.execute("UPDATE campaigns SET lat=?, lng=? WHERE id=?", (*venue_coords(c["venue"], c["city"]), c["id"]))
        # v3.1: urgent requests belong to the blood bank (admin), so the demo admin runs the KL centre
        db.execute("UPDATE users SET centre_id='c_kl' WHERE email='admin@demo.com' AND centre_id IS NULL")
        db.commit()


initialize()


class LoginBody(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=128)


class SignupBody(BaseModel):
    name: str = Field(min_length=2,max_length=90)
    email: str = Field(max_length=200)
    password: str = Field(min_length=8,max_length=128)
    blood_type: str = "Unknown"
    city: str = Field(default="",max_length=80)
    agree_privacy: bool = False


class ProfileBody(BaseModel):
    name: str = Field(min_length=2,max_length=90)
    blood_type: str = "Unknown"
    city: str = Field(default="",max_length=80)
    birth_year: Optional[int] = Field(default=None, ge=1920, le=date.today().year - 16)
    weight_kg: Optional[float] = Field(default=None, ge=30, le=250)
    sex: Optional[Literal["female", "male"]] = None  # optional; sets the donation interval (women 4 months, men 3)


class CampaignBody(BaseModel):
    title: str = Field(min_length=4,max_length=120)
    venue: str = Field(min_length=4,max_length=120)
    city: str = Field(min_length=2,max_length=80)
    event_date: date
    description: str = Field(default="",max_length=900)
    times: list[str] = Field(min_length=1,max_length=10)
    capacity: int = Field(ge=1,le=250)
    lat: Optional[float] = Field(default=None, ge=0.5, le=7.5)     # optional pin; Malaysia's latitude range
    lng: Optional[float] = Field(default=None, ge=99.5, le=119.5)


class BookingBody(BaseModel):
    slot_id: int


class InventoryBody(BaseModel):
    units: int = Field(ge=0,le=100000)
    threshold: int = Field(ge=0,le=100000)


class AssistantBody(BaseModel):
    question: str = Field(min_length=2,max_length=500)


def user_from_request(request: Request):
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401,"Please sign in")
    try:
        uid = SESSION.loads(token,max_age=60*60*24)["id"]
    except (BadSignature, SignatureExpired, KeyError, TypeError):
        raise HTTPException(401,"Session expired. Sign in again")
    with connect() as db:
        user = db.execute("""SELECT id,name,email,role,blood_type,city,birth_year,weight_kg,sex,centre_id,lat,lng,lang,created_at
                             FROM users WHERE id=?""",(uid,)).fetchone()
    if not user:
        raise HTTPException(401,"Account not found")
    return dict(user)


def only(*roles):
    def role_check(user=Depends(user_from_request)):
        if user["role"] not in roles:
            raise HTTPException(403,"This action is not permitted for your role")
        return user
    return role_check


def session_cookie(response: Response, uid: int):
    response.set_cookie(COOKIE,SESSION.dumps({"id":uid}),max_age=86400,httponly=True,
                        samesite="lax",secure=(APP_ENV=="production"),path="/")


@app.middleware("http")
async def basic_security(request:Request, call_next):
    # Extra protection for JSON APIs against blind cross-site form requests.
    if request.url.path.startswith("/api/") and request.method in ("POST","PATCH","PUT","DELETE"):
        if request.headers.get("X-HemoLink-Request") != "app":
            return Response("Missing application request header",status_code=403)
    # AI answers follow the language the app is shown in (EN / BM toggle).
    llm.reply_lang.set("ms" if request.headers.get("X-HemoLink-Lang") == "ms" else "en")
    # Overall API limit per IP (stops scripted abuse; normal use is far below this).
    if request.url.path.startswith("/api/"):
        try:
            security.limit(f"api:{security.client_ip(request)}", 300, 60)
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=429, headers=exc.headers)
    response = await call_next(request)
    # HemoScan shows the donor's own PDF in an iframe on the same site; everything else may not be framed.
    pdf_view = request.url.path.startswith("/api/hemoscan/reports/") and request.url.path.endswith("/file")
    security.add_headers(response, frame_same_origin=pdf_view, production=APP_ENV == "production")
    return response


class LangBody(BaseModel):
    lang: str = Field(pattern="^(en|ms)$")


@app.patch("/api/me/lang")
def set_lang(body: LangBody, user=Depends(user_from_request)):
    with connect() as db:
        db.execute("UPDATE users SET lang=? WHERE id=?", (body.lang, user["id"]))
        db.commit()
    return {"ok": True, "lang": body.lang}


@app.get("/api/health")
def health():
    """Used by hosting platforms to check the app is up (no login needed)."""
    return {"ok": True, "env": APP_ENV}


@app.get("/")
def home():
    # no-cache so browsers always pick up new script versions after an update
    return FileResponse(ROOT / "static" / "index.html", headers={"Cache-Control": "no-cache"})


@app.post("/api/login")
def login(body: LoginBody,request:Request,response:Response):
    email = body.email.strip().lower()
    security.limit(f"login:{security.client_ip(request)}", 20, 60, "Too many sign-in attempts — please wait a minute.")
    security.check_login_allowed(email)
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        if not row or not verify_password(body.password,row["password_hash"]):
            security.login_failed(email)
            raise HTTPException(401,"Incorrect email or password")
        security.login_ok(email)
        session_cookie(response,row["id"])
        return {"ok":True,"role":row["role"]}


@app.post("/api/signup")
def signup(body:SignupBody,request:Request,response:Response):
    security.limit(f"signup:{security.client_ip(request)}", 10, 3600, "Too many new accounts from this network — try again later.")
    if not body.agree_privacy:
        raise HTTPException(422,"Please read and accept the privacy notice to create an account.")
    email = body.email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):
        raise HTTPException(422,"Please provide a valid email address")
    if body.blood_type not in ["Unknown","A+","A-","B+","B-","AB+","AB-","O+","O-"]:
        raise HTTPException(422,"Invalid blood type")
    with connect() as db:
        try:
            lat,lng = coords(body.city)
            uid = db.execute("INSERT INTO users(name,email,password_hash,role,blood_type,city,lat,lng) VALUES(?,?,?,?,?,?,?,?)",
                (body.name.strip(),email,hash_password(body.password),"donor",body.blood_type,body.city.strip(),lat,lng)).lastrowid
            record_consent(db, uid, "privacy_notice")
            db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409,"This email is already registered")
    session_cookie(response,uid)
    return {"ok":True,"role":"donor"}


@app.post("/api/logout")
def logout(response:Response):
    response.delete_cookie(COOKIE,path="/")
    return {"ok":True}


@app.get("/api/about")
def about():
    """AGPL-3.0 §13: people using the hosted app can get its source code."""
    return {"name": "HemoLink AI", "license": "AGPL-3.0-or-later",
            "source_url": os.getenv("HEMOLINK_SOURCE_URL", "https://github.com/")}


@app.get("/source", include_in_schema=False)
def source_code():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(os.getenv("HEMOLINK_SOURCE_URL", "https://github.com/"), status_code=307)


@app.get("/api/me")
def me(user=Depends(user_from_request)):
    return user


@app.patch("/api/me")
def update_me(body:ProfileBody,user=Depends(only("donor","organizer","admin"))):
    valid = ["Unknown","A+","A-","B+","B-","AB+","AB-","O+","O-"]
    if body.blood_type not in valid:
        raise HTTPException(422,"Invalid blood group")
    with connect() as db:
        lat,lng = coords(body.city)
        db.execute("UPDATE users SET name=?,blood_type=?,city=?,lat=?,lng=?,birth_year=?,weight_kg=?,sex=? WHERE id=?",
                   (body.name.strip(),body.blood_type,body.city.strip(),lat,lng,body.birth_year,body.weight_kg,body.sex,user["id"]))
        db.commit()
    return {"ok":True}


def campaigns_for(db, organizer_id=None):
    where = "WHERE c.organizer_id=?" if organizer_id else "WHERE c.event_date>=?"
    args = (organizer_id,) if organizer_id else (date.today().isoformat(),)
    entries = rows(db.execute(f"""SELECT c.*,u.name AS organizer FROM campaigns c JOIN users u ON c.organizer_id=u.id
                              {where} ORDER BY c.event_date,c.id""",args))
    for c in entries:
        c["slots"] = rows(db.execute("""SELECT s.id,s.start_time,s.capacity,
          (SELECT COUNT(*) FROM appointments a WHERE a.slot_id=s.id AND a.status='confirmed') AS booked
          FROM slots s WHERE s.campaign_id=? ORDER BY s.start_time""",(c["id"],)))
        for slot in c["slots"]:
            slot["remaining"] = max(0,slot["capacity"]-slot["booked"])
        c["total_capacity"] = sum(s["capacity"] for s in c["slots"])
        c["total_booked"] = sum(s["booked"] for s in c["slots"])
    return entries


@app.get("/api/campaigns")
def campaigns(user=Depends(user_from_request)):
    with connect() as db:
        return campaigns_for(db)


@app.post("/api/campaigns")
def create_campaign(body:CampaignBody,user=Depends(only("organizer"))):
    if body.event_date < date.today():
        raise HTTPException(422,"Campaign date must be today or later")
    times = list(dict.fromkeys(t.strip() for t in body.times))
    if len(times) != len(body.times) or not all(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",t) for t in times):
        raise HTTPException(422,"Times must be unique HH:MM values")
    with connect() as db:
        lat, lng = (body.lat, body.lng) if body.lat is not None and body.lng is not None else venue_coords(body.venue, body.city)
        cid = db.execute("INSERT INTO campaigns(title,venue,city,event_date,description,organizer_id,lat,lng) VALUES(?,?,?,?,?,?,?,?)",
            (body.title.strip(),body.venue.strip(),body.city.strip(),body.event_date.isoformat(),body.description.strip(),user["id"],lat,lng)).lastrowid
        for t in sorted(times):
            db.execute("INSERT INTO slots(campaign_id,start_time,capacity) VALUES(?,?,?)",(cid,t,body.capacity))
        notified = notify_nearby(db, cid, body.title.strip(), body.venue.strip(), body.city.strip(), body.event_date.isoformat(), lat, lng)
        db.commit()
    return {"id":cid,"message":"Campaign created","nearby_notified":notified}


NEARBY_KM = 25


def notify_nearby(db, cid, title, venue, city, event_date, lat, lng) -> int:
    """Tell real donors within 25 km (who opted in) about a new drive."""
    import math
    import notifier
    n = 0
    for u in db.execute("""SELECT id, lat, lng FROM users WHERE role='donor' AND is_synthetic=0 AND notify_nearby=1
                           AND lat IS NOT NULL AND lng IS NOT NULL""").fetchall():
        dlat, dlng = math.radians(u["lat"] - lat), math.radians(u["lng"] - lng)
        h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(u["lat"])) * math.sin(dlng / 2) ** 2
        km = 6371 * 2 * math.asin(math.sqrt(h))
        if km <= NEARBY_KM:
            notifier.event(db, u["id"], "new_campaign_nearby", url="/#campaigns", campaign=title, date=event_date,
                           venue=venue, city=city, km=f"{km:.1f}")
            n += 1
    return n


class LocationBody(BaseModel):
    lat: float = Field(ge=0.5, le=7.5)
    lng: float = Field(ge=99.5, le=119.5)


@app.patch("/api/campaigns/{campaign_id}/location")
def move_campaign(campaign_id: int, body: LocationBody, user=Depends(only("organizer"))):
    """Organizer drags the map pin to the exact venue entrance."""
    with connect() as db:
        c = db.execute("SELECT organizer_id FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
        if not c or c["organizer_id"] != user["id"]:
            raise HTTPException(404, "Campaign not found")
        db.execute("UPDATE campaigns SET lat=?, lng=? WHERE id=?", (round(body.lat, 6), round(body.lng, 6), campaign_id))
        db.commit()
    return {"ok": True}


@app.get("/api/organizer/campaigns")
def organizer_campaigns(user=Depends(only("organizer"))):
    with connect() as db:
        return campaigns_for(db,user["id"])


@app.get("/api/organizer/bookings")
def organizer_bookings(user=Depends(only("organizer"))):
    with connect() as db:
        return rows(db.execute("""SELECT a.id,a.status,a.created_at,c.title,c.event_date,s.start_time,
               u.name AS donor_name,u.blood_type,u.is_synthetic FROM appointments a
               JOIN slots s ON a.slot_id=s.id JOIN campaigns c ON c.id=s.campaign_id
               JOIN users u ON a.donor_id=u.id WHERE c.organizer_id=?
               ORDER BY c.event_date,a.created_at DESC""",(user["id"],)))


@app.post("/api/bookings")
def book(body:BookingBody,user=Depends(only("donor"))):
    with connect() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            slot = db.execute("""SELECT s.id,s.capacity,s.campaign_id,s.start_time,c.title,c.event_date,
                c.status FROM slots s JOIN campaigns c ON s.campaign_id=c.id WHERE s.id=?""",(body.slot_id,)).fetchone()
            if not slot or slot["event_date"]<date.today().isoformat() or slot["status"]!="active":
                raise HTTPException(404,"This appointment slot is not available")
            existing = db.execute("""SELECT a.id FROM appointments a JOIN slots s ON a.slot_id=s.id
                WHERE a.donor_id=? AND s.campaign_id=? AND a.status='confirmed'""",(user["id"],slot["campaign_id"])).fetchone()
            if existing:
                raise HTTPException(409,"You already have an appointment for this campaign")
            booked = db.execute("SELECT COUNT(*) AS n FROM appointments WHERE slot_id=? AND status='confirmed'",(body.slot_id,)).fetchone()["n"]
            if booked>=slot["capacity"]:
                raise HTTPException(409,"This appointment slot is full")
            old = db.execute("SELECT id FROM appointments WHERE donor_id=? AND slot_id=?",(user["id"],body.slot_id)).fetchone()
            if old:
                db.execute("UPDATE appointments SET status='confirmed',created_at=CURRENT_TIMESTAMP WHERE id=?",(old["id"],))
                aid=old["id"]
            else:
                aid=db.execute("INSERT INTO appointments(donor_id,slot_id) VALUES(?,?)",(user["id"],body.slot_id)).lastrowid
            import notifier
            notifier.event(db, user["id"], "booking_confirmed", url="/#bookings", campaign=slot["title"],
                           date=slot["event_date"], time=slot["start_time"])
            org = db.execute("SELECT organizer_id FROM campaigns WHERE id=?", (slot["campaign_id"],)).fetchone()
            if org and org["organizer_id"]:
                notifier.event(db, org["organizer_id"], "organizer_booking", url="/#bookings", donor=user["name"],
                               campaign=slot["title"], time=slot["start_time"], booked=booked + 1, capacity=slot["capacity"])
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {"id":aid,"message":"Booking confirmed"}


@app.get("/api/bookings")
def my_bookings(user=Depends(only("donor"))):
    with connect() as db:
        return rows(db.execute("""SELECT a.id,a.status,a.created_at,c.title,c.venue,c.city,
            c.event_date,s.start_time,c.id AS campaign_id,
            (SELECT f.rating FROM feedback f WHERE f.campaign_id=c.id AND f.donor_id=a.donor_id) AS my_rating
            FROM appointments a
            JOIN slots s ON a.slot_id=s.id JOIN campaigns c ON s.campaign_id=c.id
            WHERE a.donor_id=? ORDER BY c.event_date DESC,a.created_at DESC""",(user["id"],)))


@app.post("/api/bookings/{appointment_id}/cancel")
def cancel(appointment_id:int,user=Depends(only("donor"))):
    with connect() as db:
        booking=db.execute("""SELECT a.id,a.status,c.event_date,c.title,c.organizer_id,s.start_time FROM appointments a JOIN slots s ON a.slot_id=s.id
           JOIN campaigns c ON s.campaign_id=c.id WHERE a.id=? AND a.donor_id=?""",(appointment_id,user["id"])).fetchone()
        if not booking:
            raise HTTPException(404,"Booking not found")
        if booking["event_date"]<date.today().isoformat():
            raise HTTPException(409,"Past appointments cannot be cancelled")
        db.execute("UPDATE appointments SET status='cancelled' WHERE id=?",(appointment_id,))
        import notifier
        notifier.event(db, user["id"], "booking_cancelled", url="/#bookings", campaign=booking["title"])
        if booking["organizer_id"]:
            notifier.event(db, booking["organizer_id"], "organizer_cancel", url="/#bookings", donor=user["name"],
                           campaign=booking["title"], time=booking["start_time"])
        db.commit()
    return {"ok":True}


@app.get("/api/inventory")
def inventory(user=Depends(user_from_request)):
    with connect() as db:
        return rows(db.execute("SELECT *,CASE WHEN units<threshold THEN 'low' ELSE 'healthy' END AS stock_status FROM inventory ORDER BY blood_type"))


@app.patch("/api/inventory/{inventory_id}")
def update_inventory(inventory_id:int,body:InventoryBody,user=Depends(only("admin"))):
    with connect() as db:
        result=db.execute("UPDATE inventory SET units=?, threshold=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (body.units,body.threshold,inventory_id))
        if result.rowcount==0:
            raise HTTPException(404,"Inventory record not found")
        db.commit()
    return {"ok":True,"notice":"Simulation only. No hospital inventory updated."}


@app.get("/api/notifications")
def notifications(user=Depends(user_from_request)):
    with connect() as db:
        return rows(db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC,id DESC LIMIT 30",(user["id"],)))


@app.post("/api/notifications/read")
def read_notifications(user=Depends(user_from_request)):
    with connect() as db:
        db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?",(user["id"],))
        db.commit()
    return {"ok":True}


@app.get("/api/overview")
def overview(user=Depends(user_from_request)):
    with connect() as db:
        active=db.execute("SELECT COUNT(*) FROM campaigns WHERE event_date>=? AND status='active'",(date.today().isoformat(),)).fetchone()[0]
        total=db.execute("SELECT COUNT(*) FROM users WHERE role='donor'").fetchone()[0]
        bookings=db.execute("SELECT COUNT(*) FROM appointments WHERE status='confirmed'").fetchone()[0]
        low=db.execute("SELECT COUNT(*) FROM inventory WHERE units<threshold").fetchone()[0]
        own=db.execute("SELECT COUNT(*) FROM appointments WHERE donor_id=? AND status='confirmed'",(user["id"],)).fetchone()[0]
        organizer_campaigns=db.execute("SELECT COUNT(*) FROM campaigns WHERE organizer_id=?",(user["id"],)).fetchone()[0]
        open_requests=db.execute("SELECT COUNT(*) FROM urgent_requests WHERE status='open'").fetchone()[0]
        my_alerts=db.execute("""SELECT COUNT(*) FROM alerts a JOIN urgent_requests r ON r.id=a.request_id
                                WHERE a.donor_id=? AND a.response IS NULL AND r.status='open'""",(user["id"],)).fetchone()[0]
        my_donations=db.execute("SELECT COUNT(*) FROM donations WHERE donor_id=?",(user["id"],)).fetchone()[0]
        my_upcoming=db.execute("SELECT COUNT(*) FROM campaigns WHERE organizer_id=? AND event_date>=?",(user["id"],date.today().isoformat())).fetchone()[0]
        my_campaign_bookings=db.execute("""SELECT COUNT(*) FROM appointments a JOIN slots s ON s.id=a.slot_id JOIN campaigns c ON c.id=s.campaign_id
                                           WHERE c.organizer_id=? AND a.status='confirmed'""",(user["id"],)).fetchone()[0]
        my_rating=db.execute("""SELECT ROUND(AVG(f.rating),1) FROM feedback f JOIN campaigns c ON c.id=f.campaign_id
                                WHERE c.organizer_id=?""",(user["id"],)).fetchone()[0]
        organizers=db.execute("SELECT COUNT(*) FROM users WHERE role='organizer' AND is_synthetic=0").fetchone()[0]
    return {"active_campaigns":active,"total_donors":total,"confirmed_bookings":bookings,
            "low_stock_groups":low,"my_bookings":own,"my_campaigns":organizer_campaigns,
            "open_requests":open_requests,"my_open_alerts":my_alerts,"my_donations":my_donations,
            "my_upcoming_campaigns":my_upcoming,"my_campaign_bookings":my_campaign_bookings,"my_rating":my_rating,
            "organizers":organizers,
            "simulation":True}


@app.get("/api/forecast")
def forecast(region:str="Selangor",blood_type:str="all",user=Depends(user_from_request)):
    try:
        from forecast import regions
        return {**get_forecast(region,blood_type),"regions":regions()}
    except ValueError as e:
        raise HTTPException(422,str(e))


@app.post("/api/assistant")
def assistant(body:AssistantBody,user=Depends(user_from_request)):
    """Guardrails first, then the LLM (if a key is set), then the curated FAQ. Never medical advice."""
    from ai_routes import assistant_answer
    security.limit(f"ai:{user['id']}", 20, 60, "You're asking very fast — please wait a minute.")
    return assistant_answer(body.question,user)


# AI features (shortage outlook, urgent requests + donor matching, eligibility, reports, models)
from ai_routes import router as ai_router  # noqa: E402  (needs the helpers above)
app.include_router(ai_router)

# HemoScan AI (private FBC report reader, rules-based patterns, trends, export)
from hemoscan_routes import router as hemoscan_router  # noqa: E402
app.include_router(hemoscan_router)

# HemoCare (donor health library + medication history + donation preparation)
from hemocare_routes import router as hemocare_router  # noqa: E402
app.include_router(hemocare_router)

# Notifications: email / SMS / web push, preferences, delivery log, reminders (v6)
from notify_routes import router as notify_router, start_scheduler  # noqa: E402
app.include_router(notify_router)
start_scheduler(app)

# Personal data rights: download my data, delete my account, consent records, retention (v6.1)
from privacy_routes import router as privacy_router  # noqa: E402
app.include_router(privacy_router)
