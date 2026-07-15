(() => {
  'use strict';

  const useCaseMap = {
    university: {
      title: '大学研究・教育',
      href: 'use-cases.html#university',
      description: '研究要件、SDK、購買条件から候補を整理',
      products: ['unitree-g1-d', 'unitree-g1', 'unitree-go2-edu'],
      caution: '研究テーマ、必要な制御範囲、大学購買条件により候補は変わります。',
    },
    data: {
      title: 'データ収集・VLA',
      href: 'use-cases/vla-data-collection.html',
      description: 'テレオペ、観測・行動、記録形式を設計',
      products: ['unitree-g1-d', 'agibot-g2', 'tianji-marvin'],
      caution: '標準機能、追加機材、個別開発の範囲を分けて確認します。',
    },
    inspection: {
      title: '巡回・点検',
      href: 'use-cases.html#inspection',
      description: '路面、段差、通信、センサー条件から比較',
      products: ['unitree-go2-edu'],
      caution: '自律巡回や点検機能は、センサー・通信・ソフトウェア構成を含めてPoCで確認します。',
    },
    transport: {
      title: '搬送',
      href: 'use-cases.html#transport',
      description: '可搬重量、通路、設備連携、安全条件を確認',
      products: ['agibot-g2'],
      caution: '現在掲載中の候補は研究・PoC向けです。標準AMR案件は現場条件から別途選定します。',
    },
    manipulation: {
      title: '把持・操作',
      href: 'use-cases.html#manipulation',
      description: '対象物、精度、力制御、ハンドから比較',
      products: ['agibot-g2', 'unitree-g1-d', 'tianji-marvin'],
      caution: '把持性能は対象物、ハンド、制御周期、学習方式により変わります。',
    },
    lab: {
      title: '実験室自動化',
      href: 'use-cases.html#lab',
      description: '装置連携、再現性、記録、安全を設計',
      products: ['agibot-g2', 'unitree-g1-d', 'tianji-marvin'],
      caution: '掲載製品だけで完結するとは限りません。治具、装置API、安全設計を含むシステム構成で判断します。',
    },
  };

  const useCaseAliases = {
    'vla-data-collection': 'data',
    'imitation-learning': 'data',
    teleoperation: 'data',
    inspection: 'inspection',
    education: 'university',
    'mobility-research': 'inspection',
    manipulation: 'manipulation',
    'factory-automation': 'lab',
    locomotion: 'university',
    'reinforcement-learning': 'university',
    'humanoid-research': 'university',
    'assembly-training': 'university',
    'motion-control': 'university',
    'whole-body-control': 'university',
  };

  const path = window.location.pathname;
  if (path.endsWith('/use-cases.html') || path.endsWith('use-cases.html')) renderUseCaseRecommendations();
  if (/\/products\/[^/]+\.html$/.test(path)) renderProductUseRelations();

  async function loadProducts(prefix = '') {
    const response = await fetch(`${prefix}data/products.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return (data.products || []).filter((item) => item.visibility === 'public');
  }

  async function renderUseCaseRecommendations() {
    try {
      const products = await loadProducts('');
      Object.entries(useCaseMap).forEach(([key, config]) => {
        const card = document.getElementById(key);
        if (!card || card.querySelector('[data-use-products]')) return;
        const recommended = config.products
          .map((id) => products.find((item) => item.id === id))
          .filter(Boolean);

        const block = document.createElement('div');
        block.className = 'use-product-recommendations';
        block.dataset.useProducts = key;
        block.innerHTML = `
          <strong>候補製品</strong>
          <div class="use-product-list">
            ${recommended.map((item) => `
              <a class="use-product-link" href="${escapeHtml(item.detailPage)}">
                <span><small>${escapeHtml(item.manufacturerName)} / ${escapeHtml(item.categoryLabel)}</small><b>${escapeHtml(item.name)}</b></span>
                <em>${escapeHtml(item.statusLabel)} →</em>
              </a>`).join('')}
          </div>
          <p class="use-product-caution">${escapeHtml(config.caution)}</p>`;
        card.appendChild(block);
      });
    } catch (error) {
      console.error('用途別候補製品の読み込みに失敗しました。', error);
    }
  }

  async function renderProductUseRelations() {
    try {
      const slug = path.match(/\/products\/([^/]+)\.html$/)?.[1];
      if (!slug) return;
      const products = await loadProducts('../');
      const product = products.find((item) => item.id === slug);
      if (!product) return;

      const keys = [...new Set((product.useCaseIds || []).map((id) => useCaseAliases[id]).filter(Boolean))];
      if (!keys.length) return;

      const detailMain = document.querySelector('.detail-main, .detail-grid > div, main .wrap');
      if (!detailMain || detailMain.querySelector('[data-product-use-relations]')) return;

      const section = document.createElement('section');
      section.className = 'product-use-relations';
      section.dataset.productUseRelations = slug;
      section.innerHTML = `
        <p class="eyebrow">RELATED USE CASES</p>
        <h2>この製品に関連する用途。</h2>
        <p>製品仕様だけでなく、対象タスクと成功条件から導入可否を判断します。</p>
        <div class="product-use-link-grid">
          ${keys.map((key) => {
            const item = useCaseMap[key];
            const href = item.href.startsWith('use-cases/') ? `../${item.href}` : `../${item.href}`;
            return `<a href="${escapeHtml(href)}"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.description)} →</span></a>`;
          }).join('')}
        </div>`;

      const related = [...detailMain.querySelectorAll('h2')].find((heading) => heading.textContent.includes('関連情報'));
      if (related) related.insertAdjacentElement('beforebegin', section);
      else detailMain.appendChild(section);
    } catch (error) {
      console.error('製品関連用途の読み込みに失敗しました。', error);
    }
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
    }[character]));
  }
})();
