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

  const params = new URLSearchParams(window.location.search);
  const source = {
    product: params.get('product') || '', maker: params.get('maker') || '',
    service: params.get('service') || '', theme: params.get('theme') || '',
    useCase: params.get('use_case') || '', message: params.get('message') || '',
  };

  applyPrefill();

  form.addEventListener('submit', (event) => {
    event.preventDefault(); event.stopImmediatePropagation();
    if (!validateForm()) return;
    renderSummary(); dialog.showModal();
  }, true);

  dialog.querySelector('[data-confirm-back]')?.addEventListener('click', () => dialog.close());
  dialog.querySelector('[data-confirm-send]')?.addEventListener('click', () => {
    const values = new FormData(form);
    const mailto = `mailto:airobot@robotics.air-admin8.co.jp?subject=${encodeURIComponent(createSubject(values))}&body=${encodeURIComponent(createBody(values))}`;
    dialog.close(); fallbackPanel?.classList.add('is-visible');
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

  function applyPrefill() {
    const productField = form.elements.namedItem('product');
    const categoryField = form.elements.namedItem('category');
    const useCaseField = form.elements.namedItem('use_case');
    const messageField = form.elements.namedItem('message');
    const sourceMap = {
      source_product: source.product, source_maker: source.maker,
      source_service: source.service, source_theme: source.theme,
      source_page: document.referrer || window.location.href,
    };

    Object.entries(sourceMap).forEach(([name, value]) => {
      const field = form.elements.namedItem(name); if (field) field.value = value;
    });

    if (productField && source.product) productField.value = source.product;
    if (productField && source.maker && !productField.value) productField.value = source.maker;
    if (useCaseField && source.useCase) useCaseField.value = source.useCase;
    if (messageField && source.message) messageField.value = source.message;

    const categoryMap = {
      poc: 'PoC設計', 'university-procurement': '見積・大学購買',
      'vla-data-collection': 'VLA・模倣学習データ収集',
      'technical-review': 'SDK・ROS・開発環境',
      'multi-brand-comparison': '製品比較・選定',
      'checklist-review': '製品比較・選定',
    };
    const mapped = categoryMap[source.service] || categoryMap[source.theme];
    if (categoryField && mapped) categoryField.value = mapped;

    const labels = [source.product, source.maker, mapped, source.message ? 'チェック結果' : ''].filter(Boolean);
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
      email.setAttribute('aria-invalid', 'true'); firstInvalid ||= email;
    }
    if (firstInvalid) {
      if (errorBox) { errorBox.hidden = false; errorBox.textContent = '必須項目とメールアドレスをご確認ください。'; }
      firstInvalid.focus(); return false;
    }
    if (errorBox) errorBox.hidden = true;
    return true;
  }

  function renderSummary() {
    const values = new FormData(form);
    const rows = [
      ['相談区分', values.get('category')], ['製品・メーカー', values.get('product') || '未定'],
      ['研究・業務用途', values.get('use_case')], ['大学・会社名', values.get('organization')],
      ['お名前', values.get('name')], ['メール', values.get('email')],
      ['電話番号', values.get('phone') || '未記入'], ['予算感', values.get('budget') || '未定'],
      ['希望時期', values.get('schedule') || '未定'], ['SDK・開発環境', values.get('development') || '未記入'],
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
      `大学・会社名：${values.get('organization') || ''}`, `お名前：${values.get('name') || ''}`,
      `メールアドレス：${values.get('email') || ''}`, `電話番号：${values.get('phone') || '未記入'}`,
      `相談区分：${values.get('category') || ''}`, `検討中の製品・メーカー：${values.get('product') || '未定'}`,
      `予算感：${values.get('budget') || '未定'}`, `希望時期：${values.get('schedule') || '未定'}`,
      `SDK・開発環境：${values.get('development') || '未記入'}`,
      '', '【研究・業務用途】', values.get('use_case') || '',
      '', '【補足・確認したいこと】', values.get('message') || '未記入',
      '', '【流入情報】', `参照ページ：${values.get('source_page') || window.location.href}`,
      `製品：${values.get('source_product') || ''}`, `メーカー：${values.get('source_maker') || ''}`,
      `支援：${values.get('source_service') || ''}`, `用途：${values.get('source_theme') || ''}`,
    ].join('\n');
  }

  function escapeHtml(value) {
    return value.replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
    }[character]));
  }
})();
