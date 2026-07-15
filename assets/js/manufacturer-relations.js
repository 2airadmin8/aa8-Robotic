(() => {
  'use strict';

  const path = window.location.pathname;
  const manufacturerMap = {
    unitree: {
      name: 'Unitree', page: '../manufacturers/unitree.html', products: ['unitree-g1-d', 'unitree-g1', 'unitree-go2-edu'],
      uses: [
        ['VLA・模倣学習', '../use-cases/vla-data-collection.html'],
        ['大学研究導入', '../support/university-procurement.html'],
        ['巡回・点検', '../use-cases.html#inspection'],
      ],
      resources: '../resources.html?maker=unitree',
      caseLink: '../cases/keio-selection.html',
      caseLabel: '慶應義塾大学向け選定・見積支援',
    },
    agibot: {
      name: 'AgiBot', page: '../manufacturers/agibot.html', products: ['agibot-g2', 'agibot-x2-edu'],
      uses: [
        ['移動操作・PoC', '../support.html#poc'],
        ['VLA・模倣学習', '../use-cases/vla-data-collection.html'],
        ['研究教育', '../use-cases.html#university'],
      ],
      resources: '../resources.html?maker=agibot',
    },
  };

  const productMaker = {
    'unitree-g1-d': 'unitree', 'unitree-g1': 'unitree', 'unitree-go2': 'unitree',
    'agibot-g2': 'agibot', 'agibot-x2-edu': 'agibot',
  };

  if (path.includes('/manufacturers/unitree.html')) renderManufacturerRelations('unitree');
  if (path.includes('/manufacturers/agibot.html')) renderManufacturerRelations('agibot');

  const productSlug = path.match(/\/products\/([^/]+)\.html$/)?.[1];
  if (productSlug && productMaker[productSlug]) renderProductManufacturer(productMaker[productSlug]);

  async function renderManufacturerRelations(makerId) {
    const config = manufacturerMap[makerId];
    const main = document.querySelector('main');
    if (!main || document.querySelector('[data-manufacturer-relations]')) return;

    try {
      const response = await fetch('../data/products.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const products = (data.products || []).filter((item) => config.products.includes(item.id));
      const section = document.createElement('section');
      section.className = 'section muted';
      section.dataset.manufacturerRelations = makerId;
      section.innerHTML = `
        <div class="wrap"><div class="relation-panel">
          <div class="relation-panel-head"><div><p class="eyebrow">CONNECTED INFORMATION</p><h2>製品・用途・資料をまとめて確認。</h2><p>${escapeHtml(config.name)}の製品情報を、研究用途と導入実務につなげます。</p></div></div>
          <div class="relation-grid">
            ${products.map((item) => relationCard(item.detailPage.replace(/^products\//, '../products/'), item.name, item.categoryLabel, item.statusLabel)).join('')}
            ${(config.uses || []).map(([label, href]) => relationCard(href, label, '関連用途・支援', '確認する')).join('')}
            ${config.caseLink ? relationCard(config.caseLink, config.caseLabel, '導入事例', '進行状況を確認') : ''}
          </div>
          <div class="relation-actions"><a class="button secondary" href="${config.resources}">関連SDK・資料を見る</a><a class="button primary" href="../contact.html?maker=${encodeURIComponent(config.name)}">${escapeHtml(config.name)}の導入を相談する</a></div>
        </div></div>`;
      main.insertBefore(section, main.lastElementChild);
    } catch (error) {
      console.error('メーカー関連情報の読み込みに失敗しました。', error);
    }
  }

  function renderProductManufacturer(makerId) {
    const config = manufacturerMap[makerId];
    const detailMain = document.querySelector('.detail-main, .detail-grid > div, main .wrap');
    if (!detailMain || detailMain.querySelector('[data-product-maker-link]')) return;

    const block = document.createElement('aside');
    block.className = 'manufacturer-backlink';
    block.dataset.productMakerLink = makerId;
    block.innerHTML = `<p><strong>メーカー情報</strong><br>${escapeHtml(config.name)}の関連製品、SDK、用途、導入条件をまとめて確認できます。</p><a href="${config.page}">${escapeHtml(config.name)}のメーカー・関連情報を見る →</a>`;

    const specs = detailMain.querySelector('.specs');
    if (specs) specs.insertAdjacentElement('afterend', block);
    else detailMain.appendChild(block);
  }

  function relationCard(href, title, description, status) {
    return `<a class="relation-card" href="${href}"><small>${escapeHtml(status)}</small><strong>${escapeHtml(title)}</strong><span>${escapeHtml(description)}</span></a>`;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
    }[character]));
  }
})();
