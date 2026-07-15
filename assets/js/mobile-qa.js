(() => {
  'use strict';

  const menuButton = document.querySelector('.menu');
  const navigation = document.querySelector('.nav');

  if (menuButton && navigation) {
    menuButton.setAttribute('aria-label', 'メニューを開閉する');

    const syncNavigationState = () => {
      const isOpen = navigation.classList.contains('open');
      menuButton.setAttribute('aria-expanded', String(isOpen));
      document.body.classList.toggle('nav-is-open', isOpen);
    };

    const closeNavigation = () => {
      navigation.classList.remove('open');
      syncNavigationState();
    };

    menuButton.addEventListener('click', () => {
      window.requestAnimationFrame(syncNavigationState);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && navigation.classList.contains('open')) {
        closeNavigation();
        menuButton.focus();
      }
    });

    document.addEventListener('click', (event) => {
      if (!navigation.classList.contains('open')) return;
      if (navigation.contains(event.target) || menuButton.contains(event.target)) return;
      closeNavigation();
    });

    window.addEventListener('resize', () => {
      if (window.matchMedia('(min-width: 981px)').matches) closeNavigation();
    });
  }

  // 構築時の共通フッターに会社情報が未反映でも、全ページから到達できるよう補完する。
  const footerLinks = document.querySelector('.footer-links');
  if (footerLinks && !footerLinks.querySelector('a[href$="about.html"]')) {
    const depth = window.location.pathname.includes('/products/')
      || window.location.pathname.includes('/manufacturers/')
      || window.location.pathname.includes('/use-cases/')
      || window.location.pathname.includes('/support/')
      || window.location.pathname.includes('/cases/')
      ? '../'
      : '';
    const companyLink = document.createElement('a');
    companyLink.href = `${depth}about.html`;
    companyLink.textContent = '会社情報';

    const privacyLink = [...footerLinks.querySelectorAll('a')]
      .find((link) => link.getAttribute('href')?.endsWith('privacy.html'));
    if (privacyLink) footerLinks.insertBefore(companyLink, privacyLink);
    else footerLinks.appendChild(companyLink);
  }

  // 製品一覧はJSON描画後にIDが生成されるため、描画完了後にアンカー移動する。
  const productList = document.querySelector('[data-product-list]');
  if (productList && window.location.hash) {
    const targetId = decodeURIComponent(window.location.hash.slice(1));
    const observer = new MutationObserver(() => {
      const target = document.getElementById(targetId);
      if (!target) return;
      observer.disconnect();
      window.requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
    });
    observer.observe(productList, { childList: true });
  }

  // URLのfilter指定を製品絞り込みボタンへ反映する。
  const requestedFilter = new URLSearchParams(window.location.search).get('filter');
  if (requestedFilter) {
    const filterButton = document.querySelector(`[data-product-filter="${CSS.escape(requestedFilter)}"]`);
    if (filterButton) {
      const clickWhenReady = () => {
        if (!document.querySelector('[data-product-groups]')) {
          window.requestAnimationFrame(clickWhenReady);
          return;
        }
        filterButton.click();
      };
      clickWhenReady();
    }
  }
})();
