(() => {
  'use strict';

  const siteOrigin = 'https://2airadmin8.github.io';
  const siteBase = '/aa8-Robotic/';
  const canonicalBase = `${siteOrigin}${siteBase}`;
  const path = window.location.pathname;
  const relativePath = path.startsWith(siteBase) ? path.slice(siteBase.length) : path.replace(/^\//, '');
  const cleanPath = relativePath || 'index.html';

  injectBrowserIdentity();

  const pageMap = {
    'index.html': { name: 'AirAdmin8 Robotics', type: 'WebSite' },
    'products.html': { name: '研究用AIロボット製品比較', type: 'CollectionPage' },
    'use-cases.html': { name: '研究テーマ・用途から探す', type: 'CollectionPage' },
    'support.html': { name: 'AIロボット導入支援', type: 'Service' },
    'cases.html': { name: 'AIロボット導入事例', type: 'CollectionPage' },
    'resources.html': { name: 'AIロボット開発資料・SDK', type: 'CollectionPage' },
    'manufacturers.html': { name: 'AIロボットメーカー比較', type: 'CollectionPage' },
    'contact.html': { name: 'AIロボット製品・導入相談', type: 'ContactPage' },
    'privacy.html': { name: 'プライバシーポリシー', type: 'WebPage' },
    'faq.html': { name: 'よくある質問', type: 'FAQPage' },
    'products/unitree-g1-d.html': { name: 'Unitree G1-D', type: 'Product', brand: 'Unitree', availability: 'https://schema.org/InStock' },
    'products/agibot-g2.html': { name: 'AgiBot G2', type: 'Product', brand: 'AgiBot', availability: 'https://schema.org/InStock' },
    'products/unitree-go2.html': { name: 'Unitree Go2 EDU', type: 'Product', brand: 'Unitree', availability: 'https://schema.org/InStock' },
    'products/agibot-x2-edu.html': { name: 'AgiBot X2 EDU', type: 'Product', brand: 'AgiBot', availability: 'https://schema.org/PreOrder' },
    'manufacturers/unitree.html': { name: 'Unitree Robotics', type: 'Brand' },
    'manufacturers/agibot.html': { name: 'AgiBot', type: 'Brand' },
    'use-cases/vla-data-collection.html': { name: 'VLA・模倣学習データ収集', type: 'Service' },
    'support/university-procurement.html': { name: '大学研究用AIロボット導入・購買支援', type: 'Service' },
    'cases/keio-selection.html': { name: '慶應義塾大学向け選定・見積支援', type: 'Article' },
  };

  const page = pageMap[cleanPath] || {
    name: document.querySelector('h1')?.textContent.trim() || document.title,
    type: 'WebPage',
  };

  injectJsonLd({
    '@context': 'https://schema.org',
    '@type': 'Organization',
    '@id': `${canonicalBase}#organization`,
    name: '株式会社AirAdmin8',
    alternateName: 'AirAdmin8 Robotics',
    url: canonicalBase,
    email: 'airobot@robotics.air-admin8.co.jp',
    address: {
      '@type': 'PostalAddress',
      postalCode: '100-0004',
      addressRegion: '東京都',
      addressLocality: '千代田区',
      streetAddress: '大手町一丁目9番2号 大手町フィナンシャルシティ グランキューブ18階',
      addressCountry: 'JP',
    },
  }, 'organization-schema');

  injectJsonLd(createPageSchema(page), 'page-schema');
  injectJsonLd(createBreadcrumbSchema(), 'breadcrumb-schema');

  if (cleanPath === 'faq.html') injectFaqSchema();

  function injectBrowserIdentity() {
    ensureMeta('theme-color', '#0b3143');
    ensureMeta('apple-mobile-web-app-capable', 'yes');
    ensureMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');
    ensureMeta('apple-mobile-web-app-title', 'A8 Robotics');
    ensureLink('icon', `${siteBase}assets/img/favicon.svg`, 'image/svg+xml');
    ensureLink('mask-icon', `${siteBase}assets/img/favicon.svg`, 'image/svg+xml', '#009ad2');
    ensureLink('manifest', `${siteBase}site.webmanifest`);
  }

  function ensureMeta(name, content) {
    if (document.querySelector(`meta[name="${name}"]`)) return;
    const meta = document.createElement('meta');
    meta.name = name;
    meta.content = content;
    document.head.appendChild(meta);
  }

  function ensureLink(rel, href, type = '', color = '') {
    if (document.querySelector(`link[rel="${rel}"]`)) return;
    const link = document.createElement('link');
    link.rel = rel;
    link.href = href;
    if (type) link.type = type;
    if (color) link.setAttribute('color', color);
    document.head.appendChild(link);
  }

  function createPageSchema(config) {
    const canonical = document.querySelector('link[rel="canonical"]')?.href || `${canonicalBase}${cleanPath === 'index.html' ? '' : cleanPath}`;
    const description = document.querySelector('meta[name="description"]')?.content || '';
    const base = {
      '@context': 'https://schema.org',
      '@type': config.type,
      '@id': `${canonical}#page`,
      name: config.name,
      url: canonical,
      description,
      inLanguage: 'ja-JP',
      isPartOf: {
        '@type': 'WebSite',
        '@id': `${canonicalBase}#website`,
        name: 'AirAdmin8 Robotics',
        url: canonicalBase,
      },
      provider: { '@id': `${canonicalBase}#organization` },
    };

    if (config.type === 'Product') {
      base.brand = { '@type': 'Brand', name: config.brand };
      base.category = document.querySelector('.eyebrow')?.textContent.trim() || 'AI Robot';
      base.offers = {
        '@type': 'Offer',
        url: canonical,
        priceCurrency: 'JPY',
        priceSpecification: {
          '@type': 'PriceSpecification',
          priceCurrency: 'JPY',
          description: '価格は構成・時期により異なるため正式見積で提示',
        },
        availability: config.availability,
        seller: { '@id': `${canonicalBase}#organization` },
      };
    }

    if (config.type === 'Article') {
      base.headline = config.name;
      base.author = { '@id': `${canonicalBase}#organization` };
      base.publisher = { '@id': `${canonicalBase}#organization` };
      base.dateModified = document.lastModified ? new Date(document.lastModified).toISOString() : undefined;
    }

    return base;
  }

  function createBreadcrumbSchema() {
    const breadcrumb = document.querySelector('.breadcrumb');
    const links = breadcrumb ? [...breadcrumb.querySelectorAll('a')] : [];
    const items = links.map((link, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: link.textContent.trim(),
      item: new URL(link.getAttribute('href'), window.location.href).href,
    }));

    if (!items.length || items[items.length - 1].item !== window.location.href.split(/[?#]/)[0]) {
      items.push({
        '@type': 'ListItem',
        position: items.length + 1,
        name: page.name,
        item: window.location.href.split(/[?#]/)[0],
      });
    }

    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: items,
    };
  }

  function injectFaqSchema() {
    const entries = [...document.querySelectorAll('[data-faq-item]')].map((item) => ({
      '@type': 'Question',
      name: item.querySelector('summary')?.textContent.trim() || '',
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.querySelector('.faq-answer')?.textContent.trim() || '',
      },
    })).filter((entry) => entry.name && entry.acceptedAnswer.text);

    injectJsonLd({
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: entries,
    }, 'faq-schema');
  }

  function injectJsonLd(data, id) {
    if (document.getElementById(id)) return;
    const script = document.createElement('script');
    script.id = id;
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(data);
    document.head.appendChild(script);
  }
})();