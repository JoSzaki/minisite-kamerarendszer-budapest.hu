import csv, json, subprocess, urllib.request, urllib.error, sys

PROJECT    = 'joszaki-minisite'
COLLECTION = 'joszaki_kamera'
CSV_FILE   = r'C:\Users\Szabó Norbert\Downloads\Budapesti Biztonságtechnikusok 1-7 ker - Biztonságtechnika -Budapest 1-8ker.csv'

def get_token():
    result = subprocess.run(
        'gcloud auth print-access-token',
        capture_output=True, text=True, shell=True
    )
    token = result.stdout.strip()
    if not token:
        print('HIBA: gcloud auth token nem elérhető. Futtasd: gcloud auth login')
        sys.exit(1)
    return token

BASE_URL = (
    f'https://firestore.googleapis.com/v1/projects/{PROJECT}'
    f'/databases/(default)/documents/{COLLECTION}'
)

def list_docs(token):
    req = urllib.request.Request(BASE_URL + '?pageSize=300')
    req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return [doc['name'].split('/')[-1] for doc in data.get('documents', [])]
    except urllib.error.HTTPError as e:
        print(f'  Listázás hiba {e.code}: {e.read().decode()}')
        return []

def delete_doc(doc_id, token):
    url = f'{BASE_URL}/{doc_id}'
    req = urllib.request.Request(url, method='DELETE')
    req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code

def upload_doc(doc_id, fields, token):
    url = f'{BASE_URL}/{doc_id}'
    body = json.dumps({'fields': fields}).encode()
    req  = urllib.request.Request(url, data=body, method='PATCH')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        print(f'  HTTP hiba {e.code}: {e.read().decode()}')
        return e.code

token = get_token()
print(f'Token megszerzve.\n')

# 1. Meglévő dokumentumok törlése
print('Meglévő dokumentumok törlése...')
existing = list_docs(token)
print(f'  {len(existing)} dokumentum találva.')
for doc_id in existing:
    status = delete_doc(doc_id, token)
    print(f'  [{"OK" if status == 200 else "HIBA"}] Törölve: {doc_id} - HTTP {status}')

print(f'\nFeltöltés: {COLLECTION} kollekcióba...\n')

# 2. Új adatok feltöltése
# CSV oszlopok: link,id,name,email,Telefonszám,SEO név,Székhely,...,egyedi link,Várólisták,<foto>
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        doc_id = row['SEO név'].strip()
        if not doc_id:
            continue

        phone_raw = row['Telefonszám'].strip()
        phone = f'+36{phone_raw}' if phone_raw and not phone_raw.startswith('+') else phone_raw

        # Az utolsó (névtelen) oszlop tartalmazza a fotó URL-t
        foto = list(row.values())[-1].strip()

        fields = {
            'name':  {'stringValue': row['name'].strip()},
            'phone': {'stringValue': phone},
            'foto':  {'stringValue': foto},
            'datum': {'stringValue': '2026-05-28T00:00:00Z'},
        }
        status = upload_doc(doc_id, fields, token)
        icon = 'OK' if status in (200, 201) else 'HIBA'
        print(f'  [{icon}] {doc_id} ({row["name"]}) - HTTP {status}')

print('\nKész.')
