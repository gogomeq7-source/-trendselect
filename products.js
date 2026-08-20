(() => {
  const grid = document.querySelector('#product-grid');
  if (!grid) return;

  const filters = document.querySelector('#product-filters');
  const search = document.querySelector('#product-search');
  const status = document.querySelector('#product-status');
  const empty = document.querySelector('#product-empty');
  const pagination = document.querySelector('#product-pagination');
  const pageStatus = document.querySelector('#product-page-status');
  const pageSize = 24;
  let products = [];
  let category = 'all';
  let query = '';
  let page = 1;

  const safeUrl = (value) => {
    try {
      const url = new URL(value);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : '';
    } catch { return ''; }
  };

  const money = (value, currency) => {
    const number = Number(value);
    if (!Number.isFinite(number) || !currency) return '';
    try { return new Intl.NumberFormat('de-CH', { style: 'currency', currency }).format(number); }
    catch { return `${number.toFixed(2)} ${currency}`; }
  };

  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  const productCard = (product) => {
    const link = safeUrl(product.affiliateUrl);
    const imageUrl = safeUrl(product.image);
    if (!link || !imageUrl || !product.title) return null;

    const card = element('article', 'product-card');
    const imageLink = element('a', 'product-image-link');
    imageLink.href = link;
    imageLink.target = '_blank';
    imageLink.rel = 'sponsored noopener noreferrer';
    imageLink.setAttribute('aria-label', `${product.title} beim Partner ansehen`);
    const image = element('img', 'product-image');
    image.src = imageUrl;
    image.alt = product.title;
    image.loading = 'lazy';
    image.decoding = 'async';
    image.addEventListener('error', () => imageLink.classList.add('image-unavailable'));
    imageLink.append(image);

    const body = element('div', 'product-body');
    const meta = element('p', 'product-meta', [product.category, product.merchant].filter(Boolean).join(' · '));
    const title = element('h3', '', product.title);
    const description = element('p', 'product-description', product.description || '');
    const priceRow = element('div', 'product-price-row');
    const price = element('strong', 'product-price', money(product.price, product.currency));
    priceRow.append(price);
    const oldPrice = money(product.originalPrice, product.currency);
    if (oldPrice && Number(product.originalPrice) > Number(product.price)) {
      priceRow.append(element('s', 'product-old-price', oldPrice));
    }
    const cta = element('a', 'product-link', 'Zum Angebot ↗');
    cta.href = link;
    cta.target = '_blank';
    cta.rel = 'sponsored noopener noreferrer';
    body.append(meta, title);
    if (product.description) body.append(description);
    body.append(priceRow, cta);
    card.append(imageLink, body);
    return card;
  };

  const render = () => {
    const needle = query.toLocaleLowerCase('de');
    const visible = products.filter((product) => {
      const categoryMatch = category === 'all' || product.category === category;
      const haystack = [product.title, product.description, product.merchant, product.category].join(' ').toLocaleLowerCase('de');
      return categoryMatch && haystack.includes(needle);
    });
    const pages = Math.max(1, Math.ceil(visible.length / pageSize));
    page = Math.min(page, pages);
    grid.replaceChildren();
    visible.slice((page - 1) * pageSize, page * pageSize).forEach((product) => {
      const card = productCard(product);
      if (card) grid.append(card);
    });
    const hasResults = grid.childElementCount > 0;
    empty.hidden = hasResults;
    pagination.hidden = visible.length <= pageSize;
    pageStatus.textContent = `Seite ${page} von ${pages}`;
    pagination.querySelector('[data-page-action="previous"]').disabled = page === 1;
    pagination.querySelector('[data-page-action="next"]').disabled = page === pages;
  };

  const buildFilters = () => {
    [...new Set(products.map((item) => item.category).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, 'de'))
      .forEach((name) => {
        const button = element('button', 'product-filter', name);
        button.type = 'button';
        button.dataset.category = name;
        filters.append(button);
      });
  };

  filters.addEventListener('click', (event) => {
    const button = event.target.closest('[data-category]');
    if (!button) return;
    category = button.dataset.category;
    page = 1;
    filters.querySelectorAll('button').forEach((item) => item.classList.toggle('active', item === button));
    render();
  });
  search.addEventListener('input', () => { query = search.value.trim(); page = 1; render(); });
  pagination.addEventListener('click', (event) => {
    const action = event.target.closest('[data-page-action]')?.dataset.pageAction;
    if (!action) return;
    page += action === 'next' ? 1 : -1;
    render();
    grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  fetch('data/products.json', { cache: 'no-store' })
    .then((response) => { if (!response.ok) throw new Error('Produktdaten nicht erreichbar'); return response.json(); })
    .then((data) => {
      products = Array.isArray(data.products) ? data.products : [];
      buildFilters();
      status.textContent = products.length
        ? `${products.length.toLocaleString('de-CH')} Partnerprodukte · Aktualisiert ${new Date(data.updatedAt).toLocaleDateString('de-CH')}`
        : 'Noch kein Affiliate-Produktfeed verbunden.';
      render();
    })
    .catch(() => { status.textContent = 'Produktkatalog momentan nicht verfügbar.'; render(); });
})();
