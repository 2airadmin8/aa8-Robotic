(() => {
  'use strict';

  const priorityMap = {
    'unitree-g1-d': { order: 1, label: '大学研究・VLA向け' },
    'agibot-g2': { order: 2, label: '移動操作・PoC向け' },
    'unitree-g1': { order: 3, label: '人型研究向け' },
    'unitree-go2-edu': { order: 4, label: '教育・移動研究向け' },
    'agibot-x2-edu': { order: 5, label: '研究教育向け' },
    'tianji-marvin': { order: 6, label: 'データ収集構成' },
    'limx-oli': { order: 7, label: '全身制御研究向け' },
  };

  const g1dDetailUrl = 'products/unitree-g1-d.html';

  document.querySelectorAll('[data-product-list]').forEach((root) => {
    const enhance = () => {
      const cards = [...root.querySelectorAll('.research-product-card')];
      if (!cards.length) return false;

      cards.forEach((card) => {
        const config = priorityMap[card.id] || { order: 99, label: '比較対象' };
        card.dataset.productOrder = String(config.order);

        if (!card.querySelector('.product-priority-ribbon')) {
          const ribbon = document.createElement('span');
          ribbon.className = 'product-priority-ribbon';
          ribbon.textContent = config.label;
          card.prepend(ribbon);
        }

        const body = card.querySelector('.product-body');
        const maker = card.querySelector('.product-maker');
        if (body && maker && !body.querySelector('.product-category-label')) {
          const category = document.createElement('p');
          category.className = 'product-category-label';
          category.textContent = inferCategory(card);
          maker.insertAdjacentElement('afterend', category);
        }

        const imageNote = card.querySelector('.image-note');
        if (imageNote) imageNote.textContent = '参考イメージ';

        if (card.id === 'unitree-g1-d') {
          card.classList.add('is-featured-detail-ready');
          card.querySelectorAll('a[href]').forEach((link) => {
            if (link.classList.contains('product-consult-link')) return;
            link.setAttribute('href', g1dDetailUrl);
          });
          const detailLink = card.querySelector('.product-link');
          if (detailLink) detailLink.textContent = '詳細製品ページを見る →';
        }
      });

      cards
        .sort((a, b) => Number(a.dataset.productOrder) - Number(b.dataset.productOrder))
        .forEach((card) => root.appendChild(card));

      if (!root.previousElementSibling?.classList.contains('product-list-summary')) {
        const summary = document.createElement('div');
        summary.className = 'product-list-summary';
        summary.innerHTML = `<strong>${cards.length}製品を比較</strong><span>価格・納期・SDK・取扱状態を正式見積前に確認します。</span>`;
        root.insertAdjacentElement('beforebegin', summary);
      }

      if (!document.querySelector('.g1d-detail-entry')) {
        const entry = document.createElement('a');
        entry.className = 'g1d-detail-entry';
        entry.href = g1dDetailUrl;
        entry.innerHTML = '<span><small>NEW PRODUCT DETAIL</small><strong>Unitree G1-D 詳細製品ページ</strong><em>実機構成・データ収集・モデル学習・大学導入条件を確認</em></span><b>詳しく見る →</b>';
        const summary = root.previousElementSibling;
        if (summary?.classList.contains('product-list-summary')) {
          summary.insertAdjacentElement('beforebegin', entry);
        } else {
          root.insertAdjacentElement('beforebegin', entry);
        }
      }

      if (!document.querySelector('#g1d-detail-entry-style')) {
        const style = document.createElement('style');
        style.id = 'g1d-detail-entry-style';
        style.textContent = `
          .g1d-detail-entry{display:flex;align-items:center;justify-content:space-between;gap:24px;margin:0 0 18px;padding:22px 26px;border:1px solid #bfe3ef;border-radius:20px;background:linear-gradient(135deg,#fff 0%,#eefaff 100%);box-shadow:0 14px 34px rgba(11,49,67,.08);color:#0b3143;text-decoration:none}
          .g1d-detail-entry span{display:grid;gap:4px}.g1d-detail-entry small{color:#009ad2;font-size:.72rem;font-weight:900;letter-spacing:.12em}.g1d-detail-entry strong{font-size:1.35rem}.g1d-detail-entry em{color:#607985;font-style:normal}.g1d-detail-entry b{flex:0 0 auto;color:#009ad2}
          .research-product-card.is-featured-detail-ready{outline:3px solid rgba(0,154,210,.16);outline-offset:-3px}
          @media(max-width:640px){.g1d-detail-entry{align-items:flex-start;flex-direction:column;padding:20px}.g1d-detail-entry strong{font-size:1.15rem}.g1d-detail-entry b{width:100%;padding-top:12px;border-top:1px solid #d6e8ee}}
        `;
        document.head.appendChild(style);
      }

      return true;
    };

    if (enhance()) return;

    const observer = new MutationObserver(() => {
      if (!enhance()) return;
      observer.disconnect();
    });
    observer.observe(root, { childList: true });
  });

  function inferCategory(card) {
    const groups = (card.dataset.productGroups || '').split(' ');
    if (groups.includes('mobile-manipulation')) return '移動操作・データ収集';
    if (groups.includes('quadruped')) return '四足・移動研究';
    if (groups.includes('arm')) return 'アーム・操作';
    if (groups.includes('education')) return '研究・教育';
    if (groups.includes('humanoid')) return 'ヒューマノイド';
    return 'AIロボット';
  }
})();