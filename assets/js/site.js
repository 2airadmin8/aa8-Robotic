(() => {
  'use strict';
  const button = document.querySelector('.menu');
  const nav = document.querySelector('.nav');
  if (button && nav) {
    button.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
      nav.classList.remove('open');
      button.setAttribute('aria-expanded', 'false');
    }));
  }

  document.querySelectorAll('[data-product-list]').forEach(async (root) => {
    try {
      const response = await fetch(root.dataset.source || 'data/products.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      root.innerHTML = data.products.filter((item) => item.visibility === 'public').map((item) => `
        <article class="product-card">
          <p class="eyebrow">${item.manufacturerName}</p>
          <h3><a href="${item.detailPage}">${item.name}</a></h3>
          <p>${item.summary}</p>
          <div class="meta"><span class="tag">${item.categoryLabel}</span><span class="tag">${item.statusLabel}</span></div>
          <p>${item.useLabels.join('・')}</p>
          <p style="margin-top:16px"><a href="${item.detailPage}"><strong>製品詳細を見る →</strong></a></p>
        </article>`).join('');
    } catch (error) {
      console.error(error);
      root.innerHTML = '<p>製品情報を読み込めませんでした。</p>';
    }
  });
})();
