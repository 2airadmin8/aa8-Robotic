(() => {
  'use strict';

  const cfg = window.HIKARI_CONFIG || {};
  const endpoint = String(cfg.endpoint || '').trim();
  const userId = localStorage.getItem('hikari_user_id') || `web-${crypto.randomUUID?.() || Date.now()}`;
  localStorage.setItem('hikari_user_id', userId);
  let conversationId = localStorage.getItem('hikari_conversation_id') || '';

  const holidays2026 = new Set([
    '2026-01-01','2026-01-12','2026-02-11','2026-02-23','2026-03-20','2026-04-29','2026-05-03','2026-05-04','2026-05-05','2026-05-06',
    '2026-07-20','2026-08-11','2026-09-21','2026-09-22','2026-09-23','2026-10-12','2026-11-03','2026-11-23'
  ]);

  const today = new Date();
  const localDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
  const isHoliday = today.getDay() === 0 || today.getDay() === 6 || holidays2026.has(localDate);

  const statusText = {
    ANSWER: '',
    ASK_MORE: 'もう少し条件を教えてください。',
    CONFIRM_VENDOR: 'メーカー確認が必要なため、担当者が確認します。',
    SALES_HUMAN: 'お見積・商談は営業担当が引き継ぎます。',
    SUPPORT_HUMAN: '技術サポート担当が引き継ぎます。',
    STOP: '安全上、この内容には対応できません。'
  };

  const root = document.createElement('div');
  root.className = isHoliday ? 'hikari-holiday' : '';
  root.innerHTML = `
    <button class="hikari-launcher" type="button" aria-expanded="false" aria-controls="hikari-panel">
      <span class="hikari-launcher__dot" aria-hidden="true"></span>
      <span class="hikari-launcher__label">HIKARIに質問</span>
    </button>
    <section class="hikari-panel" id="hikari-panel" aria-label="HIKARI AIサポート">
      <header class="hikari-header">
        <div class="hikari-title"><span class="hikari-avatar" aria-hidden="true">${isHoliday ? '👘' : '✦'}</span><span><strong>HIKARI</strong><small>AIロボット案内</small></span></div>
        <button class="hikari-close" type="button" aria-label="閉じる">×</button>
      </header>
      <div class="hikari-body" role="log" aria-live="polite"></div>
      <form class="hikari-form">
        <input class="hikari-input" name="query" type="text" autocomplete="off" placeholder="製品・仕様・導入について質問" aria-label="質問">
        <button class="hikari-send" type="submit">送信</button>
      </form>
    </section>`;
  document.body.appendChild(root);

  const launcher = root.querySelector('.hikari-launcher');
  const panel = root.querySelector('.hikari-panel');
  const closeBtn = root.querySelector('.hikari-close');
  const body = root.querySelector('.hikari-body');
  const form = root.querySelector('.hikari-form');
  const input = root.querySelector('.hikari-input');
  const send = root.querySelector('.hikari-send');

  const addMessage = (text, kind = 'bot', extra = {}) => {
    const el = document.createElement('div');
    el.className = `hikari-msg hikari-msg--${kind}`;
    el.textContent = text;
    if (extra.route && statusText[extra.route]) {
      const status = document.createElement('div');
      status.className = 'hikari-status';
      status.textContent = statusText[extra.route];
      el.appendChild(status);
    }
    if (Array.isArray(extra.citations) && extra.citations.length) {
      const refs = document.createElement('div');
      refs.className = 'hikari-citations';
      refs.textContent = `参照: ${extra.citations.map((c) => c.title || c.name || 'Knowledge').join(' / ')}`;
      el.appendChild(refs);
    }
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
  };

  addMessage(isHoliday
    ? 'こんにちは、HIKARIです。今日は和装でご案内します。AIロボットの製品・仕様・導入についてお気軽にどうぞ。'
    : 'こんにちは、HIKARIです。AIロボットの製品・仕様・導入についてお気軽にどうぞ。');

  const toggle = (open) => {
    panel.classList.toggle('is-open', open);
    launcher.setAttribute('aria-expanded', String(open));
    if (open) window.setTimeout(() => input.focus(), 50);
  };
  launcher.addEventListener('click', () => toggle(!panel.classList.contains('is-open')));
  closeBtn.addEventListener('click', () => toggle(false));

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = input.value.trim();
    if (!query) return;
    addMessage(query, 'user');
    input.value = '';
    send.disabled = true;

    if (!endpoint) {
      addMessage('DEV/UATのAPI接続先がまだ設定されていません。フロントUIは正常です。');
      send.disabled = false;
      return;
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          query,
          conversation_id: conversationId,
          user: userId,
          inputs: {
            email: '',
            source_page: location.href,
            product_context: document.querySelector('h1')?.textContent?.trim() || ''
          }
        })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      conversationId = data.conversation_id || data.conversationId || conversationId;
      if (conversationId) localStorage.setItem('hikari_conversation_id', conversationId);
      const answer = data.answer || data.text || data.message || '回答を取得できませんでした。';
      const route = data.route || data.judge || data.classification || '';
      const citations = data.citations || data.retriever_resources || [];
      addMessage(answer, 'bot', {route, citations});
    } catch (error) {
      console.error('HIKARI API error', error);
      addMessage('通信に失敗しました。しばらくしてから再度お試しください。');
    } finally {
      send.disabled = false;
      input.focus();
    }
  });
})();
