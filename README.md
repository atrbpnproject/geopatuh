# GeoPATUH

**GeoPATUH — Portal Analisis Tata Ruang, Utilisasi dan Hukum**

> “Satu Titik, Seluruh Status Ruang”

GeoPATUH memastikan setiap layanan pertanahan dimulai dari kepatuhan terhadap tata ruang, kebijakan pemanfaatan tanah, dan hukum.

GeoPATUH mengambil inspirasi dari motto Kabupaten Lombok Timur, “Patuh Karya”, yang mencerminkan semangat kepatuhan terhadap aturan dan kerja yang bertanggung jawab. Melalui GeoPATUH, nilai tersebut diwujudkan dalam pelayanan pertanahan berbasis geospasial, sehingga setiap keputusan didasarkan pada kepatuhan terhadap tata ruang, pemanfaatan ruang, dan ketentuan hukum yang berlaku.

## Sinkronisasi dengan Bale Ruang NTB

Mulai versi ini GeoPATUH adalah **Bale Ruang NTB edisi Kabupaten Lombok Timur**.
Sumber utama data layer dan fitur adalah repositori
[Bale Ruang NTB](https://github.com/atrbpnproject/baleruangntb); cukup perbarui
Bale Ruang, GeoPATUH ikut terbarui otomatis (sama seperti SOBAT TARU).

Yang disalin dari Bale Ruang:

- **Aplikasi**: `index.html`, `sw.js`, `css/`, `js/`, `legend/`, `webfonts/`,
  `images/`, `regulasi/`. Seluruh fitur dan tampilan Bale Ruang (analisis titik
  dan bidang, Upload SHP/KML, Alat ukur, konversi SHP/KML, PDF KKPR ke poligon,
  Foto & PDF Geotag, Regulasi, cetak laporan) ikut terbawa. Layer Persil/Bidang Tanah sengaja tidak dimuat di GeoPATUH.
- **Data**: `data/analysis` (RTRW Provinsi, LSD, LP2B 2026, KP2B, LBS, PIPPIB,
  dan layer RTRW/RDTR/Kawasan Strategis Lombok Timur) serta `data/admin-index`
  (batas desa). Hanya sel grid 0,1° yang menyentuh Lombok Timur yang disalin,
  berkasnya sama persis dengan Bale Ruang (tanpa penyederhanaan geometri).

Identitas GeoPATUH (nama, logo, slogan, ikon aplikasi) dan cakupan Lombok Timur
(tampilan awal peta, panel layer hanya kelompok Lombok Timur, layer kabupaten
lain tidak ikut dianalisis) diterapkan oleh daftar `PATCHES` di
`scripts/sync_baleruang.py`. Berkas khusus GeoPATUH (manifest dan ikon) ada di
folder `overlay/`.

Cara kerja:

- GitHub Actions **Sinkronkan Bale Ruang** memeriksa Bale Ruang setiap 6 jam dan
  hanya bekerja bila ada commit baru. Bisa juga dijalankan manual dari tab
  **Actions**, atau dipicu dari Bale Ruang lewat `repository_dispatch` dengan
  tipe `baleruang-updated`.
- Bila tampilan Bale Ruang berubah sehingga salah satu tambalan tidak cocok,
  sinkronisasi dibatalkan (workflow merah) dan GeoPATUH tetap memakai versi
  terakhir. Perbarui `PATCHES` lalu jalankan ulang.
- Status sinkronisasi terakhir: `data/baleruang_status.json`.
- Sinkron manual di komputer:
  `python scripts/sync_baleruang.py --source "D:\path\baleruangntb"`
  (tambahkan `--check` untuk menguji tambalan saja).

Jangan menyunting `index.html`, `js/`, `css/` atau `data/` langsung di repo ini;
perubahan akan tertimpa sinkronisasi berikutnya. Ubah di Bale Ruang, atau
tambahkan tambalan/berkas di `scripts/sync_baleruang.py` dan `overlay/`.
