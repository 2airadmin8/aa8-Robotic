(() => {
  'use strict';

  // ------------------------------------------------------------
  // 計測基盤
  // GA4 Measurement ID: G-XJYBMMPWWX
  // GT-5NXF29HN はGoogle tag IDであり、GTMコンテナIDではない。
  // 本サイトではGA4のgtag.jsのみを読み込み、個人情報は送信しない。
  // ------------------------------------------------------------
  initialiseAnalytics();

  function initialiseAnalytics() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };

    if (!document.querySelector('script[data-ga4-loader]')) {
      const gaScript = document.createElement('script');
      gaScript.async = true;
      gaScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-XJYBMMPWWX';
      gaScript.dataset.ga4Loader = 'true';
      document.head.appendChild(gaScript);

      window.gtag('js', new Date());
      window.gtag('config', 'G-XJYBMMPWWX', {
        anonymize_ip: true,
        send_page_view: true,
      });
    }
  }

  function trackEvent(eventName, parameters = {}) {
    const safeParameters = {
      page_path: window.location.pathname,
      ...parameters,
    };

    window.dataLayer?.push({ event: eventName, ...safeParameters });
    window.gtag?.('event', eventName, safeParameters);
  }

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
  // 共通クリック計測
  // ------------------------------------------------------------
  document.addEventListener('click', (event) => {
    const link = event.target.closest('a');
    if (!link) return;

    const href = link.getAttribute('href') || '';
    const label = link.textContent.trim().slice(0, 80);

    if (href.startsWith('mailto:')) {
      trackEvent('email_click', { link_label: label });
    } else if (link.matches('.nav-cta, .button, .product-consult-link')) {
      trackEvent('cta_click', { link_label: label, link_url: href });
    } else if (link.target === '_blank' || /^https?:\/\//.test(href)) {
      trackEvent('outbound_click', { link_label: label, link_url: href });
    }
  });

  // ------------------------------------------------------------
  // 製品カード
  // 製品情報は data/products.json を唯一の主データとして扱う。
  // 公開HTMLに事前描画済みの場合は、その内容をそのまま利用する。
  // ------------------------------------------------------------
  document.querySelectorAll('[data-product-list]').forEach(async (root) => {
    const hasPrerenderedCards = root.dataset.prerenderedProducts === 'true'
      && root.querySelector('.research-product-card');

    if (hasPrerenderedCards) {
      initialiseProductFilter(root);
      return;
    }

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
          ? '<span class="image-note">参考イメージ</span>'
          : '';
        const note = item.note
          ? `<p class="product-note">${item.note}</p>`
          : '';

        return `
          <article id="${item.id}" class="product-card research-product-card" data-product-groups="${filterGroups}" data-product-maker="${item.manufacturerId}">
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
      if (!root.querySelector('.research-product-card')) {
        root.innerHTML = '<p>製品情報を読み込めませんでした。</p>';
      }
    }
  });

  function initialiseProductFilter(productRoot) {
    const filterButtons = [...document.querySelectorAll('[data-product-filter]')];
    if (!filterButtons.length || productRoot.dataset.filterReady === 'true') return;
    productRoot.dataset.filterReady = 'true';

    const query = new URLSearchParams(window.location.search);
    const maker = query.get('maker') || 'all';
    const requestedFilter = query.get('filter') || 'all';
    const availableFilters = filterButtons.map((button) => button.dataset.productFilter);
    const initialFilter = availableFilters.includes(requestedFilter) ? requestedFilter : 'all';

    const applyFilter = (selectedGroup, shouldTrack = false) => {
      filterButtons.forEach((button) => {
        button.classList.toggle('is-active', button.dataset.productFilter === selectedGroup);
      });

      productRoot.querySelectorAll('[data-product-groups]').forEach((card) => {
        const groups = card.dataset.productGroups.split(' ');
        const groupMatch = selectedGroup === 'all' || groups.includes(selectedGroup);
        const makerMatch = maker === 'all' || card.dataset.productMaker === maker;
        card.hidden = !(groupMatch && makerMatch);
      });

      const url = new URL(window.location.href);
      if (selectedGroup === 'all') url.searchParams.delete('filter');
      else url.searchParams.set('filter', selectedGroup);
      window.history.replaceState({}, '', url);

      if (shouldTrack) {
        trackEvent('product_filter', { filter_name: selectedGroup, maker_filter: maker });
      }
    };

    filterButtons.forEach((button) => {
      button.addEventListener('click', () => applyFilter(button.dataset.productFilter, true));
    });

    applyFilter(initialFilter);
  }

  // ------------------------------------------------------------
  // 資料・SDKセンター
  // ------------------------------------------------------------
  document.querySelectorAll('[data-resource-list]').forEach(async (root) => {
    const hasPrerenderedCards = root.dataset.prerenderedResources === 'true'
      && root.querySelector('.resource-card');

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
          const searchableText = [item.title, item.description, item.makerName, item.language, ...(item.keywords || [])].join(' ').toLowerCase();
          const keywordMatch = !keyword || searchableText.includes(keyword);
          return makerMatch && productMatch && typeMatch && keywordMatch;
        });

        root.innerHTML = filtered.map(createResourceCard).join('');
        if (count) count.textContent = String(filtered.length);
        if (empty) empty.hidden = filtered.length !== 0;
      };

      const query = new URLSearchParams(window.location.search);
      const initialConditions = {
        maker: query.get('maker') || 'all',
        product: query.get('product') || 'all',
        type: query.get('type') || 'all',
        keyword: query.get('keyword') || '',
      };

      if (form) {
        Object.entries(initialConditions).forEach(([name, value]) => {
          const field = form.elements.namedItem(name);
          if (field && value) field.value = value;
        });
      }
      render(initialConditions);

      if (form) {
        form.addEventListener('submit', (event) => {
          event.preventDefault();
          const values = new FormData(form);
          const conditions = {
            maker: values.get('maker'),
            product: values.get('product'),
            type: values.get('type'),
            keyword: values.get('keyword'),
          };
          render(conditions);
          trackEvent('resource_search', {
            maker_filter: String(conditions.maker),
            product_filter: String(conditions.product),
            type_filter: String(conditions.type),
          });
        });

        form.addEventListener('reset', () => window.setTimeout(() => render(), 0));
      }

      document.querySelectorAll('[data-resource-shortcut]').forEach((button) => {
        button.addEventListener('click', () => {
          const selectedType = button.dataset.resourceShortcut;
          const typeSelect = form?.querySelector('[name="type"]');
          if (typeSelect) typeSelect.value = selectedType;
          render({ type: selectedType });
          trackEvent('resource_shortcut', { resource_type: selectedType });
          document.querySelector('#resource-search')?.scrollIntoView({ behavior: 'smooth' });
        });
      });
    } catch (error) {
      console.error('資料情報の読み込みに失敗しました。', error);
      if (hasPrerenderedCards) {
        const count = document.querySelector('[data-resource-count]');
        if (count) count.textContent = String(root.querySelectorAll('.resource-card').length);
        root.dataset.runtimeStatus = 'static-fallback';
      } else {
        root.innerHTML = '<p>資料情報を読み込めませんでした。</p>';
      }
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
      official: '公式入口', sdk: 'SDK', ros: 'ROS・ROS2', vla: 'VLA・学習',
      teleoperation: 'テレオペ', simulation: 'シミュレーション', dataset: 'データセット',
    };
    return labels[type] || type;
  }

  // ------------------------------------------------------------
  // 問い合わせフォーム
  // GitHub Pagesのため、入力内容からmailto文面を生成する。
  // 実際の送信完了は利用者のメールアプリ側で行う。
  // ------------------------------------------------------------
  const contactForm = document.querySelector('[data-contact-form]');

  if (contactForm) {
    const query = new URLSearchParams(window.location.search);
    const sourceFields = {
      source_page: document.referrer || window.location.href,
      source_product: query.get('product') || '',
      source_maker: query.get('maker') || '',
      source_service: query.get('service') || '',
      source_theme: query.get('theme') || '',
    };

    Object.entries(sourceFields).forEach(([name, value]) => {
      const field = contactForm.elements.namedItem(name);
      if (field) field.value = value;
    });

    const productField = contactForm.elements.namedItem('product');
    const categoryField = contactForm.elements.namedItem('category');
    if (productField && sourceFields.source_product) productField.value = sourceFields.source_product;
    if (productField && sourceFields.source_maker && !productField.value) productField.value = sourceFields.source_maker;

    const categoryMap = {
      poc: 'PoC設計',
      'university-procurement': '見積・大学購買',
      'vla-data-collection': 'VLA・模倣学習データ収集',
      'technical-review': 'SDK・ROS・開発環境',
      'multi-brand-comparison': '製品比較・選定',
    };
    const mappedCategory = categoryMap[sourceFields.source_service] || categoryMap[sourceFields.source_theme];
    if (categoryField && mappedCategory) categoryField.value = mappedCategory;

    let formStarted = false;
    contactForm.addEventListener('input', () => {
      if (formStarted) return;
      formStarted = true;
      trackEvent('form_start', { form_name: 'robotics_contact' });
    });

    contactForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const errorBox = contactForm.querySelector('[data-form-error]');
      const requiredFields = [...contactForm.querySelectorAll('[required]')];
      let firstInvalid = null;

      requiredFields.forEach((field) => {
        const invalid = field.type === 'checkbox' ? !field.checked : !field.value.trim();
        field.setAttribute('aria-invalid', String(invalid));
        if (invalid && !firstInvalid) firstInvalid = field;
      });

      const emailField = contactForm.elements.namedItem('email');
      if (emailField && emailField.value && !emailField.validity.valid) {
        emailField.setAttribute('aria-invalid', 'true');
        firstInvalid ||= emailField;
      }

      if (firstInvalid) {
        if (errorBox) {
          errorBox.hidden = false;
          errorBox.textContent = '必須項目とメールアドレスをご確認ください。';
        }
        firstInvalid.focus();
        trackEvent('form_error', { form_name: 'robotics_contact' });
        return;
      }

      if (errorBox) errorBox.hidden = true;
      const values = new FormData(contactForm);
      const subject = createMailSubject(values);
      const body = createMailBody(values);
      const mailtoUrl = `mailto:airobot@robotics.air-admin8.co.jp?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

      trackEvent('generate_lead', {
        form_name: 'robotics_contact',
        inquiry_category: String(values.get('category') || ''),
        source_product: String(values.get('source_product') || ''),
        source_maker: String(values.get('source_maker') || ''),
        source_service: String(values.get('source_service') || ''),
        source_theme: String(values.get('source_theme') || ''),
        submission_method: 'mailto_intent',
      });

      window.location.href = mailtoUrl;
    });
  }

  function createMailSubject(values) {
    const category = String(values.get('category') || '製品・導入相談');
    const organization = String(values.get('organization') || '');
    return `【AirAdmin8 Robotics相談】${category}｜${organization}`;
  }

  function createMailBody(values) {
    const lines = [
      'AirAdmin8 Robotics ご担当者様',
      '',
      '下記の内容で相談します。',
      '',
      `大学・会社名：${values.get('organization') || ''}`,
      `お名前：${values.get('name') || ''}`,
      `メールアドレス：${values.get('email') || ''}`,
      `電話番号：${values.get('phone') || '未記入'}`,
      `相談区分：${values.get('category') || ''}`,
      `検討中の製品・メーカー：${values.get('product') || '未定'}`,
      `予算感：${values.get('budget') || '未定'}`,
      `希望時期：${values.get('schedule') || '未定'}`,
      `SDK・開発環境：${values.get('development') || '未記入'}`,
      '',
      '【研究・業務用途】',
      values.get('use_case') || '',
      '',
      '【補足・確認したいこと】',
      values.get('message') || '未記入',
      '',
      '【流入情報】',
      `参照ページ：${values.get('source_page') || window.location.href}`,
      `製品：${values.get('source_product') || ''}`,
      `メーカー：${values.get('source_maker') || ''}`,
      `支援：${values.get('source_service') || ''}`,
      `用途：${values.get('source_theme') || ''}`,
    ];
    return lines.join('\n');
  }
})();
