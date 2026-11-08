/* Bahasa Malaysia for HemoLink.
   A translation layer: every time the app puts text on screen, exact English UI strings are swapped for Malay and
   common sentences with numbers are handled by patterns. Names, campaign titles and medical guide text stay as
   entered. Switch with the EN/BM button (login page, top bar) or Profile → Alerts & language. */

const MS = {
  // ---------- login / sign-up
  "Every drop.": "Setiap titisan.", "Every connection.": "Setiap hubungan.", "Every life.": "Setiap nyawa.",
  "Book donations, answer urgent requests and understand your blood health — all in one place.": "Tempah derma darah, jawab permintaan segera dan fahami kesihatan darah anda — semuanya di satu tempat.",
  "Sign in": "Log masuk", "Donor · Drive organizer · Blood bank portal": "Penderma · Penganjur kempen · Portal bank darah",
  "Email address": "Alamat e-mel", "Password": "Kata laluan", "Role selection": "Pilih peranan", "· try a demo account": "· cuba akaun demo",
  "Donor": "Penderma", "Organizer": "Penganjur", "Admin": "Pentadbir", "New to HemoLink?": "Baharu di HemoLink?",
  "Create a donor account": "Cipta akaun penderma",
  "Hackathon prototype. Demo data only — no real clinical eligibility, live blood stock or emergency services.": "Prototaip hackathon. Data demo sahaja — bukan kelayakan klinikal sebenar, stok darah langsung atau perkhidmatan kecemasan.",
  "Enter your password": "Masukkan kata laluan", "Join as a donor": "Sertai sebagai penderma",
  "Create your donor account to book slots, get matched to urgent requests and keep your blood health in one place.": "Cipta akaun penderma untuk menempah slot, dipadankan dengan permintaan segera dan simpan maklumat kesihatan darah anda di satu tempat.",
  "Full name": "Nama penuh", "Blood type (optional)": "Jenis darah (pilihan)", "Unknown": "Tidak diketahui", "City (optional)": "Bandar (pilihan)",
  "Create donor account": "Cipta akaun penderma", "Already have an account?": "Sudah ada akaun?", "Your name": "Nama anda",
  "At least 8 characters": "Sekurang-kurangnya 8 aksara",
  // ---------- navigation / chrome
  "HEALTH INTELLIGENCE": "KECERDASAN KESIHATAN", "MAIN MENU": "MENU UTAMA", "ACCOUNT": "AKAUN",
  "Dashboard": "Papan pemuka", "Find Campaigns": "Cari Kempen", "My Appointments": "Temujanji Saya", "Eligibility Check": "Semakan Kelayakan",
  "Notifications": "Pemberitahuan", "Health Assistant": "Pembantu Kesihatan", "Help Assistant": "Pembantu", "My Profile": "Profil Saya", "Log out": "Log keluar",
  "Need a little help?": "Perlukan bantuan?", "Ask about appointments or donation preparation.": "Tanya tentang temujanji atau persediaan menderma.",
  "Ask the assistant": "Tanya pembantu", "Open my profile": "Buka profil saya", "My profile": "Profil saya",
  "Home": "Utama", "Campaigns": "Kempen", "Alerts": "Makluman", "More": "Lagi", "Menu": "Menu", "Stock": "Stok", "Urgent": "Segera", "Check-in": "Daftar masuk",
  "My Campaigns": "Kempen Saya", "Bookings & Check-in": "Tempahan & Daftar Masuk", "Insights & Planner": "Analisis & Perancang",
  "Blood Stock": "Stok Darah", "Urgent Requests": "Permintaan Segera", "Donation Trends": "Trend Derma", "Users & Organizers": "Pengguna & Penganjur", "AI Models": "Model AI",
  "Drive Organizer": "Penganjur Kempen", "Blood Bank Admin": "Pentadbir Bank Darah",
  "HEMOLINK / DONOR PORTAL": "HEMOLINK / PORTAL PENDERMA", "HEMOLINK / DRIVE ORGANIZER PORTAL": "HEMOLINK / PORTAL PENGANJUR", "HEMOLINK / BLOOD BANK ADMIN PORTAL": "HEMOLINK / PORTAL PENTADBIR BANK DARAH",
  "Close": "Tutup", "Cancel": "Batal", "Open": "Buka", "View": "Lihat", "View all": "Lihat semua", "Send": "Hantar", "Save changes": "Simpan perubahan",
  "Yes": "Ya", "No": "Tidak", "All": "Semua", "Today": "Hari ini", "Low": "Rendah", "High": "Tinggi", "Map": "Peta", "Directions": "Arah",
  "Zoom in": "Zum masuk", "Zoom out": "Zum keluar", "Loading your data…": "Memuatkan data anda…", "Loading alert settings…": "Memuatkan tetapan makluman…",
  // ---------- dashboards
  "Find meaningful donation opportunities near you, all in one place.": "Cari peluang menderma yang bermakna berhampiran anda, semuanya di satu tempat.",
  "✦ CONNECTING PEOPLE THROUGH DATA": "✦ MENGHUBUNGKAN MASYARAKAT MELALUI DATA",
  "Together, we can make a difference.": "Bersama, kita boleh membawa perubahan.", "Bring people together to give hope.": "Satukan masyarakat untuk memberi harapan.",
  "Smarter planning, stronger communities.": "Perancangan lebih bijak, komuniti lebih kukuh.",
  "HemoLink AI connects community donation events with thoughtful, data-informed decision support.": "HemoLink AI menghubungkan acara derma komuniti dengan sokongan keputusan berasaskan data.",
  "Explore campaigns": "Terokai kempen", "Manage campaigns": "Urus kempen", "Open blood stock": "Buka stok darah",
  "Donor Milestones": "Pencapaian Penderma", "Total donations:": "Jumlah derma:", "Next milestone:": "Pencapaian seterusnya:", "so far": "setakat ini",
  "Next Eligibility Date": "Tarikh Layak Seterusnya", "You can donate": "Anda boleh menderma", "You can donate again on": "Anda boleh menderma semula pada",
  "Check today's questions": "Semak soalan hari ini", "Why?": "Kenapa?", "Upcoming Campaigns": "Kempen Akan Datang", "Find a campaign": "Cari kempen",
  "My Blood Health": "Kesihatan Darah Saya", "Latest Hb:": "Hb terkini:", "Below minimum": "Bawah minimum", "OK to donate": "Boleh menderma",
  "Blood Needed Now": "Darah Diperlukan Sekarang", "Your type": "Jenis darah anda", "is running low — your donation really matters.": "semakin berkurangan — derma anda amat bermakna.",
  "Latest Updates": "Kemas Kini Terkini", "Latest updates": "Kemas kini terkini", "All notifications": "Semua pemberitahuan",
  "Educational hackathon prototype. Stock levels, campaigns and other donors are fictional.": "Prototaip hackathon pendidikan. Tahap stok, kempen dan penderma lain adalah rekaan.",
  "Welcome to HemoLink AI": "Selamat datang ke HemoLink AI", "Find donation campaigns near you and book your first appointment.": "Cari kempen derma berhampiran anda dan tempah temujanji pertama anda.",
  "Complete your profile": "Lengkapkan profil anda", "Open my profile": "Buka profil saya", "Upload a blood test to track your haemoglobin.": "Muat naik ujian darah untuk menjejak hemoglobin anda.",
  "These blood types are below their safe level (demo stock).": "Jenis darah ini di bawah paras selamat (stok demo).", "All blood types are above their safe level today.": "Semua jenis darah melebihi paras selamat hari ini.",
  "No notifications at the moment.": "Tiada pemberitahuan buat masa ini.", "No upcoming campaigns yet.": "Belum ada kempen akan datang.",
  "Run your blood drives, check donors in, and plan the next drive where blood is needed.": "Jalankan kempen derma, daftar masuk penderma, dan rancang kempen seterusnya di tempat darah diperlukan.",
  "Watch blood stock, act on shortages and oversee donors and organizers.": "Pantau stok darah, bertindak atas kekurangan dan selia penderma serta penganjur.",
  "Shortage forecast": "Ramalan kekurangan", "Critical": "Kritikal", "Watch": "Perhati", "Healthy": "Sihat",
  "My campaigns": "Kempen saya", "Events created": "Acara dicipta", "Upcoming drives": "Kempen akan datang", "Still to run": "Belum dijalankan",
  "Donors booked": "Penderma ditempah", "Across my campaigns": "Merentas kempen saya", "Average rating": "Purata penilaian",
  "Upcoming donation campaigns": "Kempen derma akan datang", "Inventory snapshot": "Gambaran inventori", "Simulation": "Simulasi",
  "Example stock levels, not connected to a hospital.": "Contoh tahap stok, tidak disambungkan ke hospital.", "Plan a drive for low types": "Rancang kempen untuk jenis yang rendah",
  "Campaign planner": "Perancang kempen", "Where and when to hold your next drive": "Di mana dan bila mengadakan kempen seterusnya",
  "The planner picks the blood type that is running low, the area with the most eligible donors and the best weekday.": "Perancang memilih jenis darah yang semakin berkurangan, kawasan dengan penderma layak paling ramai dan hari terbaik.",
  "Open planner": "Buka perancang", "Registered donors": "Penderma berdaftar", "Demo accounts": "Akaun demo", "Drive organizers": "Penganjur kempen",
  "Approved organizers": "Penganjur diluluskan", "Open urgent requests": "Permintaan segera aktif", "Waiting for donors": "Menunggu penderma",
  "Blood types below safe level": "Jenis darah bawah paras selamat", "Simulated stock": "Stok simulasi", "Manage blood stock": "Urus stok darah",
  "AI forecasting": "Ramalan AI", "Explore expected donation counts, model metrics and data provenance.": "Terokai jangkaan bilangan derma, metrik model dan sumber data.",
  "Open forecasts": "Buka ramalan", "Thank you for being a donor. Here's your donation life at a glance.": "Terima kasih kerana menjadi penderma.",
  "AI": "AI", "From donor feedback (out of 5)": "Daripada maklum balas penderma (daripada 5)", "No ratings yet": "Belum ada penilaian",
  // ---------- campaigns + map
  "Find a donation campaign": "Cari kempen derma", "See drives near you on the map, how far they are, and book a slot.": "Lihat kempen berhampiran pada peta, sejauh mana, dan tempah slot.",
  "Use my location": "Guna lokasi saya", "Update my location": "Kemas kini lokasi saya", "Finding you…": "Mencari lokasi anda…", "Nearest first": "Terdekat dahulu", "Soonest first": "Terawal dahulu",
  "slots left": "slot tinggal", "Book a slot": "Tempah slot", "No matching events": "Tiada acara sepadan", "Try another name, city or venue.": "Cuba nama, bandar atau tempat lain.",
  "Search campaigns, venues, cities...": "Cari kempen, tempat, bandar...", "Sort campaigns": "Susun kempen", "Map of donation campaigns": "Peta kempen derma",
  "Straight-line distance; drive time is a rough estimate": "Jarak garis lurus; masa memandu ialah anggaran kasar",
  "Share your location to see how far each campaign is.": "Kongsi lokasi anda untuk melihat jarak setiap kempen.",
  "Book an appointment": "Tempah temujanji", "Choose one available appointment time.": "Pilih satu masa temujanji yang tersedia.", "Confirm booking": "Sahkan tempahan",
  "Manage the events you organize and coordinate available appointment slots.": "Urus acara anjuran anda dan selaraskan slot temujanji.",
  "Create campaign": "Cipta kempen", "Create a campaign": "Cipta kempen", "Plan a donation event with bookable time slots.": "Rancang acara derma dengan slot masa yang boleh ditempah.",
  "Campaign name": "Nama kempen", "Venue": "Tempat", "Event date": "Tarikh acara", "Time slots (comma separated)": "Slot masa (dipisahkan koma)",
  "Capacity per slot": "Kapasiti setiap slot", "Event description": "Penerangan acara", "Create event": "Cipta acara",
  "Tell donors about the event and its purpose": "Beritahu penderma tentang acara dan tujuannya", "Donation campaigns": "Kempen derma",
  "Campaign location": "Lokasi kempen", "Pin location": "Lokasi pin", "Search address": "Cari alamat", "Edit location": "Ubah lokasi", "Save location": "Simpan lokasi",
  "No campaigns within this distance": "Tiada kempen dalam jarak ini", "Try a larger distance.": "Cuba jarak yang lebih jauh.",
  // ---------- appointments / bookings
  "Manage your confirmed donation appointments.": "Urus temujanji derma yang telah disahkan.", "Appointment history": "Sejarah temujanji",
  "No appointments yet": "Belum ada temujanji", "Explore upcoming campaigns and reserve your first slot.": "Terokai kempen akan datang dan tempah slot pertama anda.",
  "Browse campaigns": "Lihat kempen", "Campaign bookings": "Tempahan kempen", "Review donor reservations across your campaigns.": "Semak tempahan penderma merentas kempen anda.",
  "All reservations": "Semua tempahan", "Event": "Acara", "Time": "Masa", "Status": "Status", "Action": "Tindakan", "Donated": "Telah menderma",
  "No-show": "Tidak hadir", "Confirmed": "Disahkan", "Cancelled": "Dibatalkan", "Rate": "Nilai", "Rate this campaign": "Nilai kempen ini",
  // ---------- eligibility
  "Eligibility check": "Semakan kelayakan", "One minute, ten quick questions. Our rules engine gives the verdict; AI explains it in plain language.": "Satu minit, lima belas soalan pantas. Enjin peraturan memberi keputusan; AI menerangkannya dalam bahasa mudah.",
  "BASED ON YOUR RECORD": "BERDASARKAN REKOD ANDA", "Open HemoScan": "Buka HemoScan", "Today's health questions": "Soalan kesihatan hari ini", "See my result": "Lihat keputusan saya",
  "Are you feeling well and healthy today?": "Adakah anda berasa sihat hari ini?",
  "Did you sleep at least 5 hours last night?": "Adakah anda tidur sekurang-kurangnya 5 jam malam tadi?",
  "Have you eaten a proper meal in the last 4 hours?": "Adakah anda telah makan hidangan lengkap dalam 4 jam yang lalu?",
  "Have you had fever, cough or flu in the last 7 days?": "Adakah anda demam, batuk atau selesema dalam 7 hari yang lalu?",
  "Have you taken antibiotics in the last 7 days?": "Adakah anda mengambil antibiotik dalam 7 hari yang lalu?",
  "Have you had a tooth extraction or dental surgery in the last 3 days?": "Adakah anda mencabut gigi atau menjalani pembedahan gigi dalam 3 hari yang lalu?",
  "Have you had a tattoo, piercing or acupuncture in the last 6 months?": "Adakah anda membuat tatu, tindikan atau akupunktur dalam 6 bulan yang lalu?",
  "Are you pregnant, or have you given birth or breastfed in the last 6 months?": "Adakah anda hamil, atau telah bersalin atau menyusukan bayi dalam 6 bulan yang lalu?",
  "Do you have a long-term condition such as heart disease, cancer or a bleeding disorder?": "Adakah anda mempunyai penyakit jangka panjang seperti penyakit jantung, kanser atau gangguan pendarahan?",
  "Have you travelled to a malaria-risk area in the last 12 months?": "Adakah anda pernah ke kawasan berisiko malaria dalam 12 bulan yang lalu?",
  "You can donate after a meal": "Anda boleh menderma selepas makan", "Not yet — please wait": "Belum lagi — sila tunggu", "Please check with staff": "Sila semak dengan kakitangan", "Not eligible": "Tidak layak",
  "eat first": "makan dahulu", "staff check": "semakan kakitangan",
  // ---------- HemoScan
  "Read your full blood count report, see what is out of range, the patterns it may point to, and how it changes over time.": "Baca laporan kiraan darah penuh anda, lihat nilai luar julat, corak yang mungkin ditunjukkan, dan perubahannya dari masa ke masa.",
  "Rules engine + AI": "Enjin peraturan + AI", "Add a blood test report": "Tambah laporan ujian darah", "PDF reader": "Pembaca PDF", "Photo reader": "Pembaca foto",
  "Upload PDF": "Muat naik PDF", "From the lab portal": "Dari portal makmal", "Take a photo": "Ambil foto", "Paper report": "Laporan bercetak",
  "Type it in": "Taip sendiri", "Enter values yourself": "Masukkan nilai sendiri", "Choose your FBC / CBC PDF": "Pilih PDF FBC / CBC anda",
  "I understand HemoScan explains number patterns and possible associations —": "Saya faham HemoScan menerangkan corak nombor dan kaitan yang mungkin —",
  "it is not a diagnosis": "ia bukan diagnosis", "and does not replace a doctor.": "dan tidak menggantikan doktor.", "Read my report": "Baca laporan saya",
  "No report handy? Try a fictional sample": "Tiada laporan? Cuba sampel rekaan", "Phone photo": "Foto telefon", "Scanned report": "Laporan diimbas",
  "How it works": "Cara ia berfungsi", "Read": "Baca", "Check": "Semak", "Analyse": "Analisis", "Explain": "Terang",
  "— we pull each test, unit and lab range from your PDF, or from a photo with OCR. Nothing is used until you check it.": "— kami ambil setiap ujian, unit dan julat makmal daripada PDF atau foto anda. Tiada apa digunakan sehingga anda menyemaknya.",
  "— you compare every value with the original and fix anything wrong. Low-confidence readings are highlighted.": "— anda bandingkan setiap nilai dengan asal dan betulkan kesilapan. Bacaan keyakinan rendah ditandakan.",
  "— transparent rules find out-of-range values and known combinations, with the reason and reference shown.": "— peraturan telus mengesan nilai luar julat dan kombinasi yang diketahui, dengan sebab dan rujukan.",
  "— AI (or a built-in template) explains the findings in plain language. Possible associations, never a diagnosis.": "— AI (atau templat terbina dalam) menerangkan penemuan dalam bahasa mudah. Kaitan yang mungkin, bukan diagnosis.",
  "Private to you — organizers and admins can't see your reports. Delete any report at any time.": "Peribadi untuk anda — penganjur dan pentadbir tidak boleh melihat laporan anda. Padam laporan bila-bila masa.",
  "Your results over time": "Keputusan anda dari masa ke masa", "Export CSV": "Eksport CSV", "Lab reference range": "Julat rujukan makmal",
  "In range": "Dalam julat", "Out of range": "Luar julat", "Report history": "Sejarah laporan", "Report date": "Tarikh laporan", "Source": "Sumber",
  "Result": "Keputusan", "Main pattern": "Corak utama", "All in range": "Semua dalam julat", "No pattern flagged": "Tiada corak ditanda",
  "Photograph your paper report": "Ambil foto laporan bercetak anda", "Flat page · good light · fill the frame · no glare": "Halaman rata · cahaya baik · penuhi bingkai · tiada silau",
  "Open camera": "Buka kamera", "Retake": "Ambil semula", "Choose a photo": "Pilih foto", "Choose another": "Pilih lain", "Read my photo": "Baca foto saya",
  "← All reports": "← Semua laporan", "Summary for my doctor": "Ringkasan untuk doktor saya", "View PDF": "Lihat PDF", "Edit values": "Ubah nilai",
  "Patterns flagged": "Corak ditanda", "Plain-language explanation": "Penerangan bahasa mudah", "Explanation": "Penerangan", "AI explanation": "Penerangan AI",
  "Questions to ask your doctor": "Soalan untuk doktor anda", "Patterns found": "Corak dijumpai", "No pattern rules were triggered.": "Tiada peraturan corak dicetuskan.",
  "Since your previous report": "Sejak laporan sebelumnya", "Your results": "Keputusan anda", "Test": "Ujian", "Value": "Nilai", "Reference range": "Julat rujukan",
  "Red cells": "Sel darah merah", "White cells": "Sel darah putih", "Platelets": "Platelet", "Original report": "Laporan asal", "Your photo": "Foto anda",
  "Out-of-range value": "Nilai luar julat", "What this means for donating": "Maksudnya untuk menderma", "Ask about this report": "Tanya tentang laporan ini",
  "Report assistant": "Pembantu laporan", "Can I still donate blood?": "Bolehkah saya masih menderma darah?", "Why do lab ranges differ?": "Kenapa julat makmal berbeza?",
  "Does this mean I have anaemia?": "Adakah ini bermaksud saya menghidap anemia?", "What is MCV?": "Apakah MCV?", "Limitations": "Had",
  "Delete report": "Padam laporan", "Type a question about this report…": "Taip soalan tentang laporan ini…", "Check the extracted values": "Semak nilai yang diekstrak",
  "Enter your blood count": "Masukkan kiraan darah anda", "Extracted values": "Nilai diekstrak", "Enter your values": "Masukkan nilai anda",
  "Report / collection date": "Tarikh laporan / pengambilan", "Sex (for typical ranges)": "Jantina (untuk julat biasa)", "Female": "Perempuan", "Male": "Lelaki",
  "Laboratory (optional)": "Makmal (pilihan)", "Lab range": "Julat makmal", "Confirm and analyse": "Sahkan dan analisis", "Discard": "Buang",
  "I have checked these values and units against my original report.": "Saya telah menyemak nilai dan unit ini dengan laporan asal saya.",
  "High confidence": "Keyakinan tinggi", "Low confidence": "Keyakinan rendah", "Not found": "Tidak dijumpai", "Haemoglobin": "Hemoglobin",
  // ---------- HemoCare
  "Your personal blood health hub — understand blood conditions, keep your medicine list, and get ready for your next donation.": "Hab kesihatan darah peribadi anda — fahami keadaan darah, simpan senarai ubat, dan bersedia untuk derma seterusnya.",
  "Educational": "Pendidikan", "Overview": "Gambaran keseluruhan", "Medical Knowledge": "Pengetahuan Perubatan", "Medication History": "Sejarah Ubat",
  "Donation Preparation": "Persediaan Menderma", "Your blood health hub": "Hab kesihatan darah anda",
  "Learn about blood conditions, symptoms, testing and what doctors may consider.": "Ketahui tentang keadaan darah, gejala, ujian dan pertimbangan doktor.",
  "Keep a private record of current and past medicines.": "Simpan rekod peribadi ubat semasa dan lepas.", "HemoScan Insights": "Wawasan HemoScan",
  "Guides related to your confirmed blood test results.": "Panduan berkaitan keputusan ujian darah anda.", "Screening checklist and a summary to show the staff.": "Senarai semak saringan dan ringkasan untuk ditunjukkan kepada kakitangan.",
  "Printable summary": "Ringkasan boleh cetak", "Explore blood health topics": "Terokai topik kesihatan darah", "Educational content": "Kandungan pendidikan",
  "Anaemia": "Anemia", "Understanding low haemoglobin": "Memahami hemoglobin rendah", "Iron deficiency": "Kekurangan zat besi", "Iron stores and blood health": "Simpanan zat besi dan kesihatan darah",
  "Thalassaemia": "Talasemia", "Inherited blood disorders": "Gangguan darah warisan", "Platelet disorders": "Gangguan platelet", "Low and high platelet counts": "Kiraan platelet rendah dan tinggi",
  "Dengue and your blood count": "Denggi dan kiraan darah anda", "Low platelets and white cells": "Platelet dan sel darah putih rendah", "Large red cells": "Sel darah merah besar",
  "White blood cell changes": "Perubahan sel darah putih", "Infection and immunity": "Jangkitan dan imuniti", "Blood pressure & donating": "Tekanan darah & menderma",
  "Second most common deferral": "Penangguhan kedua paling biasa", "Medicines & donating": "Ubat & menderma", "Why some medicines mean waiting": "Kenapa sesetengah ubat perlu menunggu",
  "Read guide": "Baca panduan", "Infection": "Jangkitan", "Donation": "Derma", "Add a medicine": "Tambah ubat", "Add medicine": "Tambah ubat", "Taking now": "Sedang diambil",
  "No current medicines recorded.": "Tiada ubat semasa direkodkan.", "Medicine history": "Sejarah ubat", "Medicines you have stopped appear here.": "Ubat yang telah dihentikan dipaparkan di sini.",
  "ELIGIBILITY (HEMOLINK CHECK)": "KELAYAKAN (SEMAKAN HEMOLINK)", "Today's questions": "Soalan hari ini", "LATEST BLOOD TEST": "UJIAN DARAH TERKINI",
  "Medicines to mention": "Ubat untuk dimaklumkan", "Edit list": "Ubah senarai", "Before you donate": "Sebelum menderma", "Sleep well the night before": "Tidur cukup pada malam sebelumnya",
  "Bring your IC or passport": "Bawa IC atau pasport anda", "Avoid coffee and cigarettes for a few hours before": "Elakkan kopi dan rokok beberapa jam sebelumnya",
  "Bring this summary or your medicine list to the screening interview": "Bawa ringkasan ini atau senarai ubat anda ke temu duga saringan",
  "Open printable screening summary": "Buka ringkasan saringan boleh cetak", "Medicine name": "Nama ubat", "Type": "Jenis", "Detect from the name": "Kesan daripada nama",
  "What it's for (optional)": "Untuk apa (pilihan)", "As written on the label (optional)": "Seperti tertulis pada label (pilihan)", "Started": "Mula", "Notes (optional)": "Nota (pilihan)",
  "Stopped today": "Berhenti hari ini", "Edit": "Ubah", "Waiting period": "Tempoh menunggu", "Tell the staff": "Beritahu kakitangan", "No effect": "Tiada kesan",
  "All guides": "Semua panduan", "← All guides": "← Semua panduan", "What it means for donating": "Maksudnya untuk menderma", "Get urgent care if you have": "Dapatkan rawatan segera jika anda mengalami",
  "References": "Rujukan", "Related:": "Berkaitan:",
  // ---------- notifications / assistant / profile / alerts
  "Urgent requests from blood banks and updates about your appointments.": "Permintaan segera daripada bank darah dan kemas kini tentang temujanji anda.",
  "Updates about your campaigns and activity.": "Kemas kini tentang kempen dan aktiviti anda.", "Mark all as read": "Tandakan semua sudah dibaca",
  "Urgent requests for you": "Permintaan segera untuk anda", "No urgent requests right now. When a blood bank needs your blood type nearby, it appears here first.": "Tiada permintaan segera sekarang. Apabila bank darah berhampiran memerlukan jenis darah anda, ia dipaparkan di sini dahulu.",
  "Updates": "Kemas kini", "My notifications": "Pemberitahuan saya", "All caught up": "Semua sudah dibaca", "You have no notifications right now.": "Anda tiada pemberitahuan sekarang.",
  "I can come": "Saya boleh datang", "Can't make it": "Tidak dapat datang", "Urgent request": "Permintaan segera", "A blood bank needs your help": "Bank darah memerlukan bantuan anda",
  "Reply in Notifications": "Balas dalam Pemberitahuan",
  "Donation help assistant": "Pembantu derma", "Quick answers about using the platform and general donor preparation.": "Jawapan pantas tentang platform dan persediaan penderma.",
  "How do I book an appointment?": "Bagaimana saya menempah temujanji?", "How should I prepare?": "Bagaimana saya perlu bersedia?", "What is HemoScan?": "Apakah HemoScan?",
  "How do I host a drive?": "Bagaimana saya menganjurkan kempen?", "What does the forecast mean?": "Apakah maksud ramalan?", "How do urgent alerts work?": "Bagaimana makluman segera berfungsi?",
  "Ask a question...": "Tanya soalan...", "Manage your basic information and donation preferences.": "Urus maklumat asas dan pilihan derma anda.",
  "Blood type": "Jenis darah", "City": "Bandar", "Birth year": "Tahun lahir", "Weight (kg)": "Berat (kg)", "City or town": "Bandar atau pekan",
  "Alerts & language": "Makluman & bahasa", "Language · Bahasa": "Bahasa · Language", "Email": "E-mel", "Demo mode": "Mod demo", "Live": "Aktif",
  "Urgent requests and appointment reminders only": "Permintaan segera dan peringatan temujanji sahaja", "Important updates only": "Kemas kini penting sahaja",
  "Mobile number (for SMS)": "Nombor telefon bimbit (untuk SMS)", "Push notifications": "Pemberitahuan tolak", "Pop-up alerts on your phone or computer": "Makluman timbul pada telefon atau komputer anda",
  "Enable on this device": "Aktifkan pada peranti ini", "Turn off here": "Matikan di sini", "On for this device ✓": "Aktif pada peranti ini ✓",
  "New drives near me": "Kempen baharu berhampiran", "When a campaign opens within 25 km of your city": "Apabila kempen dibuka dalam 25 km dari bandar anda",
  "Save alert settings": "Simpan tetapan makluman", "Send me a test alert": "Hantar makluman ujian kepada saya", "Send me a test": "Hantar ujian kepada saya",
  "Message delivery": "Penghantaran mesej", "Run reminders now": "Jalankan peringatan sekarang", "nothing yet": "belum ada", "Push": "Tolak",
  "No outside messages yet. They appear here when donors are alerted, book, or get reminders.": "Belum ada mesej luar. Ia dipaparkan di sini apabila penderma dimaklumkan, menempah atau menerima peringatan.",
  // ---------- organizer / admin pages
  "Insights & campaign planner": "Analisis & perancang kempen", "Your completed drives, donor feedback, donors to re-invite, and where to hold the next drive.": "Kempen yang selesai, maklum balas penderma, penderma untuk dijemput semula, dan lokasi kempen seterusnya.",
  "Donations at campaigns": "Derma di kempen", "Recorded at check-in": "Direkod semasa daftar masuk", "No-show rate": "Kadar tidak hadir", "Donors drifting away": "Penderma yang semakin menjauh",
  "Create this campaign": "Cipta kempen ini", "Regular donors drifting away": "Penderma tetap yang semakin menjauh", "Return prediction": "Ramalan kembali",
  "Donations": "Derma", "Last": "Terakhir", "Return": "Kembali", "Suggested message": "Mesej dicadangkan", "Model card": "Kad model", "Latest feedback": "Maklum balas terkini",
  "Blood stock & shortage outlook": "Stok darah & tinjauan kekurangan", "Best model per type": "Model terbaik setiap jenis", "units": "unit",
  "Stock (history)": "Stok (sejarah)", "Projected stock": "Stok unjuran", "Safe level": "Paras selamat", "Already below the safe level": "Sudah di bawah paras selamat",
  "Urgent requests": "Permintaan segera", "Post a request and let the AI pick the donors most likely to come — not everyone.": "Hantar permintaan dan biar AI memilih penderma yang paling mungkin datang — bukan semua orang.",
  "Post an urgent request": "Hantar permintaan segera", "Smart matching": "Padanan pintar", "Units needed": "Unit diperlukan", "Needed by": "Diperlukan sebelum",
  "Note (optional)": "Nota (pilihan)", "Find matching donors": "Cari penderma sepadan", "Requests": "Permintaan", "Request": "Permintaan", "Alerted": "Dimaklumkan",
  "Said yes": "Bersetuju", "Closed": "Ditutup", "Fulfilled": "Dipenuhi", "Open ": "Buka ",
  "AI donation forecasting": "Ramalan derma AI", "Official dataset": "Set data rasmi", "Demo model": "Model demo", "Donation volume forecast": "Ramalan jumlah derma",
  "Historical counts and seven future daily predictions": "Kiraan sejarah dan tujuh ramalan harian", "All blood groups": "Semua kumpulan darah",
  "Group A": "Kumpulan A", "Group B": "Kumpulan B", "Group AB": "Kumpulan AB", "Group O": "Kumpulan O", "Observed history": "Sejarah diperhati", "Model prediction": "Ramalan model",
  "Average forecast / day": "Purata ramalan / hari", "vs. same weekday last week": "berbanding hari sama minggu lepas", "Which method won for this series": "Kaedah yang menang untuk siri ini",
  "Cross-validated": "Disahkan silang", "Same weekday last week": "Hari sama minggu lepas", "Forecast methodology": "Metodologi ramalan", "Transparent evaluation": "Penilaian telus",
  "Algorithm:": "Algoritma:", "Validation:": "Pengesahan:", "Latest source date:": "Tarikh sumber terkini:", "Data provenance": "Sumber data", "Government source": "Sumber kerajaan",
  "Region": "Wilayah", "Blood group": "Kumpulan darah", "Users & organizers": "Pengguna & penganjur",
  "Everyone signs up as a donor. Approve community groups (universities, companies, NGOs) as drive organizers here.": "Semua orang mendaftar sebagai penderma. Luluskan kumpulan komuniti (universiti, syarikat, NGO) sebagai penganjur kempen di sini.",
  "Donors": "Penderma", "Blood bank admins": "Pentadbir bank darah", "Synthetic demo donors": "Penderma demo sintetik", "Used by the AI, cannot log in": "Digunakan oleh AI, tidak boleh log masuk",
  "Accounts": "Akaun", "Organizers": "Penganjur", "Admins": "Pentadbir", "Name": "Nama", "Role": "Peranan", "Blood": "Darah", "Activity": "Aktiviti", "Joined": "Menyertai",
  "Change to donor": "Tukar kepada penderma", "Approve as organizer": "Luluskan sebagai penganjur", "Search name or email": "Cari nama atau e-mel",
  "Organizers can create campaigns and check donors in, but cannot see stock, urgent requests or anyone's HemoScan reports.": "Penganjur boleh mencipta kempen dan mendaftar masuk penderma, tetapi tidak boleh melihat stok, permintaan segera atau laporan HemoScan sesiapa.",
  "AI models": "Model AI", "How each AI feature works, how it was validated, and whether it treats donors fairly.": "Cara setiap ciri AI berfungsi, cara ia disahkan, dan sama ada ia adil kepada penderma.",
  "Official MOH data loaded": "Data rasmi KKM dimuatkan", "Official data not imported": "Data rasmi belum diimport", "Training run": "Larian latihan", "Series trained": "Siri dilatih",
  "Official MOH data": "Data rasmi KKM", "Random Forest chosen": "Random Forest dipilih", "Simpler method chosen": "Kaedah lebih mudah dipilih", "Better than baseline": "Lebih baik daripada asas",
  "average error reduction": "purata pengurangan ralat", "Error": "Ralat", "Weekday average": "Purata hari bekerja", "Accuracy": "Ketepatan", "Predicted": "Diramal", "Actual": "Sebenar",
  "What drives the score": "Apa yang mempengaruhi skor", "Scoring rules": "Peraturan pemarkahan", "Distance (closer is better)": "Jarak (lebih dekat lebih baik)",
  "Past reply rate": "Kadar balasan lalu", "Exact blood type": "Jenis darah tepat", "Regular donor": "Penderma tetap", "Search radius": "Radius carian",
  "Matching · by age band": "Padanan · mengikut kumpulan umur", "Age": "Umur", "Eligible": "Layak", "vs best": "berbanding terbaik",
  "Return prediction · by age band": "Ramalan kembali · mengikut kumpulan umur", "Language model (AI explanations)": "Model bahasa (penerangan AI)",
  "Not set — using templates": "Belum ditetapkan — menggunakan templat", "Key set": "Kunci ditetapkan", "Provider:": "Penyedia:", "Model:": "Model:", "Used for:": "Digunakan untuk:",
  "Test AI connection": "Uji sambungan AI", "Testing…": "Menguji…", "Calibration (predicted vs actual)": "Penentukuran (diramal lwn sebenar)",
  // ---------- toasts
  "Appointment cancelled": "Temujanji dibatalkan", "Booking confirmed! See My Appointments.": "Tempahan disahkan! Lihat Temujanji Saya.", "Campaign created successfully": "Kempen berjaya dicipta",
  "Donation recorded · stock updated": "Derma direkod · stok dikemas kini", "Location found — campaigns sorted by distance": "Lokasi dijumpai — kempen disusun mengikut jarak",
  "Marked as stopped today": "Ditanda berhenti hari ini", "Medicine deleted": "Ubat dipadam", "Medicine updated": "Ubat dikemas kini",
  "New urgent request — a blood bank needs your help": "Permintaan segera baharu — bank darah memerlukan bantuan anda", "Notifications marked as read": "Pemberitahuan ditanda sudah dibaca",
  "Profile saved successfully": "Profil berjaya disimpan", "Push notifications are on for this device": "Pemberitahuan tolak aktif untuk peranti ini",
  "Push notifications turned off for this device": "Pemberitahuan tolak dimatikan untuk peranti ini", "Report deleted": "Laporan dipadam", "Request closed": "Permintaan ditutup",
  "Request created — review the AI-ranked donors": "Permintaan dicipta — semak penderma yang disusun oleh AI", "Test alert sent — check your email, phone and notifications": "Makluman ujian dihantar — semak e-mel, telefon dan pemberitahuan anda",
  "Thanks for your feedback!": "Terima kasih atas maklum balas anda!", "Values reopened for editing": "Nilai dibuka semula untuk diubah", "Your donor account has been created": "Akaun penderma anda telah dicipta",
  "Alert settings saved": "Tetapan makluman disimpan",
  "My appointments": "Temujanji saya", "When": "Bila", "To": "Kepada", "Channel": "Saluran", "Last 7 days": "7 hari lalu",
  "not configured — simulated": "belum dikonfigurasi — simulasi", "simulated": "simulasi", "sent": "dihantar", "failed": "gagal", "skipped": "dilangkau", "Demo inventory updated": "Inventori demo dikemas kini",
  "Campaigns and venues are fictional demo records with approximate locations. Distances are straight-line; drive times are rough estimates. Map data © OpenStreetMap contributors.": "Kempen dan tempat ialah rekod demo rekaan dengan lokasi anggaran. Jarak ialah garis lurus; masa memandu ialah anggaran kasar. Data peta © penyumbang OpenStreetMap.",
  "Demo placeholders — verify against Pusat Darah Negara (pdn.gov.my) before use. Final decision is made by blood bank staff.": "Nilai demo — sahkan dengan Pusat Darah Negara (pdn.gov.my) sebelum digunakan. Keputusan muktamad dibuat oleh kakitangan bank darah.",
  "Blood type, birth year and weight are self-reported and used only for the eligibility check and donor matching. They are not medically verified — screening staff make the final decision.": "Jenis darah, tahun lahir dan berat dilaporkan sendiri dan hanya digunakan untuk semakan kelayakan dan padanan penderma. Ia tidak disahkan secara perubatan — kakitangan saringan membuat keputusan muktamad.",
  "Have you eaten a meal in the last 4 hours (not fasting)?": "Adakah anda telah makan dalam 4 jam yang lalu (tidak berpuasa)?",
  "In the past week, have you had fever, flu, cough, a headache or migraine, or seen a doctor?": "Dalam seminggu yang lalu, adakah anda demam, selesema, batuk, sakit kepala atau migrain, atau berjumpa doktor?",
  "Have you taken antibiotics in the last 2 weeks?": "Adakah anda mengambil antibiotik dalam 2 minggu yang lalu?",
  "Have you had dengue in the last 6 months?": "Adakah anda menghidap denggi dalam 6 bulan yang lalu?",
  "Have you had dental treatment in the last 24 hours?": "Adakah anda menerima rawatan gigi dalam 24 jam yang lalu?",
  "In the last 6 months, have you had a tattoo, body piercing, bekam (cupping) or acupuncture?": "Dalam 6 bulan yang lalu, adakah anda membuat tatu, tindikan badan, bekam atau akupunktur?",
  "In the last 6 months, have you had surgery, a blood transfusion or a needle-stick injury?": "Dalam 6 bulan yang lalu, adakah anda menjalani pembedahan, menerima pemindahan darah atau tercucuk jarum?",
  "In the last 4 weeks, have you had a vaccine or a cosmetic injection (e.g. botox, filler)?": "Dalam 4 minggu yang lalu, adakah anda menerima vaksin atau suntikan kosmetik (cth. botoks, pengisi)?",
  "Have you been drunk in the last 24 hours?": "Adakah anda mabuk dalam 24 jam yang lalu?",
  "(Women) Are you pregnant or breastfeeding, or did you give birth or miscarry in the last 6 months?": "(Wanita) Adakah anda hamil atau menyusukan bayi, atau bersalin atau keguguran dalam 6 bulan yang lalu?",
  "(Women) Are you having your period now?": "(Wanita) Adakah anda sedang haid sekarang?",
  "Do you have a long-term condition such as heart disease, cancer, diabetes, epilepsy, kidney disease, or hepatitis B/C?": "Adakah anda mempunyai penyakit jangka panjang seperti penyakit jantung, kanser, diabetes, epilepsi, penyakit buah pinggang, atau hepatitis B/C?",
  "Have you ever had malaria, or travelled to a malaria-risk area in the last 12 months?": "Pernahkah anda menghidap malaria, atau ke kawasan berisiko malaria dalam 12 bulan yang lalu?",
  "Based on Pusat Darah Negara (PDN) donor criteria, checked Nov 2026. A guide only — the doctor or screening staff at the drive make the final decision.": "Berdasarkan kriteria penderma Pusat Darah Negara (PDN), disemak Nov 2026. Panduan sahaja — doktor atau kakitangan saringan di lokasi membuat keputusan muktamad.",
  "Sex (optional)": "Jantina (pilihan)", "Prefer not to say": "Tidak mahu nyatakan", "Sets your donation gap: women every 4 months, men every 3.": "Menentukan jarak derma: wanita setiap 4 bulan, lelaki setiap 3 bulan.",
  "Your data & privacy": "Data & privasi anda", "Download my data": "Muat turun data saya", "Privacy notice": "Notis privasi", "Delete my account": "Padam akaun saya",
  "You control your personal data under Malaysia's Personal Data Protection Act 2010. Uploaded blood test files are encrypted, and only you can see your HemoScan reports and medicine list.": "Anda mengawal data peribadi anda di bawah Akta Perlindungan Data Peribadi 2010. Fail ujian darah yang dimuat naik disulitkan, dan hanya anda boleh melihat laporan HemoScan dan senarai ubat anda.",
  "This permanently removes your profile, bookings, donation history, HemoScan reports and medicine list. It can't be undone.": "Ini akan memadam profil, tempahan, sejarah derma, laporan HemoScan dan senarai ubat anda secara kekal. Ia tidak boleh dibatalkan.",
  "Your password": "Kata laluan anda", "Type DELETE to confirm": "Taip DELETE untuk mengesahkan", "Want a copy first?": "Mahu salinan dahulu?", "Delete permanently": "Padam secara kekal",
  "Your account and data have been deleted": "Akaun dan data anda telah dipadam",
  "and agree to HemoLink storing my details to arrange donations.": "dan bersetuju HemoLink menyimpan butiran saya untuk mengatur derma.", "I have read the": "Saya telah membaca", "privacy notice": "notis privasi",
  "Too many wrong passwords. This account is locked for": "Terlalu banyak kata laluan salah. Akaun ini dikunci selama",
  "Source code": "Kod sumber", "Privacy": "Privasi",
  "Find venue on map": "Cari tempat pada peta", "Pick the campaign location": "Pilih lokasi kempen",
  "Click the map or drag the pin to the venue entrance. If you skip this, we place it from the venue and city.": "Klik peta atau seret pin ke pintu masuk tempat. Jika dilangkau, kami letakkan berdasarkan tempat dan bandar.",
  "Pinned": "Dipin", "Pin moved": "Pin dialih", "Found": "Dijumpai", "Your location": "Lokasi anda", "Current pin": "Pin semasa",
  "— drag the pin to fine-tune.": "— seret pin untuk melaraskan.", "That point is outside Malaysia — please pick a place in Malaysia.": "Titik itu di luar Malaysia — sila pilih tempat di Malaysia.",
  "Location saved — donors now see the new pin": "Lokasi disimpan — penderma kini melihat pin baharu", "Click the map to place the pin first.": "Klik peta untuk meletakkan pin dahulu.",
  "Type the venue and city first, then press Find.": "Taip tempat dan bandar dahulu, kemudian tekan Cari.", "Location permission was denied.": "Kebenaran lokasi ditolak.",
  "Location permission was denied — distances use your profile city instead.": "Kebenaran lokasi ditolak — jarak menggunakan bandar profil anda.",
  "Couldn't get your location — distances use your profile city instead.": "Lokasi anda tidak dapat diperoleh — jarak menggunakan bandar profil anda.",
};

const MS_PATTERNS = [
  [/^Good (morning|afternoon|evening), (.+)$/, (m, t, n) => `Selamat ${{ morning: "pagi", afternoon: "petang", evening: "malam" }[t]}, ${n}`],
  [/^(\d+) slots? left$/, "$1 slot tinggal"], [/^(\d+) units?$/, "$1 unit"], [/^(\d+) bookings?$/, "$1 tempahan"], [/^(\d+) donations?$/, "$1 derma"],
  [/^(\d+) left$/, "$1 tinggal"], [/^(\d+) reports?$/, "$1 laporan"], [/^(\d+) guides$/, "$1 panduan"], [/^(\d+) tests$/, "$1 ujian"], [/^(\d+) campaigns$/, "$1 kempen"],
  [/^(\d+) questions$/, "$1 soalan"], [/^(\d+) reviews?$/, "$1 ulasan"], [/^(\d+) shown$/, "$1 dipaparkan"], [/^(\d+) entries$/, "$1 rekod"],
  [/^~(\d+) min drive$/, "~$1 min memandu"], [/^(\d+)d ago$/, "$1 hari lalu"], [/^wait (\d+) days?$/, "tunggu $1 hari"],
  [/^Last donation (\d+) days ago\.$/, "Derma terakhir $1 hari lalu."], [/^Last donation (\d+) days ago\. Answer today's questions below before you go\.$/, "Derma terakhir $1 hari lalu. Jawab soalan hari ini di bawah sebelum pergi."],
  [/^(\d+) more to go · each donation can help up to 3 patients — up to$/, "$1 lagi · setiap derma boleh membantu sehingga 3 pesakit — sehingga"],
  [/^Next milestone: (\d+) donations$/, "Pencapaian seterusnya: $1 derma"], [/^(\d+) donations$/, "$1 derma"],
  [/^In (\d+) days · (.*)$/, "Dalam $1 hari · $2"], [/^From your HemoScan report of (.+)$/, "Daripada laporan HemoScan anda pada $1"],
  [/^Distances from (.+) \(your profile city\)\. Use GPS for your exact location\. Showing (\d+) of (\d+) campaigns\.$/, "Jarak dari $1 (bandar profil anda). Guna GPS untuk lokasi tepat. Memaparkan $2 daripada $3 kempen."],
  [/^Distances from your current location \(GPS, ±(.+) m\)\. Showing (\d+) of (\d+) campaigns\.$/, "Jarak dari lokasi semasa anda (GPS, ±$1 m). Memaparkan $2 daripada $3 kempen."],
  [/^≤ (\d+) km$/, "≤ $1 km"], [/^(\d+) waiting for reply$/, "$1 menunggu balasan"], [/^(\d+) current · (\d+) total$/, "$1 semasa · $2 jumlah"],
  [/^(\d+) days of supply · safe level (\d+)$/, "$1 hari bekalan · paras selamat $2"], [/^(.+) is already below the safe level$/, "$1 sudah di bawah paras selamat"],
  [/^Plan a (.+) drive$/, "Rancang kempen $1"], [/^Mobilise (.+) donors$/, "Gerakkan penderma $1"], [/^Post an urgent request for (.+)$/, "Hantar permintaan segera untuk $1"],
  [/^Edit (.+) stock level$/, "Ubah tahap stok $1"], [/^(.+) · (\d+)\/(\d+) booked$/, "$1 · $2/$3 ditempah"],
  [/^Alerts sent to (\d+) matched donors$/, "Makluman dihantar kepada $1 penderma sepadan"], [/^(\d+) demo donors replied$/, "$1 penderma demo membalas"],
  [/^Found (\d+) tests — please check them$/, "$1 ujian dijumpai — sila semak"], [/^Read (\d+) tests from your photo — please check each one$/, "$1 ujian dibaca daripada foto anda — sila semak setiap satu"],
  [/^Analysis ready · (\d+) patterns? flagged$/, "Analisis sedia · $1 corak ditanda"], [/^To (.+@.+)$/, "Kepada $1"],
  [/^(\d+) reminder\(s\) and (\d+) "donate again" alert\(s\) sent$/, "$1 peringatan dan $2 makluman \"derma semula\" dihantar"],
  [/^Campaign created · (\d+) nearby donor\(s\) notified$/, "Kempen dicipta · $1 penderma berhampiran dimaklumkan"],
  [/^Couldn't find "(.+)" — click the map to place the pin instead\.$/, "\"$1\" tidak dijumpai — klik peta untuk meletakkan pin."],
  [/^Your latest HemoScan report \((.+)\) had no patterns flagged\.$/, "Laporan HemoScan terkini anda ($1) tiada corak ditanda."],
  [/^Your HemoScan report from (\S+) shows haemoglobin (\S+) g\/dL, below the typical (\S+) g\/dL minimum\. Please speak to a doctor before booking\.$/, "Laporan HemoScan anda pada $1 menunjukkan hemoglobin $2 g/dL, di bawah minimum biasa $3 g/dL. Sila berjumpa doktor sebelum menempah."],
  [/^Your HemoScan report from (\S+) shows haemoglobin (\S+) g\/dL — fine for donating; it is re-checked on the day\.$/, "Laporan HemoScan anda pada $1 menunjukkan hemoglobin $2 g/dL — sesuai untuk menderma; ia disemak semula pada hari tersebut."],
  [/^Demo mode: (.+) aren't connected on this server yet, so those messages are recorded in the admin's delivery log instead of being sent\.$/, (m, a) => `Mod demo: ${a.replace("email", "e-mel").replace(" and ", " dan ")} belum disambungkan pada pelayan ini, jadi mesej direkodkan dalam log penghantaran pentadbir dan tidak dihantar.`],
  [/^(Donor|Drive Organizer|Blood Bank Admin|Organizer|Admin) · (.+@.+)$/, (m, r, em) => `${MS[r] || r} · ${em}`],
  [/^(\d+) simulated$/, "$1 simulasi"], [/^(\d+) sent$/, "$1 dihantar"], [/^(\d+) failed$/, "$1 gagal"],
  [/^Sources \(checked (.+)\)$/, "Sumber (disemak $1)"],
  [/^You can donate again from (.+) \((\d+) days between whole-blood donations\)\.$/, "Anda boleh menderma semula mulai $1 ($2 hari antara derma darah penuh)."],
  [/^You agreed to privacy notice version (\S+) on (.+)\.$/, "Anda bersetuju dengan notis privasi versi $1 pada $2."],
  [/^Too many wrong passwords\. This account is locked for (\d+) more minute\(s\)\.$/, "Terlalu banyak kata laluan salah. Akaun ini dikunci selama $1 minit lagi."],
  [/^Added — (.+)$/, "Ditambah — $1"], [/^Hb (.+) g\/dL$/, "Hb $1 g/dL"], [/^No medicines in the last (\d+) days\.$/, "Tiada ubat dalam $1 hari yang lalu."],
  [/^Wait until (\S+) \((.+) after the last dose\)\.$/, "Tunggu sehingga $1 ($2 selepas dos terakhir)."],
  [/^Not while taking it, and for (.+) after the last dose\.$/, "Bukan semasa mengambilnya, dan selama $1 selepas dos terakhir."],
  [/^Started (.+) · (still taking|last dose (.+))$/, (m, a, b, c) => `Mula ${a} · ${c ? "dos terakhir " + c : "masih diambil"}`],
];

function lang() {
  return state.lang === "ms" ? "ms" : "en";
}
function translateText(s) {
  const core = s.replace(/\s+/g, " ").trim();
  if (!core) return s;
  let out = MS[core];
  if (out === undefined) {
    for (const [rx, rep] of MS_PATTERNS) {
      if (rx.test(core)) {
        out = core.replace(rx, rep);
        break;
      }
    }
  }
  if (out === undefined) return s;
  const lead = s.match(/^\s*/)[0], tail = s.match(/\s*$/)[0];
  return lead + out + tail;
}
function swapText(n) {
  const t = translateText(n.nodeValue);
  if (t === n.nodeValue) return;
  const p = n.parentElement;
  if (p && p.tagName === "OPTION" && !p.hasAttribute("value")) p.setAttribute("value", p.textContent); // keep the submitted value in English
  n.nodeValue = t;
}
const SKIP = "script,style,textarea,code,.leaflet-control-attribution,[data-no-i18n]";
function translateTree(root) {
  if (lang() !== "ms" || !root) return;
  if (root.nodeType === 3) {
    if (!root.parentElement?.closest(SKIP)) swapText(root);
    return;
  }
  if (root.nodeType !== 1 || root.closest?.(SKIP)) return;
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) {
    if (n.parentElement?.closest(SKIP)) continue;
    swapText(n);
  }
  const els = [root, ...root.querySelectorAll("[placeholder],[title],[aria-label]")];
  for (const el of els) {
    for (const a of ["placeholder", "title", "aria-label"]) {
      const v = el.getAttribute?.(a);
      if (v) {
        const t = translateText(v);
        if (t !== v) el.setAttribute(a, t);
      }
    }
  }
}
const i18nObserver = new MutationObserver((muts) => {
  if (lang() !== "ms") return;
  for (const m of muts) for (const node of m.addedNodes) translateTree(node);
});

function savedLang() {
  try {
    return localStorage.getItem("hl-lang");
  } catch (err) {
    return null;
  }
}
function setLang(l, remember = true) {
  l = l === "ms" ? "ms" : "en";
  const changed = state.lang !== l;
  state.lang = l;
  if (remember)
    try {
      localStorage.setItem("hl-lang", l);
    } catch (err) {
      /* storage unavailable */
    }
  document.documentElement.lang = l === "ms" ? "ms" : "en";
  return changed;
}
async function switchLang(l) {
  setLang(l);
  if (state.user) {
    try {
      await send("/api/me/lang", { lang: l }, "PATCH");
      state.user.lang = l;
    } catch (err) {
      /* still switch locally */
    }
    await render();
  } else renderAuth();
  if (l === "ms") translateTree(document.body);
}
// Once per login: a choice made on this device wins (and is saved to the account), otherwise use the account's language.
async function syncLangWithUser() {
  if (!state.user || state.langSyncedFor === state.user.id) return;
  state.langSyncedFor = state.user.id;
  const local = savedLang();
  if (local && local !== state.user.lang) {
    setLang(local, false);
    try {
      await send("/api/me/lang", { lang: local }, "PATCH");
      state.user.lang = local;
    } catch (err) {
      /* keep the local choice */
    }
  } else if (state.user.lang) setLang(state.user.lang, false);
}
const langToggle = () =>
  `<div class="lang-toggle" role="group" aria-label="Language"><button data-lang="en" class="${lang() === "en" ? "on" : ""}" data-no-i18n>EN</button><button data-lang="ms" class="${lang() === "ms" ? "on" : ""}" data-no-i18n>BM</button></div>`;

document.addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-lang]");
  if (!b) return;
  ev.preventDefault();
  if (b.dataset.lang !== lang()) switchLang(b.dataset.lang);
});

(function initI18n() {
  const saved = savedLang();
  const browserMs = (navigator.language || "").toLowerCase().startsWith("ms");
  setLang(saved || (browserMs ? "ms" : "en"), false);
  i18nObserver.observe(document.body, { childList: true, subtree: true });
  translateTree(document.body); // anything already on screen
})();
