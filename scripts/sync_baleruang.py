"""Sinkronkan GeoPATUH dari Bale Ruang NTB.

Bale Ruang NTB (https://github.com/atrbpnproject/baleruangntb) adalah sumber
utama data layer dan fitur. GeoPATUH adalah edisi Kabupaten Lombok Timur:

1. Aplikasi (index.html, js, css, legend, webfonts, images, regulasi, sw.js)
   disalin dari Bale Ruang, lalu identitas GeoPATUH dan cakupan Lombok Timur
   diterapkan lewat daftar tambalan (PATCHES) di bawah. Setiap tambalan wajib
   cocok; bila Bale Ruang berubah sehingga tambalan tidak cocok, sinkronisasi
   dibatalkan dan GeoPATUH tetap memakai versi sebelumnya.
2. Data analisis (data/analysis) dan batas desa (data/admin-index) disalin
   hanya untuk sel grid 0,1 derajat yang menyentuh Lombok Timur, beserta paket
   dan indeks titiknya. Format, isi, dan geometri berkas sama persis dengan
   Bale Ruang (tanpa simplify/round/clip), jadi kode Bale Ruang membacanya
   tanpa perubahan.
3. Berkas khusus GeoPATUH di folder overlay/ (manifest, ikon) disalin terakhir.

Pemakaian:
  python scripts/sync_baleruang.py --source /path/salinan/baleruangntb [--ref <sha>]
  python scripts/sync_baleruang.py --check --source ...   # uji tambalan saja, tanpa menulis
"""

import argparse
import datetime
import glob
import gzip
import json
import math
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "atrbpnproject/baleruangntb"
PUBLIC_URL = "https://atrbpnproject.github.io/geopatuh/"

# Wilayah Kabupaten Lombok Timur (bbox batas desa, diberi kelonggaran ~1 km).
# Sel grid yang menyentuh kotak ini ikut disalin, termasuk sedikit wilayah
# kabupaten tetangga di tepi, agar analisis bidang di perbatasan tetap lengkap.
REGION = (116.36, -8.95, 116.77, -8.23)
REGION_NAME = "Lombok Timur"
REGION_ISLAND = "Pulau Lombok"
HOME_CENTER = "[-8.60,116.56]"
HOME_ZOOM = "11"

# Berkas/folder aplikasi yang disalin dari Bale Ruang (relatif terhadap akar repo).
APP_FILES = ["index.html", "sw.js"]
APP_DIRS = ["css", "js", "legend", "webfonts", "images", "regulasi"]
# Layer yang wajib ada di Bale Ruang dan punya data di Lombok Timur.
REQUIRED_LAYERS = ["rtrw", "lsd", "lp2b", "kp2b", "lbs", "pippib",
                   "lotim-ks", "lotim-rtrw", "lotim-rdtr-sambelia", "lotim-rdtr-pringgabaya"]

BRAND = "GeoPATUH"
TAGLINE = "Satu Titik, Seluruh Status Ruang"

# (berkas, teks lama, teks baru, jumlah kemunculan minimal). Semua wajib cocok.
PATCHES = [
    # --- Identitas GeoPATUH ---
    ("index.html", "images/bale-ruang-ntb-logo-v3.png", "images/geopatuh-logo.png", 1),
    ("index.html", "images/app/", "images/geopatuh-app/", 1),
    ("index.html", "Satu Tempat, Seluruh Informasi Ruang", TAGLINE, 1),
    ("index.html", "Bale Ruang NTB", BRAND, 5),
    ("index.html", 'content="Bale Ruang"', 'content="GeoPATUH"', 0),
    ("index.html", "<h1>Bale Ruang <span>NTB</span></h1>", "<h1>Geo<span>PATUH</span></h1>", 0),
    ("index.html", "Menyiapkan peta tata ruang NTB", "Menyiapkan peta tata ruang Lombok Timur", 0),
    ("index.html", "Tata Ruang · Pertanahan · Nusa Tenggara Barat", "Tata Ruang · Pertanahan · Kabupaten Lombok Timur", 0),
    ("index.html", "baleRuang", "geoPatuh", 1),
    ("index.html", "tampilan seluruh NTB", "tampilan Lombok Timur", 1),
    ("js/geotag-v3.js", "images/bale-ruang-ntb-logo-v3.png", "images/geopatuh-logo.png", 1),
    ("js/geotag-v3.js", "Satu Tempat, Seluruh Informasi Ruang", TAGLINE, 0),
    ("js/geotag-v3.js", "Bale Ruang NTB", BRAND, 1),
    ("js/geotag-v2.js", "images/bale-ruang-ntb-logo-v3.png", "images/geopatuh-logo.png", 0),
    ("js/geotag-v2.js", "Bale Ruang NTB", BRAND, 0),
    ("js/bidang-report.js", "https://atrbpnproject.github.io/baleruangntb/", PUBLIC_URL, 1),
    ("js/bidang-report.js", "Bale Ruang NTB", BRAND, 1),
    ("sw.js", "images/bale-ruang-ntb-logo-v3.png", "images/geopatuh-logo.png", 1),
    ("sw.js", "images/app/", "images/geopatuh-app/", 1),
    # Cache service worker dipisah dari Bale Ruang (satu origin github.io) dan
    # hanya menghapus cache milik GeoPATUH sendiri.
    ("sw.js", "'bale-ruang-", "'geopatuh-", 2),
    ("sw.js", "return k !== VERSION && k !== STATIC;",
     "return k.indexOf('geopatuh-') === 0 && k !== VERSION && k !== STATIC;", 1),
    # Identitas visual GeoPATUH (menubar & splash) dari overlay/css/geopatuh-theme.css.
    ("index.html", '<meta name="theme-color" content="#0b3a66">',
     '<meta name="theme-color" content="#123a3e">\n  <link rel="stylesheet" href="css/geopatuh-theme.css?v=2">', 1),
    # --- Cakupan Lombok Timur ---
    ("index.html", "NTB_HOME_CENTER=[-8.55,117.20],NTB_HOME_ZOOM=8",
     "NTB_HOME_CENTER=%s,NTB_HOME_ZOOM=%s" % (HOME_CENTER, HOME_ZOOM), 1),
    # Panel layer: hanya kelompok Lombok Timur (terbuka), layer kabupaten lain
    # disembunyikan dan tidak dilaporkan di hasil analisis.
    ("index.html", "window.__geopatuhDefs=defs;",
     "window.__geopatuhDefs=defs;defs.forEach(function(d){if(d.regionalGroup&&d.regionalGroup!=='%s')d.retired=true});" % REGION_NAME, 1),
    ("index.html", "container.className='layer-group';",
     "container.className='layer-group';if(group.name!=='%s')container.style.display='none';else container.open=true;" % REGION_NAME, 1),
    ("index.html", "heading.className='section-title regional-island-title';",
     "heading.className='section-title regional-island-title';if(group.island!=='%s')heading.style.display='none';" % REGION_ISLAND, 1),
    ("index.html", "Data kabupaten/kota ada di bawah.", "Data Kabupaten Lombok Timur ada di bawah.", 0),
]

# (berkas, pola regex, pengganti, jumlah kemunculan minimal) untuk bagian yang
# memuat nomor versi berubah-ubah (mis. ?v=...).
REGEX_PATCHES = [
    # Layer Persil / Bidang Tanah (BHUMI, BumiAtlas, URL sendiri) tidak dipakai
    # di GeoPATUH: panelnya dibuat oleh persil-layer.js, jadi cukup tidak dimuat.
    ("index.html", r'<script src="js/persil-(?:config|layer)\.js[^"]*"></script>\s*', "", 2),
]

# Menu Regulasi: hanya peraturan nasional, provinsi/tematik, dan Lombok Timur.
REGULASI_KEEP_GROUPS = {"Peraturan Nasional", "Provinsi", "Data Tematik"}


def filter_regulasi(stage):
    """Saring katalog di js/regulasi.js (antara /*KATALOG*/ dan /*END*/) dan
    hapus PDF lokal di regulasi/ yang tidak lagi dirujuk."""
    path = os.path.join(stage, "js", "regulasi.js")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    start, end = text.find("/*KATALOG*/"), text.find("/*END*/")
    if start < 0 or end < start:
        return ["js/regulasi.js: penanda /*KATALOG*/.../*END*/ tidak ditemukan"]
    catalog = json.loads(text[start + len("/*KATALOG*/"):end])
    kept = [e for e in catalog if e.get("pulau") in REGULASI_KEEP_GROUPS or e.get("wilayah") == REGION_NAME]
    if not any(e.get("wilayah") == REGION_NAME for e in kept):
        return ["js/regulasi.js: tidak ada regulasi %s di katalog" % REGION_NAME]
    text = text[:start] + "/*KATALOG*/" + json.dumps(kept, ensure_ascii=False, separators=(",", ":")) + text[end:]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    used = {f.get("file") for e in kept for f in e.get("files") or [] if f.get("file") and not f.get("ext")}
    folder = os.path.join(stage, "regulasi")
    for name in os.listdir(folder) if os.path.isdir(folder) else []:
        if name.lower().endswith(".pdf") and name not in used:
            os.remove(os.path.join(folder, name))
    return []


def read_assigned(path):
    with open(path, encoding="utf-8") as handle:
        code = handle.read()
    return json.loads(code[code.index("=") + 1:].strip().rstrip(";"))


def read_refs(path):
    with open(path, encoding="utf-8") as handle:
        code = handle.read()
    return json.loads(code[code.rindex("]=") + 2:].strip().rstrip(";"))


def read_gz_json(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def cell_in_region(cell, grid):
    x, y = (int(v) for v in cell.split(":"))
    west, south, east, north = REGION
    return x * grid <= east and (x + 1) * grid >= west and y * grid <= north and (y + 1) * grid >= south


def is_province_wide(cells, grid):
    """Layer provinsi (LSD, LP2B, LBS, KP2B, PIPPIB, RTRW Provinsi) punya data di
    Pulau Lombok dan Pulau Sumbawa (batas kedua pulau di Selat Alas, ~117 BT)."""
    xs = [int(c.split(":")[0]) * grid for c in cells]
    return bool(xs) and min(xs) < 116.9 and max(xs) > 117.2


def bbox_in_region(b):
    west, south, east, north = REGION
    return b[0] <= east and b[2] >= west and b[1] <= north and b[3] >= south


def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copy_cell_pidx(src_dir, dst_dir, cell):
    """Salin pidx/<cell>.json.gz dan potongan pidx/<cell>/*.json.gz."""
    name = cell.replace(":", "_m")
    main = os.path.join(src_dir, name + ".json.gz")
    if not os.path.exists(main):
        return None
    copy_file(main, os.path.join(dst_dir, name + ".json.gz"))
    sub = os.path.join(src_dir, name)
    if os.path.isdir(sub):
        shutil.copytree(sub, os.path.join(dst_dir, name))
    return read_gz_json(main)


def build_analysis(src, dst):
    catalog = read_assigned(os.path.join(src, "index.js"))
    out_catalog, summary = {}, []
    for key, entry in catalog.items():
        grid, folder = entry["grid"], entry["folder"]
        lotim_only = key.startswith("lotim-")
        if not lotim_only and not is_province_wide(entry["cells"], grid):
            continue  # layer khusus kabupaten/kota lain (RTRW/RDTR) tidak dipakai GeoPATUH
        cells = {c: p for c, p in entry["cells"].items() if lotim_only or cell_in_region(c, grid)}
        if not cells:
            continue
        packs = set()
        for cell, rel in cells.items():
            path = os.path.join(src, rel)
            copy_file(path, os.path.join(dst, rel))
            with open(path, encoding="utf-8") as handle:
                code = handle.read()
            if "__LONTAR_ANALYSIS_REFS__" in code:
                packs.update(read_refs(path))
            index = copy_cell_pidx(os.path.join(src, folder, "pidx"), os.path.join(dst, folder, "pidx"), cell)
            if index:
                packs.update((index.get("p") or {}).keys())
                packs.update(g["k"] for g in index.get("g") or [] if g.get("k"))
        missing = []
        for pack in sorted(packs):
            rel = os.path.join(folder, "packs", pack.replace(":", "_m") + ".js.gz")
            if os.path.exists(os.path.join(src, rel)):
                copy_file(os.path.join(src, rel), os.path.join(dst, rel))
            else:
                missing.append(pack)
        if missing:
            raise SystemExit("Layer %s: %d paket tidak ditemukan di Bale Ruang (%s...)" % (key, len(missing), missing[:3]))
        item = dict(entry)
        item["cells"] = cells
        out_catalog[key] = item
        summary.append({"key": key, "cells": len(cells), "packs": len(packs), "source": entry.get("source", "")})
    for name in os.listdir(src):
        if os.path.isfile(os.path.join(src, name)) and name != "index.js":
            copy_file(os.path.join(src, name), os.path.join(dst, name))
    with open(os.path.join(dst, "index.js"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("window.__LONTAR_ANALYSIS_INDEX__=" + json.dumps(out_catalog, ensure_ascii=False, separators=(",", ":")) + ";")
    missing = [k for k in REQUIRED_LAYERS if k not in out_catalog]
    if missing:
        raise SystemExit("Layer wajib tidak ada/kosong untuk Lombok Timur: %s" % ", ".join(missing))
    return summary


def build_admin(src, dst):
    with open(os.path.join(src, "index.js"), encoding="utf-8") as handle:
        code = handle.read()
    head, _, meta = code.partition(";window.__NTB_ADMIN_META__=")
    index = json.loads(head[head.index("=") + 1:])
    ids = {e["id"] for e in index if bbox_in_region(e["bbox"])}
    cells = []
    for cell in read_gz_json(os.path.join(src, "pidx", "cells.json")):
        if not cell_in_region(cell, 0.1):
            continue
        data = copy_cell_pidx(os.path.join(src, "pidx"), os.path.join(dst, "pidx"), cell)
        if data is None:
            continue
        cells.append(cell)
        ids.update(e[0] for e in data.get("s") or [])
        ids.update(g["id"] for g in data.get("g") or [] if "id" in g)
    for ident in sorted(ids):
        copy_file(os.path.join(src, "%s.js" % ident), os.path.join(dst, "%s.js" % ident))
    os.makedirs(os.path.join(dst, "pidx"), exist_ok=True)
    # mtime=0 agar hasil gzip sama persis setiap sinkron (tidak ada commit kosong).
    with open(os.path.join(dst, "pidx", "cells.json"), "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as handle:
            handle.write(json.dumps(sorted(cells), separators=(",", ":")).encode("utf-8"))
    kept = [e for e in index if e["id"] in ids]
    with open(os.path.join(dst, "index.js"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("window.__NTB_ADMIN_INDEX__=" + json.dumps(kept, separators=(",", ":")) + ";window.__NTB_ADMIN_META__=" + meta)
    for name in os.listdir(src):
        path = os.path.join(src, name)
        if os.path.isfile(path) and not name.endswith(".js"):
            copy_file(path, os.path.join(dst, name))
    return {"villages": len(ids), "cells": len(cells)}


def apply_patches(stage):
    problems = []
    for rel, old, new, minimum in PATCHES:
        path = os.path.join(stage, rel)
        if not os.path.exists(path):
            if minimum:
                problems.append("%s tidak ada" % rel)
            continue
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        count = text.count(old)
        if count < minimum:
            problems.append("%s: '%s' ditemukan %d kali (butuh >= %d)" % (rel, old[:60], count, minimum))
            continue
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text.replace(old, new))
    for rel, pattern, new, minimum in REGEX_PATCHES:
        path = os.path.join(stage, rel)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        text, count = re.subn(pattern, new, text)
        if count < minimum:
            problems.append("%s: pola '%s' ditemukan %d kali (butuh >= %d)" % (rel, pattern[:60], count, minimum))
            continue
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="folder salinan repositori Bale Ruang NTB")
    parser.add_argument("--ref", default="", help="commit Bale Ruang yang disinkronkan (untuk status)")
    parser.add_argument("--check", action="store_true", help="hanya uji tambalan, tidak menulis ke GeoPATUH")
    args = parser.parse_args()
    source = os.path.abspath(args.source)

    stage = tempfile.mkdtemp(prefix="geopatuh-sync-")
    try:
        for name in APP_FILES:
            copy_file(os.path.join(source, name), os.path.join(stage, name))
        for name in APP_DIRS:
            if os.path.isdir(os.path.join(source, name)):
                shutil.copytree(os.path.join(source, name), os.path.join(stage, name))
        problems = apply_patches(stage) + filter_regulasi(stage)
        if problems:
            for problem in problems:
                print("TAMBALAN GAGAL:", problem, file=sys.stderr)
            raise SystemExit("Sinkronisasi dibatalkan: tampilan Bale Ruang berubah, perbarui PATCHES di scripts/sync_baleruang.py.")
        if args.check:
            print("Semua tambalan cocok.")
            return 0

        data = os.path.join(stage, "data")
        layers = build_analysis(os.path.join(source, "data", "analysis"), os.path.join(data, "analysis"))
        admin = build_admin(os.path.join(source, "data", "admin-index"), os.path.join(data, "admin-index"))
        for path in glob.glob(os.path.join(source, "data", "*.js")):
            copy_file(path, os.path.join(data, os.path.basename(path)))

        overlay = os.path.join(ROOT, "overlay")
        for path in glob.glob(os.path.join(overlay, "**", "*"), recursive=True):
            if os.path.isfile(path):
                copy_file(path, os.path.join(stage, os.path.relpath(path, overlay)))

        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).replace(microsecond=0)
        status = {"status": "success", "message": "Aplikasi dan layer disinkronkan dari Bale Ruang NTB (wilayah Lombok Timur).",
                  "updatedAt": now.isoformat(), "source": "https://github.com/%s" % REPO, "ref": args.ref or "local",
                  "region": REGION_NAME, "admin": admin, "layers": layers}
        with open(os.path.join(data, "baleruang_status.json"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(status, ensure_ascii=False, indent=2) + "\n")

        # Ganti isi GeoPATUH: folder aplikasi & data ditulis ulang utuh agar berkas
        # lama yang sudah dihapus di Bale Ruang ikut hilang.
        for name in APP_DIRS + ["data"]:
            target = os.path.join(ROOT, name)
            if os.path.isdir(target):
                shutil.rmtree(target)
            if os.path.isdir(os.path.join(stage, name)):
                shutil.copytree(os.path.join(stage, name), target)
        for path in glob.glob(os.path.join(stage, "*")):
            if os.path.isfile(path):
                copy_file(path, os.path.join(ROOT, os.path.basename(path)))

        for item in layers:
            print("%-28s %4d sel  %5d paket" % (item["key"], item["cells"], item["packs"]))
        print("Batas desa: %(villages)d desa, %(cells)d sel indeks" % admin)
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
