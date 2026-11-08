"""
HemoCare Medical Knowledge — short, plain-language guides on blood conditions that matter to donors.

Rules for this content:
  * Educational, not a diagnosis. Treatment is described only as "what doctors may consider" — never doses.
  * Every guide ends with what it means for donating and when to get urgent care.
  * Facts are referenced. Donation waiting periods are placeholders until confirmed with Pusat Darah Negara.
"""
from __future__ import annotations

REVIEW = "Educational content · pending clinician review"

REFS = {
    "who_hb": "WHO (2024). Guideline on haemoglobin cutoffs to define anaemia in individuals and populations.",
    "nice_ida": "NICE Clinical Knowledge Summaries: Anaemia — iron deficiency.",
    "nbc_deferral": "Causes and factors associated with blood donor deferrals in National Blood Centre, Malaysia. "
                    "Journal of Biomedical and Clinical Sciences (jbcs.amdi.usm.my).",
    "iron_donors": "Evaluation of iron stores in regular blood donors (PMC7036564): about 250 mg iron per 450 mL unit; "
                   "25.9% of regular donors showed some iron depletion.",
    "thal_screen": "Malay Mail (1 Nov 2025): 58,428 thalassaemia carriers found among about 1.8 million Form Four "
                   "students screened since 2016 (Ministry of Health).",
    "moh_thal": "Ministry of Health Malaysia. Clinical Practice Guidelines: Management of Transfusion Dependent "
                "Thalassaemia.",
    "moh_dengue": "Ministry of Health Malaysia. Clinical Practice Guidelines: Management of Dengue Infection in Adults.",
    "lifeblood_dengue": "Australian Red Cross Lifeblood: wait at least four months after recovering from dengue "
                        "(example of another blood service's rule).",
    "nice_b12": "NICE Clinical Knowledge Summaries: Anaemia — B12 and folate deficiency.",
    "labtests": "Lab Tests Online / Testing.com: Complete blood count and white blood cell differential.",
    "drugs_list": "Drugs.com: Medications that disqualify you from donating blood (based on US blood service lists).",
}

ARTICLES = [
    {
        "id": "anaemia", "title": "Anaemia", "short": "Understanding low haemoglobin", "icon": "droplet",
        "group": "Red cells", "rules": ["isolated_low_hb", "normocytic_anaemia", "microcytic_anaemia",
                                        "macrocytic_anaemia", "pancytopenia"],
        "summary": "Anaemia means your blood has less haemoglobin than normal, so it carries less oxygen. It is a "
                   "sign with many possible causes, not a disease on its own.",
        "sections": [
            ("What the numbers mean", [
                "WHO uses haemoglobin below 12 g/dL for non-pregnant women and below 13 g/dL for men as anaemia; "
                "your lab's own range is shown on your report.",
                "The size of your red cells (MCV) helps doctors narrow down the cause: small cells often point to "
                "low iron or thalassaemia trait, large cells to low vitamin B12 or folate.",
            ]),
            ("Common signs", [
                "Tiredness or low energy", "Breathlessness when active", "Pale skin or inner eyelids",
                "Dizziness or headaches", "A fast or pounding heartbeat",
            ]),
            ("Common causes", [
                "Low iron — the most common cause worldwide (heavy periods, diet, frequent blood donation)",
                "Blood loss from the stomach or bowel", "Low vitamin B12 or folate",
                "Inherited conditions such as thalassaemia", "Long-term illness such as kidney disease",
            ]),
            ("How it is checked", [
                "Full blood count (FBC) — what HemoScan reads", "Ferritin and iron studies",
                "Vitamin B12 and folate levels", "Haemoglobin analysis if thalassaemia is suspected",
            ]),
            ("What doctors may consider", [
                "Finding and treating the cause comes first.",
                "If iron is low, doctors commonly suggest iron-rich food and may prescribe iron supplements; "
                "the type and length of treatment is their decision.",
                "Vitamin B12 or folic acid replacement when those are low.",
                "Transfusion is only for severe cases, decided in hospital.",
            ]),
        ],
        "donation": "Low haemoglobin is the most common reason donors are turned away at Malaysia's National "
                    "Blood Centre (about half of temporary deferrals in one study). Wait until a doctor has reviewed "
                    "it and your haemoglobin is back in range — the blood bank checks it again on the day.",
        "urgent": ["Chest pain or fainting", "Severe breathlessness at rest",
                   "Black, tarry stools or vomiting blood"],
        "related": ["iron", "thalassaemia", "b12-folate"],
        "refs": ["who_hb", "nice_ida", "nbc_deferral"],
    },
    {
        "id": "iron", "title": "Iron deficiency", "short": "Iron stores and blood health", "icon": "spark",
        "group": "Red cells", "rules": ["microcytic_anaemia", "rdw_supports_iron", "microcytosis_no_anaemia"],
        "summary": "Your body uses iron to make haemoglobin. Iron stores can run low long before haemoglobin "
                   "drops — common in frequent donors, women with heavy periods and people who eat little iron.",
        "sections": [
            ("Why donors should care", [
                "One whole-blood donation (about 450 mL) contains roughly 250 mg of iron.",
                "In one study of regular donors, about 1 in 4 showed some iron depletion — often with normal "
                "haemoglobin, so it is easy to miss.",
                "Ferritin is the blood test that shows your iron stores.",
            ]),
            ("Iron-rich foods (Malaysian kitchen)", [
                "Beef, mutton and chicken liver", "Ikan bilis, sardines and cockles (kerang)", "Eggs",
                "Tofu, tempeh, dhal and other lentils", "Dark leafy greens such as bayam and kangkung",
            ]),
            ("Help your body absorb it", [
                "Pair iron foods with vitamin C — guava, orange, papaya, tomato.",
                "Keep tea, coffee and teh tarik away from iron-rich meals (about an hour apart).",
                "Plant iron is absorbed less well than iron from meat or fish.",
            ]),
            ("What doctors may consider", [
                "A ferritin test to confirm low iron and finding the reason for it.",
                "Iron supplements are common, but take them only on a doctor's or pharmacist's advice — "
                "they can upset the stomach and darken stools.",
                "Keep iron tablets away from children: an overdose is dangerous for them.",
            ]),
        ],
        "donation": "If HemoScan shows small red cells or falling haemoglobin and you donate often, ask your doctor "
                    "about ferritin before your next donation. Spacing donations out gives your iron time to recover.",
        "urgent": ["Chest pain or fainting", "Black stools or blood in vomit"],
        "related": ["anaemia", "thalassaemia"],
        "refs": ["iron_donors", "nice_ida"],
    },
    {
        "id": "thalassaemia", "title": "Thalassaemia", "short": "Inherited blood disorders", "icon": "users",
        "group": "Red cells", "rules": ["mentzer", "microcytosis_no_anaemia", "microcytic_anaemia"],
        "summary": "Thalassaemia is inherited: the body makes less of part of haemoglobin. Carriers (trait) usually "
                   "feel well but have small red cells and sometimes mild anaemia.",
        "sections": [
            ("In Malaysia", [
                "It is common: Ministry of Health screening has found more than 58,000 carriers among Form Four "
                "students since 2016.",
                "Many carriers don't know until a blood test shows small red cells.",
            ]),
            ("Trait vs iron deficiency", [
                "Both give small red cells, so they are easily confused.",
                "Iron tablets won't fix thalassaemia trait — ask for testing before long-term iron.",
                "HemoScan's Mentzer index is only a hint; haemoglobin analysis (and sometimes DNA tests) confirms it.",
            ]),
            ("Family planning", [
                "If both partners are carriers, each pregnancy has a 1 in 4 chance of a child with a severe form.",
                "Couples can ask for carrier screening before starting a family.",
            ]),
            ("What doctors may consider", [
                "Haemoglobin analysis (electrophoresis or HPLC) and iron studies.",
                "Carriers usually need no treatment; severe forms are managed by specialist teams.",
            ]),
        ],
        "donation": "Many blood services accept thalassaemia carriers if their haemoglobin meets the minimum on the "
                    "day. Tell the screening staff you are a carrier — Pusat Darah Negara makes the final decision.",
        "urgent": ["Very pale skin with severe tiredness", "Yellow eyes or dark urine"],
        "related": ["anaemia", "iron"],
        "refs": ["thal_screen", "moh_thal"],
    },
    {
        "id": "platelets", "title": "Platelet disorders", "short": "Low and high platelet counts", "icon": "shield",
        "group": "Platelets", "rules": ["low_plt", "high_plt", "low_plt_low_wbc", "pancytopenia"],
        "summary": "Platelets help your blood clot. A typical range is about 150–400 ×10⁹/L, and both low and high "
                   "counts have many causes.",
        "sections": [
            ("Low platelets — common causes", [
                "Viral infections, including dengue", "Some medicines", "The immune system attacking platelets",
                "Heavy alcohol use", "Less often, bone marrow problems",
            ]),
            ("Signs of low platelets", [
                "Bruising easily", "Tiny red or purple spots on the skin", "Bleeding gums or nosebleeds",
                "Periods heavier than usual",
            ]),
            ("High platelets — common causes", [
                "A reaction to infection, inflammation or surgery",
                "Iron deficiency",
                "Rarely, a bone marrow condition — doctors repeat the test to check",
            ]),
            ("What doctors may consider", [
                "Repeating the count and looking at a blood film.",
                "Treating the cause, such as an infection or low iron.",
            ]),
        ],
        "donation": "Don't donate while your platelets are out of range — tell the screening staff and wait until a "
                    "doctor has reviewed them.",
        "urgent": ["Bleeding that won't stop", "Blood in urine or stool", "A sudden severe headache"],
        "related": ["dengue", "iron"],
        "refs": ["labtests"],
    },
    {
        "id": "dengue", "title": "Dengue and your blood count", "short": "Low platelets and white cells",
        "icon": "alert", "group": "Infection", "rules": ["low_plt_low_wbc", "low_plt", "leukopenia"],
        "summary": "Dengue is common in Malaysia. It often lowers white cells and platelets, and doctors watch the "
                   "haematocrit closely during the critical phase.",
        "sections": [
            ("Typical blood count changes", [
                "Low white cells early in the illness", "Falling platelets",
                "A rising haematocrit can mean fluid is leaking from blood vessels — doctors monitor this",
            ]),
            ("Warning signs — go to hospital", [
                "Abdominal pain or tenderness", "Vomiting that won't stop", "Bleeding from gums or nose",
                "Feeling very drowsy or restless", "Little or no urine",
            ]),
            ("While you have dengue", [
                "See a doctor early and follow their monitoring plan.",
                "Health authorities advise avoiding aspirin and ibuprofen-type painkillers — ask a doctor or "
                "pharmacist which painkiller is safe.",
                "Drink fluids as your doctor advises.",
            ]),
        ],
        "donation": "Don't donate while you have dengue. After you recover, blood services ask you to wait — "
                    "Australia's Lifeblood, for example, asks for at least four months. Confirm the Malaysian rule with "
                    "Pusat Darah Negara.",
        "urgent": ["Any warning sign above", "Fainting or cold, clammy skin"],
        "related": ["platelets", "white-cells"],
        "refs": ["moh_dengue", "lifeblood_dengue"],
    },
    {
        "id": "b12-folate", "title": "Vitamin B12 & folate", "short": "Large red cells", "icon": "spark",
        "group": "Red cells", "rules": ["macrocytic_anaemia", "macrocytosis_no_anaemia"],
        "summary": "Your body needs vitamin B12 and folate to make healthy red cells. When they are low, red cells "
                   "can become larger than normal (high MCV).",
        "sections": [
            ("Common causes", [
                "Low intake — B12 comes mainly from animal foods, so strict vegetarians and vegans are at risk",
                "Problems absorbing B12 (for example pernicious anaemia)",
                "Some long-term medicines, such as metformin", "Heavy alcohol use", "Pregnancy (folate)",
            ]),
            ("Signs", [
                "Tiredness", "Pins and needles or numbness", "A sore, red tongue", "Memory or mood changes",
            ]),
            ("Food sources", [
                "B12: meat, fish, eggs, milk and fortified foods",
                "Folate: dark leafy greens, beans, lentils, oranges",
            ]),
            ("What doctors may consider", [
                "Blood tests for B12 and folate.",
                "Tablets or injections when levels are low — the doctor decides which.",
            ]),
        ],
        "donation": "Wait until a doctor has looked at large red cells or low haemoglobin before donating.",
        "urgent": ["Numbness or weakness that is getting worse", "Trouble walking or balancing"],
        "related": ["anaemia"],
        "refs": ["nice_b12"],
    },
    {
        "id": "white-cells", "title": "White blood cell changes", "short": "Infection and immunity",
        "icon": "users", "group": "White cells",
        "rules": ["neutrophilia", "lymphocytosis", "leukopenia", "eosinophilia", "pancytopenia"],
        "summary": "White cells fight infection. Their numbers rise and fall with infections, stress, allergies and "
                   "medicines — most changes are temporary.",
        "sections": [
            ("High white cells — common causes", [
                "Bacterial infection (neutrophils)", "Viral infection (lymphocytes)",
                "Allergies, asthma or parasites (eosinophils)", "Stress, smoking or steroid medicines",
            ]),
            ("Low white cells — common causes", [
                "Viral infections such as dengue or flu", "Some medicines",
                "Autoimmune conditions", "Less often, bone marrow problems",
            ]),
            ("What doctors may consider", [
                "Repeating the count once you are well.",
                "Looking at which type of white cell changed (the differential).",
            ]),
        ],
        "donation": "Don't donate while you have an infection or fever. Wait until you are fully well and any course "
                    "of antibiotics has finished.",
        "urgent": ["Fever with very low neutrophils", "Fever above 38 °C that won't settle",
                   "Night sweats with weight loss"],
        "related": ["dengue", "medicines"],
        "refs": ["labtests"],
    },
    {
        "id": "blood-pressure", "title": "Blood pressure & donating", "short": "Second most common deferral",
        "icon": "pulse", "group": "Donation",
        "rules": [],
        "summary": "Blood pressure is checked before every donation. High readings were the second most common reason "
                   "for temporary deferral in a National Blood Centre study.",
        "sections": [
            ("Before your donation", [
                "Sleep well the night before", "Eat a proper meal and drink water",
                "Skip coffee and cigarettes for a few hours", "Arrive early and sit quietly for a few minutes",
            ]),
            ("If you take blood pressure medicine", [
                "Keep taking it as prescribed — never stop a medicine just to donate.",
                "Tell the staff; controlled blood pressure on treatment is often accepted, but they decide.",
            ]),
        ],
        "donation": "A single high reading usually means a short wait, not a permanent ban. If readings stay high, see "
                    "a doctor first.",
        "urgent": ["Severe headache with confusion", "Chest pain", "Sudden weakness or trouble speaking"],
        "related": ["medicines"],
        "refs": ["nbc_deferral"],
    },
    {
        "id": "medicines", "title": "Medicines & donating", "short": "Why some medicines mean waiting",
        "icon": "pill", "group": "Donation", "rules": [],
        "summary": "Most everyday medicines are fine, but a few mean waiting before you donate — to protect the "
                   "patient who receives your blood, or because of the illness being treated.",
        "sections": [
            ("Why waiting periods exist", [
                "Some medicines could harm an unborn baby if a pregnant patient receives the blood (e.g. isotretinoin "
                "for acne, finasteride or dutasteride for hair loss or prostate).",
                "Blood thinners affect clotting and platelet donations.",
                "Antibiotics usually mean an infection — you need to be fully well first.",
            ]),
            ("Good habits", [
                "Never stop a prescribed medicine just to donate.",
                "Keep your list up to date in HemoCare → Medication History.",
                "Bring the list (or your HemoCare summary) to the screening interview.",
            ]),
        ],
        "donation": "HemoCare checks your medicine list against example waiting periods and shows when you may donate. "
                    "The periods are placeholders from other blood services — Pusat Darah Negara staff decide on the day.",
        "urgent": ["A serious reaction to a medicine — swelling of the face or lips, or trouble breathing"],
        "related": ["blood-pressure"],
        "refs": ["drugs_list"],
    },
]

BY_ID = {a["id"]: a for a in ARTICLES}


def summary_list() -> list[dict]:
    return [{k: a[k] for k in ("id", "title", "short", "icon", "group", "summary")} for a in ARTICLES]


def article(article_id: str) -> dict | None:
    a = BY_ID.get(article_id)
    if not a:
        return None
    return {**a, "sections": [{"heading": h, "points": p} for h, p in a["sections"]],
            "refs": [REFS[r] for r in a["refs"]], "review": REVIEW,
            "related": [{"id": r, "title": BY_ID[r]["title"]} for r in a["related"] if r in BY_ID]}


def for_rules(rule_ids: list[str]) -> list[dict]:
    """Articles matching HemoScan findings, most relevant first."""
    scored = []
    for a in ARTICLES:
        hits = [r for r in rule_ids if r in a["rules"]]
        if hits:
            scored.append((min(a["rules"].index(h) for h in hits) - len(hits), a))
    scored.sort(key=lambda x: x[0])
    return [{"id": a["id"], "title": a["title"], "short": a["short"]} for _, a in scored]
