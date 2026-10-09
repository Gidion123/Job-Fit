# Prompt update copywriting JobFit (untuk Open Design)

**Untuk file:** `JobFit-design2.html` (JobFit v3, prototipe interaksi lokal)
**Dibuat:** 9 Oktober 2026 · **Keputusan pemilik:** sapaan "kamu"; label utama Bahasa Indonesia dengan sub-label English untuk nama fitur; dua versi copy (demo dan live); antarmuka dwibahasa (Indonesia dan English).
**Dasar:** README, D-102 sampai D-105 di `docs/decisions.md`, `docs/checkpoint_3/CP3_03_Streamlit_UI.md`, `docs/cv-coach-plan.md`, `docs/privacy-threat-model.md`.

Cara pakai: salin semua isi di bawah garis ke Open Design sebagai satu prompt. Jika terlalu panjang, kirim Bagian 0 sampai 4 dulu, lalu Bagian 5 per layar (5.1, 5.2, dan seterusnya). Setiap kiriman harus selalu diawali Bagian 0.

---

## 0. Tugas dan batasan

Kamu adalah UX writer dan product designer senior untuk produk digital Indonesia. Perbarui **copy** pada prototipe JobFit ini (`index.html` dan script aplikasinya) sesuai spesifikasi di bawah.

**Yang harus dilakukan:**
1. Ganti semua teks antarmuka sesuai tabel di Bagian 5.
2. Buat sistem copy dwibahasa (`id` dan `en`) dengan dua mode (`demo` dan `live`), sesuai Bagian 4.
3. Tambahkan tombol ganti bahasa **ID / EN** di header.
4. Perbaiki bug copy di Bagian 4.4.

**Yang TIDAK boleh diubah:**
- Layout, grid, spacing, token warna, tipografi, ikon, komponen, dan animasi. Jangan ubah CSS kecuali benar-benar perlu untuk tombol bahasa (pakai gaya `.session-btn` yang sudah ada).
- Nama `data-action`, `id` elemen, struktur state `S`, alur halaman, logika skor, logika filter, dan parameter `?scenario=`.
- Atribut `value` pada `<option>` filter (contoh: `Singapore`, `3–4 tahun`, `AI / ML Engineering`). Yang diterjemahkan hanya teks yang tampil. Logika filter mencocokkan `value`, jadi jangan sampai rusak.
- Fixture di `window.JOBFIT`: teks CV contoh, teks JD contoh, nama perusahaan sintetis, dan teks requirement. Ini dokumen contoh, bukan teks antarmuka, dan logika bukti bergantung padanya. Satu-satunya pengecualian ada di Bagian 4.4.
- Regex sanitizer. Yang diterjemahkan hanya teks pengganti seperti `[email disamarkan]`.

Jika ada teks yang tidak tercantum di tabel, tulis ulang mengikuti panduan voice di Bagian 1 dan glosarium di Bagian 2. Jangan biarkan teks itu tetap memakai "Anda".

---

## 1. Panduan voice dan tone

### 1.1 Karakter: "Mentor karier yang jujur"

Pengguna JobFit adalah pencari kerja tahap awal di bidang AI dan data: fresh graduate sampai pengalaman 2 tahun. Banyak dari mereka sedang cemas, sudah berkali-kali ditolak, dan menghadapi lowongan "junior" yang ternyata meminta pengalaman bertahun-tahun. JobFit berbicara seperti senior yang jujur dan peduli: tidak menghakimi, tidak melebih-lebihkan, dan selalu menunjukkan langkah berikutnya.

| Prinsip | Artinya | Contoh |
| --- | --- | --- |
| **Jujur** | Sebut batasnya. Jangan menjanjikan hasil. | "Bukan peluang diterima kerja." |
| **Jelas** | Satu konsep, satu istilah. Tanpa jargon teknis. | "deskripsi lowongan", bukan "JD" atau "corpus" |
| **Hangat, tidak lebay** | Ramah dan tenang. Tanpa slang, tanpa seruan berlebihan. | "Tidak apa-apa." Hindari "Yuk!", "Kuy", "Mantap!" |
| **Memberi jalan** | Setiap kabar kurang enak diikuti langkah berikutnya. | "Hapus filter untuk melihatnya lagi." |
| **Menghormati pengguna** | Tidak menyalahkan dan tidak menggurui. | "Belum ada bukti bukan berarti belum pernah." |

### 1.2 Tone per konteks

| Konteks | Tone | Rumus |
| --- | --- | --- |
| Beranda | Yakin, tajam | Masalah nyata → janji yang bisa dibuktikan |
| Unggah dan privasi | Tenang, transparan, spesifik | Apa yang terjadi → siapa yang memegang kendali |
| Proses | Informatif, sabar | Tahap nyata, tanpa persentase palsu |
| Hasil cek | Netral, faktual | Fakta → artinya → batasnya |
| Gap atau belum ada bukti | Empatik, tidak menghakimi | Fakta → bukan vonis → langkah jujur |
| Syarat pengalaman tidak terpenuhi | Lugas tapi hormat | Fakta → menulis ulang tidak mengubahnya |
| Error | Menenangkan, solutif | Apa yang terjadi → data aman → coba apa |
| Hapus sesi | Tegas, jelas konsekuensinya | Apa yang hilang → apa yang tidak ikut terhapus |

### 1.3 Aturan bahasa (Bahasa Indonesia)

1. **Sapaan "kamu"**, selalu huruf kecil kecuali di awal kalimat. Tulis "CV kamu", bukan "CV-mu" atau "CV Anda". Tidak boleh ada kata "Anda" yang tersisa.
2. **Pernyataan dari pengguna** (checkbox persetujuan) memakai "Saya": "Saya sudah memeriksa…".
3. **JobFit menyebut dirinya "JobFit"** untuk temuan analisis ("JobFit belum menemukan bukti…"). Hindari "kami".
4. **Kapitalisasi:** sentence case untuk judul, tombol, dan label ("Cari lowongan yang relevan"). Pengecualian: nama fitur di Bagian 2 ditulis sebagai nama produk (Title Case) saat muncul sebagai nama, misalnya di menu, judul kartu, dan eyebrow.
5. **Panjang:** judul ≤ 8 kata, tombol 1–4 kata diawali kata kerja, kalimat isi ≤ 20 kata. Satu paragraf memuat satu gagasan.
6. **Tanda baca:** tanpa tanda seru dan tanpa emoji. Hindari garis miring di kalimat ("identitas/kontak" menjadi "identitas dan kontak"). Tanda `·` hanya untuk metadata.
7. **Angka dan tanggal:** koma desimal ("1,4 tahun"), tanggal "9 Okt 2026" atau "9 Oktober 2026".
8. **Istilah asing:** pakai padanan Indonesia bila sudah lazim (unggah, unduh, sesi, filter, data). Pertahankan istilah pasar kerja yang memang dipakai pencari kerja: CV, AI, remote, hybrid, on-site, entry level, judul pekerjaan, dan nama role family. Istilah ini tidak dimiringkan di UI.
9. **Sub-label English** hanya untuk nama fitur di Bagian 2, dan hanya di lokasi yang disebut di Bagian 4.3.

### 1.4 Aturan bahasa (English)

- Plain, warm, direct. Address the user as "you". JobFit may say "we" for system actions ("we couldn't read this file"), and uses "JobFit" for analysis verdicts.
- Sentence case everywhere except feature names. No exclamation marks, no emoji.
- Decimal point ("1.4 years"), dates "9 Oct 2026".
- Keep the same length budget as Indonesian. Buttons use `white-space: nowrap`, so EN labels must stay short.

### 1.5 Kunci kejujuran (tidak boleh dilanggar di bahasa atau mode mana pun)

1. Skor adalah **cakupan bukti CV**, bukan peluang diterima kerja dan bukan skor ATS.
2. Hasil pencarian **tidak diberi skor**. Relevan belum tentu cocok.
3. Jangan pernah mengklaim CV menjadi anonim atau aman 100%. Pembersihan data pribadi **punya batas**.
4. **Demo:** tidak ada data yang dikirim ke server atau layanan AI. **Live:** teks dikirim ke layanan AI melalui OpenRouter **hanya setelah persetujuan**, dan hasilnya hanya ada di sesi.
5. Deskripsi lowongan yang ditempel hanya dipakai di sesi itu dan **tidak masuk database lowongan**.
6. Fitur Perkuat CV **tidak pernah menambah klaim**: tidak ada alat, angka, atau pengalaman baru. Jawaban pengguna **tidak mengubah skor**.
7. Kekurangan durasi pengalaman **hanya disimpulkan** jika pengguna mengonfirmasi riwayat kerjanya lengkap.
8. Batas: **3 cek kecocokan per sesi**. Di live juga berlaku **1 pencarian per sesi**. Di live, jangan menjanjikan "jatah tidak berkurang" kecuali untuk kasus yang ditandai aman di tabel.
9. Jangan menjanjikan "lebih mudah diterima", "lolos ATS", atau hasil apa pun di luar bukti.

---

## 2. Glosarium (satu konsep, satu istilah)

| Konsep (kode) | ID: label utama | Sub-label English (di UI ID) | EN UI |
| --- | --- | --- | --- |
| Find Jobs | **Cari Lowongan** | Find Jobs | Find Jobs |
| Check a Job | **Cek Lowongan** | Check a Job | Check a Job |
| Analyze Fit | **Cek Kecocokan** (tombol: "Cek kecocokan") | Analyze Fit | Analyze Fit (button: "Analyze fit") |
| Relevant Jobs | **Lowongan Relevan** | Relevant Jobs | Relevant Jobs |
| CV Evidence Coverage | **Cakupan Bukti CV** | CV Evidence Coverage | CV Evidence Coverage |
| Improve My CV for This Job | **Perkuat CV** (lengkap: "Perkuat CV untuk lowongan ini") | Improve My CV for This Job | Improve My CV (full: "Improve my CV for this job") |
| Market skills | Keterampilan yang paling dicari | — | Most-requested skills |
| corpus | database lowongan JobFit (demo: lowongan contoh) | — | JobFit's job database (demo: sample jobs) |
| JD | deskripsi lowongan | — | job description |
| requirement / required / preferred | syarat / syarat wajib / nilai tambah | — | requirement / required / nice to have |
| evidence / quote | bukti / kutipan dari CV kamu | — | evidence / quoted from your CV |
| sanitize / mask | membersihkan data pribadi / menyamarkan | — | remove personal details / hide |
| consent | persetujuan | — | approval / agree |
| parse | membaca CV | — | read your CV |
| provider AI | layanan AI (live: melalui OpenRouter) | — | AI service (live: via OpenRouter) |
| quota | jatah cek kecocokan | — | fit checks |
| synthetic / demo CV | CV contoh | — | sample CV |
| session | sesi | — | session |

### Label status bukti (badge)

| Kode | Lama | ID | EN |
| --- | --- | --- | --- |
| MATCH | Didukung | Ada bukti | Evidence found |
| PARTIAL | Sebagian didukung | Bukti sebagian | Partial evidence |
| NO_MATCH | Belum ada bukti | Belum ada bukti | No evidence yet |
| UNVERIFIED | Tidak terverifikasi | Belum bisa dipastikan | Can't confirm yet |
| CONFLICT | Konflik terkonfirmasi | Belum memenuhi syarat | Requirement not met |

### Opsi filter (yang diubah hanya teks tampilan; `value` tetap)

| value | ID | EN |
| --- | --- | --- |
| (kosong) | Semua | Any |
| AI / ML Engineering, Data Science, GenAI / LLM, Software-AI | (tetap sama) | (same) |
| Indonesia / Singapore / Malaysia | Indonesia / Singapura / Malaysia | Indonesia / Singapore / Malaysia |
| Entry / 1–2 tahun / 3–4 tahun / 5+ tahun | Entry level / 1–2 tahun / 3–4 tahun / 5+ tahun | Entry level / 1–2 years / 3–4 years / 5+ years |
| On-site / Hybrid / Remote | (tetap sama) | (same) |
| posted: kosong / 7 / 30 | Kapan saja / 7 hari terakhir / 30 hari terakhir | Any time / Last 7 days / Last 30 days |

Metadata pengalaman di kartu lowongan juga diterjemahkan dari `value` (`3–4 tahun` menjadi "3–4 years" di EN).

---

## 3. Masalah di copy lama yang harus hilang

- Kata "Anda" di semua layar.
- Campuran yang tidak konsisten: "Find Jobs" di sebelah "Cari lowongan", "CV Evidence Coverage" di sebelah "Cakupan bukti CV", "Perbaiki CV untuk job ini", "Apply / sumber", "Role family", "Evidence-first career tools".
- Satu konsep dengan banyak nama (Analyze Fit / Analisis bukti / Hasil Analyze Fit; Perbaiki CV / Improve My CV; Cek lowongan / Check a Job).
- Jargon: corpus, parsing, provider AI, metadata, representasi pencarian CV, persyaratan yang dikenali, fakta latar belakang.
- Sisa bahasa Prancis: "CV actif", "Texte exact…", "JobFit-CV-synthetique.txt".
- Label "Teks CV yang disetujui" muncul sebelum pengguna menyetujui.

---

## 4. Implementasi sistem copy

### 4.1 Struktur

- Buat objek `COPY = { id: {...}, en: {...} }` dan helper `t(key, vars)` dengan interpolasi `{nama}`.
- Bila sebuah string berbeda antara demo dan live, simpan sebagai `{ demo: '…', live: '…' }`. `t()` memilih versi sesuai `MODE`.
- `MODE` dibaca dari `?mode=live`. Default `demo`. Mode live hanya untuk meninjau copy produk beta. Jangan tampilkan tautan ke mode live di UI.
- Bahasa disimpan di `S.lang`, dibaca dari `?lang=en`, dengan default `id`. **Jangan pakai localStorage**: prototipe ini menyatakan tidak menyimpan data di browser.
- Saat bahasa berganti: render ulang halaman aktif **tanpa** mereset sesi, lalu perbarui `<html lang>`, `document.title`, `<meta name="description">`, header, footer, `noscript`, skip link, dan semua `aria-label`. Teks yang sekarang statis di HTML harus dirender dari `COPY`.
- Simpan keputusan draf sebagai kode (`accepted`, `rejected`, `edited`, `review`), lalu terjemahkan saat render. Kode lama membandingkan `c.decision==='Diterima'`, jadi ganti menjadi `c.decision==='accepted'`.

### 4.2 Tombol bahasa

Taruh di `.header-actions`, sebelum tombol Bantuan. Isinya dua tombol, **ID** dan **EN**, dengan gaya `.session-btn`, `aria-pressed` untuk bahasa aktif, dan grup ber-`aria-label` "Bahasa" (EN: "Language"). Target sentuh minimal 44px. Di layar ≤ 374px, label "Bantuan" boleh disembunyikan seperti sekarang, tetapi tombol bahasa tetap tampil.

### 4.3 Aturan sub-label English (hanya di UI Indonesia)

Tampilkan nama fitur English sebagai `<span class="small muted" lang="en">Find Jobs</span>` **hanya** di tempat-tempat berikut:
1. Eyebrow judul halaman fitur. Format: `Cari Lowongan · Find Jobs`.
2. Judul kartu pilihan di layar CV siap: baris kecil di bawah H2.
3. Di bawah tombol "Perkuat CV untuk lowongan ini" pada sidebar hasil (menggantikan teks kecil yang sudah ada).
4. Di dialog Bantuan, dalam kurung setelah nama fitur pertama kali disebut.

Sub-label **tidak** ditampilkan di menu navigasi, tombol, badge, atau toast. Di UI English tidak ada sub-label.

### 4.4 Perbaikan bug copy

1. Dialog "Tinjau CV": judul `CV actif` dan trik `.replace()` dari teks Prancis harus dihapus. Pakai `t('dialog.review.*')`.
2. Nama file unduhan `JobFit-CV-synthetique.txt` diganti: ID `JobFit-CV-contoh.txt`, EN `JobFit-sample-CV.txt`.
3. Layar keterampilan: angka "/ 10" ditulis langsung di kode. Ganti dengan jumlah lowongan sebenarnya (`D.jobs.length`).
4. Label "Teks CV yang disetujui" di layar peninjauan diganti "Teks yang akan dianalisis" (pengguna belum menyetujui).
5. Placeholder teks manual harus tetap diawali judul bagian yang dikenali sanitizer: `PENGALAMAN KERJA` (ID) atau `WORK EXPERIENCE` (EN).

### 4.5 Pemeriksaan sebelum selesai

- [ ] Tidak ada kata "Anda" di UI Indonesia.
- [ ] Tidak ada "corpus", "provider", "parsing", "JD", atau "metadata" di UI Indonesia.
- [ ] Tidak ada teks Prancis.
- [ ] Setiap kunci punya versi `id` dan `en`, dan setiap string bervarian punya `demo` dan `live`.
- [ ] Semua `?scenario=` (expired, parse-error, privacy-error, provider, hold, empty-search, limit, unconfirmed, confirmed) tampil benar di 2 bahasa × 2 mode.
- [ ] Tidak ada tombol yang meluap di lebar 320px dan 375px. Jika meluap, perpendek teksnya, jangan ubah CSS.
- [ ] Kunci kejujuran di Bagian 1.5 terpenuhi di semua kombinasi.
- [ ] Atribut `lang` benar, dan semua `aria-label`, `title` halaman, serta pesan `role="status"` ikut diterjemahkan.

---

## 5. Tabel copy per layar

Format: **Kunci** · teks lama · **ID** · **EN**. "D:" artinya versi demo, "L:" artinya versi live. Bila tidak ada D/L, teksnya sama di kedua mode.

### 5.1 Global: head, header, navigasi, footer

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| meta.title | JobFit — Bukti, bukan tebakan | JobFit — Bukti, bukan tebakan | JobFit — Evidence, not guesswork |
| meta.description | JobFit — temukan lowongan AI dan data… | JobFit membantu kamu menemukan lowongan AI dan data yang relevan, lalu menunjukkan bagian CV yang menjadi bukti untuk setiap syarat. | JobFit finds relevant AI and data jobs, then shows exactly which lines of your CV back up each requirement. |
| skip | Langsung ke konten | Langsung ke konten | Skip to content |
| loading | Menyiapkan JobFit… | Menyiapkan JobFit… | Loading JobFit… |
| brand.aria | JobFit, kembali ke awal | JobFit, kembali ke beranda | JobFit, back to home |
| brand.tag | Bukti, bukan tebakan. | Bukti, bukan tebakan. | Evidence, not guesswork. |
| header.help | Bantuan | Bantuan | Help |
| header.help.aria | Bantuan dan batas prototipe | D: Bantuan dan batasan demo · L: Bantuan | D: Help and demo limits · L: Help |
| header.delete | Hentikan & hapus sesi | Hentikan & hapus sesi | Stop & delete session |
| header.lang.aria | — | Bahasa | Language |
| nav.aria | Aksi utama JobFit | Menu utama JobFit | JobFit main menu |
| nav.find | Find Jobs | Cari Lowongan | Find Jobs |
| nav.check | Check a Job | Cek Lowongan | Check a Job |
| nav.cv | CV siap ✓ | CV siap ✓ | CV ready ✓ |
| footer.left | JobFit · Evidence-first career tools | JobFit · Cek CV berbasis bukti | JobFit · Evidence-first career tools |
| footer.right | Prototipe lokal · Lowongan sintetis · Analisis simulasi | D: Mode demo · Lowongan contoh · Analisis simulasi · L: Beta terbatas · 3 cek kecocokan per sesi | D: Demo mode · Sample jobs · Simulated analysis · L: Limited beta · 3 fit checks per session |
| footer.link | Pelajari batasnya | D: Lihat batasannya · L: Cara kerja & privasi | D: See the limits · L: How it works & privacy |
| noscript.h1 | Aktifkan JavaScript untuk menggunakan JobFit | Aktifkan JavaScript untuk memakai JobFit | Turn on JavaScript to use JobFit |
| noscript.p | Prototipe interaktif ini memerlukan JavaScript… | D: Demo ini butuh JavaScript untuk membaca file di perangkat kamu dan menjalankan alurnya. Tidak ada CV yang dikirim ke layanan AI. · L: JobFit butuh JavaScript agar bisa berjalan. | D: This demo needs JavaScript to read files on your device and run the flow. No CV is sent to an AI service. · L: JobFit needs JavaScript to run. |
| dialog.close.aria | Tutup dialog | Tutup dialog | Close dialog |
| dialog.ok | Mengerti | Mengerti | Got it |

**Judul tab per halaman** (`JobFit — {label}`):

| Halaman | ID | EN |
| --- | --- | --- |
| landing | Beranda | Home |
| upload | Unggah CV | Upload CV |
| privacy | Cek teks CV | Review CV text |
| edit | Edit teks CV | Edit CV text |
| ready | CV siap | CV ready |
| find | Cari Lowongan | Find Jobs |
| results | Lowongan Relevan | Relevant Jobs |
| check | Cek Lowongan | Check a Job |
| analysis | Hasil Cek Kecocokan | Fit result |
| coach | Perkuat CV | Improve My CV |
| market | Keterampilan yang paling dicari | Most-requested skills |
| deleted | Sesi dihapus | Session deleted |
| expired | Sesi berakhir | Session ended |
| error | Proses terhenti | Something went wrong |
| processing | Sedang diproses | Processing |

### 5.2 Beranda (landing)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| landing.eyebrow | Karier AI & data · Berbasis bukti | Untuk karier AI & data | For AI & data careers |
| landing.h1 | Temukan peluang.<br>Pahami bukti di CV Anda. | Cari lowongan.<br>Lihat buktinya di CV kamu. | Find the jobs.<br>See the proof in your CV. |
| landing.lead | Cari lowongan AI dan data yang relevan, lalu lihat… | Judul lowongan tidak selalu menyebut level, padahal syaratnya bisa minta pengalaman 3 tahun. JobFit menunjukkan syarat mana yang sudah ada buktinya di CV kamu, lengkap dengan kutipannya. | Job titles don't always show the level, yet the requirements may ask for 3+ years. JobFit shows which requirements your CV already backs up, quoting the exact lines. |
| landing.cta | Unggah CV → | Unggah CV → | Upload CV → |
| landing.demo | Coba dengan CV demo | Coba dengan CV contoh | Try a sample CV |
| landing.privacy | Tinjau teks Anda sebelum memberi persetujuan. | Data pribadi dibersihkan dulu, dan kamu menyetujui teksnya sebelum dianalisis. | Personal details are removed first, and you approve the text before any analysis. |
| landing.preview.eyebrow | Bukti, bukan tebakan | Bukti, bukan tebakan | Evidence, not guesswork |
| landing.preview.note | Contoh cara membaca hasil • CV sintetis | Contoh hasil · CV contoh | Sample result · Sample CV |
| landing.preview.quoteLabel | Bukti persis dari CV | Kutipan dari CV | Quoted from the CV |
| landing.preview.foot | Setiap kesimpulan punya alasan yang bisa dibaca. | Setiap hasil disertai kutipan yang bisa kamu cek sendiri. | Every result comes with a quote you can check yourself. |
| landing.how.aria | Cara kerja JobFit | Cara kerja JobFit | How JobFit works |
| landing.how1.h | Temukan lowongan relevan | Cari lowongan yang relevan | Find relevant jobs |
| landing.how1.p | Mulai dari CV dan preferensi Anda. | Mulai dari CV dan preferensi kamu. | Start from your CV and preferences. |
| landing.how2.h | Periksa bukti Anda | Cek kecocokan dengan bukti | Check fit with evidence |
| landing.how2.p | Bandingkan persyaratan dengan kutipan CV. | Setiap syarat lowongan dibandingkan dengan kutipan dari CV kamu. | Each requirement is compared with quotes from your CV. |
| landing.how3.h | Pahami langkah berikutnya | Perkuat CV dengan jujur | Strengthen your CV honestly |
| landing.how3.p | Perjelas pengalaman, tanpa menambah klaim. | Perjelas pengalaman yang memang kamu punya, tanpa menambah klaim. | Clarify experience you really have, with no new claims. |

Catatan: kalimat "3 tahun" pada lead berasal dari data CP1 (128 dari 405 judul tanpa level ternyata meminta pengalaman 3 tahun atau lebih). Jangan ubah menjadi klaim yang lebih besar.

### 5.3 Langkah persiapan dan Unggah CV

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| steps.aria | Persiapan CV | Persiapan CV | CV setup |
| steps.1 / 2 / 3 | Unggah CV / Tinjau & setujui / CV siap | Unggah CV / Cek & setujui / CV siap | Upload CV / Review & approve / CV ready |
| upload.h1 | Mulai dari CV Anda | Mulai dari CV kamu | Start with your CV |
| upload.desc | Pilih dokumen yang ingin Anda gunakan… | Pilih file CV. Sebelum lanjut, kamu akan melihat dan menyetujui teks yang dipakai. | Choose your CV file. Before anything else, you'll see and approve the text we'll use. |
| upload.zone.h | Unggah CV | Unggah CV | Upload CV |
| upload.zone.formats | PDF, DOCX, TXT, atau MD · Maks. 10 MB | PDF, DOCX, TXT, atau MD · Maks. 10 MB | PDF, DOCX, TXT or MD · Max 10 MB |
| upload.file.label (sr) | Pilih berkas CV | Pilih file CV | Choose CV file |
| upload.notice | **Anda memegang kendali.** Pada produk live… | D: **Kamu yang pegang kendali.** Di demo ini, file dibaca langsung di browser dan tidak dikirim ke server atau layanan AI. · L: **Kamu yang pegang kendali.** File kamu disimpan sementara di server JobFit hanya untuk membaca teksnya. Data pribadi dibersihkan dulu, lalu kamu melihat dan menyetujui teksnya sebelum ada yang dikirim ke layanan AI. | D: **You stay in control.** In this demo, your file is read in your browser and isn't sent to any server or AI service. · L: **You stay in control.** Your file is held briefly on JobFit's server only to read its text. Personal details are removed first, and you see and approve the text before anything goes to an AI service. |
| upload.small | Dalam prototipe ini, ekstraksi dilakukan di browser… | D: Ingin mencoba tanpa CV sendiri? Unduh CV contoh, atau langsung pakai di sini. · L: Pembersihan otomatis punya batas. Cek lagi teksnya di langkah berikutnya. | D: Want to try without your own CV? Download the sample CV or use it directly. · L: Automatic cleanup has limits. Check the text again in the next step. |
| upload.download | Unduh contoh CV | Unduh CV contoh | Download sample CV |
| upload.demo | Coba CV demo | Pakai CV contoh | Use sample CV |
| upload.manual.summary | Gunakan teks CV | Tempel teks CV saja | Paste CV text instead |
| upload.manual.label | Teks CV profesional | Teks CV | CV text |
| upload.manual.placeholder | PROFESSIONAL EXPERIENCE↵Tuliskan pengalaman… | PENGALAMAN KERJA↵Tulis pengalaman, proyek, pendidikan, dan keterampilan kamu. | WORK EXPERIENCE↵List your experience, projects, education and skills. |
| upload.manual.hint | Alternatif untuk PDF scan… | Untuk PDF hasil scan atau file yang tidak terbaca. Teks ini juga dibersihkan dari data pribadi. | For scanned PDFs or files that can't be read. This text is also cleaned of personal details. |
| upload.manual.submit | Tinjau privasi | Lanjut ke pengecekan | Continue to review |

**Pesan error unggah**

| Kunci | ID | EN |
| --- | --- | --- |
| err.format | Format ini belum didukung. Pilih file PDF, DOCX, TXT, atau MD. | This format isn't supported. Choose a PDF, DOCX, TXT or MD file. |
| err.size | File kosong atau lebih dari 10 MB. Pilih file lain yang berisi teks CV. | The file is empty or over 10 MB. Choose another file that contains your CV. |
| err.pdfLocal (D saja) | Untuk membaca PDF, buka demo ini lewat server lokal. File TXT, MD, dan DOCX bisa langsung dicoba. | To read PDFs, open this demo through a local server. TXT, MD and DOCX work directly. |
| err.pages | PDF lebih dari 50 halaman. Pilih versi CV yang lebih ringkas. | This PDF has more than 50 pages. Choose a shorter version of your CV. |
| err.docx | Pembaca DOCX belum siap. Coba pakai file TXT dulu. | The DOCX reader isn't available. Try a TXT file instead. |
| err.tooLittle | Teks yang terbaca terlalu sedikit. Kalau ini PDF hasil scan, simpan ulang sebagai DOCX atau TXT, lalu unggah lagi. | We couldn't read enough text. If it's a scanned PDF, save it as DOCX or TXT and upload again. |
| err.unreadable | File tidak bisa dibaca. Simpan ulang sebagai TXT atau DOCX, lalu coba lagi. | We couldn't read this file. Save it as TXT or DOCX and try again. |
| err.noSection (juga scenario privacy-error) | JobFit belum menemukan bagian pengalaman, proyek, pendidikan, atau keterampilan. Tambahkan judul bagian seperti PENGALAMAN KERJA atau SKILLS, lalu coba lagi. | We couldn't find an experience, projects, education or skills section. Add a heading such as WORK EXPERIENCE or SKILLS, then try again. |
| err.tooShort | Setelah data pribadi dibersihkan, teks yang tersisa terlalu pendek. Tambahkan pengalaman, proyek, atau keterampilan kamu yang sebenarnya, lalu coba lagi. | After removing personal details, the remaining text is too short. Add your real experience, projects or skills, then try again. |

**Teks pengganti sanitizer** (mengikuti bahasa UI saat teks dibersihkan): `[email disamarkan]` / `[email hidden]` · `[telepon disamarkan]` / `[phone hidden]` · `[identitas disamarkan]` / `[ID number hidden]` · `[tautan pribadi disamarkan]` / `[personal link hidden]`.

### 5.4 Cek teks CV (privacy) dan Edit

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| privacy.h1 | Tinjau teks yang akan dianalisis | Cek teks yang akan dianalisis | Check the text we'll analyze |
| privacy.desc | Ini adalah teks persis yang akan digunakan… | Ini teks persis yang akan dipakai setelah kamu setuju. Pastikan pengalaman kerjanya tetap akurat. | This is the exact text that will be used once you agree. Make sure your work experience still reads correctly. |
| privacy.tag | Teks telah dibersihkan | Data pribadi dibersihkan | Personal details removed |
| privacy.edit | Edit teks | Edit teks | Edit text |
| privacy.notice | Pembersihan menghapus atau menyamarkan… | Nama, kontak, ringkasan profil, dan bagian pribadi yang dikenali sudah dihapus atau disamarkan. Pembersihan ini punya batas, jadi cek lagi apakah masih ada info sensitif. | Your name, contact details, profile summary and other personal sections we recognize have been removed or hidden. This cleanup has limits, so check for anything sensitive that's left. |
| privacy.what.summary | Apa yang dibersihkan? | Apa saja yang dibersihkan? | What gets removed? |
| privacy.what.body | Header identitas, email, telepon… | D: **Dihapus:** bagian identitas di atas CV, kontak, ringkasan (Summary, Profile, Objective), minat, organisasi, dan referensi. **Disamarkan:** email, nomor telepon, nomor identitas, dan tautan profil pribadi. **Tetap dipakai:** pengalaman kerja, proyek, pendidikan, keterampilan, dan tanggal. · L: sama seperti D, tetapi bagian "Disamarkan" ditambah: alamat lengkap, nama kamu yang muncul lagi di isi CV, dan nama orang setelah label seperti Supervisor atau Mentor. | D: **Removed:** the identity header, contact details, summary (Summary, Profile, Objective), interests, organizations and references. **Hidden:** emails, phone numbers, ID numbers and personal profile links. **Kept:** work experience, projects, education, skills and dates. · L: same as D, with "Hidden" also covering full addresses, your name if it appears again in the CV, and people's names after labels such as Supervisor or Mentor. |
| privacy.label | Teks CV yang disetujui | Teks yang akan dianalisis | Text to be analyzed |
| privacy.source.sample | Sumber: CV sintetis JobFit. | Sumber: CV contoh JobFit. | Source: JobFit sample CV. |
| privacy.source.user | Sumber: dokumen atau teks yang Anda pilih. | Sumber: file atau teks yang kamu pilih. | Source: the file or text you provided. |
| privacy.source.editNote | Mengedit teks akan menjalankan pembersihan kembali… | Kalau kamu mengedit teks, pembersihan dijalankan lagi dan kamu perlu menyetujuinya ulang. | If you edit the text, cleanup runs again and you'll need to approve it again. |
| privacy.consent.strong | Saya telah meninjau teks di atas dan menyetujui… | Saya sudah memeriksa teks di atas dan setuju teks ini dipakai untuk analisis. | I've checked the text above and agree to it being used for analysis. |
| privacy.consent.small | Produk live menggunakan provider AI setelah persetujuan… | D: Di demo ini, analisis disimulasikan di browser. Tidak ada yang dikirim ke layanan AI. · L: Setelah kamu setuju, teks ini dikirim ke layanan AI melalui OpenRouter dengan pengaturan tanpa penyimpanan data (zero data retention). Hasilnya hanya ada selama sesi ini. | D: In this demo, analysis is simulated in your browser. Nothing is sent to an AI service. · L: Once you agree, this text is sent to AI services through OpenRouter with zero-data-retention settings. Results exist only for this session. |
| privacy.replace | Ganti CV | Ganti CV | Replace CV |
| privacy.continue | Siapkan CV saya → | Lanjutkan → | Continue → |
| toast.needConsent | Tinjau dan setujui versi teks CV ini terlebih dahulu. | Centang persetujuan dulu untuk versi teks ini. | Tick the approval box for this version of the text first. |
| edit.h1 | Perbaiki teks CV | Edit teks CV | Edit CV text |
| edit.desc | Teks yang Anda simpan akan dibersihkan lagi… | Setelah disimpan, teks dibersihkan lagi dan kamu perlu menyetujuinya ulang. Persetujuan dan hasil sebelumnya sudah tidak berlaku. | When you save, the text is cleaned again and you'll need to approve it again. Your earlier approval and results no longer apply. |
| edit.label | Teks profesional CV | Teks CV | CV text |
| edit.back | Kembali ke pratinjau | Kembali tanpa menyimpan | Back without saving |
| edit.submit | Bersihkan & tinjau | Simpan & cek lagi | Save & review |

### 5.5 CV siap (ready)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| ready.eyebrow | Persiapan selesai | Persiapan selesai | Setup complete |
| ready.h1 | CV siap. Apa langkah Anda berikutnya? | CV kamu siap. Mau mulai dari mana? | Your CV is ready. Where do you want to start? |
| ready.desc | Pilih cara menemukan kecocokan berbasis bukti. | Pilih salah satu. Kamu bisa pindah kapan saja lewat menu di atas. | Pick one. You can switch anytime from the menu above. |
| ready.summary.title | CV profesional siap digunakan | CV siap dipakai | CV ready to use |
| ready.summary.meta | {n} baris teks · CV sintetis/CV unggahan · Parsing simulasi | D: {n} baris teks · CV contoh atau CV unggahan · Dibaca dengan simulasi · L: {n} baris teks · CV unggahan | D: {n} lines of text · Sample CV or Uploaded CV · Simulated reading · L: {n} lines of text · Uploaded CV |
| ready.review | Tinjau CV | Lihat teks CV | View CV text |
| ready.find.eyebrow | Temukan peluang | Belum punya lowongan incaran? | No job in mind yet? |
| ready.find.h2 (+ sub-label) | Find Jobs | Cari Lowongan · sub: Find Jobs | Find Jobs |
| ready.find.p | Cari lowongan dalam corpus JobFit… | D: Cari lowongan AI dan data yang relevan dengan CV dan preferensi kamu, dari kumpulan lowongan contoh. · L: Cari lowongan AI dan data di database JobFit yang relevan dengan CV dan preferensi kamu. | D: Find AI and data roles that match your CV and preferences, from the sample jobs. · L: Search JobFit's job database for AI and data roles that match your CV and preferences. |
| ready.find.btn | Cari lowongan → | Cari lowongan → | Find jobs → |
| ready.check.eyebrow | Sudah punya lowongan? | Sudah punya lowongan incaran? | Already found a job? |
| ready.check.h2 (+ sub-label) | Check a Job | Cek Lowongan · sub: Check a Job | Check a Job |
| ready.check.p | Tempel deskripsi pekerjaan untuk melihat bukti… | Tempel deskripsi lowongan dari mana saja, lalu lihat syarat mana yang sudah ada buktinya di CV kamu. | Paste a job description from anywhere and see which requirements your CV already backs up. |
| ready.check.btn | Cek lowongan | Cek lowongan | Check a job |
| ready.history.h3 | Riwayat pengalaman | Riwayat kerja | Work history |
| ready.history.desc | Opsional. Membantu membedakan informasi… | Opsional. Jawaban ini membantu JobFit membedakan pengalaman yang belum bisa dipastikan dari yang memang belum memenuhi syarat. | Optional. This helps JobFit tell apart experience it can't confirm from experience that clearly falls short. |
| history.check.strong | CV ini memuat seluruh riwayat kerja profesional saya… | CV ini memuat seluruh riwayat kerja saya. | This CV lists my complete work history. |
| history.check.small | Biarkan kosong jika ada pekerjaan lama… | Biarkan kosong kalau ada pekerjaan lama atau yang kurang relevan yang tidak kamu cantumkan. Jawaban ini hanya berlaku untuk versi CV ini. | Leave unticked if you left out older or less relevant jobs. This applies to this version of your CV only. |
| toast.history.on | Kelengkapan riwayat dikonfirmasi untuk CV ini. | Riwayat kerja dikonfirmasi lengkap untuk CV ini. | Work history confirmed as complete for this CV. |
| toast.history.off | Riwayat tidak dikonfirmasi lengkap; konflik durasi… | Riwayat kerja tidak dikonfirmasi lengkap. JobFit tidak akan menyimpulkan pengalaman kamu kurang lama. | Work history not confirmed as complete. JobFit won't conclude that your experience is too short. |
| ready.skills.summary | Ringkasan profesional dari teks Anda | Keterampilan yang terbaca dari CV kamu | Skills found in your CV |
| ready.skills.note | Ringkasan simulasi dari kata kunci; bukan profil hasil model AI. | D: Di demo ini, keterampilan dikenali lewat kata kunci, bukan oleh model AI. · L: Dibaca oleh AI dari teks yang kamu setujui. | D: In this demo, skills are detected by keywords, not by an AI model. · L: Read by AI from the text you approved. |
| ready.skills.empty | Belum ada keterampilan yang dikenali oleh simulasi. | Belum ada keterampilan yang terbaca. | No skills detected yet. |
| ready.market | Jelajahi keterampilan pasar | Lihat keterampilan yang paling dicari | See the most-requested skills |

### 5.6 Cari Lowongan (find)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| find.eyebrow | Find Jobs | Cari Lowongan · Find Jobs | Find Jobs |
| find.h1 | Temukan lowongan yang relevan | Cari lowongan yang relevan | Find relevant jobs |
| find.desc | Semua filter bersifat opsional… | Semua filter opsional. Tanpa filter, JobFit mencari di seluruh lowongan yang tersedia. | All filters are optional. Without them, JobFit searches every available job. |
| quota | {n} dari 3 analisis digunakan | Sisa {sisa} dari 3 cek kecocokan (jika 0: Jatah cek kecocokan habis) | {left} of 3 fit checks left (if 0: No fit checks left) |
| find.panel.h2 | Preferensi pencarian | Preferensi pencarian | Search preferences |
| find.panel.optional | Opsional | Opsional | Optional |
| filter.role | Role family | Bidang peran | Role family |
| filter.country | Negara | Negara | Country |
| filter.city / placeholder | Kota / Semua kota | Kota / Semua kota | City / All cities |
| filter.experience | Kebutuhan pengalaman | Pengalaman yang diminta | Experience required |
| filter.mode | Mode kerja | Mode kerja | Work mode |
| filter.posted | Diposting dalam | Tayang dalam | Posted within |
| filter.more | Opsi tambahan | Opsi lain | More options |
| filter.unknown.label | Sertakan lowongan dengan informasi yang belum tersedia | Tetap tampilkan lowongan yang datanya belum lengkap | Include jobs with missing details |
| filter.unknown.small | Jika dicentang, nilai metadata yang kosong… | Misalnya lowongan tanpa info lokasi atau tanggal tayang. Lowongan ini tidak disaring keluar hanya karena datanya kosong. | For example, jobs with no location or posting date. They won't be filtered out just because a detail is missing. |
| find.hint | Relevansi dahulu. Analisis bukti setelah Anda memilih. | Pencarian menampilkan lowongan relevan. Kecocokan dicek setelah kamu memilih satu lowongan. | Search shows relevant jobs. Fit is checked after you pick one. |
| find.submit | Cari lowongan | Cari lowongan | Find jobs |
| find.corpusNote | Corpus prototipe: {n} lowongan sintetis · Tanggal acuan 9 Oktober 2026. | D: Demo ini memakai {n} lowongan contoh · Data per 9 Oktober 2026. · L: Di versi beta, pencarian berlaku sekali per sesi. Setelah itu, kamu bebas menyaring hasilnya. · Data lowongan per {tanggal_snapshot}. | D: This demo uses {n} sample jobs · Data as of 9 October 2026. · L: In the beta, you can search once per session. After that, filter the results as much as you like. · Job data as of {snapshot_date}. |
| find.backToResults | Kembali ke hasil sebelumnya | Kembali ke hasil sebelumnya | Back to previous results |

### 5.7 Lowongan Relevan (results) dan kartu lowongan

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| results.eyebrow | Relevant Jobs | Lowongan Relevan · Relevant Jobs | Relevant Jobs |
| results.h1 | Lowongan relevan | Lowongan yang relevan dengan CV kamu | Jobs relevant to your CV |
| results.desc | Hasil ini relevan dengan CV dan filter Anda… | Diurutkan dari yang paling relevan dengan CV dan filter kamu. Relevan belum tentu cocok: pilih Cek kecocokan untuk melihat buktinya. | Sorted by relevance to your CV and filters. Relevant doesn't mean a fit yet: choose Analyze fit to see the evidence. |
| results.meta | CV aktif · Urutan relevansi dipertahankan | Urutan: paling relevan dulu | Order: most relevant first |
| results.changeSearch | Ubah filter pencarian | D: Ubah pencarian · L: lihat Bagian 6B | D: Change search · L: see Section 6B |
| refine.summary | Filter hasil ({n}) | Saring hasil ({n}) | Filter results ({n}) |
| refine.sr | Refine these results | Saring hasil ini | Refine these results |
| refine.p | Filter ini hanya mengubah lowongan yang ditampilkan… | Hanya mengubah lowongan yang ditampilkan. Tidak ada pencarian atau cek kecocokan baru. | Only changes which jobs are shown. No new search or fit check is run. |
| refine.reset | Reset filter hasil | Hapus filter | Clear filters |
| results.list.aria | Hasil pencarian | Hasil pencarian | Search results |
| results.h2 | Hasil pencarian | Hasil pencarian | Search results |
| results.count | Menampilkan {x} dari {y} lowongan relevan | Menampilkan {x} dari {y} lowongan | Showing {x} of {y} jobs |
| results.emptyFiltered.h | Tidak ada hasil dengan filter ini | Tidak ada lowongan yang cocok dengan filter ini | No jobs match these filters |
| results.emptyFiltered.p | Hasil pencarian tetap tersimpan… | Hasil pencarian kamu masih tersimpan. Hapus filter untuk melihatnya lagi. | Your search results are still here. Clear the filters to see them again. |
| results.emptySearch.h | Belum ada lowongan yang ditemukan | Belum ada lowongan yang ditemukan | No jobs found |
| results.emptySearch.p | Coba perluas lokasi, pengalaman… | D: Coba longgarkan lokasi, pengalaman, atau waktu tayang. CV kamu tetap siap dipakai. · L: lihat Bagian 6B | D: Try widening the location, experience or posting date. Your CV is still ready. · L: see Section 6B |
| results.emptySearch.btn | Ubah filter pencarian | D: Ubah pencarian | D: Change search |
| results.foot | Lowongan sintetis untuk demonstrasi · Tidak ada skor fit… | D: Lowongan contoh untuk demo · Hasil pencarian belum diberi skor kecocokan. · L: Hasil pencarian belum diberi skor. Skor hanya muncul setelah kamu cek kecocokan. | D: Sample jobs for this demo · Search results have no fit score. · L: Search results have no score. A score appears only after you analyze fit. |
| job.location.none | Lokasi belum tersedia | Lokasi tidak dicantumkan | Location not listed |
| job.mode.none | Mode kerja belum tersedia | Mode kerja tidak dicantumkan | Work mode not listed |
| job.experience | {x} pengalaman | Pengalaman {x} | {x} experience |
| job.experience.none | Pengalaman belum tersedia | Pengalaman tidak dicantumkan | Experience not listed |
| job.role.none | Role belum tersedia | Bidang tidak dicantumkan | Role not listed |
| job.date | Diposting {n} hari sebelum 9 Okt 2026 | D: Tayang {n} hari sebelum 9 Okt 2026 · L: Tayang {n} hari lalu | D: Posted {n} days before 9 Oct 2026 · L: Posted {n} days ago |
| job.date.none | Tanggal belum tersedia | Tanggal tidak dicantumkan | Date not listed |
| job.analyze | Analyze Fit → | Cek kecocokan → | Analyze fit → |
| job.viewResult | Lihat analisis → | Lihat hasil cek → | View fit result → |
| job.cachedNote | Analisis tersedia | Sudah dicek | Already checked |
| job.apply | Apply / sumber ↗ | Lihat lowongan asli ↗ | View original posting ↗ |

### 5.8 Cek Lowongan (check)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| check.eyebrow | Check a Job | Cek Lowongan · Check a Job | Check a Job |
| check.h1 | Cek lowongan yang Anda temukan | Cek lowongan yang kamu temukan | Check a job you found |
| check.desc | Tempel deskripsi lengkap agar… | Tempel deskripsi lowongan lengkap, termasuk bagian syaratnya, supaya bisa dibandingkan dengan bukti di CV kamu. | Paste the full job description, including the requirements, so it can be compared with the evidence in your CV. |
| check.label | Deskripsi pekerjaan (wajib) | Deskripsi lowongan (wajib) | Job description (required) |
| check.hint | JD hanya dipakai dalam sesi ini… | Deskripsi ini hanya dipakai di sesi ini dan tidak ditambahkan ke database lowongan JobFit. | Used in this session only. It's never added to JobFit's job database. |
| check.error | Tambahkan deskripsi lengkap, minimal 60 karakter… | Deskripsinya terlalu pendek. Tempel minimal 60 karakter, termasuk syarat pekerjaannya. | That's too short. Paste at least 60 characters, including the job requirements. |
| check.sample | Isi contoh JD | Pakai contoh deskripsi | Use a sample description |
| check.submit | Analyze Fit → | Cek kecocokan → | Analyze fit → |
| check.foot | Analisis pada prototipe memakai aturan lokal terbatas… | D: Di demo ini, syarat dikenali dengan aturan sederhana. Kalau syaratnya tidak terbaca jelas, JobFit menahan hasilnya dan tidak memberi skor asal. · L: Kalau syarat lowongan tidak terbaca jelas, JobFit menahan hasilnya dan tidak memberi skor asal. | D: In this demo, requirements are detected with simple rules. If they can't be read clearly, JobFit holds the result instead of guessing a score. · L: If the requirements can't be read clearly, JobFit holds the result instead of guessing a score. |
| pasted.company | JD Anda · sesi ini | Deskripsi dari kamu · sesi ini | Your job description · this session |
| pasted.titleFallback | Lowongan yang Anda tempel | Lowongan yang kamu tempel | Job you pasted |

### 5.9 Hasil Cek Kecocokan (analysis)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| analysis.back.check | Kembali ke JD | Kembali ke deskripsi | Back to description |
| analysis.back.results | Kembali ke hasil | Kembali ke hasil | Back to results |
| analysis.eyebrow | Hasil Analyze Fit | Hasil Cek Kecocokan · Analyze Fit | Fit result |
| analysis.apply | Apply / sumber ↗ | Lihat lowongan asli ↗ | View original posting ↗ |
| coverage.aria / label | Cakupan bukti CV | Cakupan bukti CV | CV evidence coverage |
| coverage.h2 | CV Evidence Coverage | Cakupan Bukti CV (sub-label tidak perlu; label sudah ada di bawah angka) | CV Evidence Coverage |
| coverage.disclaimer | Mengukur cakupan bukti CV — bukan probabilitas diterima kerja. | Mengukur seberapa banyak syarat wajib yang ada buktinya di CV kamu. Bukan peluang diterima kerja. | Measures how many required items your CV has evidence for. It's not your chance of getting hired. |
| coverage.counts | {a} didukung · {b} sebagian · {c} belum ada bukti | {a} ada bukti · {b} bukti sebagian · {c} belum ada bukti | {a} with evidence · {b} partial · {c} no evidence yet |
| coverage.basis | Simulasi lokal atas {n} persyaratan wajib yang dikenali. | D: Simulasi dari {n} syarat wajib yang terbaca. · L: Dihitung dari {n} syarat wajib di lowongan ini. | D: Simulated from {n} required items detected. · L: Based on {n} required items in this job. |
| req.h2 | Bukti per persyaratan | Bukti untuk setiap syarat | Evidence for each requirement |
| req.meta | Kutipan dari versi CV aktif | Kutipan dari CV yang kamu setujui | Quotes from the CV you approved |
| req.required | Persyaratan wajib | Syarat wajib | Required |
| req.preferred | Preferensi · di luar skor | Nilai tambah · tidak dihitung di skor | Nice to have · not scored |
| req.quoteLabel | Bukti persis dari CV Anda | Kutipan dari CV kamu | Quoted from your CV |
| reason.match | Kutipan memuat tindakan dan konteks… | Kutipan ini menunjukkan apa yang kamu kerjakan dan konteksnya, sesuai dengan syarat ini. | This quote shows what you did and in what context, matching this requirement. |
| reason.partial.rag | Prototipe retrieval menunjukkan pengalaman terkait… | Ada pengalaman retrieval di proyek prototipe, tapi belum terlihat evaluasi RAG di lingkungan produksi. | There's retrieval experience in a prototype project, but no sign yet of evaluating RAG in production. |
| reason.partial | Ada informasi yang relevan, tetapi konteks… | Ada informasi yang terkait, tapi konteks atau kontribusi kamu belum cukup jelas. | There's related information, but your context or contribution isn't clear enough yet. |
| reason.partial.aws | Ada pengalaman cloud, tetapi platform AWS belum disebutkan… | Ada pengalaman cloud, tapi AWS tidak disebut. Cloud belum tentu AWS. | There's cloud experience, but AWS isn't mentioned. Cloud doesn't automatically mean AWS. |
| reason.none | JobFit belum menemukan bukti pendukung… | JobFit belum menemukan buktinya di CV ini. Bukan berarti kamu tidak punya keterampilan ini. | JobFit didn't find evidence of this in your CV. That doesn't mean you lack the skill. |
| exp.h3 | Kebutuhan durasi pengalaman | Pengalaman yang diminta | Experience required |
| exp.asks | Lowongan meminta / {x}+ tahun | Lowongan meminta / {x}+ tahun | The job asks for / {x}+ years |
| exp.confirmed | Riwayat CV terkonfirmasi / 1,4 tahun | Terkonfirmasi di CV kamu / 1,4 tahun | Confirmed in your CV / 1.4 years |
| exp.conflict | Ini kendala latar belakang, bukan masalah penulisan… | Ini soal latar belakang, bukan cara menulis. Mengubah kalimat di CV tidak menambah lama pengalaman. | This is about your background, not your wording. Rewriting your CV can't add years of experience. |
| exp.met | Riwayat CV memenuhi kebutuhan durasi pada contoh ini. | Riwayat di CV kamu memenuhi durasi yang diminta. | Your CV history meets the required duration. |
| exp.sampleDates (D saja) | Durasi contoh: Januari 2025–Mei 2026. | Durasi contoh: Januari 2025–Mei 2026. | Sample duration: January 2025–May 2026. |
| exp.unverified | Durasi pengalaman belum terverifikasi dari CV ini… | Lama pengalaman belum bisa dipastikan dari CV ini, karena riwayat kerja belum dikonfirmasi lengkap atau tanggalnya kurang jelas. | Your experience length can't be confirmed from this CV, because your work history isn't confirmed as complete or the dates are unclear. |
| exp.reviewBtn | Tinjau riwayat CV | Konfirmasi riwayat kerja | Confirm work history |
| exp.coachNote | Tidak ada tindakan rewrite untuk kendala ini. | Tidak ada saran penulisan untuk hal ini. | No rewriting advice applies here. |
| calc.summary | Bagaimana cakupan ini dihitung? | Bagaimana skor ini dihitung? | How is this score calculated? |
| calc.body | Setiap persyaratan wajib yang didukung bernilai 1… | Setiap syarat wajib yang ada buktinya bernilai 1, dan bukti sebagian bernilai 0,5. Totalnya dibagi {n} syarat wajib. Nilai tambah dan hal yang belum bisa dipastikan tidak dihitung. | Each required item with evidence counts as 1, and partial evidence as 0.5. The total is divided by {n} required items. Nice-to-haves and items that can't be confirmed aren't counted. |
| calc.note | Formula mengikuti model cakupan requirement JobFit… | D: Rumusnya sama dengan JobFit versi penuh. Di demo ini, syarat dan bukti dikenali dengan aturan contoh, bukan model AI. · L: Syarat dibaca dan dicocokkan oleh model AI, lalu setiap kutipan dicek ulang agar persis sama dengan teks CV kamu. | D: The formula matches the full JobFit. In this demo, requirements and evidence are detected with sample rules, not an AI model. · L: Requirements are read and matched by an AI model, and every quote is re-checked to match your CV text exactly. |
| side.strong.h3 | Bukti kuat | Sudah ada buktinya | Already backed up |
| side.strong.empty | Belum ada bukti kuat pada persyaratan yang dikenali. | Belum ada syarat dengan bukti yang kuat. | No requirements with strong evidence yet. |
| side.gaps.h3 | Bukti yang perlu diperjelas | Perlu diperjelas atau dilengkapi | Needs clarifying or adding |
| side.gaps.empty | Semua persyaratan wajib yang dikenali didukung. | Semua syarat wajib sudah ada buktinya. | Every required item has evidence. |
| side.gaps.note | Gap bukti belum tentu gap kemampuan. | Belum ada bukti belum tentu belum mampu. | Missing evidence isn't missing ability. |
| side.next.h3 | Langkah berikutnya | Langkah berikutnya | Next step |
| side.next.p | Perjelas pengalaman yang benar-benar Anda miliki. | Perjelas pengalaman yang memang kamu punya. | Clarify experience you really have. |
| side.next.btn | Perbaiki CV untuk job ini | Perkuat CV untuk lowongan ini | Improve my CV for this job |
| side.next.sub | Improve My CV for This Job | (sub-label) Improve My CV for This Job | (dihapus di EN) |
| analysis.empty.h | Pilih lowongan terlebih dahulu | Pilih lowongan dulu | Pick a job first |
| analysis.empty.p | Analisis bukti dimulai dari lowongan yang Anda pilih. | Cek kecocokan dimulai dari lowongan yang kamu pilih. | Fit checks start from a job you choose. |
| analysis.empty.btn | Cari lowongan | Cari lowongan | Find jobs |

### 5.10 Perkuat CV (coach)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| coach.back | Kembali ke analisis | Kembali ke hasil cek | Back to fit result |
| coach.eyebrow | Improve My CV for This Job | Perkuat CV · Improve My CV for This Job | Improve My CV |
| coach.h1 | Perjelas bukti. Tetap jujur. | Perjelas bukti. Tetap jujur. | Clarify the evidence. Stay honest. |
| coach.desc | Perbaiki CV untuk {job}. Saran tidak mengubah CV sumber… | Saran untuk {job}. Saran ini tidak mengubah CV asli atau skor kamu. | Suggestions for {job}. They don't change your original CV or your score. |
| coach.partial.h2 | Perbaiki penyajian bukti | Perjelas bukti yang sudah ada | Clarify evidence you already have |
| coach.partial.tag | Sebagian didukung | Bukti sebagian | Partial evidence |
| coach.item.asks | Lowongan ini meminta | Lowongan ini meminta | This job asks for |
| coach.item.current | Bukti CV saat ini | Bukti di CV kamu saat ini | Current evidence in your CV |
| coach.item.aws | Jika akurat, sebutkan platform cloud… | Kalau memang begitu, sebutkan platform cloud yang benar-benar kamu pakai. Jangan ganti "cloud" menjadi "AWS" kalau kamu tidak memakainya. | If accurate, name the cloud platform you actually used. Don't change "cloud" to "AWS" unless you used it. |
| coach.item.generic | Jika akurat, jelaskan apa yang Anda kerjakan… | Kalau memang begitu, jelaskan apa yang kamu kerjakan, alat atau metode yang dipakai, dan hasilnya. Pengalaman di prototipe belum tentu sama dengan pengalaman produksi. | If accurate, explain what you did, the tools or methods you used, and the result. Prototype experience isn't the same as production experience. |
| coach.item.add | Tambahkan fakta pendukung | Tambahkan fakta pendukung | Add supporting facts |
| coach.item.addNote | Isi hanya pengalaman yang benar-benar dilakukan. | Isi hanya dengan pengalaman yang benar-benar kamu lakukan. | Only include things you actually did. |
| coach.partial.empty | Tidak ada bukti parsial yang perlu diperjelas… | Tidak ada bukti sebagian yang perlu diperjelas. | No partial evidence to clarify. |
| coach.missing.h2 | Mungkin belum tertulis di CV | Mungkin belum tertulis di CV | Possibly missing from your CV |
| coach.missing.p | Belum ada bukti bukan berarti belum pernah… | Belum ada bukti bukan berarti belum pernah. Jawab dengan jujur dulu. | No evidence doesn't mean you've never done it. Answer honestly first. |
| coach.missing.q | Apakah Anda benar-benar pernah melakukan ini? | Apakah kamu pernah melakukan ini? | Have you actually done this? |
| coach.missing.empty | Tidak ada persyaratan wajib tanpa bukti… | Tidak ada syarat wajib yang belum ada buktinya. | No required items without evidence. |
| coach.yes / no | Ya, pernah / Belum pernah | Ya, pernah / Belum pernah | Yes, I have / Not yet |
| coach.no.notice | Tidak perlu menambahkan klaim ini ke CV… | Tidak apa-apa. Jangan tambahkan klaim ini ke CV. Kalau ingin menutup gap ini, cari proyek atau pengalaman yang relevan, lalu catat kontribusi yang benar-benar kamu lakukan. | That's fine. Don't add this to your CV. If you want to close this gap, look for a relevant project or experience and note what you actually did. |
| coach.changeAnswer | Ubah jawaban | Ubah jawaban | Change answer |
| coach.form.intro | Empat fakta berikut wajib diisi. Metrik opsional. | Isi empat pertanyaan wajib ini. Angka boleh dikosongkan. | Answer these four required questions. The number is optional. |
| coach.q.where / hint | Di mana Anda melakukannya? / Konteks proyek/pekerjaan dan waktu. | Di mana dan kapan kamu melakukannya? / Nama proyek atau pekerjaan, dan waktunya. | Where and when did you do it? / The project or job, and when. |
| coach.q.action / hint | Apa kontribusi pribadi Anda? / Tindakan yang benar-benar Anda lakukan. | Bagian mana yang kamu kerjakan sendiri? / Tulis yang benar-benar kamu lakukan, bukan kerja tim secara umum. | Which part did you do yourself? / What you personally did, not the team overall. |
| coach.q.tool / hint | Tool atau metode apa yang digunakan? / Tuliskan nama yang tepat. Jangan menebak. | Alat atau metode apa yang kamu pakai? / Tulis nama yang tepat. Jangan menebak. | Which tools or methods did you use? / Use the exact names. Don't guess. |
| coach.q.outcome / hint | Apa hasilnya? / Hasil faktual; tidak harus berupa angka. | Apa hasilnya? / Hasil yang nyata. Tidak harus berupa angka. | What was the result? / A real outcome. It doesn't have to be a number. |
| coach.q.metric / placeholder | Metrik yang dapat dipertanggungjawabkan / Opsional | Angka yang bisa kamu pertanggungjawabkan / Opsional | A number you can back up / Optional |
| coach.field.error | Isi fakta yang benar untuk melanjutkan. | Isi dengan jawaban yang benar untuk lanjut. | Add a true answer to continue. |
| coach.form.error | Lengkapi konteks, kontribusi, tool/metode, hasil. | Lengkapi dulu: {daftar}. (konteks, kontribusi, alat atau metode, hasil) | Please complete: {list}. (context, contribution, tools or methods, result) |
| coach.submit | Susun draft dari jawaban | Susun draf dari jawaban | Draft from my answers |
| coach.resetYesNo | Ubah jawaban pernah/belum | Ganti jawaban Ya atau Belum | Change my Yes or Not yet answer |
| draft.h4 | Draft dari fakta Anda | Draf dari jawaban kamu | Draft from your answers |
| draft.note | Periksa kembali kebenarannya… | Cek lagi kebenarannya sebelum dimasukkan ke CV. JobFit tidak menambahkan alat, angka, atau pengalaman apa pun. | Double-check it's true before adding it to your CV. JobFit doesn't add any tools, numbers or experience. |
| draft.template | • {action}↵Konteks: {where}. Tool/metode: {tool}.↵Hasil: {outcome} Metrik: {metric} | • {action}↵Konteks: {where}. Alat atau metode: {tool}.↵Hasil: {outcome} Angka: {metric} | • {action}↵Context: {where}. Tools or methods: {tool}.↵Result: {outcome} Number: {metric} |
| draft.editLabel / save | Edit draft / Simpan edit | Edit draf / Simpan | Edit draft / Save |
| draft.actions | Terima / Edit / Tolak / Salin | Terima / Edit / Tolak / Salin | Accept / Edit / Reject / Copy |
| draft.status | Diterima / Ditolak / Diedit oleh Anda / Perlu ditinjau | Diterima / Ditolak / Kamu edit / Perlu dicek | Accepted / Rejected / Edited by you / Needs review |
| draft.facts | Fakta yang digunakan | Jawaban yang dipakai | Answers used |
| draft.factLabels | Konteks / Kontribusi / Tool/metode / Hasil / Metrik | Konteks / Kontribusi / Alat atau metode / Hasil / Angka | Context / Contribution / Tools or methods / Result / Number |
| dialog.accept.title | Sudah memeriksa kebenaran draft? | Sudah cek kebenarannya? | Have you checked it's accurate? |
| dialog.accept.body | Pastikan setiap detail benar… | Pastikan setiap detail benar dan bisa kamu jelaskan saat wawancara. Draf hanya disimpan di sesi ini. CV asli dan skor tidak berubah. | Make sure every detail is true and something you can explain in an interview. The draft is kept in this session only. Your original CV and score don't change. |
| dialog.accept.yes / no | Ya, simpan draft / Tinjau lagi | Ya, simpan draf / Cek lagi | Yes, save draft / Review again |
| toast.accepted | Draft diterima di sesi ini. CV sumber belum diubah. | Draf disimpan di sesi ini. CV asli kamu belum berubah. | Draft saved in this session. Your original CV hasn't changed. |
| toast.rejected | Draft ditolak. Jawaban faktual tetap tersedia… | Draf ditolak. Jawaban kamu masih ada kalau ingin diperbaiki. | Draft rejected. Your answers are still here if you want to revise them. |
| toast.copied | Draft disalin. Periksa kembali… | Draf disalin. Cek lagi sebelum dimasukkan ke CV. | Draft copied. Check it again before adding it to your CV. |
| dialog.copy.title / label | Salin draft / Pilih teks dan salin | Salin draf / Pilih teks, lalu salin | Copy draft / Select the text, then copy it |
| coach.location.h3 | Lokasi dan izin kerja | Lokasi dan izin kerja | Location and work permit |
| coach.location.p | Informasi ini belum diverifikasi dari CV… | Hal ini belum bisa dipastikan dari CV. JobFit tidak menganggapnya sebagai gap dan tidak menyarankan klaim baru. | This can't be confirmed from your CV. JobFit doesn't treat it as a gap or suggest any new claim. |

### 5.11 Keterampilan yang paling dicari (market)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| market.back | Kembali ke CV siap | Kembali ke CV siap | Back to CV ready |
| market.eyebrow | Eksplorasi sekunder | Wawasan tambahan | Extra insight |
| market.h1 | Keterampilan dalam corpus contoh | Keterampilan yang paling sering diminta | Most-requested skills |
| market.desc | Frekuensi penyebutan pada 10 lowongan sintetis… | D: Dihitung dari {n} lowongan contoh di demo ini. Bukan gambaran seluruh pasar kerja. · L: Dihitung dari lowongan di database JobFit per {tanggal_snapshot}. Bukan gambaran seluruh pasar kerja. | D: Counted from the {n} sample jobs in this demo. Not a picture of the whole job market. · L: Counted from jobs in JobFit's database as of {snapshot_date}. Not a picture of the whole job market. |
| market.row | {n} / 10 | {n} dari {total} lowongan | {n} of {total} jobs |

### 5.12 Proses (processing)

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| proc.defaultTitle | Memproses… | Sedang diproses… | Working on it… |
| proc.sub.local | Berkas diproses sementara di browser ini. | File dibaca sementara di browser ini. | Your file is read temporarily in this browser. |
| proc.sub | Simulasi lokal · tidak ada panggilan ke provider AI. | D: Simulasi di browser · tidak ada yang dikirim ke layanan AI. · L: Jangan tutup halaman ini. Prosesnya bisa memakan waktu hingga beberapa menit. | D: Simulated in your browser · nothing is sent to an AI service. · L: Keep this page open. This can take up to a few minutes. |
| proc.firstStage | Menyiapkan proses | Memulai | Getting started |
| proc.elapsed.start | Sedang bekerja… | Baru dimulai… | Just started… |
| proc.elapsed | Aktif selama {n} detik | Berjalan {n} detik | Running for {n} s |
| proc.cancel | Batalkan | Batalkan | Cancel |
| toast.cancelled | Proses dibatalkan. Anda dapat melanjutkan kembali. | D: Proses dibatalkan. Kamu bisa mulai lagi kapan saja. · L: Proses dihentikan di layar ini. Permintaan yang sudah terkirim tetap diselesaikan di server. | D: Cancelled. You can start again anytime. · L: Stopped on this screen. A request already sent will still finish on the server. |

**Judul dan tahap tiap proses** (hanya tahap yang nyata, tanpa persentase):

| Proses | ID | EN |
| --- | --- | --- |
| Membaca file | **Membaca CV kamu** · Mengambil teks dari file | **Reading your CV** · Extracting text from the file |
| Pembersihan | **Membersihkan data pribadi** · Mencari bagian pengalaman, proyek, dan pendidikan · Menyamarkan data pribadi · Menyiapkan teks untuk kamu cek | **Removing personal details** · Finding experience, projects and education · Hiding personal details · Preparing the text for your review |
| Membaca CV (parse) | **Menyiapkan CV kamu** · Memeriksa teks yang kamu setujui · Membaca pengalaman dan keterampilan · Menyiapkan profil pencarian | **Preparing your CV** · Checking the text you approved · Reading experience and skills · Preparing your search profile |
| Pencarian | **Mencari lowongan yang relevan…** · Memahami isi CV kamu · D: Menelusuri lowongan contoh / L: Menelusuri database lowongan · Mengurutkan dari yang paling relevan | **Finding relevant jobs…** · Understanding your CV · D: Searching sample jobs / L: Searching the job database · Sorting by relevance |
| Cek kecocokan | **Mengecek kecocokan dengan lowongan ini…** · Membaca syarat lowongan · Mencocokkan dan memeriksa ulang bukti di CV kamu · Menyusun yang sudah kuat dan yang perlu diperjelas | **Checking your fit for this job…** · Reading the job requirements · Matching and re-checking evidence in your CV · Summarizing strengths and gaps |

### 5.13 Error, batas, dan dialog

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| error.default.h1 / p | Proses belum dapat dilanjutkan / Kembali dan coba lagi. | Proses belum bisa dilanjutkan / Kembali, lalu coba lagi. | We couldn't continue / Go back and try again. |
| error.default.detail | CV dan persetujuan yang masih valid tetap tersedia. | CV dan persetujuan kamu yang masih berlaku tetap aman. | Your CV and any valid approval are still here. |
| error.retry / back | Coba lagi / Kembali | Coba lagi / Kembali | Try again / Back |
| error.parse.h1 | CV belum berhasil disiapkan | CV belum berhasil disiapkan | We couldn't prepare your CV |
| error.parse.p | Proses parsing terhenti. Teks yang Anda setujui… | Prosesnya terhenti. Teks yang kamu setujui masih tersimpan di sesi ini. | The process stopped. The text you approved is still saved in this session. |
| error.parse.detail | Coba lagi atau periksa teks… | Coba lagi, atau cek apakah bagian pengalaman dan keterampilan terbaca dengan benar. | Try again, or check that your experience and skills sections read correctly. |
| error.search.h1 | Layanan pencarian sementara tidak tersedia | Pencarian sedang tidak tersedia | Search is unavailable right now |
| error.search.p | Permintaan belum menghasilkan lowongan. CV Anda tetap siap… | Belum ada lowongan yang dimuat. CV kamu tetap siap dipakai. | No jobs were loaded. Your CV is still ready. |
| error.search.detail | Coba lagi beberapa saat. Tidak ada analisis yang terpakai. | Coba lagi sebentar lagi. Jatah cek kecocokan kamu tidak berkurang. | Try again shortly. Your fit checks haven't been used. |
| error.hold.h1 | Analisis ditahan — bukti belum siap dinilai | Hasil ditahan: syarat lowongan belum jelas | Result on hold: requirements unclear |
| error.hold.p | Persyaratan wajib belum dapat dikenali… | JobFit belum bisa mengenali syarat wajib dengan cukup jelas, jadi tidak ada skor yang ditampilkan. | JobFit couldn't identify the required items clearly enough, so no score is shown. |
| error.hold.detail | Tempel JD yang memuat tanggung jawab… Analisis ini tidak memakai kuota. | D: Tempel deskripsi yang memuat tanggung jawab dan syarat secara jelas. Hasil ini tidak memakai jatah cek kecocokan. · L: Tempel deskripsi yang memuat tanggung jawab dan syarat secara jelas. **[KONFIRMASI ke backend sebelum menambah kalimat soal jatah]** | D: Paste a description with clear responsibilities and requirements. This didn't use a fit check. · L: Paste a description with clear responsibilities and requirements. **[CONFIRM with backend before adding any quota sentence]** |
| error.hold.btn | Perbaiki JD | Perbaiki deskripsi | Fix description |
| error.provider.h1 | Provider sementara tidak tersedia | Layanan AI sedang tidak tersedia | The AI service is unavailable right now |
| error.provider.p | Analisis belum selesai. Tidak ada skor yang dibuat dan kuota Anda belum berkurang. | D: Cek kecocokan belum selesai. Tidak ada skor yang dibuat dan jatah kamu belum berkurang. · L: Analisis AI sedang tidak tersedia. Silakan coba lagi nanti. Tidak ada skor yang dibuat. **[KONFIRMASI soal jatah]** | D: The fit check didn't finish. No score was created and your fit checks haven't been used. · L: Live AI analysis is temporarily unavailable. Please try again later. No score was created. **[CONFIRM quota]** |
| error.provider.detail | CV dan lowongan tetap tersedia. Coba lagi beberapa saat. | D: CV dan lowongan kamu masih ada. Coba lagi sebentar lagi. · L: CV dan lowongan kamu masih ada. Sementara itu, kamu bisa mencoba demo dengan CV contoh. | D: Your CV and the job are still here. Try again shortly. · L: Your CV and the job are still here. Meanwhile, you can try the demo with a sample CV. |
| limit.title | Batas analisis sesi tercapai | Jatah cek kecocokan habis | You've used all fit checks |
| limit.body | Anda telah menggunakan 3 analisis… | Kamu sudah memakai 3 cek kecocokan di sesi ini. Hasil yang sudah ada tetap bisa dibuka. | You've used 3 fit checks in this session. You can still open your existing results. |
| limit.small | Batas beta ini menjaga biaya… | D: Batas ini menjaga biaya layanan beta tetap terkendali. Di demo ini tidak ada pembayaran atau upgrade. · L: Batas ini menjaga biaya layanan beta tetap terkendali. Kamu bisa mencoba lagi setelah 24 jam. | D: This limit keeps beta costs under control. There's no payment or upgrade in this demo. · L: This limit keeps beta costs under control. You can try again after 24 hours. |
| dialog.review.title | CV actif | Teks CV yang dipakai | CV text in use |
| dialog.review.body | Teks persis dari versi yang disetujui… | Ini teks persis yang kamu setujui. Kalau kamu mengeditnya, persetujuan dan hasil yang terkait akan dihapus. | This is the exact text you approved. Editing it clears your approval and related results. |
| dialog.review.btns | Edit teks / Tutup | Edit teks / Tutup | Edit text / Close |
| dialog.replace.title | Ganti CV saat ini? | Ganti CV ini? | Replace this CV? |
| dialog.replace.body | Persetujuan, ringkasan, hasil… Hitungan analisis sesi tetap berlaku. | Persetujuan, hasil, jawaban riwayat kerja, dan draf untuk CV ini akan dihapus. Jatah cek kecocokan yang sudah terpakai tetap terhitung. | Your approval, results, work-history answer and drafts for this CV will be deleted. Fit checks you've already used still count. |
| dialog.replace.btns | Ganti CV / Batal | Ganti CV / Batal | Replace CV / Cancel |
| dialog.apply.pasted.title / body | Deskripsi yang Anda tempel / JD ini hanya tersedia dalam sesi… | Deskripsi yang kamu tempel / Deskripsi ini hanya ada di sesi ini. Untuk melamar, buka situs asal lowongannya. | The description you pasted / This description exists only in this session. To apply, go to the site where you found it. |
| dialog.apply.corpus.title / body | Lowongan sintetis / Perusahaan dan lowongan ini dibuat untuk demonstrasi… | D: Lowongan contoh / Perusahaan dan lowongan ini dibuat untuk demo. Tidak ada tautan lamaran. · L: Lowongan asli / Kamu akan membuka situs lowongan aslinya di tab baru. JobFit tidak mengirim lamaran atau CV kamu. Tombol: Buka lowongan | D: Sample job / This company and job were made up for the demo. There's no application link. · L: Original posting / You'll open the original job posting in a new tab. JobFit doesn't send your application or CV. Button: Open posting |
| dialog.help.title | Bukti, bukan tebakan | Cara membaca hasil JobFit | How to read JobFit results |
| dialog.help.p1 | **Find Jobs** mencari relevansi. **Analyze Fit** memeriksa bukti… | **Cari Lowongan** (Find Jobs) menampilkan lowongan yang relevan dengan CV kamu. **Cek Kecocokan** (Analyze Fit) membandingkan setiap syarat lowongan dengan kutipan dari CV kamu. | **Find Jobs** shows jobs relevant to your CV. **Analyze Fit** compares each requirement with quotes from your CV. |
| dialog.help.p2 | **CV Evidence Coverage** adalah cakupan bukti… | **Cakupan Bukti CV** (CV Evidence Coverage) menunjukkan seberapa banyak syarat wajib yang ada buktinya. Ini bukan peluang diterima kerja dan bukan skor ATS. | **CV Evidence Coverage** shows how many required items have evidence. It's not your chance of getting hired, and it's not an ATS score. |
| dialog.help.p3 | Belum ada bukti di CV tidak berarti… | Belum ada bukti di CV bukan berarti kamu tidak punya keterampilannya. Hal yang belum bisa dipastikan ditandai **Belum bisa dipastikan**. | Missing evidence doesn't mean you lack the skill. Anything JobFit can't confirm is marked **Can't confirm yet**. |
| dialog.help.small | Prototipe lokal: lowongan sintetis… | D: Ini demo. Lowongan dan perusahaannya contoh, pencarian dan analisis disimulasikan, dan tidak ada layanan AI yang dipakai. File dan semua isian kamu tetap di browser ini. · L: Beta terbatas: 1 pencarian dan 3 cek kecocokan per sesi. File kamu diproses sementara di server, dibersihkan dari data pribadi, dan baru dikirim ke layanan AI melalui OpenRouter setelah kamu setuju. Hasil hanya disimpan selama sesi berjalan. | D: This is a demo. The jobs and companies are samples, search and analysis are simulated, and no AI service is used. Your file and everything you enter stay in this browser. · L: Limited beta: 1 search and 3 fit checks per session. Your file is processed briefly on the server, cleaned of personal details, and sent to AI services through OpenRouter only after you agree. Results are kept only while your session lasts. |
| dialog.delete.title | Hentikan & hapus sesi? | Hentikan & hapus sesi? | Stop & delete this session? |
| dialog.delete.body | Teks CV, persetujuan, hasil analisis, JD, dan draft… | Teks CV, persetujuan, hasil cek, deskripsi lowongan, dan draf di sesi ini akan dihapus. Proses yang sedang berjalan juga dihentikan. | Your CV text, approval, fit results, job descriptions and drafts in this session will be deleted. Anything running will stop. |
| dialog.delete.small | Tindakan ini tidak dapat dibatalkan… | Tindakan ini tidak bisa dibatalkan. File asli di perangkat kamu tidak ikut terhapus. | This can't be undone. The original file on your device isn't affected. |
| dialog.delete.btns | Hapus sesi / Batal | Hapus sesi / Batal | Delete session / Cancel |

### 5.14 Sesi dihapus dan sesi berakhir

| Kunci | Lama | ID | EN |
| --- | --- | --- | --- |
| deleted.h1 | Sesi telah dihapus | Sesi sudah dihapus | Session deleted |
| deleted.desc | Teks CV, hasil, JD, dan draft di memori prototipe… | D: Teks CV, hasil, deskripsi lowongan, dan draf sudah dihapus dari memori demo ini. Tidak ada data sesi yang disimpan di browser. · L: Server JobFit sudah mengonfirmasi bahwa teks CV, hasil, deskripsi lowongan, dan draf kamu dihapus. (Tampilkan hanya setelah konfirmasi server diterima.) | D: Your CV text, results, job descriptions and drafts have been cleared from this demo's memory. No session data is stored in your browser. · L: JobFit's server has confirmed that your CV text, results, job descriptions and drafts are deleted. (Show only after the server confirms.) |
| expired.h1 | Sesi Anda sudah berakhir | Sesi kamu sudah berakhir | Your session has ended |
| expired.desc | Mulai sesi baru untuk menggunakan JobFit kembali. | D: Mulai sesi baru untuk memakai JobFit lagi. · L: Sesi berakhir karena tidak ada aktivitas, dan datanya sudah dihapus. Mulai sesi baru untuk memakai JobFit lagi. | D: Start a new session to use JobFit again. · L: Your session ended after a period of inactivity, and its data was deleted. Start a new session to use JobFit again. |
| terminal.h2 | Anda tetap memegang kendali. | Kendali tetap di tangan kamu. | You're still in control. |
| terminal.p.expired | Sesi sementara tidak dipulihkan otomatis… | Sesi lama tidak dipulihkan otomatis. Unggah CV lagi dan setujui ulang teksnya. | Old sessions aren't restored. Upload your CV again and re-approve the text. |
| terminal.p.deleted | Pada produk live, konfirmasi penghapusan harus berasal dari server… | D: Di demo ini, yang dihapus adalah data di browser. Di versi beta, penghapusan dikonfirmasi oleh server. · L: Kamu bisa mulai lagi kapan saja dengan CV yang sama atau CV baru. | D: In this demo, only data in your browser is cleared. In the beta, deletion is confirmed by the server. · L: You can start again anytime with the same CV or a new one. |
| terminal.btn | Kembali ke awal | Kembali ke beranda | Back to home |

---

## 6. Opsional: penyelarasan dengan keputusan produk D-105 dan D-103

Bagian ini mengubah sedikit **perilaku**, bukan hanya copy. Kerjakan hanya jika pemilik menyetujuinya.

### 6A. Pindahkan pertanyaan riwayat kerja (D-105)

Saat ini pertanyaan riwayat kerja ada di layar CV siap. Menurut D-105, pertanyaan ini diajukan **tepat sebelum Cek Kecocokan pertama**: di atas daftar Lowongan Relevan, dan di atas tombol pada Cek Lowongan. Defaultnya tidak dicentang. Setelah cek kecocokan pertama untuk versi CV itu, jawabannya terkunci (checkbox tampil nonaktif).
- Judul kecil: "Sebelum cek kecocokan" / "Before you analyze fit"
- Teks checkbox tetap `history.check.*`.
- Teks saat terkunci: "Jawaban ini dipakai untuk semua cek kecocokan dengan versi CV ini. Unggah atau edit CV untuk mengubahnya." / "This answer applies to every fit check for this version of your CV. Upload or edit your CV to change it."
- Hapus bagian `ready.history.*` dari layar CV siap.

### 6B. Satu pencarian per sesi di mode live (D-103)

Di mode live, tombol "Ubah pencarian" dan "Kembali ke hasil sebelumnya" **tidak ditampilkan**, karena beta publik hanya mengizinkan satu pencarian per sesi. Di mode demo keduanya tetap ada.
- results.emptySearch.p (L): "Pencarian di sesi ini sudah terpakai dan tidak menemukan lowongan dengan filter tersebut. Kamu masih bisa memakai Cek Lowongan dengan deskripsi lowongan yang kamu temukan sendiri." / "This session's search found no jobs with those filters. You can still use Check a Job with a job description you found yourself."
- results.emptySearch.btn (L): "Cek lowongan" / "Check a job"

### 6C. State tambahan khusus live (untuk ditinjau lewat `?scenario=budget`)

- **Kapasitas harian habis:** judul "Kapasitas analisis hari ini sudah habis" / "Today's analysis capacity is used up"; isi "Beta ini punya batas harian agar biayanya tetap terkendali. Coba lagi besok, atau lihat demo dengan CV contoh." / "This beta has a daily limit to keep costs under control. Try again tomorrow, or explore the demo with a sample CV."; tombol "Coba dengan CV contoh" / "Try a sample CV".
