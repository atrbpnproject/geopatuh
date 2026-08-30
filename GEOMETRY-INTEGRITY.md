# Kebijakan Integritas Geometri GeoPATUH

GeoPATUH memperlakukan geometri sumber sebagai **source of truth**.

- Tampilan layer harus berasal dari geometri sumber atau salinan chunk yang koordinatnya identik dengan sumber.
- Analisis spasial harus memakai geometri sumber atau salinan identik tersebut.
- Dilarang memakai `simplify`, generalisasi, Douglas–Peucker, tolerance geometry, smoothing vertex, atau pembulatan koordinat untuk membentuk geometri analisis/tampilan.
- `smoothFactor` Leaflet ditetapkan `0`.
- Optimasi yang diperbolehkan: spatial index/grid, bounding-box prefilter, lazy loading, chunk loading tanpa clip/simplify, batching render, caching, dan Canvas renderer.
- Folder `data/display` lama telah dihapus karena berisi geometri hasil pemotongan/penyederhanaan dan tidak boleh dipakai kembali.
- `Leaflet.VectorGrid.js` lama yang tidak digunakan telah dihapus karena membawa mekanisme simplifikasi internal dan tidak diperlukan aplikasi.

## Dataset chunk presisi

`data/analysis` untuk LSD, LP2B, dan LBS hanya berfungsi sebagai indeks spasial. Satu fitur dapat muncul pada beberapa cell agar mudah ditemukan, tetapi geometry-nya harus identik dengan geometry sumber.
