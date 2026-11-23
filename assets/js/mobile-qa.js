(() => {
  'use strict';

  const menuButton = document.querySelector('.menu');
  const navigation = document.querySelector('.nav');
  const corporateShell = document.body.classList.contains('aa8-corporate-v1');

  if (menuButton && navigation) {
    menuButton.setAttribute('aria-label', 'メニューを開閉する');

    const syncNavigationState = () => {
      const isOpen = navigation.classList.contains('open');
      menuButton.setAttribute('aria-expanded', String(isOpen));
      document.body.classList.toggle('nav-is-open', isOpen);
      if (corporateShell) {
        document.body.classList.toggle('aa8-corporate-menu-open', isOpen);
        menuButton.setAttribute('aria-label', isOpen ? 'メニューを閉じる' : 'メニューを開く');
      }
    };

    const closeNavigation = () => {
      navigation.classList.remove('open');
      syncNavigationState();
    };

    // SPメニューはこのファイルを唯一の制御元とする。
    // captureで旧site.jsの重複ハンドラより先に処理し、二重toggleを防止する。
    menuButton.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      navigation.classList.toggle('open');
      syncNavigationState();
    }, true);

    navigation.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', closeNavigation);
    });

    document.addEventListener('keydown', (event) => {
      if (!navigation.classList.contains('open')) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        closeNavigation();
        menuButton.focus();
        return;
      }
      if (!corporateShell || event.key !== 'Tab') return;
      const links = [...navigation.querySelectorAll('a[href]')]
        .filter(node => node.getClientRects().length);
      const focusOrder = [menuButton, ...links];
      const first = focusOrder[0], last = focusOrder[focusOrder.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    document.addEventListener('click', (event) => {
      if (!navigation.classList.contains('open')) return;
      if (navigation.contains(event.target) || menuButton.contains(event.target)) return;
      closeNavigation();
    });

    window.addEventListener('resize', () => {
      // Corporate mother-site breakpoint is 1023px; legacy pages remain 980px.
      const minDesktop = corporateShell ? 1024 : 981;
      if (window.innerWidth >= minDesktop) closeNavigation();
    });

    syncNavigationState();
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
