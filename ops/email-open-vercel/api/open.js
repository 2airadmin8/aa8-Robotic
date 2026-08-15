// AirAdmin8 Email Open Tracking endpoint
// Production runtime: Vercel
// Public endpoint: https://aa8-email-open-test.vercel.app/api/open
//
// mode=pixel -> 1x1 transparent GIF for production tracking
// mode=logo  -> branded test image (runtime deployment currently embeds AA8 logo)
// sid        -> 送信管理ID

const PIXEL_GIF = Buffer.from(
  'R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==',
  'base64'
);

export default function handler(req, res) {
  const sid = String(req.query.sid || '').trim();
  const mode = String(req.query.mode || 'pixel').trim().toLowerCase();
  const isTest = String(req.query.test || '') === '1';
  const openedAt = new Date().toISOString();
  const ua = String(req.headers['user-agent'] || '');
  const ip = String(req.headers['x-forwarded-for'] || '')
    .split(',')[0]
    .trim();

  console.log(JSON.stringify({
    event: 'email_open',
    sid,
    mode,
    is_test: isTest,
    opened_at: openedAt,
    ua,
    ip
  }));

  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');
  res.setHeader('X-Robots-Tag', 'noindex');

  // Production tracking path.
  // The deployed Vercel version also supports mode=logo for visible AA8 test verification.
  res.setHeader('Content-Type', 'image/gif');
  return res.status(200).send(PIXEL_GIF);
}
