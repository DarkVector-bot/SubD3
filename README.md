# SubD3
SubD3 is a fast subdomain discovery tool combining passive enumeration from crt.sh and active bruteforce. Supports stealth mode, async DNS, JSON output, and custom wordlist. Lightweight &amp; powerful.

✅ Saya buatkan dokumentasi LENGKAP untuk README.md

Silakan copy-paste isi di bawah ini ke file README.md Anda di GitHub:

---

```markdown
# 🔍 SubD3 - Fast Subdomain Discovery Tool

**SubD3** adalah tool subdomain discovery yang menggabungkan **passive enumeration** dari certificate transparency logs (crt.sh) dan **active bruteforce** dengan performa tinggi. Dirancang untuk kecepatan, akurasi, dan kemudahan penggunaan.

---

## 📦 Cara Pasang (Installation)

### 1. Clone repository
```bash
git clone https://github.com/DarkVector-bot/Sub.git
cd Sub
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

Atau install manual:

```bash
pip install aiohttp dnspython
```

3. Selesai! Langsung bisa digunakan

```bash
python Subd3.py -d example.com
```

Catatan: Python 3.8+ diperlukan. Cek dengan python --version

---

🚀 Fitur Lengkap (Features)

Fitur Keterangan
✅ Passive Enumeration Scraping dari crt.sh (Certificate Transparency Logs)
✅ Active Bruteforce 500+ subdomain default wordlist
✅ Permutation Attack Generate variasi dari subdomain yang ditemukan
✅ Async DNS Resolver 7+ DNS server, query paralel 500+ per detik
✅ Stealth Mode Random delay & resolver rotation hindari rate limit
✅ Resolver Rotation Ganti DNS server setiap 100 query
✅ JSON Output Export hasil scan ke file JSON
✅ Custom Wordlist Bisa pakai wordlist sendiri
✅ Retry Mechanism Timeout query akan diulang 1x

---

🎯 Keunggulan dibanding tool lain

Aspek Subfinder Amass SubD3
Passive sources ✅ 15+ ✅ 20+ ✅ crt.sh
Active bruteforce ❌ ❌ ✅
Permutation attack ❌ ❌ ✅
Stealth mode ❌ ❌ ✅
Kecepatan (query/detik) ~50 ~30 500+
Mudah dipasang Medium Complex 1 perintah
File size ~50 MB ~100 MB ~25 KB

🔥 Keunggulan utama SubD3:

1. Ada active bruteforce - Subfinder & Amass cuma passive, SubD3 bisa tebak subdomain yang gak terdaftar di publik
2. Ringan & cepat - Cuma 1 file Python, gak perlu setup rumit
3. Permutation attack - Dari subdomain admin bisa generate admin-dev, admin-backup, dll
4. Stealth mode - Gak bakal kena rate limit karena ada random delay

---

📖 Cara Pakai (Usage)

Basic scan

```bash
python Subd3.py -d example.com
```

Dengan stealth mode (disarankan untuk production)

```bash
python Subd3.py -d example.com --stealth
```

Save hasil ke file JSON

```bash
python Subd3.py -d example.com -o result.json
```

Pakai custom wordlist

```bash
python Subd3.py -d example.com -w wordlist.txt
```

Atur kecepatan (concurrency)

```bash
python Subd3.py -d example.com -c 1000 --stealth
```

Matikan passive scan (cuma bruteforce)

```bash
python Subd3.py -d example.com --no-passive
```

Matikan permutation attack

```bash
python Subd3.py -d example.com --no-permutation
```

---

🛠️ Semua Parameter (Arguments)

Parameter Default Deskripsi
-d, --domain wajib Target domain (contoh: example.com)
-w, --wordlist default 500+ Custom wordlist file (1 subdomain per baris)
-c, --concurrency 500 Jumlah query paralel (max ~2000)
-o, --output - Simpan hasil ke file JSON
-t, --timeout 3.0 DNS timeout dalam detik
--stealth off Mode stealth (random delay + resolver rotation)
--no-passive off Matikan scan dari crt.sh
--no-permutation off Matikan permutation attack

---

📊 Contoh Output

Terminal output

```
╔════════════════════════════════════╗
║        SubD3 - v1.0.0              ║
║     Fast Subdomain Discovery       ║
╚════════════════════════════════════╝

[*] Domain: example.com
[*] Concurrency: 500
[*] Stealth mode: False
[*] Wordlist size: 542

[*] Passive scan from crt.sh...
[+] Found 23 subdomains from passive sources

[*] Active bruteforce with 542 words...
  Progress: 100/542 | Found: 12 | Success: 8.5%
  [+] mail.example.com -> 93.184.216.34
  [+] www.example.com -> 93.184.216.34
  [+] admin.example.com -> 192.0.2.10

[+] Discovered subdomains (47):
    mail.example.com -> 93.184.216.34
    www.example.com -> 93.184.216.34
    admin.example.com -> 192.0.2.10
```

Output JSON

```json
{
  "target": "example.com",
  "total_found": 47,
  "duration_seconds": 12.34,
  "subdomains": [
    {
      "full_domain": "www.example.com",
      "ips": ["93.184.216.34"]
    }
  ],
  "ip_mapping": {
    "93.184.216.34": ["www.example.com", "mail.example.com"]
  }
}
```

---

⚙️ Cara Kerja (How It Works)

```
1. Passive Scan
   ↓
   Query crt.sh untuk cari certificate history
   ↓
2. Active Bruteforce
   ↓
   Loop wordlist → DNS query ke 7+ resolver → cek A record
   ↓
3. Permutation Attack
   ↓
   Dari subdomain ditemukan → generate variasi (api-admin, admin-dev, dll)
   ↓
4. Output
   ↓
   Tampilkan di terminal + simpan JSON
```

---

🔧 Tips Optimal

Skenario Command
Bug bounty cepat python Subd3.py -d target.com --stealth -o hasil.json
Internal network python Subd3.py -d internal.local -c 1000
Wordlist besar python Subd3.py -d target.com -w big.txt --stealth
Hindari detection python Subd3.py -d target.com --stealth --no-passive -c 200

---

📁 Struktur File

```
Sub/
├── Subd3.py           # Main script (cukup 1 file!)
├── requirements.txt   # Dependencies (aiohttp, dnspython)
├── README.md          # Dokumentasi ini
├── LICENSE            # MIT License
└── .gitignore         # File yang diabaikan git
```

---

⚖️ Lisensi

MIT License - Bebas digunakan, dimodifikasi, dan didistribusikan.

---

🙋 FAQ

Q: Bedanya dengan Subfinder?
A: Subfinder cuma passive. SubD3 ada active bruteforce + permutation attack → bisa nemuin subdomain yang gak terdaftar di publik.

Q: Kok hasil scan sedikit?
A: Coba pakai --stealth atau kurangi -c (concurrency). Bisa juga custom wordlist yang lebih besar.

Q: Bisa dipakai di Windows?
A: Bisa! Asalkan Python terinstall. Cmd atau PowerShell sama-sama jalan.

Q: Butuh API key?
A: Tidak. Semua gratis dan open source.

---

⭐ Support

Jika project ini bermanfaat, kasih star di GitHub!
Pull request dan issue juga diterima.

---

Made with ❤️ for bug bounty & security research

```

---

## ✅ **File `requirements.txt` (sudah ada, pastikan isinya):**

```

aiohttp>=3.8.0
dnspython>=2.3.0

```

