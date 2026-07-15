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

  const draftKey = 'airadmin8-contact-draft-v1';
  const params = new URLSearchParams(window.location.search);
  const source = {
    product: params.get('product') || '',
    maker: params.get('maker') || '',
    service: params.get('service') || '',
    theme: params.get('theme') || '',
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
    inspection: { category: '導入条件整理', label: '巡回・点検' },
    transport: { category: '導入条件整理', label: '搬送' },
    manipulation: { category: '導入条件整理', label: '把持・操作' },
    'lab-automation': { category: 'PoC設計', label: '実験室自動化' },
    'use-case-review': { category: '導入条件整理', label: '用途からの条件整理' },
  };

  restoreDraft();
  applyPrefill();
  installDraftControls();

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
  dialog.querySelector('[data-confirm-send]')?.addEventListener('click', () => {
    const values = new FormData(form);
    const subject = createSubject(values);
    const body = createBody(values);
    const mailto = `mailto:airobot@robotics.air-admin8.co.jp?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

    saveDraft();
    dialog.close();
    fallbackPanel?.classList.add('is-visible');
    fallbackPanel?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    window.location.href = mailto;
  });

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

    const labels = [source.product, source.maker, config?.label].filter(Boolean);
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
