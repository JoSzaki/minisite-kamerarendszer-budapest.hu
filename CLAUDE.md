# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# MiniSite Rendszer — Fejlesztői Útmutató

## Mi ez?

E-mail kampányokhoz készített, Firebase-alapú dinamikus landing page rendszer.
Minden kampányhoz egy statikus HTML oldal + Firestore névlista + Cloud Function.

Egy szakember a saját `?id=` linkjén keresztül látja az oldalt a saját nevével, telefonjával, fotójával.
Ha megveszi az oldalt, az admin "Megnyerte" gombbal véglegesíti: hardkódolja az adatait és leválasztja a Firebase-ről.

**Teljes technikai dokumentáció (adatmodellek, JS kód, flow diagram, Python scriptek):** [`PRODUCTION.md`](PRODUCTION.md)

---

## Parancsok

```bash
# Helyi fejlesztés — statikus fájlok kiszolgálása
npx serve .                          # vagy bármilyen static file server

# Firebase deploy
firebase deploy --only firestore:rules   # csak firestore.rules
cd functions && npm install && firebase deploy --only functions   # Cloud Function

# Szakember adatok feltöltése Firestore-ba
python upload_to_firestore.py szakemberek.csv
python upload_to_firestore.py szakemberek.csv --collection joszaki_lakatos
python upload_kampany.py kampany.csv
python upload_kampany.py kampany.csv --collection joszaki_lakatos

# Profilképek pipeline (joszaki.hu → háttér eltávolítás → GCS)
python process_profile_images.py              # minden sor
python process_profile_images.py --limit 50  # első 50 sor
python process_profile_images.py slug1 slug2 # konkrét slugok

# GitHub token secret beállítás (interaktív, külső terminálban kell!)
firebase functions:secrets:set GITHUB_TOKEN
```

**Python csomagok:** `pip install gspread google-auth Pillow requests rembg onnxruntime google-cloud-storage`

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

---

## Fájlstruktúra és architektúra

```
projekt-mappa/
├── index.html              ← főoldal (dinamikus Firebase betöltéssel)
├── erdekel.html            ← érdeklődő-rögzítő (noindex)
├── admin.html              ← admin panel (noindex)
├── profil.webp             ← fallback profilkép placeholder
├── css/style.css           ← megosztott CSS (design system, nav, footer, komponensek)
├── js/main.js              ← megosztott JS (nav toggle, FAQ accordion, scroll animáció)
├── firebase.json           ← Firebase konfig (megosztott)
├── .firebaserc             ← Firebase projekt hivatkozás
├── firestore.rules         ← Firestore biztonsági szabályok
├── functions/              ← Cloud Function (MEGOSZTOTT — ne másold!)
│   └── index.js            ← index.html-t GitHub-ra mentő endpoint
├── template/               ← Sablon fájlok új projektekhez (ne deployold!)
├── upload_to_firestore.py  ← CSV → Firestore feltöltő
├── upload_kampany.py       ← kampány CSV → Firestore feltöltő
├── process_profile_images.py ← joszaki.hu → rembg → GCS pipeline
└── blog/, arak/, kapcsolat/, rolunk/, szerviz/, referenciak/
    ipari-kamerarendszer/, otthoni-kamerarendszer/,
    tarsashazi-kamerarendszer/, uzleti-kamerarendszer/, telepites/
                            ← Statikus SEO-tartalom oldalak (css/style.css + js/main.js)
```

### css/style.css és js/main.js

Ezeket **minden statikus tartalom oldal** (blog, arak, stb.) használja közösen. Az `index.html`, `erdekel.html` és `admin.html` viszont inline CSS/JS-t tartalmaz — nem hivatkoznak ezekre.

- `css/style.css`: design token-ek CSS változókkal, nav, footer, kártyák, gombók, reszponzív (1024px, 640px breakpointok)
- `js/main.js`: hamburger menü, FAQ accordion, active nav link, smooth scroll, számláló animáció (Intersection Observer)

### index.html két módja

- **`?id=` nélkül**: betölti a `joszaki_kamera` Firestore kollekciót, szakember-listát jelenít meg
- **`?id={slug}`-gal**: az adott szakember profilját tölti be, megjeleníti nevét/telefonját/fotóját és a hívógombot

A Firebase betöltő IIFE az `if (!id) return` feltétellel azonosítható — ez alapján találja meg és törli az admin a "Megnyerte" flow-ban.

A hero szekcióban canvas-alapú scroll-animáció fut (`#scrollAnimCanvas`), az `assembled-to-exploded-pingpong.webm` videóból kinyert framekből.

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
| `%%RATING_VALUE%%` | aggregateRating értéke | `4.9` |
| `%%REVIEW_COUNT%%` | Google értékelések száma | `187` |
| `%%FRAME_COUNT%%` | Canvas animáció frame-ek száma | `97` |
| `%%HERO_STAT_1_SZAM%%` | Hero első stat szám | `340+` |
| `%%HERO_STAT_1_LABEL%%` | Hero első stat felirat | `Elvégzett telepítés` |
| `%%HERO_STAT_2_SZAM%%` | Hero második stat szám | `8 év` |
| `%%HERO_STAT_2_LABEL%%` | Hero második stat felirat | `Fővárosi tapasztalat` |
| `%%STAT_STRIP_1_LABEL%%` | Stats-strip 1. sor felirata | `Telepített rendszer` |
| `%%STAT_STRIP_2_SZAM%%` | Stats-strip 2. sor száma | `23` |
| `%%STAT_STRIP_2_LABEL%%` | Stats-strip 2. sor felirata | `Budapesti Kerületben` |
| `%%STAT_STRIP_3_LABEL%%` | Stats-strip 3. sor felirata | `Fővárosi tapasztalat` |
| `%%SAVE_URL%%` | Cloud Function URL (megosztott, fix érték) | `https://saveminisite-e3yxgwd3oq-ey.a.run.app` |

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

`index.html` Firebase IIFE-ben:
```javascript
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

### 5. Firestore rules frissítése
Az új kollekcióhoz add hozzá a szabályokat `firestore.rules`-ban, majd:
```bash
firebase deploy --only firestore:rules
```

### 6. Szakember CSV feltöltése Firestore-ba
```bash
python upload_to_firestore.py   # COLLECTION változó a script tetején
```

### 7. Tesztelés
- `/?id={szakember-id}` — profil betöltés ellenőrzése
- `/erdekel.html?id={szakember-id}` — érdeklődés rögzítés
- `/admin.html` — admin panel, profilok listája

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

CSV formátum (upload_to_firestore.py):
```csv
id,name,phone,foto
kovacs-peter-1,Kovács Péter,+36301234567,https://storage.googleapis.com/...
```

CSV formátum (upload_kampany.py):
```csv
id,name,mobile,kép
```

- `id`: URL-safe slug, egyedi a collection-on belül
- `foto`/`kép`: opcionális GCS URL; ha üres, fallback: `joszaki-assets/minisite_assests/{id}.webp`
