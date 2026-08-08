(() => {
  'use strict';

  const form = document.querySelector('[data-contact-form]');
  const dialog = document.querySelector('[data-contact-confirm]');
  const summary = document.querySelector('[data-confirm-summary]');
  const errorBox = document.querySelector('[data-form-error]');
  const prefillNotice = document.querySelector('[data-prefill-notice]');
  const fallbackPanel = document.querySelector('[data-mail-fallback]');
  const copyStatus = document.querySelector('[data-copy-status]');

  if (!form || !dialog || !summary) return;

  // Apps Script Web App のデプロイ後、この1箇所だけ本番URLへ置換する。
  const INQUIRY_WEB_APP_URL = '';
  const draftKey = 'airadmin8-contact-draft-v1';
  const requestTimeoutMs = 20000;

  const params = new URLSearchParams(window.location.search);
  const source = {
    product: params.get('product') || '',
    maker: params.get('maker') || '',
    service: params.get('service') || '',
    theme: params.get('theme') || '',
    caseId: params.get('case') || '',
    useCase: params.get('use_case') || '',
    message: params.get('message') || '',
  };

  const sourceConfig = {
    poc: { category: 'PoC設計', label: 'PoC設計' },
    'university-procurement': { category: '見積・大学購買', label: '大学購買支援' },
    'vla-data-collection': { category: 'VLA・模倣学習データ収集', label: 'VLA・模倣学習データ収集' },
    'technical-review': { category: 'SDK・ROS・開発環境', label: '技術条件確認' },
    'multi-brand-comparison': { category: '製品比較・選定', label: '複数メーカー比較' },
    'checklist-review': { category: '導入条件整理', label: '導入前チェック結果' },
    'company-inquiry': { category: '会社・協業相談', label: '会社・協業相談' },
    'case-based-consultation': { category: '導入条件整理', label: '事例ベース相談' },
    inspection: { category: '導入条件整理', label: '巡回・点検' },
    transport: { category: '導入条件整理', label: '搬送' },
    manipulation: { category: '導入条件整理', label: '把持・操作' },
    'lab-automation': { category: 'PoC設計', label: '実験室自動化' },
    'use-case-review': { category: '導入条件整理', label: '用途からの条件整理' },
  };

  const caseLabels = {
    'keio-selection': '慶應義塾大学向け選定・見積支援事例',
  };

  restoreDraft();
  applyPrefill();
  installDraftControls();
  updateLegacyCopy();

  form.addEventListener('input', debounce(saveDraft, 350));
  form.addEventListener('change', saveDraft);

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (!validateForm()) return;
    saveDraft();
    renderSummary();
    dialog.showModal();
  }, true);

  dialog.querySelector('[data-confirm-back]')?.addEventListener('click', () => dialog.close());
  dialog.querySelector('[data-confirm-send]')?.addEventListener('click', submitInquiry);

  document.querySelector('[data-copy-mail]')?.addEventListener('click', async () => {
    const values = new FormData(form);
    const text = `件名：${createSubject(values)}\n\n${createBody(values)}`;
    try {
      await navigator.clipboard.writeText(text);
      if (copyStatus) copyStatus.textContent = '相談内容をコピーしました。メールに貼り付けて送信してください。';
    } catch (error) {
      if (copyStatus) copyStatus.textContent = 'コピーできませんでした。下のメールアドレスから直接ご連絡ください。';
    }
  });

  dialog.addEventListener('click', (event) => {
    const box = dialog.getBoundingClientRect();
    const outside = event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom;
    if (outside) dialog.close();
  });

  async function submitInquiry() {
    const sendButton = dialog.querySelector('[data-confirm-send]');
    if (!validateForm()) {
      dialog.close();
      return;
    }

    if (!INQUIRY_WEB_APP_URL) {
      dialog.close();
      showSubmitError('問い合わせ送信APIが未接続です。下のメール連絡をご利用ください。');
      showFallback();
      return;
    }

    const submissionToken = createToken('submission');
    const responseToken = createToken('response');
    const payload = buildPayload(submissionToken, responseToken);

    setSendingState(sendButton, true);

    try {
      const result = await postViaHiddenIframe(payload, responseToken);
      if (!result.ok) throw new Error(result.error || '送信できませんでした。');

      localStorage.removeItem(draftKey);
      const destination = new URL('/contact-thanks.html', window.location.origin);
      destination.searchParams.set('status', 'success');
      if (result.inquiryId) destination.searchParams.set('id', result.inquiryId);
      window.location.assign(destination.toString());
    } catch (error) {
      dialog.close();
      showSubmitError(error?.message || '送信できませんでした。時間をおいて再度お試しください。');
      showFallback();
      setSendingState(sendButton, false);
    }
  }

  function postViaHiddenIframe(payload, responseToken) {
    return new Promise((resolve, reject) => {
      const frameName = `aa8-inquiry-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const iframe = document.createElement('iframe');
      const postForm = document.createElement('form');
      let settled = false;

      iframe.name = frameName;
      iframe.hidden = true;
      iframe.setAttribute('aria-hidden', 'true');

      postForm.method = 'POST';
      postForm.action = INQUIRY_WEB_APP_URL;
      postForm.target = frameName;
      postForm.hidden = true;
      postForm.acceptCharset = 'UTF-8';

      Object.entries(payload).forEach(([name, value]) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = String(value ?? '');
        postForm.appendChild(input);
      });

      const cleanup = () => {
        window.removeEventListener('message', onMessage);
        window.clearTimeout(timer);
        postForm.remove();
        window.setTimeout(() => iframe.remove(), 100);
      };

      const finish = (callback) => {
        if (settled) return;
        settled = true;
        cleanup();
        callback();
      };

      const onMessage = (event) => {
        if (event.source !== iframe.contentWindow) return;
        const data = event.data;
        if (!data || data.type !== 'aa8-inquiry-response') return;
        if (data.responseToken !== responseToken) return;
        finish(() => resolve(data));
      };

      const timer = window.setTimeout(() => {
        finish(() => reject(new Error('送信確認がタイムアウトしました。通信環境をご確認ください。')));
      }, requestTimeoutMs);

      window.addEventListener('message', onMessage);
      document.body.appendChild(iframe);
      document.body.appendChild(postForm);
      postForm.submit();
    });
  }

  function buildPayload(submissionToken, responseToken) {
    const values = new FormData(form);
    return {
      category: values.get('category') || '',
      organization: values.get('organization') || '',
      name: values.get('name') || '',
      email: values.get('email') || '',
      phone: values.get('phone') || '',
      product: values.get('product') || '',
      use_case: values.get('use_case') || '',
      budget: values.get('budget') || '',
      schedule: values.get('schedule') || '',
      development: values.get('development') || '',
      message: values.get('message') || '',
      source_page: values.get('source_page') || window.location.href,
      source_product: values.get('source_product') || '',
      source_maker: values.get('source_maker') || '',
      source_service: values.get('source_service') || '',
      source_theme: values.get('source_theme') || '',
      source_case: values.get('source_case') || '',
      utm_source: params.get('utm_source') || '',
      utm_medium: params.get('utm_medium') || '',
      utm_campaign: params.get('utm_campaign') || '',
      ga_client_id: getGaClientId(),
      submission_token: submissionToken,
      response_token: responseToken,
      website: '',
    };
  }

  function createToken(prefix) {
    if (window.crypto?.randomUUID) return `${prefix}-${window.crypto.randomUUID()}`;
    const random = Math.random().toString(36).slice(2);
    return `${prefix}-${Date.now()}-${random}`;
  }

  function getGaClientId() {
    const match = document.cookie.match(/(?:^|;\s*)_ga=GA\d+\.\d+\.(\d+\.\d+)/);
    return match ? match[1] : '';
  }

  function setSendingState(button, sending) {
    if (!button) return;
    button.disabled = sending;
    button.setAttribute('aria-busy', String(sending));
    button.textContent = sending ? '送信中…' : 'この内容で送信する';
  }

  function showSubmitError(message) {
    if (!errorBox) return;
    errorBox.hidden = false;
    errorBox.textContent = message;
    errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function showFallback() {
    fallbackPanel?.classList.add('is-visible');
    fallbackPanel?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function updateLegacyCopy() {
    const headingText = document.querySelector('.contact-form-heading p:last-child');
    if (headingText) headingText.textContent = '入力後に確認画面を表示し、内容を確認してから送信します。';

    const progressItems = document.querySelectorAll('.contact-progress li');
    if (progressItems[2]) progressItems[2].innerHTML = '<strong>3</strong>確認して送信';

    const submitExplanation = document.querySelector('.submit-explanation');
    if (submitExplanation) submitExplanation.textContent = 'この時点では送信されません。次の確認画面から送信します。';

    const confirmText = dialog.querySelector('.confirm-dialog-header p');
    if (confirmText) confirmText.textContent = '内容を確認後、「この内容で送信する」を押してください。';

    const confirmSend = dialog.querySelector('[data-confirm-send]');
    if (confirmSend) confirmSend.textContent = 'この内容で送信する';
  }

  function installDraftControls() {
    const anchor = prefillNotice?.parentElement ? prefillNotice : form;
    const panel = document.createElement('div');
    panel.className = 'contact-draft-panel';
    panel.dataset.contactDraftPanel = '';
    panel.innerHTML = `
      <div>
        <strong>入力内容はこの端末に自動保存されます。</strong>
        <span data-contact-draft-status>未保存</span>
      </div>
      <button type="button" data-contact-draft-clear>下書きを消去</button>`;

    if (anchor === form) form.prepend(panel);
    else anchor.insertAdjacentElement('afterend', panel);

    panel.querySelector('[data-contact-draft-clear]')?.addEventListener('click', () => {
      if (!window.confirm('保存した下書きと現在の入力内容を消去しますか？')) return;
      localStorage.removeItem(draftKey);
      form.reset();
      applyPrefill();
      updateDraftStatus('下書きを消去しました。');
    });

    updateDraftStatus(localStorage.getItem(draftKey) ? '保存済みの下書きを復元しました。' : '入力すると自動保存されます。');
  }

  function saveDraft() {
    const payload = {};
    [...form.elements].forEach((field) => {
      if (!field.name || field.type === 'hidden' || field.name === 'privacy' || field.disabled) return;
      payload[field.name] = field.value;
    });

    const hasContent = Object.values(payload).some((value) => String(value || '').trim());
    if (!hasContent) {
      localStorage.removeItem(draftKey);
      updateDraftStatus('入力すると自動保存されます。');
      return;
    }

    localStorage.setItem(draftKey, JSON.stringify({ savedAt: Date.now(), values: payload }));
    updateDraftStatus('この端末に保存しました。');
  }

  function restoreDraft() {
    try {
      const raw = localStorage.getItem(draftKey);
      if (!raw) return;
      const draft = JSON.parse(raw);
      Object.entries(draft.values || {}).forEach(([name, value]) => {
        const field = form.elements.namedItem(name);
        if (field && typeof value === 'string') field.value = value;
      });
    } catch (error) {
      localStorage.removeItem(draftKey);
    }
  }

  function updateDraftStatus(message) {
    const status = document.querySelector('[data-contact-draft-status]');
    if (status) status.textContent = message;
  }

  function applyPrefill() {
    const productField = form.elements.namedItem('product');
    const categoryField = form.elements.namedItem('category');
    const useCaseField = form.elements.namedItem('use_case');
    const messageField = form.elements.namedItem('message');
    const sourceMap = {
      source_product: source.product,
      source_maker: source.maker,
      source_service: source.service,
      source_theme: source.theme,
      source_case: source.caseId,
      source_page: document.referrer || window.location.href,
    };

    Object.entries(sourceMap).forEach(([name, value]) => {
      const field = form.elements.namedItem(name);
      if (field) field.value = value;
    });

    if (productField && source.product) productField.value = source.product;
    if (productField && source.maker && !productField.value) productField.value = source.maker;
    if (useCaseField && source.useCase) useCaseField.value = source.useCase;
    if (messageField && source.message) messageField.value = source.message;

    const config = sourceConfig[source.service] || sourceConfig[source.theme];
    if (categoryField && config?.category) categoryField.value = config.category;

    if (source.caseId && useCaseField && !useCaseField.value) {
      useCaseField.value = `${caseLabels[source.caseId] || source.caseId}を参考に、同様の条件整理を希望`;
    }

    const labels = [source.product, source.maker, config?.label, caseLabels[source.caseId]].filter(Boolean);
    if (labels.length && prefillNotice) {
      prefillNotice.hidden = false;
      prefillNotice.textContent = `前のページから「${labels.join('・')}」を引き継ぎました。内容は自由に変更できます。`;
    }
  }

  function validateForm() {
    const requiredFields = [...form.querySelectorAll('[required]')];
    let firstInvalid = null;

    requiredFields.forEach((field) => {
      const invalid = field.type === 'checkbox' ? !field.checked : !String(field.value || '').trim();
      field.setAttribute('aria-invalid', String(invalid));
      if (invalid && !firstInvalid) firstInvalid = field;
    });

    const email = form.elements.namedItem('email');
    if (email && email.value && !email.validity.valid) {
      email.setAttribute('aria-invalid', 'true');
      firstInvalid ||= email;
    }

    if (firstInvalid) {
      if (errorBox) {
        errorBox.hidden = false;
        errorBox.textContent = '必須項目とメールアドレスをご確認ください。';
      }
      firstInvalid.focus();
      return false;
    }

    if (errorBox) errorBox.hidden = true;
    return true;
  }

  function renderSummary() {
    const values = new FormData(form);
    const rows = [
      ['相談区分', values.get('category')],
      ['製品・メーカー', values.get('product') || '未定'],
      ['研究・業務用途', values.get('use_case')],
      ['大学・会社名', values.get('organization')],
      ['お名前', values.get('name')],
      ['メール', values.get('email')],
      ['電話番号', values.get('phone') || '未記入'],
      ['予算感', values.get('budget') || '未定'],
      ['希望時期', values.get('schedule') || '未定'],
      ['SDK・開発環境', values.get('development') || '未記入'],
      ['補足', values.get('message') || '未記入'],
    ];

    summary.innerHTML = `<dl>${rows.map(([term, value]) => `<div><dt>${escapeHtml(String(term))}</dt><dd>${escapeHtml(String(value || ''))}</dd></div>`).join('')}</dl>`;
  }

  function createSubject(values) {
    return `【AirAdmin8 Robotics相談】${values.get('category') || '製品・導入相談'}｜${values.get('organization') || ''}`;
  }

  function createBody(values) {
    return [
      'AirAdmin8 Robotics ご担当者様', '', '下記の内容で相談します。', '',
      `大学・会社名：${values.get('organization') || ''}`,
      `お名前：${values.get('name') || ''}`,
      `メールアドレス：${values.get('email') || ''}`,
      `電話番号：${values.get('phone') || '未記入'}`,
      `相談区分：${values.get('category') || ''}`,
      `検討中の製品・メーカー：${values.get('product') || '未定'}`,
      `予算感：${values.get('budget') || '未定'}`,
      `希望時期：${values.get('schedule') || '未定'}`,
      `SDK・開発環境：${values.get('development') || '未記入'}`,
      '', '【研究・業務用途】', values.get('use_case') || '',
      '', '【補足・確認したいこと】', values.get('message') || '未記入',
      '', '【流入情報】',
      `参照ページ：${values.get('source_page') || window.location.href}`,
      `製品：${values.get('source_product') || ''}`,
      `メーカー：${values.get('source_maker') || ''}`,
      `支援：${values.get('source_service') || ''}`,
      `用途：${values.get('source_theme') || ''}`,
      `事例：${values.get('source_case') || ''}`,
    ].join('\n');
  }

  function debounce(callback, wait) {
    let timer;
    return (...args) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => callback(...args), wait);
    };
  }

  function escapeHtml(value) {
    return value.replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
    }[character]));
  }
})();
