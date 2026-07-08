let lights = [];
let strains = [];

const brandFolders = {
  'ac_infinity_inc': 'ac-infinity',
  'california_lightworks': 'clw',
  'gavita_horticultural_lighting': 'gavita',
  'growers_choice_horticultural_lighting': 'growers_choice',
  'horticulture_lighting_group': 'hlg',
  'mammoth_lighting': 'mammoth',
  'mars_hydro': 'mars-hydro',
  'photontek_lighting': 'photontek',
  'spider_farmer': 'spider-farmer',
  'vivosun': 'vivosun'
};

const brandSelect = document.getElementById('brand-select');
const modelSelect = document.getElementById('model-select');
const strainInput = document.getElementById('strain-input');
const strainDropdown = document.getElementById('strain-dropdown');
const strainBadge = document.getElementById('strain-badge');
const results = document.getElementById('results');

// Load data
Promise.all([
  fetch('lighting-data-complete.json').then(r => r.json()),
  fetch('strain-index.json').then(r => r.json())
]).then(([lightData, strainData]) => {
  lights = lightData;
  strains = strainData;
  populateBrands();
  loadFromURL();
});

// Populate brand dropdown
function populateBrands() {
  const brands = [...new Set(lights.map(l => l.make))].sort();
  brands.forEach(b => {
    const opt = document.createElement('option');
    opt.value = b;
    opt.textContent = b;
    brandSelect.appendChild(opt);
  });
}

// Brand change -> populate models
brandSelect.addEventListener('change', () => {
  modelSelect.innerHTML = '<option value="">Select model...</option>';
  modelSelect.disabled = !brandSelect.value;
  if (!brandSelect.value) return;

  const models = lights.filter(l => l.make === brandSelect.value);
  models.forEach(l => {
    const opt = document.createElement('option');
    opt.value = l.index;
    opt.textContent = `${l.model} (${l.max_Watts}W)`;
    modelSelect.appendChild(opt);
  });
});

// Model change -> calculate
modelSelect.addEventListener('change', calculate);

// Strain search
let searchTimeout;
strainInput.addEventListener('input', () => {
  clearTimeout(searchTimeout);
  const q = strainInput.value.trim().toLowerCase();
  if (q.length < 2) { strainDropdown.classList.add('hidden'); return; }

  searchTimeout = setTimeout(() => {
    const matches = strains
      .filter(s => s.name.toLowerCase().includes(q))
      .slice(0, 20);
    renderStrainDropdown(matches);
  }, 150);
});

strainInput.addEventListener('focus', () => {
  if (strainInput.value.length >= 2) strainInput.dispatchEvent(new Event('input'));
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('.strain-search')) strainDropdown.classList.add('hidden');
});

function renderStrainDropdown(matches) {
  if (!matches.length) { strainDropdown.classList.add('hidden'); return; }

  strainDropdown.innerHTML = matches.map(s => {
    const logo = s.logo || getDefaultLogo();
    return `<div class="strain-option" data-name="${s.name}" data-days="${s.flower_days}" data-auto="${s.auto}" data-logo="${logo}">
      <img src="${logo}" alt="" onerror="this.src='${getDefaultLogo()}'">
      <span>${s.name}</span>
      <span class="days">${s.flower_days}d${s.auto ? ' · auto' : ''}</span>
    </div>`;
  }).join('');

  strainDropdown.classList.remove('hidden');
}

// Strain selection
strainDropdown.addEventListener('click', (e) => {
  const opt = e.target.closest('.strain-option');
  if (!opt) return;

  const name = opt.dataset.name;
  const days = parseInt(opt.dataset.days);
  const auto = opt.dataset.auto === 'true';
  const logo = opt.dataset.logo;

  // Set flower weeks from days
  document.getElementById('flower-weeks').value = (days / 7).toFixed(1);

  // If auto, set veg to 0 (autos don't have separate veg)
  if (auto) document.getElementById('veg-weeks').value = 0;

  // Show badge
  document.getElementById('strain-logo').src = logo;
  document.getElementById('strain-name').textContent = name;
  document.getElementById('strain-days').textContent = `${days} days${auto ? ' · auto' : ''}`;
  strainBadge.classList.remove('hidden');

  strainInput.value = '';
  strainDropdown.classList.add('hidden');
  calculate();
});

// Clear strain
document.getElementById('strain-clear').addEventListener('click', () => {
  strainBadge.classList.add('hidden');
  document.getElementById('flower-weeks').value = 8;
  document.getElementById('veg-weeks').value = 4;
  calculate();
});

// Random default logo
function getDefaultLogo() {
  const n = Math.floor(Math.random() * 10) + 1;
  return `img/strains/default-${n}.png`;
}

// Calculate
function calculate() {
  const light = lights.find(l => l.index === modelSelect.value);
  if (!light) { results.classList.add('hidden'); return; }

  const watts = parseFloat(light.max_Watts);
  const vegWeeks = parseFloat(document.getElementById('veg-weeks').value) || 0;
  const flowerWeeks = parseFloat(document.getElementById('flower-weeks').value) || 8;
  const rate = parseFloat(document.getElementById('electric-rate').value) || 0.16;
  const vegHrs = parseFloat(document.getElementById('veg-hours').value) || 18;
  const flowerHrs = parseFloat(document.getElementById('flower-hours').value) || 12;

  const vegDays = Math.round(vegWeeks * 7);
  const flowerDays = Math.round(flowerWeeks * 7);
  const totalDays = vegDays + flowerDays;

  const vegKwh = (watts * vegHrs * vegDays) / 1000;
  const flowerKwh = (watts * flowerHrs * flowerDays) / 1000;
  const totalKwh = vegKwh + flowerKwh;

  const vegCost = vegKwh * rate;
  const flowerCost = flowerKwh * rate;
  const totalCost = totalKwh * rate;
  const dailyCost = totalDays > 0 ? totalCost / totalDays : 0;
  const monthlyCost = dailyCost * 30;

  // Display results
  document.getElementById('total-cost').textContent = `$${totalCost.toFixed(2)}`;
  document.getElementById('veg-cost').textContent = `$${vegCost.toFixed(2)}`;
  document.getElementById('veg-detail').textContent = `${vegDays}d × ${vegHrs}hrs`;
  document.getElementById('flower-cost').textContent = `$${flowerCost.toFixed(2)}`;
  document.getElementById('flower-detail').textContent = `${flowerDays}d × ${flowerHrs}hrs`;
  document.getElementById('daily-cost').textContent = `$${dailyCost.toFixed(2)}`;
  document.getElementById('monthly-cost').textContent = `$${monthlyCost.toFixed(2)}`;

  // Light info
  const lightImg = document.getElementById('light-img');
  if (light.img) {
    const folder = brandFolders[light.make_slug] || light.make_slug;
    lightImg.src = `brand/${folder}/images/${light.img}`;
    lightImg.alt = light.make + ' ' + light.model;
    lightImg.classList.remove('hidden');
    lightImg.onerror = () => lightImg.classList.add('hidden');
  } else {
    lightImg.classList.add('hidden');
  }

  document.getElementById('light-name').textContent = `${light.make} ${light.model}`;
  const coverage = light.flowering_footprint_length_ft && light.flowering_footprint_width_ft
    ? `${light.flowering_footprint_length_ft}×${light.flowering_footprint_width_ft} ft`
    : '';
  document.getElementById('light-specs').textContent = `${watts}W${coverage ? ' · ' + coverage : ''}`;

  // Metrics
  const price = parseFloat(light.price);
  document.getElementById('light-price').textContent = price ? `$${price.toFixed(0)}` : '';
  document.getElementById('light-ppw').textContent = price ? `$${(price / watts).toFixed(2)}/W` : '';

  const fl = parseFloat(light.flowering_footprint_length_ft);
  const fw = parseFloat(light.flowering_footprint_width_ft);
  document.getElementById('light-wpsf').textContent = (fl && fw) ? `${(watts / (fl * fw)).toFixed(1)} W/sqft` : '';

  // Affiliate link (prefer affiliate_url, fallback to url)
  const link = document.getElementById('affiliate-link');
  const productUrl = light.affiliate_url || light.url;
  if (productUrl) {
    link.href = productUrl;
    link.classList.remove('hidden');
  } else {
    link.classList.add('hidden');
  }

  results.classList.remove('hidden');
  document.getElementById('share-btn').classList.remove('hidden');
  results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Recalculate on input changes
['veg-weeks', 'flower-weeks', 'electric-rate', 'veg-hours', 'flower-hours'].forEach(id => {
  document.getElementById(id).addEventListener('input', calculate);
});

// Tent size filter
document.querySelectorAll('.tent-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tent-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterByTent(parseInt(btn.dataset.size));
  });
});

function filterByTent(size) {
  const matching = lights.filter(l => {
    const fl = parseFloat(l.flowering_footprint_length_ft);
    const fw = parseFloat(l.flowering_footprint_width_ft);
    if (!fl || !fw) return false;
    return (fl >= size - 0.5 && fl <= size + 0.5) && (fw >= size - 0.5 && fw <= size + 0.5);
  }).sort((a, b) => {
    const ppwA = parseFloat(a.price) / parseFloat(a.max_Watts);
    const ppwB = parseFloat(b.price) / parseFloat(b.max_Watts);
    return (ppwA || 999) - (ppwB || 999);
  });

  const container = document.getElementById('tent-results');
  if (!matching.length) {
    container.innerHTML = '<p class="muted">No lights found for this tent size.</p>';
    return;
  }

  container.innerHTML = matching.slice(0, 10).map(l => {
    const watts = parseFloat(l.max_Watts);
    const price = parseFloat(l.price);
    const ppw = price ? `$${(price / watts).toFixed(2)}/W` : '';
    return `<div class="tent-card">
      <div class="tent-card-info">
        <h4>${l.make} ${l.model}</h4>
        <p>${watts}W · ${l.flowering_footprint_length_ft}×${l.flowering_footprint_width_ft} ft${l.efficacy_umol_joule ? ' · ' + l.efficacy_umol_joule + ' µmol/J' : ''}</p>
      </div>
      <div class="tent-card-stats">
        ${price ? `<div class="price">$${price.toFixed(0)}</div>` : ''}
        <div class="muted">${ppw}</div>
      </div>
    </div>`;
  }).join('');
}

// Share calculation
document.getElementById('share-btn').addEventListener('click', () => {
  const params = new URLSearchParams();
  params.set('light', modelSelect.value);
  params.set('veg', document.getElementById('veg-weeks').value);
  params.set('flower', document.getElementById('flower-weeks').value);
  params.set('rate', document.getElementById('electric-rate').value);
  params.set('vh', document.getElementById('veg-hours').value);
  params.set('fh', document.getElementById('flower-hours').value);

  const url = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
  navigator.clipboard.writeText(url).then(() => {
    const confirm = document.getElementById('share-confirm');
    confirm.classList.remove('hidden');
    setTimeout(() => confirm.classList.add('hidden'), 2000);
  });
});

// Load from URL params (shared links)
function loadFromURL() {
  const params = new URLSearchParams(window.location.search);
  const lightId = params.get('light');
  if (!lightId) return;

  const light = lights.find(l => l.index === lightId);
  if (!light) return;

  // Set brand
  brandSelect.value = light.make;
  brandSelect.dispatchEvent(new Event('change'));

  // Set model (after brand change populates models)
  setTimeout(() => {
    modelSelect.value = lightId;

    if (params.get('veg')) document.getElementById('veg-weeks').value = params.get('veg');
    if (params.get('flower')) document.getElementById('flower-weeks').value = params.get('flower');
    if (params.get('rate')) document.getElementById('electric-rate').value = params.get('rate');
    if (params.get('vh')) document.getElementById('veg-hours').value = params.get('vh');
    if (params.get('fh')) document.getElementById('flower-hours').value = params.get('fh');

    calculate();
  }, 50);
}
