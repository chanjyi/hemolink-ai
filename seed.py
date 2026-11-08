"""
Synthetic demo data for the AI features (all FICTIONAL — clearly marked in the UI).

Adds, on top of the v1 demo accounts and campaigns:
  * 5 collection centres and map coordinates for Klang Valley towns
  * 300 synthetic donor records (cannot log in) with donation history
  * 180 days of simulated daily stock movements per blood type (collected / used)
  * past urgent requests and how donors replied (training data for matching)
  * past campaigns with attended / no-show bookings and ratings (for reports)
"""
from __future__ import annotations

import math
import random
from datetime import date, timedelta

BLOOD_TYPES = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
# rough Malaysian donor shares; negatives boosted a little so the demo has some
TYPE_SHARE = {"O+": 0.385, "O-": 0.035, "A+": 0.235, "A-": 0.015, "B+": 0.255, "B-": 0.015, "AB+": 0.055, "AB-": 0.005}

AREAS = {
    "Kuala Lumpur": (3.139, 101.6869),
    "Cheras": (3.0847, 101.7417),
    "Setapak": (3.2, 101.7167),
    "Petaling Jaya": (3.1073, 101.6067),
    "Shah Alam": (3.0738, 101.5183),
    "Subang Jaya": (3.0565, 101.5851),
    "Klang": (3.0449, 101.4456),
    "Ampang": (3.15, 101.76),
    "Kajang": (2.9935, 101.7871),
    "Seri Kembangan": (3.0225, 101.7055),
    "Cyberjaya": (2.9213, 101.6559),
    "Putrajaya": (2.9264, 101.6964),
}

CENTRES = [
    ("c_kl", "HemoLink Centre Kuala Lumpur", "Kuala Lumpur"),
    ("c_sa", "HemoLink Centre Shah Alam", "Shah Alam"),
    ("c_pj", "HemoLink Centre Petaling Jaya", "Petaling Jaya"),
    ("c_kj", "HemoLink Centre Kajang", "Kajang"),
    ("c_pt", "HemoLink Centre Putrajaya", "Putrajaya"),
]

FIRST = ["Aina", "Hafiz", "Nurul", "Amir", "Siti", "Faizal", "Wei Ling", "Jun Hao", "Mei Xin", "Kai Wen",
         "Priya", "Arjun", "Kavitha", "Ravi", "Farah", "Izzat", "Hui Min", "Jia Hui", "Darren", "Aisyah",
         "Syafiq", "Nadia", "Vikram", "Deepa", "Zul", "Liyana", "Chee Keong", "Yvonne", "Haziq", "Anis"]
LAST = ["Rahman", "Ismail", "Abdullah", "Hassan", "Tan", "Lim", "Wong", "Lee", "Chong", "Ng",
        "Kumar", "Raj", "Nair", "Subramaniam", "Othman", "Yusof", "Goh", "Teo", "Krishnan", "Aziz"]

DEMAND_WEEKDAY = [1.1, 1.05, 1.0, 1.0, 0.95, 0.8, 0.75]   # Mon..Sun (Python weekday)
COLLECT_WEEKDAY = [0.9, 0.86, 0.86, 0.86, 0.9, 1.35, 1.25]
NETWORK_DAILY_USE = 60.0  # red-cell units per day across all centres (demo scale)
SYNTHETIC_DOMAIN = "@donors.hemolink.test"


def coords(city: str) -> tuple[float, float]:
    for name, c in AREAS.items():
        if name.lower() == (city or "").strip().lower():
            return c
    return AREAS["Kuala Lumpur"]


# Approximate public locations of the demo venues (for the campaign map; demo only)
VENUES = {
    "mmu cyberjaya campus": (2.9286, 101.6413),
    "sunway pyramid convention centre": (3.0731, 101.6069),
    "universiti malaya": (3.1210, 101.6538),
    "presint 3 community hall": (2.9172, 101.6855),
}


def venue_coords(venue: str, city: str) -> tuple[float, float]:
    """Known venue → its location; otherwise the city centre plus a small stable offset so pins don't overlap."""
    known = VENUES.get((venue or "").strip().lower())
    if known:
        return known
    lat, lng = coords(city)
    h = sum(ord(ch) * (i + 1) for i, ch in enumerate((venue or "").lower()))
    return round(lat + ((h % 21) - 10) * 0.0012, 5), round(lng + (((h // 21) % 21) - 10) * 0.0012, 5)


def iso(d: date) -> str:
    return d.isoformat()


def seed_demo(db, today: date | None = None) -> None:
    """Idempotent: does nothing if synthetic donors already exist."""
    if db.execute(f"SELECT 1 FROM users WHERE email LIKE '%{SYNTHETIC_DOMAIN}' LIMIT 1").fetchone():
        return
    today = today or date.today()
    rnd = random.Random(20261102)
    sig = lambda x: 1 / (1 + math.exp(-x))  # noqa: E731

    # ---------------- centres ----------------
    for cid, name, city in CENTRES:
        lat, lng = AREAS[city]
        db.execute("INSERT OR IGNORE INTO centres(id,name,city,lat,lng) VALUES(?,?,?,?,?)", (cid, name, city, lat, lng))

    # ---------------- v1 demo accounts get AI fields ----------------
    lat, lng = AREAS["Cyberjaya"]
    db.execute("""UPDATE users SET blood_type='O-', birth_year=2001, weight_kg=54, lat=?, lng=?
                  WHERE email='donor@demo.com'""", (lat, lng))
    donor = db.execute("SELECT id FROM users WHERE email='donor@demo.com'").fetchone()["id"]
    for days_ago in (470, 340, 215, 104):
        db.execute("INSERT INTO donations(donor_id,donated_on,source) VALUES(?,?,'history')", (donor, iso(today - timedelta(days=days_ago))))
    lat, lng = AREAS["Kuala Lumpur"]
    db.execute("UPDATE users SET centre_id='c_kl', lat=?, lng=? WHERE email='organizer@demo.com'", (lat, lng))
    lat, lng = AREAS["Putrajaya"]
    db.execute("UPDATE users SET lat=?, lng=? WHERE email='admin@demo.com'", (lat, lng))

    # ---------------- synthetic donors ----------------
    def draw_type() -> str:
        r = rnd.random()
        for t in BLOOD_TYPES:
            r -= TYPE_SHARE[t]
            if r <= 0:
                return t
        return "O+"

    propensity: dict[int, float] = {donor: 0.8}
    donor_rows = []
    for i in range(300):
        city = rnd.choice(list(AREAS))
        la, ln = AREAS[city]
        loyalty = rnd.gauss(0, 1)
        p = sig(-0.2 + 1.1 * loyalty)
        donor_rows.append((i, city, la + (rnd.random() - 0.5) * 0.04, ln + (rnd.random() - 0.5) * 0.04, p))
    sim_ids = []
    for i, city, la, ln, p in donor_rows:
        name = f"{rnd.choice(FIRST)} {rnd.choice(LAST)}"
        uid = db.execute(
            """INSERT INTO users(name,email,password_hash,role,blood_type,city,lat,lng,birth_year,weight_kg,no_shows,is_synthetic)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,1)""",
            (name, f"sim{i:03d}{SYNTHETIC_DOMAIN}", "!synthetic-no-login", "donor", draw_type(), city, la, ln,
             1966 + rnd.randrange(40), round(46 + rnd.random() * 45),
             (1 + int(rnd.random() * 3 * (1 - p))) if rnd.random() < 0.25 * (1 - p) + 0.03 else 0),
        ).lastrowid
        propensity[uid] = p
        sim_ids.append(uid)
        if rnd.random() > 0.14:
            d = -int(120 + rnd.random() * 1000)
            while d < -1:
                db.execute("INSERT INTO donations(donor_id,donated_on,source) VALUES(?,?,'history')", (uid, iso(today + timedelta(days=d))))
                if rnd.random() < 0.1 + 0.45 * (1 - p):
                    break
                d += int(92 + rnd.random() * 60 + (1 - p) * 220 * rnd.random())

    # ---------------- stock history + consistent inventory ----------------
    for t in BLOOD_TYPES:
        base = NETWORK_DAILY_USE * TYPE_SHARE[t]
        used_last = []
        for k in range(180, 0, -1):
            d = today - timedelta(days=k)
            wd = d.weekday()
            dip = 0.55 if (k <= 24 and t == "O-") else 0.85 if (k <= 24 and t == "O+") else 1.0
            seasonal = 1 + 0.06 * math.sin(2 * math.pi * k / 60)
            used = max(0, round(base * DEMAND_WEEKDAY[wd] * seasonal * (1 + 0.12 * rnd.gauss(0, 1))))
            coll = max(0, round(base * dip * COLLECT_WEEKDAY[wd] * seasonal * (1 + 0.15 * rnd.gauss(0, 1))))
            db.execute("INSERT INTO stock_history(date,blood_type,collected,used) VALUES(?,?,?,?)", (iso(d), t, coll, used))
            if k <= 28:
                used_last.append(used)
        avg = sum(used_last) / len(used_last)
        target_days = 2.2 if t == "O-" else 4.6 if t == "O+" else 7 + rnd.random() * 7
        threshold = max(1, math.ceil(avg * 3))
        units = max(1, round(avg * target_days))
        db.execute("UPDATE inventory SET units=?, threshold=?, updated_at=CURRENT_TIMESTAMP WHERE blood_type=?", (units, threshold, t))

    # ---------------- past urgent requests + replies ----------------
    organizer = db.execute("SELECT id FROM users WHERE email='organizer@demo.com'").fetchone()["id"]
    compat = {
        "O-": ["O-"], "O+": ["O+", "O-"], "A-": ["A-", "O-"], "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"], "B+": ["B+", "B-", "O+", "O-"], "AB-": ["AB-", "A-", "B-", "O-"], "AB+": BLOOD_TYPES,
    }
    sim = {r["id"]: r for r in db.execute(
        "SELECT id,blood_type,lat,lng FROM users WHERE is_synthetic=1").fetchall()}
    centres = {r["id"]: r for r in db.execute("SELECT * FROM centres").fetchall()}
    for k in range(14):
        cid = rnd.choice(list(centres))
        t = rnd.choice(["O+", "O-", "A+", "B+", "O+", "B+", "A-", "O-"])
        created = today - timedelta(days=12 + rnd.randrange(150))
        rid = db.execute(
            """INSERT INTO urgent_requests(centre_id,blood_type,units,needed_by,note,status,created_by,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (cid, t, 4 + rnd.randrange(10), iso(created + timedelta(days=3)), "Past request (demo history)",
             "fulfilled" if rnd.random() < 0.8 else "closed", organizer, iso(created)),
        ).lastrowid
        c = centres[cid]
        candidates = [u for u in sim.values() if u["blood_type"] in compat[t]]
        rnd.shuffle(candidates)
        for u in candidates[:25]:
            km = math.dist((u["lat"], u["lng"]), (c["lat"], c["lng"])) * 111
            yes_p = propensity[u["id"]] * max(0.15, 1 - km / 45)
            answered = rnd.random() < 0.85
            db.execute(
                "INSERT INTO alerts(request_id,donor_id,score,reasons,sent_at,response,responded_at) VALUES(?,?,?,?,?,?,?)",
                (rid, u["id"], 0, "[]", iso(created), ("yes" if rnd.random() < yes_p else "no") if answered else None,
                 iso(created) if answered else None),
            )
        if t == "O-":
            db.execute(
                "INSERT INTO alerts(request_id,donor_id,score,reasons,sent_at,response,responded_at) VALUES(?,?,?,?,?,?,?)",
                (rid, donor, 0, "[]", iso(created), "yes", iso(created)),
            )

    # ---------------- bookings on v1 campaigns + past campaigns ----------------
    slots = db.execute("""SELECT s.id, s.capacity FROM slots s JOIN campaigns c ON c.id=s.campaign_id
                          WHERE c.event_date >= ?""", (iso(today),)).fetchall()
    pool = sim_ids[:]
    rnd.shuffle(pool)
    for s in slots:
        for _ in range(int(s["capacity"] * (0.15 + rnd.random() * 0.25))):
            if pool:
                db.execute("INSERT OR IGNORE INTO appointments(donor_id,slot_id,status) VALUES(?,?,'confirmed')", (pool.pop(), s["id"]))

    comments_good = ["Nurses were very friendly and quick.", "Easy parking and clear signs.",
                     "Booking a slot saved me a lot of time.", "Loved the refreshments after!"]
    comments_bad = ["Waited 40 minutes before my slot.", "A bit crowded around lunch time."]
    past = [("Weekend Community Drive", "Masjid Negara, Dewan Serbaguna", "Kuala Lumpur", 20),
            ("City Office Drive", "KL Sentral Office Tower, L2", "Kuala Lumpur", 45)]
    for title, venue, city, ago in past:
        cid = db.execute(
            "INSERT INTO campaigns(title,venue,city,event_date,description,organizer_id,status) VALUES(?,?,?,?,?,?,'completed')",
            (title, venue, city, iso(today - timedelta(days=ago)), "Completed demo campaign.", organizer),
        ).lastrowid
        for st in ("09:00", "11:00", "14:00"):
            sid = db.execute("INSERT INTO slots(campaign_id,start_time,capacity) VALUES(?,?,?)", (cid, st, 15)).lastrowid
            for _ in range(10 + rnd.randrange(5)):
                if not pool:
                    break
                uid = pool.pop()
                status = "donated" if rnd.random() < 0.85 else "no_show"
                db.execute("INSERT INTO appointments(donor_id,slot_id,status) VALUES(?,?,?)", (uid, sid, status))
                if status == "donated" and rnd.random() < 0.4:
                    rating = max(1, min(5, round(4.2 + rnd.gauss(0, 0.8))))
                    db.execute(
                        "INSERT OR IGNORE INTO feedback(campaign_id,donor_id,rating,comment,created_at) VALUES(?,?,?,?,?)",
                        (cid, uid, rating, rnd.choice(comments_good if rating >= 4 else comments_bad), iso(today - timedelta(days=ago))),
                    )
