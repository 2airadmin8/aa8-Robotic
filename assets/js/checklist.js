(() => {
  'use strict';

  const sheet = document.querySelector('[data-checklist-sheet]');
  if (!sheet) return;

  const storageKey = 'airadmin8-robotics-checklist-v1';
  const status = document.querySelector('[data-checklist-status]');
  const progress = document.querySelector('[data-checklist-progress]');
  const copyButton = document.querySelector('[data-checklist-copy]');
  const consultLinks = [...document.querySelectorAll('[data-checklist-consult]')];
  const resetButton = document.querySelector('[data-checklist-reset]');
  const items = [...sheet.querySelectorAll('[data-check-item]')];
  const summaryFields = [...sheet.querySelectorAll('[data-summary-field]')];

  restore();
  updateInterface(false);

  items.forEach((item) => {
    const checkbox = item.querySelector('input[type="checkbox"]');
    const memo = item.querySelector('[data-check-memo]');
    checkbox?.addEventListener('change', () => updateInterface());
    memo?.addEventListener('input', () => updateInterface());
  });

  summaryFields.forEach((field) => field.addEventListener('input', () => updateInterface()));

  copyButton?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(buildSummary());
      showStatus('チェック結果をコピーしました。');
    } catch (error) {
      showStatus('コピーできませんでした。印刷・PDF保存をご利用ください。');
    }
  });

  resetButton?.addEventListener('click', () => {
    if (!window.confirm('入力したチェック内容をすべて消去しますか？')) return;
    items.forEach((item) => {
      const checkbox = item.querySelector('input[type="checkbox"]');
      const memo = item.querySelector('[data-check-memo]');
      if (checkbox) checkbox.checked = false;
      if (memo) memo.value = '';
    });
    summaryFields.forEach((field) => { field.value = ''; });
    localStorage.removeItem(storageKey);
    updateInterface(false);
    showStatus('チェック内容を消去しました。');
  });

  function updateInterface(shouldSave = true) {
    const checked = items.filter((item) => item.querySelector('input[type="checkbox"]')?.checked).length;
    if (progress) progress.textContent = `${checked} / ${items.length} 項目確認済み`;
    items.forEach((item) => item.classList.toggle('is-checked', Boolean(item.querySelector('input[type="checkbox"]')?.checked)));
    updateConsultLinks();
    if (shouldSave) save();
  }

  function save() {
    const data = {
      items: items.map((item) => ({
        checked: Boolean(item.querySelector('input[type="checkbox"]')?.checked),
        memo: item.querySelector('[data-check-memo]')?.value || '',
      })),
      summary: summaryFields.map((field) => field.value || ''),
    };
    localStorage.setItem(storageKey, JSON.stringify(data));
    showStatus('端末内に自動保存しました。', 1200);
  }

  function restore() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
      if (!saved) return;
      items.forEach((item, index) => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        const memo = item.querySelector('[data-check-memo]');
        if (checkbox) checkbox.checked = Boolean(saved.items?.[index]?.checked);
        if (memo) memo.value = saved.items?.[index]?.memo || '';
      });
      summaryFields.forEach((field, index) => { field.value = saved.summary?.[index] || ''; });
      showStatus('前回の入力内容を復元しました。');
    } catch (error) {
      localStorage.removeItem(storageKey);
    }
  }

  function buildSummary() {
    const lines = ['【AIロボット導入前チェック結果】'];
    let currentSection = '';

    items.forEach((item) => {
      const section = item.closest('.checklist-section');
      const sectionTitle = section?.querySelector('h2')?.textContent.trim() || '';
      if (sectionTitle !== currentSection) {
        currentSection = sectionTitle;
        lines.push('', `■ ${currentSection}`);
      }
      const title = item.querySelector('strong')?.textContent.trim() || '';
      const checked = item.querySelector('input[type="checkbox"]')?.checked ? '確認済' : '未確認';
      const memo = item.querySelector('[data-check-memo]')?.value.trim() || '記載なし';
      lines.push(`・${title}：${checked}｜${memo}`);
    });

    lines.push('', '■ 正式見積前の判断');
    summaryFields.forEach((field) => {
      lines.push(`・${field.dataset.summaryLabel}：${field.value.trim() || '未記入'}`);
    });
    return lines.join('\n');
  }

  function updateConsultLinks() {
    const params = new URLSearchParams({
      service: 'checklist-review',
      use_case: 'AIロボット導入前チェックリストの確認を希望',
      message: buildSummary(),
    });
    consultLinks.forEach((link) => { link.href = `contact.html?${params.toString()}`; });
  }

  function showStatus(message, timeout = 2400) {
    if (!status) return;
    status.textContent = message;
    window.clearTimeout(showStatus.timer);
    showStatus.timer = window.setTimeout(() => { status.textContent = ''; }, timeout);
  }
})();
