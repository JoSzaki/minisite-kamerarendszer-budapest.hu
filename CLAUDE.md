# MiniSite Rendszer — Fejlesztői Útmutató

## Mi ez?

E-mail kampányokhoz készített, Firebase-alapú dinamikus landing page rendszer.
Minden kampányhoz egy statikus HTML oldal + Firestore névlista + Cloud Function.

Egy szakember a saját `?id=` linkjén keresztül látja az oldalt a saját nevével, telefonjával, fotójával.
Ha megveszi az oldalt, az admin "Megnyerte" gombbal véglegesíti: hardkódolja az adatait és leválasztja a Firebase-ről.

---

## Infrastruktúra (MEGOSZTOTT — minden projektnél ugyanez)

| Elem | Érték |
|---|---|
| Firebase projekt | `joszaki-minisite` |
| Firebase API key | `AIzaSyDfdCNl3LeuBT4xIYQPYluSVKKMFJTGVws` |
| Cloud Function URL | `https://saveminisite-e3yxgwd3oq-ey.a.run.app` |
| Cloud Function régió | `europe-west3` (Frankfurt) |
| GitHub owner | `JoSzaki` |
| GCS fotó bucket | `https://storage.googleapis.com/joszaki-assets/minisite_assests/{id}.webp` |

**Cloud Function deploy:** `cd functions && npm install && firebase deploy --only functions`
**GitHub token secret:** `firebase functions:secrets:set GITHUB_TOKEN` (interaktív, külső terminálban)

---

## Placeholderek — amit ki kell tölteni minden új projektnél

| Placeholder | Leírás | Példa |
|---|---|---|
| `%%DOMAIN%%` | A webhely domainje | `kamerearendszer-budapest.hu` |
| `%%PROJEKT_COLLECTION%%` | Firestore profil-kollekció | `joszaki_kamera` |
| `%%ERDEKEL_COLLECTION%%` | Firestore érdeklődő-kollekció | `joszaki_kamera_erdekel` |
| `%%GITHUB_OWNER%%` | GitHub felhasználónév | `JoSzaki` |
| `%%GITHUB_REPO%%` | GitHub repo neve | `minisite-kamerarendszer-budapest.hu` |
| `%%ADMIN_PASSWORD%%` | Admin panel jelszava | (egyedi, erős jelszó) |
| `%%SITE_NEV%%` | Oldal/brand neve | `KameraRendszer Budapest` |
| `%%SITE_SLOGAN%%` | Rövid szlogen | `Profi biztonságtechnika` |
| `%%SZAKMA_JELZO%%` | A szakember szerepköre | `Kamerarendszer szakértő` |
| `%%VAROS%%` | Város | `Budapest` |

---

## Új projekt létrehozásának lépései

### 1. GitHub repo létrehozása
```
gh repo create JoSzaki/minisite-{domain} --public
```
**FONTOS:** Minden projektnek saját repo kell. Soha ne felülírd a meglévőt.

### 2. Template másolása
A `template/` mappából másold a következő fájlokat az új projekt mappájába:
- `index.html` — a főoldal (tartalom projekt-specifikus, de placeholderek generikusak)
- `erdekel.html` — érdeklődő-rögzítő oldal
- `admin.html` — adminisztrációs panel

### 3. Placeholderek kitöltése

**Minden fájlban cseréld ki (`%%PROJEKT_COLLECTION%%` stb.):**

`index.html`:
```javascript
// Firebase IIFE-ben:
'databases/(default)/documents/%%PROJEKT_COLLECTION%%/'
// → cseréld pl. 'joszaki_lakatos/' -ra
```

`erdekel.html` és `admin.html` tetején:
```javascript
const PROJEKT_COLLECTION = '%%PROJEKT_COLLECTION%%';  // pl. 'joszaki_lakatos'
const ERDEKEL_COLLECTION = '%%ERDEKEL_COLLECTION%%';  // pl. 'joszaki_lakatos_erdekel'
const GITHUB_OWNER       = '%%GITHUB_OWNER%%';        // 'JoSzaki'
const GITHUB_REPO        = '%%GITHUB_REPO%%';         // 'minisite-lakatos-budapest.hu'
const ADMIN_PW           = '%%ADMIN_PASSWORD%%';      // erős egyedi jelszó
```

**Naming convention kollekciókhoz:**
- Profil: `joszaki_{projekt}` pl. `joszaki_kamera`, `joszaki_lakatos`, `joszaki_viz`
- Érdeklődők: `joszaki_{projekt}_erdekel` pl. `joszaki_kamera_erdekel`

### 4. Git inicializálás és push
```bash
cd uj-projekt-mappa
git init
git remote add origin https://github.com/JoSzaki/minisite-{domain}.git
git add .
git commit -m "Initial commit"
git push -u origin master
```

### 5. Szakember CSV feltöltése Firestore-ba
Szerkeszd a `sample_szakemberek.csv`-t az új adatokkal, majd:
```bash
python upload_to_firestore.py
```
A script tetején állítsd be a helyes `COLLECTION` értéket!

### 6. Tesztelés
- `/?id={szakember-id}` — profil betöltés ellenőrzése
- `/erdekel.html?id={szakember-id}` — érdeklődés rögzítés
- `/admin.html` — admin panel, profilok listája

---

## Fájlstruktúra

```
projekt-mappa/
├── index.html              ← főoldal (dinamikus Firebase betöltéssel)
├── erdekel.html            ← érdeklődő-rögzítő (noindex)
├── admin.html              ← admin panel (noindex)
├── profil.webp             ← fallback profilkép placeholder
├── css/style.css           ← (ha külső CSS-t használsz)
├── js/main.js              ← (ha külső JS-t használsz)
├── sample_szakemberek.csv  ← CSV az upload scripthez
├── upload_to_firestore.py  ← feltöltő script
├── firebase.json           ← Firebase konfig (megosztott)
├── .firebaserc             ← Firebase projekt hivatkozás
├── functions/              ← Cloud Function (MEGOSZTOTT — ne másold!)
│   ├── index.js
│   └── package.json
└── template/               ← Sablon fájlok új projektekhez
    ├── index.html
    ├── erdekel.html
    └── admin.html
```

---

## Párhuzamos projektek — kollekció névtáblázat

| Projekt | Repo | Profil kollekció | Érdeklődő kollekció |
|---|---|---|---|
| kamerearendszer-budapest.hu | minisite-kamerarendszer-budapest.hu | `joszaki_kamera` | `joszaki_kamera_erdekel` |
| *(következő projekt)* | minisite-{domain} | `joszaki_{projekt}` | `joszaki_{projekt}_erdekel` |

**Mindig töltsd ki ezt a táblázatot mielőtt új projektet indítasz!**

---

## Megnyerte flow — hogyan működik

1. Admin megnyitja `admin.html`, belép jelszóval
2. Látja a Firestore `PROJEKT_COLLECTION` szakembereket
3. Rákattint "Megnyerte" → megerősítő modal
4. A modal elvégzi:
   - Letölti az `index.html`-t a GitHub raw URL-ről
   - DOM-ban: kicseréli `.dyn-name` / `.dyn-phone` elemeket
   - Frissíti a SITE config `nev`, `telefon`, `telefonMegjelenit` mezőit
   - Eltávolítja a Firebase IIFE scriptet
   - Eltávolítja a `#fabBtn` FAB gombot
   - Hozzáad redirect scriptet (`?id=` → főoldal)
   - POST → Cloud Function (`SAVE_URL`) → GitHub API → `index.html` frissítve
   - Törli az összes többi profilt a `PROJEKT_COLLECTION`-ből

**Visszaállítás teszt után:**
```bash
git checkout {előző_commit_hash} -- index.html
git add index.html && git commit -m "Restore dynamic state" && git push
```

---

## Firebase IIFE azonosítása (Megnyerte törléshez)

Az admin a következő feltételekkel azonosítja és törli a Firebase IIFE scriptet:
```javascript
s.textContent.includes('documents/' + PROJEKT_COLLECTION + '/') && 
s.textContent.includes('if (!id) return')
```
**Ezért fontos**, hogy minden projekt saját collection nevet használjon —
különben az admin más projekt IIFE-jét azonosíthatná tévesen.

---

## Figyelmeztetések

- **Soha ne használd ugyanazt a Firestore collection nevet két projektben** — keresztbe írják egymás adatait
- **Soha ne push-old manuálisan a Cloud Function URL-t** — az a `firebase deploy` után adott URL, ne cseréld más projektre
- **A GitHub token (`GITHUB_TOKEN` secret) megosztott** — minden projektre működik, de csak `JoSzaki` owner alatti repókat enged
- **Az admin.html jelszava projektenként különböző legyen** — ha valaki megszerzi, csak azt az egy projektet érinti
- **A `template/` mappát ne deployold** — csak fejlesztési referencia

---

## CSV feltöltő script használata

```bash
# COLLECTION változót állítsd be a script tetején!
python upload_to_firestore.py
```

CSV formátum:
```csv
id,name,phone,foto
kovacs-peter-1,Kovács Péter,+36301234567,https://storage.googleapis.com/...
```

- `id`: URL-safe slug, egyedi a collection-on belül
- `foto`: opcionális GCS URL; ha üres, fallback: `joszaki-assets/minisite_assests/{id}.webp`
