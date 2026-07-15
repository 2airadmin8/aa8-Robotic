(() => {
  'use strict';

  const button = document.querySelector('.menu');
  const nav = document.querySelector('.nav');

  if (button && nav) {
    button.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
    });

    nav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        nav.classList.remove('open');
        button.setAttribute('aria-expanded', 'false');
      });
    });
  }

  document.querySelectorAll('[data-product-list]').forEach(async (root) => {
    try {
      const response = await fetch(root.dataset.source || 'data/products.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const limit = Number(root.dataset.limit || 0);
      const products = data.products.filter((item) => item.visibility === 'public');
      const visibleProducts = limit > 0 ? products.slice(0, limit) : products;

      root.innerHTML = visibleProducts.map((item) => `
        <article class="product-card">
          <a class="product-visual" href="${item.detailPage}" aria-label="${item.name}の詳細を見る">
            <img src="${item.image}" alt="${item.name}のカテゴリイメージ" loading="lazy">
          </a>
          <div class="product-body">
            <div class="product-topline">
              <p class="product-maker">${item.manufacturerName}</p>
              <span class="status">${item.statusLabel}</span>
            </div>
            <h3><a href="${item.detailPage}">${item.name}</a></h3>
            <p>${item.summary}</p>
            <div class="meta">
              <span class="tag">${item.categoryLabel}</span>
              <span class="tag">${item.priceLabel}</span>
              <span class="tag">${item.leadTimeLabel}</span>
            </div>
            <p>${item.useLabels.join('・')}</p>
            <a class="product-link" href="${item.detailPage}">製品詳細を見る →</a>
          </div>
        </article>
      `).join('');
    } catch (error) {
      console.error('製品情報の読み込みに失敗しました。', error);
      root.innerHTML = '<p>製品情報を読み込めませんでした。</p>';
    }
  });
})();