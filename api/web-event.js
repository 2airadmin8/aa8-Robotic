const ALLOWED_ORIGINS = new Set([
  'https://robotics.air-admin8.co.jp',
  'https://2airadmin8.github.io'
]);

const ALLOWED_EVENTS = new Set([
  'pdf_open',
  'lead_page_view',
  'lead_product_click',
  'product_view'
]);

function setCors(req, res) {
  const origin = req.headers.origin || '';
  if (ALLOWED_ORIGINS.has(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
  }
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');
}

function readBody(req) {
  if (typeof req.body === 'object' && req.body !== null) return req.body;
  if (typeof req.body === 'string') {
    try { return JSON.parse(req.body); } catch (_) { return {}; }
  }
  return {};
}

function cleanText(value, maxLen) {
  if (typeof value !== 'string') return '';
  return value.trim().slice(0, maxLen);
}

export default function handler(req, res) {
  setCors(req, res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'method_not_allowed' });

  const body = readBody(req);
  const event = cleanText(body.event, 64);
  const deliveryId = cleanText(body.delivery_id, 160);

  if (!ALLOWED_EVENTS.has(event)) {
    return res.status(400).json({ ok: false, error: 'invalid_event' });
  }
  if (!/^DLV-[A-Za-z0-9._-]+$/.test(deliveryId)) {
    return res.status(400).json({ ok: false, error: 'invalid_delivery_id' });
  }

  const record = {
    schema: 'aa8_web_event_v1',
    received_at: new Date().toISOString(),
    event,
    delivery_id: deliveryId,
    page_path: cleanText(body.page_path, 500),
    page_type: cleanText(body.page_type, 80),
    product_id: cleanText(body.product_id, 160),
    target_product_id: cleanText(body.target_product_id, 160),
    document_name: cleanText(body.document_name, 160),
    source: 'robotics_web'
  };

  console.log('AA8_WEB_EVENT ' + JSON.stringify(record));
  return res.status(204).end();
}
