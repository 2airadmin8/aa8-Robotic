import OpenAI from 'openai';

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const buckets = new Map();

const PRODUCT_CONTEXT = `
AirAdmin8 Roboticsの公開サイト相談用コンテキスト。
主要製品の役割:
- Unitree G1-D: 研究用データ取得、遠隔操作、模倣学習・VLA、実機評価。
- Unitree G1: 全身運動、操作研究、模倣学習・強化学習、教育研究。
- Unitree Go2: 四足歩行、巡回・点検、地形認識、センシング、二次開発。
- AGIBOT X2 EDU: 組立・調整、運動制御、ROS 2二次開発、授業・PBL・研究入門。
- AGIBOT X2 REC: 全身遠隔操作、データ収集、模倣学習・VLA、実機評価。
- AGIBOT G2: 精密操作、産業PoC、力制御、具身AI研究。
- AGIBOT A3: 長時間運用、案内・教育・展示・サービス、複数台運用。
- AGIBOT A2 Ultra: 研究・案内・対話・自律移動を想定するフルサイズヒューマノイド。
AirAdmin8の支援範囲: 現状調査、要件定義、製品選定、システム構成、PoC、環境構築、納品・検収、運用保守。
`;

function allow(ip) {
  const now = Date.now();
  const entry = buckets.get(ip) || { count: 0, reset: now + 60_000 };
  if (now > entry.reset) { entry.count = 0; entry.reset = now + 60_000; }
  entry.count += 1; buckets.set(ip, entry);
  return entry.count <= 20;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });
  const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown').split(',')[0].trim();
  if (!allow(ip)) return res.status(429).json({ error: 'rate_limited' });
  if (!process.env.OPENAI_API_KEY) return res.status(503).json({ error: 'chat_not_configured' });

  const message = String(req.body?.message || '').trim().slice(0, 1000);
  const page = String(req.body?.page || '').slice(0, 200);
  if (!message) return res.status(400).json({ error: 'empty_message' });

  const instructions = `
あなたはAirAdmin8 Robotics公式サイトのAIロボット相談アシスタントです。
目的は、相談者が製品・研究テーマ・PoC・導入条件を整理し、次の行動を判断できるようにすることです。
${PRODUCT_CONTEXT}
必須ルール:
1. 日本語で、簡潔かつ専門的に答える。
2. 製品の比較・研究用途・一般的なシステム構成・公開SDK/資料の案内は回答してよい。
3. 価格、値引き、在庫、納期、契約条件、保証範囲、性能保証、PSE・技適等の法令適合を確定しない。これらは「担当者確認が必要」と明示する。
4. メーカー公式仕様とAirAdmin8の提案・見解を混同しない。
5. 不明な仕様を推測しない。
6. 個人情報の入力を要求しない。具体相談を人へ引き継ぐ場合のみ、問い合わせフォームへの移動を案内する。
7. 回答の最後に、必要なら次に確認すべき2〜4項目を提示する。
現在ページ: ${page}
`;

  try {
    const response = await client.responses.create({
      model: process.env.OPENAI_CHAT_MODEL || 'gpt-5.6',
      instructions,
      input: message,
      store: false,
      max_output_tokens: 700,
    });
    return res.status(200).json({ answer: response.output_text || '担当者確認が必要です。お問い合わせをご利用ください。' });
  } catch (error) {
    console.error('chat_error', error?.message || error);
    return res.status(502).json({ error: 'chat_failed' });
  }
}
