# GeoPATUH — Integritas Geometri LSD

LSD pada paket ini dibangun ulang langsung dari `LSD_LOMBOK_TIMUR.shp` yang diberikan sebagai sumber pembanding ArcGIS.

Kebijakan geometri:
- sumber: ESRI:54034 / World Cylindrical Equal Area;
- target web: EPSG:4326;
- reproyeksi dilakukan langsung dari setiap vertex sumber;
- tidak ada simplify/generalize;
- tidak ada pembulatan koordinat buatan;
- tidak ada clipping geometri untuk membuat chunk;
- spatial chunk hanya menggandakan fitur utuh ke cell bbox yang disentuh;
- tampilan LSD dan analisis LSD memakai chunk presisi yang sama;
- Leaflet `smoothFactor` dipaksa `0`.

Hasil rebuild:
- fitur sumber: 64.155;
- vertex yang direproyeksi: 1.836.641;
- Polygon: 56.845;
- MultiPolygon: 7.310;
- cell indeks spasial: 60;
- extent EPSG:4326: 116.37607977796098, -8.917754761229304 sampai 116.72353947189573, -8.255140717306004.

Hash sumber:
b7d2baf48b93e6d55e9c5afa57b092f0a09426bc071f5070c7f6ac0ddda96dc3  /mnt/data/lsd_src/LSD LOMBOK TIMUR/LSD_LOMBOK_TIMUR.shp
4b0a0e1cead2fbe25934bc9b7b8e9b3e4ed118ed0ae6c81603045af8b5f7623c  /mnt/data/lsd_src/LSD LOMBOK TIMUR/LSD_LOMBOK_TIMUR.prj

Catatan: reproyeksi CRS diperlukan agar data dapat digambar di web. Reproyeksi mengubah representasi angka koordinat dari meter ke longitude/latitude, tetapi seluruh vertex sumber dipertahankan; tidak ada pengurangan vertex.


## 2026-08-29 — Restore geometri dari export QGIS
LSD TIDAK DIUBAH pada tahap ini. Layer berikut dikembalikan langsung ke geometri file export QGIS WebGISTARULotim-main: Batas Administrasi, RTRW Provinsi, Kawasan Strategis, RTRW Kabupaten, RDTR Sambelia, RDTR Pringgabaya, LCP2B, LP2B, KP2B, dan PIPPIB. Nama variabel JS disesuaikan hanya agar kompatibel dengan GeoPATUH. Geometry/coordinates/properties berasal dari export QGIS. Spatial-index LP2B dibangun ulang dari geometry QGIS tanpa simplify/clip/round. LBS tidak diubah karena tidak tersedia pada export QGIS pembanding.

## LBS source rebuild
- Source: `LBS LOTIM MERGE.shp` supplied by user.
- Features: 15681.
- Vertices: 1448956.
- CRS: `EPSG:23837` -> `EPSG:4326`.
- Policy: full source vertices; no simplify, generalize, rounding, or clipping.
- Display and analysis chunks were regenerated from the same source geometry.
