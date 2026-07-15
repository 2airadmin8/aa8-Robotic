(() => {
  'use strict';

  const productRoot = document.querySelector('[data-product-list]');
  const compareBar = document.querySelector('[data-compare-bar]');
  const selectedNames = document.querySelector('[data-compare-selected]');
  const openButton = document.querySelector('[data-compare-open]');
  const clearButton = document.querySelector('[data-compare-clear]');
  const dialog = document.querySelector('[data-compare-dialog]');
  const tableTarget = document.querySelector('[data-compare-table]');
  const consultLink = document.querySelector('[data-compare-consult]');
  const limitMessage = document.querySelector('[data-compare-limit]');

  if (!productRoot || !compareBar || !dialog || !tableTarget) return;

  const selected = new Set();
  let products = [];

  initialise();

  async function initialise() {
    try {
      const response = await fetch(productRoot.dataset.source || 'data/products.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      products = (data.products || []).filter((item) => item.visibility === 'public');
      restoreSelectionFromUrl();
      attachControlsWhenReady();
    } catch (error) {
      console.error('製品比較データの読み込みに失敗しました。', error);
    }
  }

  function attachControlsWhenReady() {
    const cards = [...productRoot.querySelectorAll('.research-product-card')];
    if (!cards.length) {
      const observer = new MutationObserver(() => {
        if (!productRoot.querySelector('.research-product-card')) return;
        observer.disconnect();
        attachControlsWhenReady();
      });
      observer.observe(productRoot, { childList: true });
      return;
    }

    cards.forEach((card) => {
      if (card.querySelector('[data-compare-checkbox]')) return;
      const product = products.find((item) => item.id === card.id);
      if (!product) return;

      const label = document.createElement('label');
      label.className = 'product-compare-select';
      label.innerHTML = `<input type="checkbox" data-compare-checkbox value="${escapeHtml(product.id)}"><span>比較に追加</span>`;
      const checkbox = label.querySelector('input');
      checkbox.checked = selected.has(product.id);
      card.classList.toggle('is-compare-selected', checkbox.checked);
      checkbox.addEventListener('change', () => toggleProduct(product.id, checkbox, card));

      const body = card.querySelector('.product-body');
      body?.insertBefore(label, body.querySelector('.product-card-actions'));
    });

    updateInterface();
  }

  function toggleProduct(productId, checkbox, card) {
    if (checkbox.checked && selected.size >= 3) {
      checkbox.checked = false;
      showLimitMessage('比較できる製品は3件までです。');
      return;
    }

    if (checkbox.checked) selected.add(productId);
    else selected.delete(productId);

    card.classList.toggle('is-compare-selected', checkbox.checked);
    updateInterface();
  }

  function updateInterface() {
    const selectedProducts = getSelectedProducts();
    compareBar.classList.toggle('is-visible', selectedProducts.length > 0);
    compareBar.setAttribute('aria-hidden', String(selectedProducts.length === 0));

    if (selectedNames) {
      selectedNames.innerHTML = selectedProducts.map((item) => `<span>${escapeHtml(item.name)}</span>`).join('');
    }

    if (openButton) {
      openButton.disabled = selectedProducts.length < 2;
      openButton.textContent = selectedProducts.length < 2
        ? `あと${2 - selectedProducts.length}製品選択`
        : `${selectedProducts.length}製品を比較`;
    }

    updateCompareUrl();
  }

  function openComparison() {
    const selectedProducts = getSelectedProducts();
    if (selectedProducts.length < 2) return;
    tableTarget.innerHTML = buildComparisonTable(selectedProducts);

    if (consultLink) {
      const names = selectedProducts.map((item) => item.name).join(' / ');
      consultLink.href = `contact.html?product=${encodeURIComponent(names)}&service=multi-brand-comparison`;
    }

    dialog.showModal();
  }

  function buildComparisonTable(items) {
    const rows = [
      ['製品カテゴリ', (item) => item.categoryLabel],
      ['取扱・確認状態', (item) => item.statusLabel],
      ['概要', (item) => item.summary],
      ['主な構成・特徴', (item) => tags(item.featureLabels)],
      ['適した研究・用途', (item) => tags(item.useLabels)],
      ['価格', (item) => item.priceLabel],
      ['納期', (item) => item.leadTimeLabel],
      ['SDK・ROS関連', (item) => tags((item.relatedResourceIds || []).map(resourceLabel))],
      ['最終確認日', (item) => item.verifiedAt || '未確認'],
      ['注意事項', (item) => item.note || '構成・時期・利用環境により正式確認'],
    ];

    return `
      <table class="compare-table">
        <thead>
          <tr>
            <th scope="col">比較項目</th>
            ${items.map((item) => `
              <th scope="col">
                <div class="compare-product-head">
                  <small>${escapeHtml(item.manufacturerName)}</small>
                  <strong>${escapeHtml(item.name)}</strong>
                  <a href="${escapeHtml(item.detailPage)}">詳細を見る →</a>
                </div>
              </th>
            `).join('')}
          </tr>
        </thead>
        <tbody>
          ${rows.map(([label, renderer]) => `
            <tr>
              <th scope="row">${escapeHtml(label)}</th>
              ${items.map((item) => `<td>${renderer(item)}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  function clearSelection() {
    selected.clear();
    productRoot.querySelectorAll('[data-compare-checkbox]').forEach((checkbox) => {
      checkbox.checked = false;
      checkbox.closest('.research-product-card')?.classList.remove('is-compare-selected');
    });
    updateInterface();
    dialog.close();
  }

  function restoreSelectionFromUrl() {
    const ids = new URLSearchParams(window.location.search).get('compare');
    if (!ids) return;
    ids.split(',').slice(0, 3).forEach((id) => {
      if (products.some((item) => item.id === id)) selected.add(id);
    });
  }

  function updateCompareUrl() {
    const url = new URL(window.location.href);
    if (selected.size) url.searchParams.set('compare', [...selected].join(','));
    else url.searchParams.delete('compare');
    window.history.replaceState({}, '', url);
  }

  function getSelectedProducts() {
    return [...selected]
      .map((id) => products.find((item) => item.id === id))
      .filter(Boolean);
  }

  function showLimitMessage(message) {
    if (!limitMessage) return;
    limitMessage.hidden = false;
    limitMessage.textContent = message;
    window.setTimeout(() => { limitMessage.hidden = true; }, 3200);
  }

  function tags(values = []) {
    if (!values.length) return '要確認';
    return `<div class="compare-cell-tags">${values.map((value) => `<span>${escapeHtml(value)}</span>`).join('')}</div>`;
  }

  function resourceLabel(value) {
    const map = {
      sdk: 'SDK', ros2: 'ROS2', mujoco: 'MuJoCo', hdf5: 'HDF5', rlds: 'RLDS',
    };
    return map[value] || value;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
    }[character]));
  }

  openButton?.addEventListener('click', openComparison);
  clearButton?.addEventListener('click', clearSelection);
  dialog.querySelector('[data-compare-close]')?.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (event) => {
    const box = dialog.getBoundingClientRect();
    const outside = event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom;
    if (outside) dialog.close();
  });
})();