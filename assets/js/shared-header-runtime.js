(() => {
  'use strict';

  const restoreOfficialLogo = () => {
    const header = document.querySelector('.site-header[data-shared-layout="header"]');
    const brand = header?.querySelector('.brand');
    if (!(brand instanceof HTMLElement)) return;

    brand.setAttribute('aria-label', 'AirAdmin8 Robotics ホームへ戻る');
    brand.innerHTML = `
      <img class="brand-logo brand-logo-pc" src="/assets/img/airadmin8-robotics-logo-pc.svg?v=20260805-4" alt="AirAdmin8 Robotics" width="193" height="40">
      <img class="brand-logo brand-logo-sp" src="/assets/img/airadmin8-robotics-logo-sp.svg?v=20260805-4" alt="AirAdmin8 Robotics" width="154" height="32">`;
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreOfficialLogo, { once: true });
  } else {
    restoreOfficialLogo();
  }

  window.addEventListener('load', restoreOfficialLogo, { once: true });
})();
