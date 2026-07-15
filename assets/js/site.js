(() => {
  'use strict';

  // ------------------------------------------------------------
  // モバイルナビゲーション
  // ------------------------------------------------------------
  const menuButton = document.querySelector('.menu');
  const navigation = document.querySelector('.nav');

  if (menuButton && navigation) {
    menuButton.addEventListener('click', () => {
      const isOpen = navigation.classList.toggle('open');
      menuButton.setAttribute('aria-expanded', String(isOpen));
    });

    navigation.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        navigation.classList.remove('open');
        menuButton.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ------------------------------------------------------------
  // 製品カード
  // 製品情報は data/products.json を唯一の主データとして扱う。
  // ------------------------------------------------------------
  document.querySelectorAll('[data-product-list]').forEach(async (root) => {
    try {
      const response = await fetch(root.dataset.source || 'data/products.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const limit = Number(root.dataset.limit || 0);
      const products = data.products.filter((item) => item.visibility === 'public');
      const visibleProducts = limit > 0 ? products.slice(0, limit) : products;

      root.innerHTML = visibleProducts.map((item) => {
        const filterGroups = (item.filterGroups || [item.categoryId]).join(' ');
        const featureLabels = (item.featureLabels || []).slice(0, 4);
        const useLabels = (item.useLabels || []).slice(0, 4);
        const placeholderLabel = item.imageStatus === 'placeholder'
          ? '<span class="image-note">製品画像準備中</span>'
          : '';
        const note = item.note
          ? `<p class="product-note">${item.note}</p>`
          : '';

        return `
          <article id="${item.id}" class="product-card research-product-card" data-product-groups="${filterGroups}">
            <a class="product-visual" href="${item.detailPage}" aria-label="${item.name}の詳細を見る">
              <img src="${item.image}" alt="${item.imageAlt || `${item.name}の製品イメージ`}" loading="lazy">
              ${placeholderLabel}
            </a>
            <div class="product-body">
              <div class="product-topline">
                <p class="product-maker">${item.manufacturerName}</p>
                <span class="status status-${item.status}">${item.statusLabel}</span>
              </div>
              <h3><a href="${item.detailPage}">${item.name}</a></h3>
              <p class="product-summary">${item.summary}</p>
              <div class="feature-list">
                ${featureLabels.map((label) => `<span>${label}</span>`).join('')}
              </div>
              <div class="meta product-condition-meta">
                <span class="tag">${item.priceLabel}</span>
                <span class="tag">${item.leadTimeLabel}</span>
              </div>
              <p class="use-labels">${useLabels.join('・')}</p>
              ${note}
              <div class="product-card-actions">
                <a class="product-link" href="${item.detailPage}">詳細を見る →</a>
                <a class="product-consult-link" href="contact.html?product=${encodeURIComponent(item.name)}">研究用途を相談</a>
              </div>
            </div>
          </article>
        `;
      }).join('');

      initialiseProductFilter(root);
    } catch (error) {
      console.error('製品情報の読み込みに失敗しました。', error);
      root.innerHTML = '<p>製品情報を読み込めませんでした。</p>';
    }
  });

  // ------------------------------------------------------------
  // 製品カテゴリ絞り込み
  // ------------------------------------------------------------
  function initialiseProductFilter(productRoot) {
    const filterButtons = document.querySelectorAll('[data-product-filter]');
    if (!filterButtons.length) return;

    filterButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const selectedGroup = button.dataset.productFilter;

        filterButtons.forEach((item) => item.classList.remove('is-active'));
        button.classList.add('is-active');

        productRoot.querySelectorAll('[data-product-groups]').forEach((card) => {
          const groups = card.dataset.productGroups.split(' ');
          const shouldShow = selectedGroup === 'all' || groups.includes(selectedGroup);
          card.hidden = !shouldShow;
        });
      });
    });
  }

  // ------------------------------------------------------------
  // 資料・SDKセンター
  // 公式URL、用途分類、確認状態は data/resources.json で管理する。
  // ------------------------------------------------------------
  document.querySelectorAll('[data-resource-list]').forEach(async (root) => {
    try {
      const response = await fetch(root.dataset.source || 'data/resources.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const resources = data.resources || [];
      const form = document.querySelector('[data-resource-filter-form]');
      const count = document.querySelector('[data-resource-count]');
      const empty = document.querySelector('[data-resource-empty]');

      const render = (conditions = {}) => {
        const maker = conditions.maker || 'all';
        const product = conditions.product || 'all';
        const type = conditions.type || 'all';
        const keyword = (conditions.keyword || '').trim().toLowerCase();

        const filtered = resources.filter((item) => {
          const makerMatch = maker === 'all' || item.makerId === maker;
          const productMatch = product === 'all' || item.productGroups.includes(product);
          const typeMatch = type === 'all' || item.types.includes(type);
          const searchableText = [
            item.title,
            item.description,
            item.makerName,
            item.language,
            ...(item.keywords || []),
          ].join(' ').toLowerCase();
          const keywordMatch = !keyword || searchableText.includes(keyword);

          return makerMatch && productMatch && typeMatch && keywordMatch;
        });

        root.innerHTML = filtered.map(createResourceCard).join('');
        if (count) count.textContent = String(filtered.length);
        if (empty) empty.hidden = filtered.length !== 0;
      };

      render();

      if (form) {
        form.addEventListener('submit', (event) => {
          event.preventDefault();
          const values = new FormData(form);
          render({
            maker: values.get('maker'),
            product: values.get('product'),
            type: values.get('type'),
            keyword: values.get('keyword'),
          });
        });

        form.addEventListener('reset', () => {
          window.setTimeout(() => render(), 0);
        });
      }

      document.querySelectorAll('[data-resource-shortcut]').forEach((button) => {
        button.addEventListener('click', () => {
          const selectedType = button.dataset.resourceShortcut;
          const typeSelect = form?.querySelector('[name="type"]');
          if (typeSelect) typeSelect.value = selectedType;
          render({ type: selectedType });
          document.querySelector('#resource-search')?.scrollIntoView({ behavior: 'smooth' });
        });
      });
    } catch (error) {
      console.error('資料情報の読み込みに失敗しました。', error);
      root.innerHTML = '<p>資料情報を読み込めませんでした。</p>';
    }
  });

  function createResourceCard(item) {
    const typeLabels = item.types.map((type) => `<span>${resourceTypeLabel(type)}</span>`).join('');
    const action = item.url
      ? `<a class="resource-open-link" href="${item.url}" target="_blank" rel="noopener noreferrer">公式ページを開く ↗</a>`
      : '<span class="resource-link-pending">公式URL確認中</span>';

    return `
      <article class="resource-card">
        <div class="resource-card-topline">
          <p class="resource-maker">${item.makerName}</p>
          <span class="resource-status ${item.reviewStatus}">${item.reviewLabel}</span>
        </div>
        <h3>${item.title}</h3>
        <p class="resource-description">${item.description}</p>
        <div class="resource-type-list">${typeLabels}</div>
        <dl class="resource-meta-list">
          <div><dt>出典</dt><dd>${item.sourceLabel}</dd></div>
          <div><dt>言語</dt><dd>${item.language}</dd></div>
        </dl>
        <div class="resource-card-footer">${action}</div>
      </article>
    `;
  }

  function resourceTypeLabel(type) {
    const labels = {
      official: '公式入口',
      sdk: 'SDK',
      ros: 'ROS・ROS2',
      vla: 'VLA・学習',
      teleoperation: 'テレオペ',
      simulation: 'シミュレーション',
      dataset: 'データセット',
    };

    return labels[type] || type;
  }
})();