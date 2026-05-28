"""
Jószaki profilkép pipeline:
1. Beolvassa a seo_name listát a Google Sheet-ből
2. Letölti a profilképet a joszaki.hu oldalról
3. 512px-re méretezi, WebP formátumban menti
4. Feltölti a GCS joszaki-assets/minisite_assests/ mappába
5. A publikus képlinket visszaírja a sheet Column 8 oszlopába

Ha nincs profilkép: a default-avatar.webp URL kerül a sheetbe.

--cleanup flag: törli az összes GCS képet (kivéve default-avatar.webp), majd újrafuttatja.
"""

import sys
import os
import io
import subprocess
import csv

import requests
from bs4 import BeautifulSoup
from PIL import Image
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
DEFAULT_AVATAR_URL = "https://joszaki.hu/_nuxt/img/default-avatar.9677c28.png"
DEFAULT_AVATAR_GCS_NAME = "default-avatar.webp"
GCS_BUCKET = "gs://joszaki-assets/minisite_assests/"
GCS_PUBLIC_BASE = "https://storage.googleapis.com/joszaki-assets/minisite_assests/"
SHEET_ID = "1WM2IOBZqdTLEsNnTYBrwSIDwlZddBetVg0Cv01rGrnU"
SHEET_GID = "1184434414"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
GSUTIL = r"C:\Users\Szabó Norbert\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gsutil.cmd"
GCLOUD = r"C:\Users\Szabó Norbert\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

OAUTH_CLIENT_PATH = "C:/Temp/oauth_desktop.json"
OAUTH_TOKEN_PATH = "C:/Temp/oauth_token.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_client():
    creds = None
    if os.path.exists(OAUTH_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(OAUTH_TOKEN_PATH, SHEETS_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_PATH, SHEETS_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(OAUTH_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return gspread.authorize(creds)


def load_sheet_data(worksheet, limit=None, offset=None, force=False):
    """Visszaadja a (seo_name, row_index) párokat. force=True esetén a már kitöltött sorokat is feldolgozza.
    offset: sheet sor száma (1-alapú, fejléc nélkül), ahonnan induljon (pl. 51 = 51. adatsor)."""
    all_rows = worksheet.get_all_values()
    if not all_rows:
        return []
    header = all_rows[0]
    try:
        seo_col = next(
            header.index(h) for h in ("seo_name", "SEO név", "SEO nev") if h in header
        )
    except StopIteration:
        seo_col = 1
    result = []
    skipped = 0
    for i, row in enumerate(all_rows[1:], start=2):
        if offset and i < offset:
            continue
        if len(row) <= seo_col:
            continue
        seo_name = row[seo_col].strip()
        if not seo_name:
            continue
        if not force:
            existing_url = row[10].strip() if len(row) > 10 else ""
            if existing_url:
                skipped += 1
                continue
        result.append((seo_name, i))
        if limit and len(result) >= limit:
            break
    if skipped:
        print(f"  {skipped} sor kihagyva (már van kép URL)")
    return result


def write_image_url_to_sheet(worksheet, row_index, public_url):
    worksheet.update_cell(row_index, 11, public_url)


def get_profile_image_url(slug):
    url = f"https://joszaki.hu/szakember/{slug}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    imgs = [i["src"] for i in soup.find_all("img") if "storage.googleapis" in i.get("src", "")]
    if not imgs:
        return None
    return imgs[0].replace("_256.jpg", "_512.jpg")


def download_image(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 404:
        url = url.replace("_512.jpg", "_256.jpg")
        r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.content


def save_as_webp(img, path, max_size=512):
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
    img.save(path, "WEBP", quality=90)


def upload_file_to_gcs(local_path, gcs_name):
    dest = GCS_BUCKET + gcs_name
    result = subprocess.run(
        [GSUTIL, "-h", "Content-Type:image/webp", "cp", local_path, dest],
        capture_output=True, text=True, shell=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"gsutil hiba: {result.stderr}")
    return GCS_PUBLIC_BASE + gcs_name


def upload_to_gcs(local_path, slug):
    return upload_file_to_gcs(local_path, f"{slug}.webp")


def cleanup_gcs():
    """Törli az összes .webp fájlt a GCS bucketből, kivéve a default-avatar.webp-t."""
    print("GCS cleanup...")
    result = subprocess.run(
        [GSUTIL, "ls", GCS_BUCKET + "*.webp"],
        capture_output=True, text=True, shell=False
    )
    if result.returncode != 0:
        print("  Nincs törölni való fájl (üres bucket vagy hiba)")
        return
    files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    default_path = GCS_BUCKET + DEFAULT_AVATAR_GCS_NAME
    to_delete = [f for f in files if f != default_path]
    if not to_delete:
        print("  Nincs törölni való fájl")
        return
    print(f"  {len(to_delete)} fájl törlése...")
    del_result = subprocess.run(
        [GSUTIL, "-m", "rm"] + to_delete,
        capture_output=True, text=True, shell=False
    )
    if del_result.returncode != 0:
        print(f"  Törlési figyelmeztetés: {del_result.stderr}")
    print(f"  Törölve: {len(to_delete)} fájl")


def ensure_default_avatar():
    """Feltölti a default avatart GCS-re, ha még nincs ott. Visszaadja a publikus URL-t."""
    dest = GCS_BUCKET + DEFAULT_AVATAR_GCS_NAME
    check = subprocess.run(
        [GSUTIL, "ls", dest],
        capture_output=True, text=True, shell=False
    )
    if check.returncode == 0:
        print(f"  Default avatar már megvan a GCS-en")
        return GCS_PUBLIC_BASE + DEFAULT_AVATAR_GCS_NAME

    print("  Default avatar feltöltése GCS-re...")
    img_bytes = download_image(DEFAULT_AVATAR_URL)
    tmp_dir = "C:/Temp/joszaki_imgs"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, DEFAULT_AVATAR_GCS_NAME)
    try:
        img = Image.open(io.BytesIO(img_bytes))
        save_as_webp(img, tmp_path)
        url = upload_file_to_gcs(tmp_path, DEFAULT_AVATAR_GCS_NAME)
        print(f"  Default avatar feltöltve: {url}")
        return url
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def process_slug(slug, row_index, worksheet, default_avatar_public_url):
    print(f"[{slug}] Feldolgozás...")

    img_url = get_profile_image_url(slug)
    if not img_url:
        print(f"  Nincs profilkep, default avatar URL a sheetbe")
        if worksheet and row_index:
            write_image_url_to_sheet(worksheet, row_index, default_avatar_public_url)
            print(f"  Sheet frissítve (sor {row_index})")
        return True

    print(f"  Kép URL: {img_url}")
    img_bytes = download_image(img_url)
    print(f"  Letöltve ({len(img_bytes)//1024} KB)")

    img = Image.open(io.BytesIO(img_bytes))

    tmp_dir = "C:/Temp/joszaki_imgs"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"{slug}.webp")

    try:
        save_as_webp(img, tmp_path)
        public_url = upload_to_gcs(tmp_path, slug)
        print(f"  Feltöltve: {public_url}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if worksheet and row_index:
        write_image_url_to_sheet(worksheet, row_index, public_url)
        print(f"  Sheet frissítve (sor {row_index})")

    return True


def main(slugs=None, limit=None, offset=None, cleanup=False):
    gc = get_sheets_client()
    worksheet = gc.open_by_key(SHEET_ID).get_worksheet_by_id(int(SHEET_GID))

    if cleanup:
        cleanup_gcs()

    default_avatar_public_url = ensure_default_avatar()

    if slugs:
        print("Sheet-ből keresem a sor indexeket...")
        all_data = load_sheet_data(worksheet, force=True)
        slug_to_row = {s: r for s, r in all_data}
        targets = [(slug, slug_to_row.get(slug)) for slug in slugs]
    else:
        force = cleanup
        offset_txt = f', {offset}. sortól' if offset else ''
        print(f"Sheet-ből töltöm a seo_name listát{f' (első {limit})' if limit else ''}{offset_txt}...")
        targets = load_sheet_data(worksheet, limit=limit, offset=offset, force=force)
        print(f"  {len(targets)} slug betöltve")

    ok, fail = 0, 0
    for slug, row_index in targets:
        try:
            if process_slug(slug, row_index, worksheet, default_avatar_public_url):
                ok += 1
            else:
                fail += 1
        except Exception as e:
            print(f"  HIBA: {e}")
            fail += 1

    print(f"\nKész: {ok} sikeres, {fail} sikertelen")


if __name__ == "__main__":
    # python script.py                          → teljes sheet feldolgozása
    # python script.py --limit 50              → első 50 sor (kihagyja a már kész sorokat)
    # python script.py --offset 51             → 51. sortól végig
    # python script.py --offset 51 --limit 20  → 51. sortól 20 sor
    # python script.py --limit 50 --cleanup    → GCS cleanup, majd első 50 újrafeldolgozása
    # python script.py slug1 slug2             → egyedi slugok
    args = sys.argv[1:]
    cleanup = "--cleanup" in args
    if cleanup:
        args = [a for a in args if a != "--cleanup"]

    limit = None
    offset = None

    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])
        args = [a for a in args if a not in ("--limit", args[idx + 1])]

    if "--offset" in args:
        idx = args.index("--offset")
        offset = int(args[idx + 1])
        args = [a for a in args if a not in ("--offset", args[idx + 1])]

    if args:
        main(slugs=args, cleanup=cleanup)
    else:
        main(limit=limit, offset=offset, cleanup=cleanup)
