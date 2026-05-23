const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');

const GITHUB_TOKEN = defineSecret('GITHUB_TOKEN');

const OWNER  = 'JoSzaki';
const REPO   = 'minisite-kamerarendszer-budapest.hu';
const FILE   = 'index.html';
const BRANCH = 'master';

exports.saveMinisite = onRequest(
  { secrets: [GITHUB_TOKEN], cors: true, region: 'europe-west3', invoker: 'public' },
  async (req, res) => {
    // CORS preflight
    if (req.method === 'OPTIONS') {
      res.set('Access-Control-Allow-Origin', '*');
      res.set('Access-Control-Allow-Methods', 'POST');
      res.set('Access-Control-Allow-Headers', 'Content-Type');
      res.status(204).send('');
      return;
    }

    if (req.method !== 'POST') {
      res.status(405).json({ error: 'Method Not Allowed' });
      return;
    }

    const { html, winner_id } = req.body;
    if (!html) {
      res.status(400).json({ error: 'html mező kötelező' });
      return;
    }

    const token   = GITHUB_TOKEN.value();
    const apiUrl  = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${FILE}`;
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    };

    // 1. Aktuális fájl SHA lekérése (a GitHub API PUT-hoz kötelező)
    const getRes = await fetch(`${apiUrl}?ref=${BRANCH}`, { headers });
    if (!getRes.ok) {
      const detail = await getRes.text();
      console.error('GitHub GET failed:', detail);
      res.status(500).json({ error: 'GitHub GET sikertelen', detail });
      return;
    }
    const { sha } = await getRes.json();

    // 2. Fájl frissítése
    const content = Buffer.from(html).toString('base64');
    const putRes  = await fetch(apiUrl, {
      method: 'PUT',
      headers,
      body: JSON.stringify({
        message: `Megnyerte: ${winner_id || 'winner'} — oldal véglegesítve`,
        content,
        sha,
        branch: BRANCH,
      }),
    });

    if (!putRes.ok) {
      const detail = await putRes.text();
      console.error('GitHub PUT failed:', detail);
      res.status(500).json({ error: 'GitHub PUT sikertelen', detail });
      return;
    }

    console.log('Sikeresen feltöltve, winner_id:', winner_id);
    res.json({ ok: true, winner_id });
  }
);
