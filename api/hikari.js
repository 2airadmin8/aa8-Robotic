const DIFY_API_BASE = process.env.DIFY_API_BASE || 'https://api.dify.ai/v1';
const DIFY_API_KEY = process.env.DIFY_API_KEY || '';

const ALLOWED_ORIGINS = new Set([
  'https://robotics.air-admin8.co.jp',
  'https://2airadmin8.github.io',
  'https://hikari-proxy-dev-git-dev-ceo-2852s-projects.vercel.app',
  'http://localhost:3000',
  'http://127.0.0.1:3000'
]);

function isAllowedOrigin(origin) {
  if (!origin) return true;
  if (ALLOWED_ORIGINS.has(origin)) return true;
  return /^https:\/\/hikari-proxy-[a-z0-9-]+-ceo-2852s-projects\.vercel\.app$/i.test(origin);
}

function setCors(req, res) {
  const origin = req.headers.origin || '';
  if (isAllowedOrigin(origin) && origin) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
  }
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');
}

function cleanString(value, maxLength) {
  return String(value || '').trim().slice(0, maxLength);
}

export default async function handler(req, res) {
  setCors(req, res);

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });

  const origin = req.headers.origin || '';
  if (!isAllowedOrigin(origin)) {
    return res.status(403).json({ error: 'origin_not_allowed' });
  }

  if (!DIFY_API_KEY) {
    return res.status(503).json({ error: 'dify_api_key_not_configured' });
  }

  const query = cleanString(req.body?.query, 4000);
  const user = cleanString(req.body?.user, 160) || 'robotics-web';
  const conversationId = cleanString(req.body?.conversation_id, 200);
  const email = cleanString(req.body?.inputs?.email, 320);

  if (!query) return res.status(400).json({ error: 'query_required' });

  try {
    const upstream = await fetch(`${DIFY_API_BASE}/chat-messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: { email },
        query,
        response_mode: 'blocking',
        conversation_id: conversationId,
        user
      })
    });

    const payload = await upstream.json().catch(() => ({}));

    if (!upstream.ok) {
      console.error('Dify upstream error', upstream.status, payload?.code || payload?.message || 'unknown');
      return res.status(502).json({ error: 'dify_upstream_error', status: upstream.status });
    }

    const metadata = payload.metadata || {};
    const citations = metadata.retriever_resources || [];

    return res.status(200).json({
      answer: payload.answer || '',
      conversation_id: payload.conversation_id || '',
      message_id: payload.message_id || payload.id || '',
      citations
    });
  } catch (error) {
    console.error('HIKARI proxy error', error);
    return res.status(500).json({ error: 'proxy_error' });
  }
}
