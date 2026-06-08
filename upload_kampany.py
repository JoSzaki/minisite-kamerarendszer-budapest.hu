import csv, json, subprocess, urllib.request, urllib.error, sys, argparse

PROJECT      = 'joszaki-minisite'
DEFAULT_FOTO = 'https://storage.googleapis.com/joszaki-assets/minisite_assests/default-avatar.png'
SAMPLE_IDS   = ['kovacs-peter-1', 'nagy-janos-2', 'szabo-laszlo-3', 'horvath-gabor-4']

parser = argparse.ArgumentParser(
    description='Kampány CSV → Firestore feltöltő (csak mintaadatokat töröl, majd feltölt)',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''Példák:
  python upload_kampany.py kampany.csv
  python upload_kampany.py kampany.csv --collection joszaki_lakatos
'''
)
parser.add_argument('csv_file', help='Kampány CSV fájl elérési útja (id,name,mobile,kép oszlopok)')
parser.add_argument('--collection', default='joszaki_kamera',
                    help='Firestore kollekció neve (alapértelmezett: joszaki_kamera)')
args = parser.parse_args()

CSV_FILE   = args.csv_file
COLLECTION = args.collection

def get_token():
    result = subprocess.run('gcloud auth print-access-token',
                            capture_output=True, text=True, shell=True)
    token = result.stdout.strip()
    if not token:
        print('HIBA: gcloud token nem elérhető. Futtasd: gcloud auth login')
        sys.exit(1)
    return token

def firestore_request(doc_id, body, method, token):
    url = (f'https://firestore.googleapis.com/v1/projects/{PROJECT}'
           f'/databases/(default)/documents/{COLLECTION}/{doc_id}')
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    if body:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code

def format_phone(raw):
    digits = ''.join(c for c in raw if c.isdigit())
    if digits.startswith('36'):
        digits = digits[2:]
    if digits.startswith('06'):
        digits = digits[2:]
    return '+36' + digits

token = get_token()
print(f'Token megszerzve. Kollekció: {COLLECTION}\n')

# 1. Minták törlése
print('Minták törlése...')
for sid in SAMPLE_IDS:
    status = firestore_request(sid, None, 'DELETE', token)
    print(f'  DELETE {sid}: HTTP {status}')

# 2. Kampány CSV feltöltése
print(f'\nFeltöltés: {COLLECTION}...\n')
ok = err = 0
with open(CSV_FILE, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        doc_id = row['id'].strip()
        name   = row['name'].strip()
        phone  = format_phone(row['mobile'].strip())
        foto   = row['kép'].strip() if row.get('kép') else ''
        if not foto or 'default-avatar' in foto:
            foto = DEFAULT_FOTO

        fields = {
            'name':  {'stringValue': name},
            'phone': {'stringValue': phone},
            'foto':  {'stringValue': foto},
            'datum': {'stringValue': '2026-05-26T00:00:00Z'},
        }
        status = firestore_request(doc_id, {'fields': fields}, 'PATCH', token)
        icon = 'OK' if status in (200, 201) else 'HIBA'
        if status in (200, 201):
            ok += 1
        else:
            err += 1
        print(f'  [{icon}] {doc_id} ({name}) – HTTP {status}')

print(f'\nKész: {ok} OK, {err} hiba.')
