# PRODUCTION.md — Teljes technikai dokumentáció

Ez a fájl minden részletet tartalmaz, ami az oldal nulláról való újraépítéséhez szükséges.

---

## 1. Infrastruktúra áttekintés

| Szolgáltatás | Projekt / Azonosító | Megjegyzés |
|---|---|---|
| Firebase projekt | `joszaki-minisite` | megosztott minden projekten |
| Firebase API key | `AIzaSyDfdCNl3LeuBT4xIYQPYluSVKKMFJTGVws` | publikus, client-side |
| Firestore REST endpoint | `https://firestore.googleapis.com/v1/projects/joszaki-minisite/databases/(default)/documents/` | |
| Cloud Function | `https://saveminisite-e3yxgwd3oq-ey.a.run.app` | europe-west3, megosztott |
| GitHub owner | `JoSzaki` | |
| GitHub repo (ez a projekt) | `minisite-kamerarendszer-budapest.hu` | branch: `master` |
| GitHub raw URL alap | `https://raw.githubusercontent.com/JoSzaki/{repo}/master/index.html` | |
| GCS bucket | `gs://joszaki-assets/minisite_assests/` | figyelj: `assests` (typo, de ez az éles) |
| GCS public URL alap | `https://storage.googleapis.com/joszaki-assets/minisite_assests/` | |
| Domain | `kamerearendszer-budapest.hu` | GitHub Pages, CNAME fájl |
| Admin jelszó | `joszaki2025admin` | |
| Visszahívási szám (erdekel.html) | `+36303911638` | |

---

## 1b. Új projekt pipeline — teljes lépéssorozat

### Pre-build kérdések (build előtt kötelező kitölteni)

| # | Kérdés | Példa |
|---|---|---|
| 1 | Szakma neve (egyes szám)? | `lakatos` |
| 2 | Domain neve? | `lakatoszolgalat-budapest.hu` |
| 3 | GitHub repo neve? | `minisite-lakatoszolgalat-budapest.hu` |
| 4 | Firestore profil kollekció neve? | `joszaki_lakatos` |
| 5 | Firestore érdeklődő kollekció neve? | `joszaki_lakatos_erdekel` |
| 6 | Admin jelszó (projekt-specifikus, erős)? | |
| 7 | **Visszahívási telefonszám** (erdekel.html thanks state)? | `+36 30 391-1638` |
| 8 | **aggregateRating ratingValue** (valós szám!)? | `4.9` |
| 9 | **aggregateRating reviewCount** (valós szám!)? | `187` |
| 10 | Scroll animáció forrás videó (MP4 vagy WebM)? **Fehér obj. sötét háttéren kell!** | `animacio.mp4` |
| 11 | **`%%FRAME_COUNT%%`** — automatikusan kiderül az ffmpeg után, nem kell előre tudni | `97` |
| 12 | **`%%HERO_STAT_1_SZAM%%`** — első hero stat szám | `340+` |
| 13 | **`%%HERO_STAT_1_LABEL%%`** — első hero stat felirat | `Elvégzett telepítés` |
| 14 | **`%%HERO_STAT_2_SZAM%%`** — második hero stat szám | `8 év` |
| 15 | **`%%HERO_STAT_2_LABEL%%`** — második hero stat felirat | `Fővárosi tapasztalat` |
| 16 | **`%%STAT_STRIP_1_LABEL%%`** — stats-strip 1. felirat | `Telepített rendszer` |
| 17 | **`%%STAT_STRIP_2_SZAM%%`** / **`%%STAT_STRIP_2_LABEL%%`** | `23` / `Budapesti Kerületben` |
| 18 | **`%%STAT_STRIP_3_LABEL%%`** — stats-strip 3. felirat | `Fővárosi tapasztalat` |
| 19 | Entity-AEO oldal (entity-tabs struktúra) kell? | igen / nem |
| 20 | Kampány indítási datum (datum mező a Firestore-ba)? | `2026-06-10T00:00:00Z` |

---

### Pipeline lépései

#### Lépés 1 — GitHub repo létrehozása
```bash
gh repo create JoSzaki/minisite-{domain} --public
```

#### Lépés 2 — Könyvtár inicializálása
```bash
mkdir {domain}
# template/ mappa tartalmát másold át:
# index.html, erdekel.html, admin.html
# + css/style.css, js/main.js, profil.webp, firebase.json, .firebaserc, firestore.rules
```

#### Lépés 3 — SITE config és placeholderek cseréje

Az `index.html` tetején a `var SITE = { ... }` blokkban:
```javascript
domain, nev, telefon, telefonMegjelenit, varos, kerulet, szakmaJelzo,
schemaType, title, description, keywords, ogTitle, ogDesc, faqSchema
```
Frissíteni kell a JSON-LD-ben is:
- `aggregateRating.ratingValue` és `reviewCount` → **pre-build kérdés #8-9**
- `openingHoursSpecification` → szakmára jellemző nyitvatartás

Az `erdekel.html`-ben:
- `PROJEKT_COLLECTION`, `ERDEKEL_COLLECTION`, `DOMAIN` konstansok
- Thanks state visszahívási szám (hardcoded) → **pre-build kérdés #7**
- `href="tel:..."` a call button-on

Az `admin.html`-ben:
- `ADMIN_PW`, `GITHUB_REPO`, `PROJEKT_COLLECTION`, `ERDEKEL_COLLECTION` konstansok

#### Lépés 4 — Scroll animáció frames generálása

A canvas animáció 61 db JPEG frame-et vár a `./frames/` mappába (`f0001.jpg`…`f0061.jpg`, 1948×1060 px).

**Forrás:** fehér/világos objektum fekete vagy sötét háttéren (a canvas `ctx.filter='invert(1)'` + `mix-blend-mode:screen` a fehér hátteret eltünteti).

**Teljes workflow:**

**1. lépés — forrás MP4 → WebM konverzió** (`/mp4-to-webm` skill-lel):
```bash
ffmpeg -i forras_animacio.mp4 \
  -c:v libvpx-vp9 -crf 33 -b:v 0 \
  -deadline good -cpu-used 2 -row-mt 1 \
  -an \
  assembled-to-exploded-pingpong.webm
```
A `/mp4-to-webm` Claude skill automatikusan generálja ezt a parancsot. A "pingpong" verzió azt jelenti, hogy az animáció előre+visszafele fut (61 frame = ~30 frame előre + ~30 frame vissza), hogy zökkenőmentes legyen a loop.

**2. lépés — WebM → JPEG frame-ek kinyerése:**
```bash
mkdir frames
ffmpeg -i assembled-to-exploded-pingpong.webm frames/f%04d.jpg
```
- Felbontás: **1948×1060** (natív, nincs scale)
- Frame rate: **24 fps**
- Eredmény: **97 db** `f0001.jpg`…`f0097.jpg` (egyirányú: assembled → exploded)

**Miért JPEG frame-ek, nem live video?**
A scroll-driven animációhoz (frame = scroll pozíció) a video `pause()` + `currentTime` seek megbízhatatlan volt (lásd memory: `rAF+play loop működik; pause+seek nem`). A pre-loaded ImageBitmap megközelítés GPU-ready és frame-pontos.

**Forrásanyag követelmény:** fehér/világos objektum sötét vagy fekete háttéren. A canvas `ctx.filter='invert(1)'` + `mix-blend-mode:screen` kombináció a fekete hátteret átlátszóvá teszi (fekete → transparent screen blenddel), a fehér objektum marad látható.

#### Lépés 5 — Firestore rules ✅ automatikus

A `joszaki-minisite` Firebase projektben **univerzális regex-alapú szabályok** vannak élesben:

```
joszaki_[a-z]+          → read only  (profil kollekciók)
joszaki_[a-z]+_erdekel  → create + read  (érdeklődő kollekciók)
minden más              → tiltva
```

Új projektnél **semmi teendő** — a naming convention betartása elegendő:
- profil kollekció: `joszaki_{egyszó}` (pl. `joszaki_lakatos`)
- érdeklődő kollekció: `joszaki_{egyszó}_erdekel`

A kollekció maga automatikusan létrejön az első dokumentum íráskor (CSV feltöltéskor).

#### Lépés 6 — default-avatar.webp ellenőrzés a GCS-en

```bash
gsutil ls gs://joszaki-assets/minisite_assests/default-avatar.webp
```
Ha nincs: a `process_profile_images.py` `ensure_default_avatar()` funkciója feltölti automatikusan első futáskor.

Az összes HTML fallback (`/default-avatar.webp`) a gyökér-relatív URL-t használja — ez GitHub Pages-en a repo gyökeréből szolgál ki, tehát a `default-avatar.webp` fájlnak a repo gyökerében is kell lennie (symlink vagy másolat a GCS-ről letöltve).

#### Lépés 7 — Profilképek feldolgozása

```bash
python process_profile_images.py --limit 50
# Ha Google Sheet még nincs: python process_profile_images.py slug1 slug2 slug3
```
Előfeltétel: `C:/Temp/oauth_desktop.json` OAuth client fájl megvan.

#### Lépés 8 — CSV feltöltés Firestore-ba

```bash
# Joszaki.hu export alapján:
python upload_to_firestore.py szakemberek.csv --collection joszaki_{projekt}

# Kampány CSV alapján:
python upload_kampany.py kampany.csv --collection joszaki_{projekt}
```

#### Lépés 9 — GDPR oldal frissítése

A `gdpr-adatvedelem/index.html`-ben minden projekt-specifikus adatot a `SITE` config változókból kell kiszedni:
- Adatkezelő neve → `SITE.nev` (vagy a cég neve)
- Elérhetőség → `SITE.telefon`, `SITE.domain`
- Tevékenység leírása → `SITE.szakmaJelzo`

A GDPR szöveg **nem tartalmazhat hardcoded** cégnevet vagy telefonszámot — minden dinamikus értéket a SITE config-ból kell behelyettesíteni a sablon generálásakor.

#### Lépés 10 — Git push és GitHub Pages aktiválás

```bash
cd {projekt-mappa}
git init
git remote add origin https://github.com/JoSzaki/minisite-{domain}.git
git add .
git commit -m "Initial commit"
git push -u origin master
```
GitHub repo Settings → Pages → Source: `master`, folder: `/` → Save.
CNAME fájl a repo gyökerében: `{domain}` (egy sor, újsor nélkül).

#### Lépés 11 — Tesztelési checklist

- [ ] `/{domain}` → főoldal betölt, canvas animáció fut
- [ ] `/?id={slug}` → profil kártya megjelenik (fotó, név, telefon, hívógomb)
- [ ] `/?id=ismeretlen` → graceful fallback (nincs JS error)
- [ ] `/erdekel.html?id={slug}` → csendes mentés + thanks state megjelenik
- [ ] `/erdekel.html` (id nélkül) → form + submit → Firestore `_erdekel` kollekcióba ment
- [ ] `/admin.html` → jelszóval belép, profilok és érdeklődők listája tölt
- [ ] Megnyerte flow tesztelése → HTML módosítva + GitHub commit → visszaállítás git-tel
- [ ] Képek: fotó betölt GCS-ről, `/default-avatar.webp` fallback működik
- [ ] Firestore rules: böngészőből `DELETE` → 403 (rules éles)
- [ ] Mobile: nav, canvas, hívógomb, erdekel form

---

## 2. Firestore adatmodellek

### `joszaki_kamera` (profil kollekció)

| Mező | Típus | Leírás |
|---|---|---|
| `name` | stringValue | Teljes név, pl. `Kovács Péter` |
| `phone` | stringValue | E.164 formátum, pl. `+36301234567` |
| `foto` | stringValue | Teljes GCS URL vagy üres (fallback: `{id}.webp`) |
| `datum` | stringValue | ISO 8601, pl. `2026-05-28T00:00:00Z` |

Dokumentum ID = URL-safe slug, pl. `kovacs-peter-1`

### `joszaki_kamera_erdekel` (érdeklődő kollekció)

| Mező | Típus | Leírás |
|---|---|---|
| `nev` | stringValue | Érdeklődő neve |
| `telefon` | stringValue | Telefonszáma |
| `email` | stringValue | E-mail (opcionális) |
| `kerulet` | stringValue | Pl. `XIII. kerület` vagy `Pest megye` |
| `ref_id` | stringValue | Szakember slug (ha `?id=`-val jött), üres ha form |
| `domain` | stringValue | `kamerearendszer-budapest.hu` |
| `datum` | stringValue | ISO 8601 timestamp |

---

## 3. Firestore szabályok

```plaintext
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /joszaki_kamera/{doc} {
      allow read: if true;
    }
    match /joszaki_kamera_erdekel/{doc} {
      allow create: if true;
      allow read: if true;
      allow update, delete: if false;
    }
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

Deploy: `firebase deploy --only firestore:rules`

Új projekt hozzáadásakor az új kollekció nevét (`joszaki_{projekt}` és `joszaki_{projekt}_erdekel`) fel kell venni a szabályokba azonos mintával.

---

## 4. Cloud Function — `functions/index.js`

A függvény GitHub API-n keresztül felülírja az `index.html`-t a megnyerés után.

```javascript
const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');

const GITHUB_TOKEN  = defineSecret('GITHUB_TOKEN');
const ALLOWED_OWNER = 'JoSzaki';

exports.saveMinisite = onRequest(
  { secrets: [GITHUB_TOKEN], cors: true, region: 'europe-west3', invoker: 'public' },
  async (req, res) => {
    // OPTIONS preflight
    if (req.method === 'OPTIONS') { /* CORS headers + 204 */ return; }
    if (req.method !== 'POST') { res.status(405).json({ error: 'Method Not Allowed' }); return; }

    const { html, winner_id, owner, repo, branch = 'master' } = req.body;
    // Validáció: html, owner, repo kötelező; owner === 'JoSzaki'

    const token  = GITHUB_TOKEN.value();
    const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/index.html`;
    const headers = { 'Authorization': `Bearer ${token}`, 'Accept': 'application/vnd.github+json',
                      'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json' };

    // 1. SHA lekérés (szükséges a PUT-hoz)
    const { sha } = await fetch(`${apiUrl}?ref=${branch}`, { headers }).then(r => r.json());

    // 2. Fájl felülírása base64 content-tel
    await fetch(apiUrl, { method: 'PUT', headers, body: JSON.stringify({
      message: `Megnyerte: ${winner_id} — oldal véglegesítve`,
      content: Buffer.from(html).toString('base64'),
      sha, branch
    }) });

    res.json({ ok: true, winner_id, repo: `${owner}/${repo}` });
  }
);
```

**Deploy:**
```bash
cd functions && npm install && firebase deploy --only functions
```

**Secret beállítás** (egyszer, interaktív terminálban):
```bash
firebase functions:secrets:set GITHUB_TOKEN
```
A token a Firebase Secret Manager-ben él, nem env fájlban. Minden `JoSzaki/` repóra működik.

**`functions/package.json` függőségek:**
```json
{
  "engines": { "node": "20" },
  "dependencies": {
    "firebase-functions": "^6.x"
  }
}
```

---

## 5. `index.html` — teljes struktúra

### 5.1 SITE config blokk (oldal tetején, `<head>`-ben)

```javascript
var SITE = {
  domain:            'kamerearendszer-budapest.hu',
  nev:               'Kovács Péter',          // ← Megnyertékor cserélődik
  telefon:           '+3612345678',            // ← Megnyertékor cserélődik
  telefonMegjelenit: '+36-1-234-5678',         // ← Megnyertékor cserélődik
  varos:             'Budapest',
  kerulet:           'XIII. kerület',
  szakmaJelzo:       'Biztonságtechnikai szakértő',
  schemaType:        'LocalBusiness',
  title:             'Kamerarendszer telepítés Budapesten | Profi biztonságtechnika 2025',
  description:       '...',
  keywords:          '...',
  ogTitle:           '...',
  ogDesc:            '...',
  faqSchema:         [ { q: '...', a: '...' }, ... ]
};
```

Közvetlenül utána fut egy IIFE, ami a `document.head`-be írja: `<meta>` tageket, `canonical` linket, `og:*` tageket, `LocalBusiness` és `FAQPage` JSON-LD structured data-t.

### 5.2 Design system — CSS változók

```css
:root {
  --navy:       #1a3a6b;
  --navy-dark:  #0f2347;
  --navy-light: #1e4d8c;
  --red:        #e8390e;
  --red-dark:   #c42d0a;
  --cream:      #f1f5f9;
  --white:      #ffffff;
  --text:       #334155;
  --text-mid:   #64748b;
  --text-light: #94a3b8;
  --warm:       #c4955a;
  --warm-light: #d9b07e;
  --border:     rgba(0,0,0,0.08);
  --border-light: rgba(255,255,255,0.08);
  --success:    #16a34a;
  --ff-display: 'Cormorant Garamond', Georgia, serif;
  --ff-body:    'Manrope', system-ui, sans-serif;
  --ease:       cubic-bezier(0.23, 1, 0.32, 1);
}
```

**Google Fonts betöltés:**
```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### 5.3 Oldal szekciók (HTML struktúra)

```
<body>
  <nav class="nav">                          ← sticky, scrolled osztály JS-ből
  <section id="fooldal" class="hero">       ← ← ez az ID kell a canvas animációnak
    <canvas id="scrollAnimCanvas" ...>      ← mix-blend-mode: screen
    <div class="hero-inner">
      <div class="hero-text">...</div>
      <div class="hero-cred">              ← jobb oldali kártya
        <div class="cred-form">            ← ?id= nélkül látszik
        <div class="cred-profile">         ← ?id= esetén látszik
          <img id="profilImg">
          <div class="cred-name dyn-name">
          <a class="cred-phone-num dyn-phone">
  <section class="stats-strip">
  <section id="szolgaltatasok">            ← szolgáltatás kártyák
  <section id="folyamat" class="sec-dark"> ← 4-lépéses process track
  <section id="elonyok">                  ← USP grid
  <section id="referenciak">              ← testimonials
  <section class="cta-band">
  <section id="faq">
  <section id="kapcsolat">
  <footer>
  <div id="fabBtn">                        ← FAB "Hívjon" gomb — Megnyertékor törlődik
  <div id="editSaveBar" ...>              ← inline szerkesztő save bar (rejtett)

  <!-- Firebase IIFE script -->
  <script>(function(){
    ... 'documents/joszaki_kamera/' ...
    ... if (!id) return ...               ← e két sor alapján azonosítja az admin
  })();</script>

  <!-- Canvas animáció script -->
  <script>(function(){
    var hero = document.getElementById('fooldal');
    var cvs  = document.getElementById('scrollAnimCanvas');
    // FRAME_COUNT = 61, frames: ./frames/f0001.jpg … ./frames/f0061.jpg
    // drawFrame: ctx.filter='invert(1)' + mix-blend-mode:screen → fehér háttér eltűnik
    // onScroll: frac = -rect.top / (rect.height * 0.4), idx = round(frac * 60)
  })();</script>
</body>
```

### 5.4 Firebase IIFE — dinamikus profil betöltés

Az `index.html` alján lévő IIFE **két módban** fut, `?id=` query param alapján:

**`?id=` nélkül (lista mód):**
- Betölti az összes dokumentumot a `joszaki_kamera` kollekcióból
- A `.cred-form` div-et megjeleníti
- Listázza a szakembereket linkkel: `/?id={slug}`

**`?id={slug}`-gal (profil mód):**
- Lekéri az egy dokumentumot: `GET .../joszaki_kamera/{id}?key=...`
- `.cred-profile` div-et megjeleníti
- `#profilImg` src = `foto` mező, fallback GCS URL
- `.dyn-name` elemekbe → `name` mező
- `.dyn-phone` elemekbe → `phone` mező
- `href="tel:..."` linkekbe → phone E.164

Az IIFE azonosítója az admin számára (törléshez):
```javascript
s.textContent.includes('documents/joszaki_kamera/') &&
s.textContent.includes('if (!id) return')
```

### 5.5 Inline szerkesztő mód

Az `index.html`-ben van egy inline edit mód (Megnyerés után finomhangoláshoz):
- `initEditMode()` — jelszó prompt, majd `contentEditable` minden `p/h*` elemen
- `saveEdits()` — POST a Cloud Functionre (`SAVE_URL`)
- Konstansok: `SAVE_URL`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_BRANCH` — az oldal aljáról

### 5.6 Canvas scroll animáció

```javascript
var FRAME_COUNT = 61;
// Képek: ./frames/f0001.jpg … ./frames/f0061.jpg (1948×1060 px)
// preload: ImageBitmap (GPU-ready)
// onScroll: frac = max(0, min(1, -rect.top / (rect.height * 0.4)))
//           idx  = round(frac * 60)
// drawFrame: ctx.filter='invert(1)' → fehér pixelek feketék lesznek
//            mix-blend-mode: screen a canvas-on → fekete = átlátszó, fehér = látható
```

---

## 6. `erdekel.html` — érdeklődő rögzítő

**Konstansok:**
```javascript
const FB_KEY             = 'AIzaSyDfdCNl3LeuBT4xIYQPYluSVKKMFJTGVws';
const FB_BASE            = 'https://firestore.googleapis.com/v1/projects/joszaki-minisite/databases/(default)/documents/';
const PROJEKT_COLLECTION = 'joszaki_kamera';
const ERDEKEL_COLLECTION = 'joszaki_kamera_erdekel';
const DOMAIN             = 'kamerearendszer-budapest.hu';
const id                 = new URLSearchParams(location.search).get('id');
```

**Két mód:**

`?id=` van → csendes mentés `joszaki_kamera_erdekel`-be (nev+telefon a Firestore profilból, kerulet üres), azonnal thanks state.

`?id=` nincs → form jelenik meg (nev, telefon, email, kerület dropdown I–XXIII + Pest megye), submit → mentés `joszaki_kamera_erdekel`-be, thanks state.

**Thanks state:** zöld pipa + `Hívjon most: 30/391-1638` animált call gomb (`tel:+36303911638`).

**Design:** Manrope font, navy/red/green CSS változók, teljes vertikális centering, max-width 480px fehér kártya.

---

## 7. `admin.html` — adminisztrációs panel

**Konstansok:**
```javascript
const FB_KEY             = 'AIzaSyDfdCNl3LeuBT4xIYQPYluSVKKMFJTGVws';
const FB_BASE            = 'https://firestore.googleapis.com/v1/projects/joszaki-minisite/databases/(default)/documents/';
const ADMIN_PW           = 'joszaki2025admin';
const SAVE_URL           = 'https://saveminisite-e3yxgwd3oq-ey.a.run.app';
const GITHUB_OWNER       = 'JoSzaki';
const GITHUB_REPO        = 'minisite-kamerarendszer-budapest.hu';
const GITHUB_BRANCH      = 'master';
const PROJEKT_COLLECTION = 'joszaki_kamera';
const ERDEKEL_COLLECTION = 'joszaki_kamera_erdekel';
const GITHUB_RAW         = 'https://raw.githubusercontent.com/' + GITHUB_OWNER + '/' + GITHUB_REPO + '/' + GITHUB_BRANCH + '/index.html';
```

**Betöltés flow:**
1. Login screen → jelszó check (`ADMIN_PW`) → `loadAll()`
2. `loadProfiles()` → GET `FB_BASE + PROJEKT_COLLECTION + '?key=' + FB_KEY`
3. `loadLeads()` → GET `FB_BASE + ERDEKEL_COLLECTION + '?key=' + FB_KEY`
4. Profil táblázat: Előnézet gomb (`/?id={id}`), Megnyerte gomb, Törlés gomb
5. Érdeklődő táblázat: nev, telefon, email, kerulet, ref_id, datum, Törlés

**`doMegnyerte()` — lépések sorban:**

```
1. fetch(GITHUB_RAW) → nyers HTML szöveg
2. DOMParser → doc
3a. var SITE → nev, telefon, telefonMegjelenit regex-replace
3b. doc.querySelectorAll('.dyn-name') → textContent = p.name
3c. doc.querySelectorAll('.dyn-phone') → textContent = p.phone
    doc.querySelectorAll('a[href^="tel:"]') → href = 'tel:+36...'
3d. Firebase IIFE keresés és eltávolítás:
    s.textContent.includes('documents/joszaki_kamera/') &&
    s.textContent.includes('if (!id) return')
3e. doc.getElementById('fabBtn').remove()
3f. új <script>if(location.search)history.replaceState(null,'',location.pathname);</script> → body végére
3g. ha p.foto: doc.getElementById('profilImg').setAttribute('src', p.foto)
4. '<!DOCTYPE html>\n' + doc.documentElement.outerHTML → newHtml
5. POST SAVE_URL → { html: newHtml, winner_id: p.id, owner, repo, branch }
6. DELETE minden más profil a joszaki_kamera kollekcióból
```

**Telefon formázás megnyertékor:**
```javascript
const telDisp = p.phone.replace(/(\+36)(\d{2})(\d{3})(\d{4})/, '$1-$2-$3-$4');
// pl. +36301234567 → +36-30-123-4567
```

---

## 8. Python scriptek

### 8.1 `upload_to_firestore.py`

Célja: joszaki.hu alapú CSV → Firestore feltöltés (töröl mindent, majd újratölt).

**Használat:**
```bash
python upload_to_firestore.py <csv_file> [--collection <kollekció>]

# Példák:
python upload_to_firestore.py szakemberek.csv
python upload_to_firestore.py szakemberek.csv --collection joszaki_lakatos
```

**CSV formátum (joszaki.hu export):**
```
link, id, name, email, Telefonszám, SEO név, Székhely, ..., egyedi link, Várólisták, <foto URL>
```
- `doc_id` = `row['SEO név']`
- `phone` = `+36` + maradék (ha nem `+`-szal kezdődik)
- `foto` = az utolsó névtelen oszlop (`list(row.values())[-1]`)
- `datum` = hardcoded `'2026-05-28T00:00:00Z'`

**Auth:** `gcloud auth print-access-token` → Bearer token Firestore REST API-hoz. Előfeltétel: `gcloud auth login`.

### 8.2 `upload_kampany.py`

Célja: kampány CSV → Firestore (csak mintaadatokat töröl, majd feltölt).

**Használat:**
```bash
python upload_kampany.py <csv_file> [--collection <kollekció>]

# Példák:
python upload_kampany.py kampany.csv
python upload_kampany.py kampany.csv --collection joszaki_lakatos
```

**CSV formátum:**
```
id, name, mobile, kép
```
- `phone` = `format_phone(mobile)` → `+36` + 9 jegyű szám
- ha `kép` üres vagy tartalmaz `default-avatar` → GCS `default-avatar.png` kerül

**Töröl** a `SAMPLE_IDS` listában lévő mintaprofilokat (`kovacs-peter-1` stb.), majd PATCH minden sort.

### 8.3 `process_profile_images.py`

Célja: joszaki.hu → rembg háttér eltávolítás → GCS upload → Google Sheet URL visszaírás.

**Konstansok:**
```python
GCS_BUCKET        = 'gs://joszaki-assets/minisite_assests/'
GCS_PUBLIC_BASE   = 'https://storage.googleapis.com/joszaki-assets/minisite_assests/'
SHEET_ID          = '1WM2IOBZqdTLEsNnTYBrwSIDwlZddBetVg0Cv01rGrnU'
SHEET_GID         = '1184434414'
DEFAULT_AVATAR_URL = 'https://joszaki.hu/_nuxt/img/default-avatar.9677c28.png'
GSUTIL            = r'C:\Users\Szabó Norbert\AppData\Local\Google\Cloud SDK\...\gsutil.cmd'
OAUTH_CLIENT_PATH  = 'C:/Temp/oauth_desktop.json'
OAUTH_TOKEN_PATH   = 'C:/Temp/oauth_token.json'
```

**Lépések egy slugra:**
1. GET `https://joszaki.hu/szakember/{slug}` → BeautifulSoup → `<img src="...storage.googleapis...">` → `_256.jpg` → `_512.jpg`
2. Download kép, `Image.open` (Pillow)
3. `img.thumbnail((512, 512))` + `img.save(path, 'WEBP', quality=90)`
4. `gsutil -h Content-Type:image/webp cp {local} gs://.../minisite_assests/{slug}.webp`
5. `worksheet.update_cell(row_index, 11, public_url)` → Google Sheets Column 11

**Sheet-ből kihagyja a már kitöltött sorokat** (Column 11 nem üres), kivéve `--cleanup` esetén.

**Python csomagok:**
```bash
pip install gspread google-auth google-auth-oauthlib requests beautifulsoup4 Pillow
```
(A `rembg`/`onnxruntime` opcionális — a jelenlegi kód Pillow-t használ, nem rembg-t)

---

## 9. Statikus tartalom oldalak

Az alábbi könyvtárak statikus SEO-oldalakat tartalmaznak, amelyek a `css/style.css` és `js/main.js` fájlokra hivatkoznak:

```
blog/                     ← 5+ cikk (pl. hikvision-kamera, ip-kamera-rendszer, stb.)
arak/                     ← árak és csomagok
kapcsolat/                ← elérhetőségek
rolunk/                   ← bemutatkozás
szerviz/                  ← szerviz és karbantartás
referenciak/              ← ügyfél vélemények
ipari-kamerarendszer/
otthoni-kamerarendszer/
tarsashazi-kamerarendszer/
uzleti-kamerarendszer/
telepites/
gdpr-adatvedelem/
```

Ezek **nem** importálják a Firebase SDK-t. A `css/style.css` és `js/main.js` csak ezeken az oldalakon aktív — az `index.html`, `erdekel.html` és `admin.html` inline CSS/JS-t használ.

---

## 10. GitHub Pages konfiguráció

- `CNAME` fájl a repo gyökerében: `kamerearendszer-budapest.hu`
- GitHub Pages source: `master` branch, root `/`
- Deploy automatikus minden `master` push után

---

## 11. Teljes rendszer flow diagram

```
[CSV feltöltés]
upload_to_firestore.py / upload_kampany.py
         ↓
Firestore: joszaki_kamera kollekció
         ↓
[Profilkép pipeline]
process_profile_images.py
joszaki.hu → resize → WebP → GCS
         ↓
gs://joszaki-assets/minisite_assests/{slug}.webp
         ↓
[Kampány e-mail]
Link: kamerearendszer-budapest.hu/?id={slug}
         ↓
index.html — Firebase IIFE betölti a profilt
  - ?id= van → profil kártya + hívógomb
  - ?id= nincs → szakember lista
         ↓
[Érdeklődés]
/erdekel.html?id={slug}
  → Firestore: joszaki_kamera_erdekel
         ↓
[Admin döntés]
/admin.html → jelszó → Megnyerte gomb
         ↓
doMegnyerte():
  1. fetch GitHub raw HTML
  2. DOM: nev, telefon, foto hardkódolás
  3. Firebase IIFE törlése
  4. FAB törlése + redirect script
  5. POST → Cloud Function (europe-west3)
  6. Cloud Function → GitHub API PUT
  7. DELETE többi Firestore profil
         ↓
GitHub Pages auto-deploy (1-2 perc)
         ↓
[Végleges statikus oldal — nincs Firebase]
```

---

## 12. Visszaállítás Megnyerés után (teszteléshez)

```bash
git log --oneline -5                           # megkeresed az előző commitot
git checkout {hash} -- index.html              # csak index.html visszaállítása
git add index.html
git commit -m "Restore dynamic state"
git push
```

Firestore profil kollekció manuális feltöltése utána: `python upload_kampany.py`

---

## 13. Entitás-alapú egyoldalas bemutatkozó (AEO / E-E-A-T sablon) — bármely szakmára újrahasznosítható

Ez a szekció egy **újrahasznosítható egyoldalas (one-pager) sablont** ír le, amely egy konkrét
szakembert vagy vállalkozást mutat be **kérdés-alapú szakaszokban** (Q&A heading struktúra).
Célja az **AEO** (Answer Engine Optimization) és az **entity SEO**: az LLM-ek és a Google
entitás-grafikonja számára egyértelműen leírja, *ki* az adott szakember, *mit* csinál, *hol*,
és *mi a kapcsolata* a fő témához (`main_topic`).

A sablon **profession-agnosztikus**: az eredeti minta jogász-specifikus szókincset használt
(„law", „litigation", „bar membership"), ezt **változókra** cseréltük. Egy új projektnél
csak a változókat kell kitölteni — a heading-hierarchia (H1→H4) **soha nem változik**.

> Ez illeszthető a meglévő rendszerbe: lehet **önálló one-pager** (`index.html` egy mikrosite-on),
> vagy a minisite **`rolunk/` / `bemutatkozas/`** aloldala. A `css/style.css` + `js/main.js`
> párost használja (lásd 9. szekció), nem a Firebase IIFE-t.

---

### 13.1 Változók (placeholderek) — ezt kell kitölteni minden új projektnél

Minden szöveges placeholder `[szögletes_zárójelben]` áll. Egy projekt indításakor töltsd ki
ezt a táblázatot **először**, utána a find/replace mechanikus.

| Változó | Leírás | Példa (SOS villanyszerelés) | Példa (biztosítótábla csere) |
|---|---|---|---|
| `[person_name]` | A szakember teljes neve | `Kovács Zoltán` | `Nagy Tamás` |
| `[entity_name]` | A vállalkozás / brand neve | `VillanyGyors` | `BizTábla Pro` |
| `[profession]` | A szakma megnevezése (foglalkozás) | `villanyszerelő` | `villanyszerelő` |
| `[profession_field]` | A szakág / szakterület (tevékenység) | `villanyszerelés` | `villanyszerelés` |
| `[main_topic]` | A fő szolgáltatás / téma (a landing fókusza) | `SOS villanyszerelés` | `biztosítótábla csere` |
| `[city]` | Elsődleges város / székhely | `Budapest` | `Debrecen` |
| `[service_area]` | Ellátott terület | `Budapest és Pest megye` | `Hajdú-Bihar megye` |
| `[entity_type]` | schema.org típus | `Electrician` | `Electrician` |
| `[phone]` | Telefonszám (E.164) | `+36301234567` | `+36209876543` |
| `[email]` | E-mail | `info@villanygyors.hu` | `kapcsolat@biztabla.hu` |
| `[domain]` | Domain | `sos-villanyszereles-budapest.hu` | `biztositotabla-csere.hu` |

**Toldalékfigyelmeztetés (magyar):** a placeholder + magyar toldalék (pl. `[person_name]t`,
`[main_topic]ról`) **nem fog mindig helyes lenni** a magánhangzó-harmónia és a hangrend miatt.
A generáláskor a toldalékot a tényleges szóhoz kell igazítani (pl. *Kovács Zoltánt*,
*biztosítótábla cseréről*). Ezt a generáló lépés (13.7) explicit feladatként kezeli.

---

### 13.2 Szókincs-csere szótár (jogász-minta → semleges → bármely szakma)

Az eredeti jogász-minta kifejezéseinek általánosítása. Ezt használd, ha új szakmát
illesztesz be — a bal oldali fogalmat a középső placeholderrel, majd a konkrét szakma
szavával helyettesíted.

| Eredeti (jogász) | Semleges placeholder | Példa (villanyszerelés) |
|---|---|---|
| lawyer | `[profession]` | villanyszerelő |
| law / legal field | `[profession_field]` | villanyszerelés |
| areas of law | `[profession_field]` szakterületek | villanyszerelési szakterületek |
| law firms / institutions | cégek / intézmények | kivitelezők / cégek |
| notable cases | kiemelkedő munkák / projektek | kiemelkedő munkák |
| legal community | szakmai közösség | villanyszerelő szakma |
| bar memberships / legal associations | kamarai tagság / szakmai szövetség | MKEH / kamarai tagság |
| jurisdictions | ellátott területek | ellátott területek / városok |
| universities / law schools | iskolák / képzések | szakiskola / OKJ képzés |
| legal trainings / certifications | képesítések / tanúsítványok | érintésvédelmi minősítés |
| client representation / case strategy | ügyfélmunka / munkavégzés | helyszíni felmérés / kivitelezés |
| negotiation & litigation | árazás & problémamegoldás | árazás & hibakeresés |
| ethics in legal practice | átláthatóság & minőség | átláthatóság & garancia |
| advocating for justice | minőségi munka / ügyfél segítése | gyors, biztonságos megoldás |
| case evaluation | árajánlat / felmérés | ingyenes árajánlat |
| virtual / online legal services | online konzultáció / foglalás | online időpontfoglalás |

---

### 13.3 A 40 szakasz — generikus heading-sablon (a szintek KÖTÖTTEK)

Az alábbi a teljes vázszerkezet. A bal oszlop a **DOM heading szint** (ezt soha ne változtasd),
a jobb oldali a **magyar fejléc** placeholderekkel. A H4 elemek a felettük lévő H3 **alpontjai** —
a hierarchiát a HTML-ben is tartsd (ne lapítsd ki). Minden fejléc után közvetlenül egy
**válaszbekezdés** jön (lásd 13.4).

| # | Szint | Magyar fejléc (placeholderekkel) |
|---|---|---|
| 1 | **H1** | Ki az a [person_name]? |
| 2 | **H2** | Mi [person_name] szakmai háttere? |
| 3 | H3 | Mi inspirálta [person_name]t, hogy [profession] legyen? |
| 4 | H3 | Milyen [profession_field] szakterületekre specializálódott [person_name]? |
| 5 | H3 | Mi [person_name] küldetése és jövőképe a [profession_field] terén? |
| 6 | H3 | Hogyan határozza meg [person_name] a sikert a [profession_field] munkában? |
| 7 | H3 | Milyen [person_name] szakmai pályafutása? |
| 8 | H3 | Mely cégekkel vagy intézményekkel dolgozott [person_name]? |
| 9 | H4 | Melyek [person_name] kiemelkedő munkái vagy eredményei? |
| 10 | H3 | Hogyan járult hozzá [person_name] a [profession] szakmai közösséghez? |
| 11 | H3 | Melyek [person_name] fontosabb elismerései, díjai vagy referenciái? |
| 12 | H4 | Tagja-e [person_name] szakmai szövetségnek vagy kamarának? |
| 13 | **H2** | Hol dolgozik jelenleg [person_name]? |
| 14 | H3 | Honnan származik [person_name]? |
| 15 | H4 | Helyben, régiósan vagy országosan dolgozik [person_name]? |
| 16 | **H2** | Mely területeket vagy városokat szolgálja ki [person_name]? |
| 17 | H3 | Milyen [person_name] szakmai képzettsége? |
| 18 | H4 | Mely iskolákban vagy képzéseken vett részt [person_name]? |
| 19 | H4 | Milyen képesítéseket, tanúsítványokat vagy speciális képzéseket szerzett [person_name]? |
| 20 | H4 | Hogyan tartja naprakészen [person_name] a tudását a változó szabványok, előírások és technológiák terén? |
| 21 | **H2** | Milyen [profession_field] szolgáltatásokat kínál [person_name]? |
| 22 | H3 | Hogyan közelíti meg [person_name] az ügyfélmunkát és a munkavégzést? |
| 23 | H3 | Milyen ügyfél- vagy ingatlantípusokat szolgál ki jellemzően [person_name]? |
| 24 | H3 | Mi [person_name] filozófiája az árazásról és a problémamegoldásról? |
| 25 | H3 | Hogyan biztosítja [person_name] az átláthatóságot és a minőséget a [profession_field] során? |
| 26 | H3 | Mit gondol [person_name] a(z) [main_topic] témáról? |
| 27 | H3 | Hogyan látja [person_name] a(z) [main_topic] jövőjét a [profession_field] terén? |
| 28 | **H2** | Milyen újításokról gondolja [person_name], hogy átalakítják a [profession_field] szakmát? |
| 29 | H3 | Hogyan használja [person_name] a technológiát és a modern eszközöket a [profession_field] során? |
| 30 | H3 | Mi [person_name] véleménye az ügyfelek tájékoztatásáról és tudatosságáról? |
| 31 | **H2** | Melyek [person_name] pályafutásának vezérelvei? |
| 32 | H3 | Milyen kedvenc idézetek vagy mottók inspirálják [person_name]t? |
| 33 | H3 | Mely szakmai vezetőket vagy mentorokat tisztel [person_name]? |
| 34 | H3 | Mi motiválja [person_name]t, hogy folyamatosan minőségi munkát végezzen? |
| 35 | **H2** | Hogyan egyensúlyozza [person_name] a szakmai kiválóságot az ügyfélközpontúsággal? |
| 36 | H3 | Melyek [person_name] / [entity_name] hivatalos közösségi média fiókjai? |
| 37 | H3 | Hol találhatók [person_name] cikkei, referenciái vagy interjúi? |
| 38 | H3 | Hogyan lehet kapcsolatba lépni [person_name]nal konzultáció céljából? |
| 39 | **H2** | Hogyan lehet időpontot foglalni vagy árajánlatot kérni [person_name]tól? |
| 40 | H3 | Kínál-e [person_name] online konzultációt vagy online foglalást? |

**Heading-szint összesítő (validációhoz):** H1×1, H2×8 (#2,13,16,21,28,31,35,39), H4×6 (#9,12,15,18,19,20), a többi H3.
Generálás után ezt **ellenőrizd** — a szintek elcsúszása rontja az outline-t és az AEO-parszolást.

---

### 13.4 Válaszírási szabályok (AEO answer-block)

Minden fejléc után **közvetlen válaszbekezdés** áll. Ezek a szabályok döntik el, hogy egy
LLM idézi-e az oldalt forrásként:

1. **Első mondat = önálló válasz.** Az első mondat a fejléc kérdésére *önmagában* feleljen,
   és tartalmazza az entitást: `[person_name]` + `[profession]` + `[city]`.
   Pl. *„[person_name] budapesti [profession], aki a(z) [main_topic] területre szakosodott."*
2. **Ne kezdj „Igen / Nem"-mel.** Mondd ki a teljes állítást (a kérdés szavait visszhangozva).
3. **Egy szakasz = 40–90 szó**, egy bekezdés vagy rövid (3–5 elemű) lista. Ne ömlessz.
4. **Entitás-grounding:** természetes ismétléssel hozd vissza a `[person_name]`, `[main_topic]`,
   `[city]`, `[service_area]` kulcsszavakat — kulcsszóhalmozás nélkül.
5. **Konkrét számok > általánosságok:** évek tapasztalata, kiszállási idő, garancia hónapok,
   ellátott kerületek száma. A számok idézhetők.
6. **H4 = a szülő H3 mélyítése.** A H4 válasz ne ismételje a H3-at, hanem részletezze.
7. **A #26–27 (`[main_topic]`) a topikális mag** — ide kerüljön a legtöbb szakmai mélység,
   mert ez köti az entitást a kulcsszóhoz.

---

### 13.5 Structured data (JSON-LD) — entitás-grafikon

A `<head>`-be (a meglévő SITE IIFE mintájára, lásd 5.1) **három** JSON-LD blokk kerül:

1. **`Person`** — a szakember mint entitás (ez a sablon lényege):
```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "[person_name]",
  "jobTitle": "[profession]",
  "knowsAbout": ["[main_topic]", "[profession_field]"],
  "worksFor": { "@type": "[entity_type]", "name": "[entity_name]" },
  "areaServed": "[service_area]",
  "alumniOf": "…(18-19. szakasz)",
  "telephone": "[phone]",
  "email": "[email]",
  "sameAs": ["…socials (36. szakasz)"],
  "url": "https://[domain]/"
}
```
2. **`[entity_type]` / `LocalBusiness`** — a vállalkozás (a meglévő minisite `LocalBusiness`
   mintáját követi, `name`, `telephone`, `areaServed`, `address`, `openingHours`).
3. **`FAQPage`** — mind a 40 fejléc → `Question`, a válaszbekezdés → `acceptedAnswer`.

> **Megjegyzés a FAQ rich resultról:** a Google 2023 óta a FAQ rich snippetet jellemzően
> csak hatósági/egészségügyi oldalakon jeleníti meg, így itt **látható rich result nem garantált**.
> A `FAQPage` markup itt elsősorban az **AEO/LLM-parszolást és az entitás-megértést** segíti —
> ezért érdemes kitenni, de nem ez a fő cél. A `Person` + `[entity_type]` a primer.

---

### 13.6 Technikai felépítés — illeszkedés a meglévő rendszerhez

A one-pager tetejére kerül egy **`ENTITY` config blokk** (a SITE config mintájára, 5.1),
hogy a find/replace egy helyen történjen:

```javascript
var ENTITY = {
  person_name:     'Kovács Zoltán',
  entity_name:     'VillanyGyors',
  profession:      'villanyszerelő',
  profession_field:'villanyszerelés',
  main_topic:      'SOS villanyszerelés',
  city:            'Budapest',
  service_area:    'Budapest és Pest megye',
  entity_type:     'Electrician',   // schema.org
  phone:           '+36301234567',
  email:           'info@villanygyors.hu',
  domain:          'sos-villanyszereles-budapest.hu'
};
```

- **CSS/JS:** a `css/style.css` + `js/main.js` párost használja (design tokenek, nav, footer,
  FAQ accordion, scroll animáció) — **nem** importál Firebase SDK-t.
- **DOM:** a 40 fejléc egymás után, `<section>` elemekben **H2 szinten lapítva** (a 9. szekció
  szemantikai szabálya), a H3/H4 a szekciókon **belül** ágyazva.
- **Opcionális dinamizmus:** ha a szakember neve/telefonja a kampány alatt még változó
  (`?id=` flow), a `[person_name]`/`[phone]` helyére `.dyn-name`/`.dyn-phone` osztály kerülhet,
  és a Megnyerte flow (CLAUDE.md) ugyanúgy hardkódolja — de ez **opcionális**, alapból statikus.

---

### 13.7 Újragenerálási munkafolyamat (Claude Code-nak, lépésről lépésre)

Új szakma + entitás esetén:

1. **Töltsd ki a 13.1 változótáblát** a konkrét projektre (12 érték).
2. **Másold** a sablon one-pager `index.html`-jét az új projekt mappájába.
3. **Find/replace** a 13.1 placeholderekre — `[person_name]`, `[main_topic]` stb.
4. **Toldalék-pass:** menj végig a fejléceken és a válaszokon, és **javítsd a magyar toldalékokat**
   a tényleges szavakhoz (vowel harmony) — `[main_topic]ról` → *…cseréről* / *…szerelésről*.
5. **Töltsd ki a 40 válaszbekezdést** a 13.4 szabályok szerint (a #26–27 kapja a legtöbb mélységet).
6. **Frissítsd a 3 JSON-LD blokkot** (13.5) a konkrét adatokkal; a `sameAs` és `alumniOf`
   a 18–19. és 36. szakasz tartalmából jöjjön.
7. **Validáld a heading-szinteket** a 13.3 összesítő ellen (H1×1, H2×8, H4×6).
8. **`<title>` / meta / canonical** a `[domain]`-ra és `[main_topic]`-ra.
9. Helyi teszt (`npx serve .`), majd deploy a meglévő GitHub Pages flow szerint (10. szekció).

---

### 13.8 Kidolgozott példa — „SOS villanyszerelés", Kovács Zoltán / VillanyGyors

A 40 fejléc kitöltve (csak a fejlécek; a válaszokat a 13.4 szerint kell megírni).
Figyeld a **javított toldalékokat**.

```
H1   Ki az a Kovács Zoltán?
H2   Mi Kovács Zoltán szakmai háttere?
H3     Mi inspirálta Kovács Zoltánt, hogy villanyszerelő legyen?
H3     Milyen villanyszerelési szakterületekre specializálódott Kovács Zoltán?
H3     Mi Kovács Zoltán küldetése és jövőképe a villanyszerelés terén?
H3     Hogyan határozza meg Kovács Zoltán a sikert a villanyszerelő munkában?
H3     Milyen Kovács Zoltán szakmai pályafutása?
H3     Mely cégekkel vagy intézményekkel dolgozott Kovács Zoltán?
H4       Melyek Kovács Zoltán kiemelkedő munkái vagy eredményei?
H3     Hogyan járult hozzá Kovács Zoltán a villanyszerelő szakmai közösséghez?
H3     Melyek Kovács Zoltán fontosabb elismerései, díjai vagy referenciái?
H4       Tagja-e Kovács Zoltán szakmai szövetségnek vagy kamarának?
H2   Hol dolgozik jelenleg Kovács Zoltán?
H3     Honnan származik Kovács Zoltán?
H4       Helyben, régiósan vagy országosan dolgozik Kovács Zoltán?
H2   Mely területeket vagy városokat szolgálja ki Kovács Zoltán?
H3     Milyen Kovács Zoltán szakmai képzettsége?
H4       Mely iskolákban vagy képzéseken vett részt Kovács Zoltán?
H4       Milyen képesítéseket, tanúsítványokat vagy speciális képzéseket szerzett Kovács Zoltán?
H4       Hogyan tartja naprakészen Kovács Zoltán a tudását a változó szabványok, előírások és technológiák terén?
H2   Milyen villanyszerelési szolgáltatásokat kínál Kovács Zoltán?
H3     Hogyan közelíti meg Kovács Zoltán az ügyfélmunkát és a munkavégzést?
H3     Milyen ügyfél- vagy ingatlantípusokat szolgál ki jellemzően Kovács Zoltán?
H3     Mi Kovács Zoltán filozófiája az árazásról és a problémamegoldásról?
H3     Hogyan biztosítja Kovács Zoltán az átláthatóságot és a minőséget a villanyszerelés során?
H3     Mit gondol Kovács Zoltán az SOS villanyszerelésről?
H3     Hogyan látja Kovács Zoltán az SOS villanyszerelés jövőjét a villanyszerelés terén?
H2   Milyen újításokról gondolja Kovács Zoltán, hogy átalakítják a villanyszerelő szakmát?
H3     Hogyan használja Kovács Zoltán a technológiát és a modern eszközöket a villanyszerelés során?
H3     Mi Kovács Zoltán véleménye az ügyfelek tájékoztatásáról és tudatosságáról?
H2   Melyek Kovács Zoltán pályafutásának vezérelvei?
H3     Milyen kedvenc idézetek vagy mottók inspirálják Kovács Zoltánt?
H3     Mely szakmai vezetőket vagy mentorokat tisztel Kovács Zoltán?
H3     Mi motiválja Kovács Zoltánt, hogy folyamatosan minőségi munkát végezzen?
H2   Hogyan egyensúlyozza Kovács Zoltán a szakmai kiválóságot az ügyfélközpontúsággal?
H3     Melyek Kovács Zoltán / VillanyGyors hivatalos közösségi média fiókjai?
H3     Hol találhatók Kovács Zoltán cikkei, referenciái vagy interjúi?
H3     Hogyan lehet kapcsolatba lépni Kovács Zoltánnal konzultáció céljából?
H2   Hogyan lehet időpontot foglalni vagy árajánlatot kérni Kovács Zoltántól?
H3     Kínál-e Kovács Zoltán online konzultációt vagy online foglalást?
```

Ugyanez a váz **„biztosítótábla csere", Nagy Tamás / BizTábla Pro** projektre: csak a 13.1
táblát töltöd újra, a `[main_topic]` = `biztosítótábla csere`, és a #26 fejléc lesz
*„Mit gondol Nagy Tamás a biztosítótábla cseréről?"* — a váz azonos.

---

### 13.9 Indítási checklist (új projekt)

- [ ] 13.1 változótábla kitöltve (12 érték)
- [ ] sablon `index.html` átmásolva, find/replace kész
- [ ] toldalék-pass lefutott (magyar ragozás javítva)
- [ ] 40 válaszbekezdés megírva (13.4 szabályok, #26–27 a legmélyebb)
- [ ] 3 JSON-LD blokk (Person + [entity_type] + FAQPage) kitöltve és validálva
- [ ] heading-szintek ellenőrizve (H1×1, H2×8, H4×6)
- [ ] `<title>`, meta, canonical, og:* a domainre állítva
- [ ] `css/style.css` + `js/main.js` hivatkozva, Firebase SDK **nincs** importálva
- [ ] helyi teszt + GitHub Pages deploy (10. szekció)

---

### 13.10 Tabos megjelenítés — a 8 H2-téma fülekre bontva

Az egyoldalas blokk **tabos (fül-alapú) felületen** is megjeleníthető. A 8 darab **H2** lesz a
8 fül; minden fül **maximum 2 szavas címkét** kap. Egy fülre kattintva az adott **H2 + a hozzá
tartozó összes H3/H4 alkérdés** bontódik ki (a H2 a következő H2-ig „birtokolja" az alkérdéseit).
**Alapból az első téma (Háttér) van nyitva.** A H1 (`#1`) a fülek **fölött**, fejlécként marad —
ez a lap entitás-horgonya, nem fül.

Referencia implementáció (kész, működő fájl): **`entity-tabs.html`**.

#### Fül → H2 leképezés (a címkék profession-agnosztikusak, bármely szakmára jók)

| Fül | Címke (max 2 szó) | H2 (szakasz #) | Birtokolt alkérdések |
|---|---|---|---|
| 01 | **Háttér** | #2 — Mi [person_name] szakmai háttere? | #3–#12 |
| 02 | **Helyszín** | #13 — Hol dolgozik jelenleg [person_name]? | #14–#15 |
| 03 | **Ellátott terület** | #16 — Mely területeket szolgálja ki [person_name]? | #17–#20 |
| 04 | **Szolgáltatások** | #21 — Milyen [profession_field] szolgáltatásokat kínál? | #22–#27 |
| 05 | **Jövőkép** | #28 — Milyen újításokról gondolja [person_name]…? | #29–#30 |
| 06 | **Vezérelvek** | #31 — Melyek [person_name] vezérelvei? | #32–#34 |
| 07 | **Szemlélet** | #35 — Hogyan egyensúlyozza a kiválóságot…? | #36–#38 |
| 08 | **Kapcsolat** | #39 — Hogyan lehet időpontot foglalni…? | #40 |

> A címkék témaalapúak, ezért **nem kell szakmánként cserélni** őket (a *biztosítótábla csere*
> projektben is `Háttér / Helyszín / … / Kapcsolat`). Csak ha egy projektnél más a hangsúly,
> akkor finomítsd (pl. `Jövőkép` → `Innováció`).

#### Kötelező DOM-struktúra

A fülek és a panelek `aria` attribútumokkal vannak összekötve (`id` ↔ `aria-controls` /
`aria-labelledby`). A **H2 a panelen belül marad** (szemantikailag továbbra is H2), a H3/H4
alkérdések alatta, a 13.3 hierarchia szerint.

```html
<div class="tabs-shell">
  <div class="tablist" role="tablist" aria-label="Bemutatkozás témakörök">
    <button class="tab" role="tab" id="tab-0" aria-controls="panel-0" aria-selected="true">
      <span class="ix">01</span>Háttér</button>
    <!-- … tab-1 … tab-7, aria-selected="false" -->
  </div>
</div>

<main class="panels">
  <section class="panel active" id="panel-0" role="tabpanel" aria-labelledby="tab-0">
    <h2 class="panel-h2">Mi [person_name] szakmai háttere?</h2>
    <p class="panel-lead">…közvetlen válasz (13.4)…</p>
    <div class="qa"><h3>…#3…</h3><p>…</p></div>
    <!-- … #4–#11 … -->
    <div class="qa sub"><h4>…#9 / #12 (H4 = behúzva)…</h4><p>…</p></div>
  </section>
  <!-- panel-1 … panel-7 (active osztály nélkül) -->
</main>
```

#### JS — fülváltó logika

Egyetlen `activate(i)` függvény: beállítja az `aria-selected`-et, ki/be kapcsolja a panel
`active` osztályát (ami `display:block` + belépő animáció), és kezeli a billentyűzetet.

```javascript
(function(){
  var tabs   = [].slice.call(document.querySelectorAll('.tab'));
  var panels = [].slice.call(document.querySelectorAll('.panel'));

  function activate(i, focus){
    tabs.forEach(function(t,k){
      t.setAttribute('aria-selected', k===i ? 'true':'false');
      t.tabIndex = k===i ? 0 : -1;
    });
    panels.forEach(function(p,k){
      if(k===i){ p.classList.remove('active'); void p.offsetWidth; p.classList.add('active'); } // animáció újraindítás
      else p.classList.remove('active');
    });
    if(focus){ tabs[i].focus(); tabs[i].scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'}); }
  }

  tabs.forEach(function(tab,i){
    tab.addEventListener('click', function(){ activate(i,false); });
    tab.addEventListener('keydown', function(e){
      var n=tabs.length;
      if(e.key==='ArrowRight'||e.key==='ArrowDown'){ e.preventDefault(); activate((i+1)%n,true); }
      else if(e.key==='ArrowLeft'||e.key==='ArrowUp'){ e.preventDefault(); activate((i-1+n)%n,true); }
      else if(e.key==='Home'){ e.preventDefault(); activate(0,true); }
      else if(e.key==='End'){ e.preventDefault(); activate(n-1,true); }
    });
  });

  activate(0,false);   // alapból az első téma nyitva
})();
```

#### CSS — a lényeges szabályok

```css
.tabs-shell{position:sticky;top:0;z-index:20;background:rgba(241,245,249,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}
.tablist{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none}   /* mobilon vízszintes görgetés */
.tablist::-webkit-scrollbar{display:none}
.tab{appearance:none;background:none;border:none;cursor:pointer;color:var(--text-mid);font-weight:600;padding:18px 18px 16px;white-space:nowrap;position:relative}
.tab::after{content:"";position:absolute;left:14px;right:14px;bottom:0;height:3px;background:var(--red);transform:scaleX(0);transition:transform .35s var(--ease)}
.tab[aria-selected="true"]{color:var(--navy-dark)}
.tab[aria-selected="true"]::after{transform:scaleX(1)}            /* aktív fül piros aláhúzás */
.panel{display:none}
.panel.active{display:block}
.qa.sub{margin-left:22px;padding-left:22px;border-left:2px solid var(--border)}  /* H4 alárendelés */
```

#### Akadálymentesség és viselkedés

- **ARIA:** `role="tablist" / "tab" / "tabpanel"`, `aria-selected`, `aria-controls`,
  `aria-labelledby`. Az inaktív fülek `tabIndex=-1` (roving tabindex).
- **Billentyűzet:** ←/→ (és ↑/↓) fülváltás, Home/End az első/utolsó fülre.
- **Mobil:** a tabsor vízszintesen görgethető, az aktív fül `scrollIntoView`-val középre ugrik.
- **Belépő animáció:** panelváltáskor a H2 és a `.qa` blokkok staggered (lépcsőzött) `rise`
  animációval jelennek meg.

#### SEO / AEO megjegyzés (FONTOS)

A rejtett panelek **`display:none`-nal** vannak elrejtve, **nem lazy-loadolva** — a teljes
40 szakasz **benne van a HTML forrásban** a kezdeti betöltéskor. Ezért a Google és az LLM-ek
**mind a 8 témát látják és indexelik**, a tabozás csak vizuális. Ne cseréld JS-ből betöltött
(fetch utáni) tartalomra a paneleket, mert azzal elveszne az AEO-érték.

> Opció: ha kell egy „Összes megnyitása" / nyomtatás nézet, tegyél egy kapcsolót, ami minden
> `.panel`-re ráteszi az `active` osztályt (vagy egy `body.expand-all .panel{display:block}` szabályt).

#### Illeszkedés a 13.7 munkafolyamatba

A tabos verzió nem változtat a generálási lépéseken — ugyanaz a 40 szakasz, csak panelekbe
csoportosítva. A 13.7 lépései után:

10. **Csoportosítsd** a 40 szakaszt a fenti fül-leképezés szerint 8 `.panel`-be (H2 = panel kezdete).
11. **Add hozzá** a `.tablist`-et 8 `role="tab"` gombbal és a fenti JS-t.
12. **Ellenőrizd**, hogy a teljes tartalom a forrásban van (nincs fetch-elt panel), és az első panel `active`.
