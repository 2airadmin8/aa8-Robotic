(() => {
  'use strict';

  const root = document.querySelector('[data-manufacturer-list]');
  if (!root) return;

  const form = document.querySelector('[data-manufacturer-filter-form]');
  const count = document.querySelector('[data-manufacturer-count]');
  const empty = document.querySelector('[data-manufacturer-empty]');

  fetch(root.dataset.source || 'data/manufacturers.json')
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      const manufacturers = data.manufacturers || [];

      const render = (conditions = {}) => {
        const strength = conditions.strength || 'all';
        const status = conditions.status || 'all';
        const keyword = (conditions.keyword || '').trim().toLowerCase();

        const filtered = manufacturers.filter((item) => {
          const strengthMatch = strength === 'all' || item.strengths.includes(strength);
          const statusMatch = status === 'all' || item.status === status;
          const searchableText = [
            item.name,
            item.nameJa,
            item.country,
            item.summary,
            item.note,
            ...(item.productLabels || []),
            ...(item.developmentLabels || []),
            ...(item.keywords || []),
          ].join(' ').toLowerCase();
          const keywordMatch = !keyword || searchableText.includes(keyword);

          return strengthMatch && statusMatch && keywordMatch;
        });

        root.innerHTML = filtered.map(createManufacturerCard).join('');
        if (count) count.textContent = String(filtered.length);
        if (empty) empty.hidden = filtered.length !== 0;
      };

      render();

      form?.addEventListener('submit', (event) => {
        event.preventDefault();
        const values = new FormData(form);
        render({
          strength: values.get('strength'),
          status: values.get('status'),
          keyword: values.get('keyword'),
        });
      });

      form?.addEventListener('reset', () => {
        window.setTimeout(() => render(), 0);
      });

      document.querySelectorAll('[data-manufacturer-shortcut]').forEach((button) => {
        button.addEventListener('click', () => {
          const selectedStrength = button.dataset.manufacturerShortcut;
          const strengthSelect = form?.querySelector('[name="strength"]');
          if (strengthSelect) strengthSelect.value = selectedStrength;
          render({ strength: selectedStrength });
          document.querySelector('#manufacturer-list')?.scrollIntoView({ behavior: 'smooth' });
        });
      });
    })
    .catch((error) => {
      console.error('メーカー情報の読み込みに失敗しました。', error);
      root.innerHTML = '<p>メーカー情報を読み込めませんでした。</p>';
    });

  function createManufacturerCard(item) {
    const products = (item.productLabels || []).map((label) => `<span>${label}</span>`).join('');
    const development = (item.developmentLabels || []).map((label) => `<span>${label}</span>`).join('');
    const detailLink = item.detailPage
      ? `<a class="manufacturer-detail-link" href="${item.detailPage}">メーカー詳細を見る →</a>`
      : '<span class="manufacturer-detail-pending">詳細情報整理中</span>';
    const resourceLink = item.resourceUrl
      ? `<a href="${item.resourceUrl}">公式資料を見る</a>`
      : '';

    return `
      <article class="manufacturer-card">
        <div class="manufacturer-card-topline">
          <p class="manufacturer-country">${item.country}</p>
          <span class="manufacturer-status status-${item.status}">${item.statusLabel}</span>
        </div>
        <p class="manufacturer-en-name">${item.name}</p>
        <h3>${item.nameJa}</h3>
        <p class="manufacturer-summary">${item.summary}</p>

        <div class="manufacturer-card-section">
          <strong>主な製品・領域</strong>
          <div class="manufacturer-tag-list">${products}</div>
        </div>

        <div class="manufacturer-card-section">
          <strong>開発環境・公開資産</strong>
          <div class="manufacturer-tag-list development-tags">${development}</div>
        </div>

        <div class="manufacturer-verification">
          <span>確認状態</span>
          <strong>${item.verificationLabel}</strong>
          <p>${item.note}</p>
        </div>

        <div class="manufacturer-card-actions">
          ${detailLink}
          ${resourceLink}
          <a href="${item.officialUrl}" target="_blank" rel="noopener noreferrer">公式サイト ↗</a>
        </div>
      </article>
    `;
  }
})();