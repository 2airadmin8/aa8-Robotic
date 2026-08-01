(() => {
  'use strict';

  const stylesheet = document.querySelector('link[href*="main-site-experience.css"]');
  const baseUrl = stylesheet
    ? new URL(stylesheet.getAttribute('href'), document.baseURI).href.replace(/assets\/css\/main-site-experience\.css(?:\?[^#]*)?$/, '')
    : new URL('./', document.baseURI).href;

  const makeUrl = (path) => new URL(path, baseUrl).href;
  const logoMarkup = `<img class="aa8-main-logo" src="${makeUrl('assets/img/airadmin8-official-logo.png?v=20260731-1')}" alt="AirAdmin8">`;

  document.querySelectorAll(
    '.site-header .brand, .header .brand, header[role="banner"] .brand, .mobile-menu .brand, .drawer .brand, .menu-drawer .brand, .nav-drawer .brand'
  ).forEach((brand) => {
    if (!(brand instanceof HTMLElement)) return;
    brand.setAttribute('aria-label', 'AirAdmin8 ロボティクス ホーム');
    brand.innerHTML = logoMarkup;
  });

  document.querySelectorAll('.site-footer strong, .site-footer .footer-brand, footer .brand').forEach((brand) => {
    if (!(brand instanceof HTMLElement)) return;
    brand.classList.add('aa8-footer-brand');
    brand.innerHTML = logoMarkup;
  });

  const topButton = document.createElement('button');
  topButton.className = 'aa8-back-to-top';
  topButton.type = 'button';
  topButton.setAttribute('aria-label', 'ページ上部へ戻る');
  topButton.setAttribute('title', 'ページ上部へ戻る');
  topButton.innerHTML = '<span aria-hidden="true">↑</span>';
  topButton.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  document.body.appendChild(topButton);

  const updateTopButton = () => topButton.classList.toggle('is-visible', window.scrollY > 480);
  window.addEventListener('scroll', updateTopButton, { passive: true });
  updateTopButton();

  document.querySelectorAll('.aa8-mobile-quicknav').forEach((nav) => nav.remove());

  if (document.querySelector('.product-page-hero')) {
    const productFixes = document.createElement('style');
    productFixes.id = 'aa8-product-page-runtime-fixes';
    productFixes.textContent = `
      .product-page-hero { padding-bottom: 30px !important; }
      .product-page-hero + .section { padding-top: 34px !important; }
      .priority-category-main,
      .priority-category-main h3,
      .priority-category-main p,
      .priority-category-main strong,
      .priority-category-main .card-index { color: #fff !important; }
      .priority-category-main p {
        color: rgba(255,255,255,.94) !important;
        font-weight: 600;
        line-height: 1.75;
      }
      .priority-category-main h3,
      .priority-category-main strong { text-shadow: 0 1px 2px rgba(0,45,72,.18); }
      .category-priority-grid { margin-bottom: 0 !important; }
      #lineup { padding-top: 38px !important; }
      main > section:nth-of-type(4) { padding-bottom: 34px !important; }
      main > section:nth-of-type(5) { padding-top: 38px !important; }
      @media (max-width: 760px) {
        .product-page-hero { padding-bottom: 22px !important; }
        .product-page-hero + .section { padding-top: 26px !important; }
        #lineup { padding-top: 30px !important; }
        main > section:nth-of-type(4) { padding-bottom: 26px !important; }
        main > section:nth-of-type(5) { padding-top: 30px !important; }
      }
    `;
    document.head.appendChild(productFixes);

    const categoryGrid = document.querySelector('.category-priority-grid');
    const categorySection = categoryGrid?.closest('section');
    if (categorySection instanceof HTMLElement) {
      categorySection.style.paddingBottom = window.matchMedia('(max-width: 760px)').matches ? '26px' : '34px';
    }

    document.querySelectorAll('.selection-note li').forEach((item) => {
      if (!(item instanceof HTMLElement)) return;
      item.textContent = item.textContent
        .replace('SDK・ROS・シミュレータ', 'SDK・ROS・シミュレーター')
        .replace('保証・改造・日本導入条件', '保証・改造・導入条件');
    });
  }

  if (document.querySelector('.theme-grid')) {
    const themeFixes = document.createElement('style');
    themeFixes.id = 'aa8-theme-card-runtime-fixes';
    themeFixes.textContent = `
      .theme-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        align-items: stretch !important;
      }
      .theme-grid .theme-card {
        align-self: stretch !important;
        height: 100%;
        border-top: 4px solid #009ad2 !important;
      }
      .theme-links {
        margin-top: 20px !important;
        padding-top: 0 !important;
        min-height: 32px;
        align-items: center;
      }
      .theme-card > p:not(.theme-label) {
        min-height: 3.6em;
      }
      .theme-tags {
        min-height: 36px;
      }
      @media (max-width: 980px) {
        .theme-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }
        .theme-card > p:not(.theme-label),
        .theme-tags,
        .theme-links { min-height: 0; }
      }
      @media (max-width: 640px) {
        .theme-grid { grid-template-columns: 1fr !important; }
        .theme-grid .theme-card { height: auto; }
      }
    `;
    document.head.appendChild(themeFixes);
  }

  document.querySelectorAll('p').forEach((node) => {
    if (!(node instanceof HTMLElement)) return;
    if (node.textContent?.includes('公開Repository')) {
      node.textContent = node.textContent.replace('公開Repository', '公開リポジトリ');
    }
  });

  document.querySelectorAll('[id]').forEach((node) => {
    if (node instanceof HTMLElement) node.style.scrollMarginTop = '96px';
  });
})();
