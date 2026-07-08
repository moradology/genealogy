// Acceptance spec for index.html: self-containment, per-line map plates, content
// preservation, themes, interactions, responsiveness, and portrait cameos.
// Run from any directory with playwright installed:  node tools/acceptance_spec.js
// (or via npx: npm exec --package=playwright -- node tools/acceptance_spec.js)

const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const path = require('node:path');
const FILE = path.join(__dirname, '..', 'index.html');
const URL = 'file://' + FILE;

// Derived from verifiedEventData/familyLinkData + plate rules:
// line plate = events of that anchor + links of that anchor or referencing them
// (referenced non-own events render as guests); convergence = Kansas-window subset.
const PLATE_EXPECT = {
  'map-convergence': { markers: 14, edges: 6 },
  'map-line-zimmerman': { markers: 10, edges: 6, guests: 1 },
  'map-line-mundell': { markers: 4, edges: 2, guests: 2 },
  'map-line-dible': { markers: 6, edges: 3, guests: 0 },
  'map-line-connelly': { markers: 7, edges: 4, guests: 0 },
};
const LINK_TOTAL = 10;
const SOURCE_ITEMS = 170;
const PERSON_DIVS = 76;
const PERSON_IDS = 76;
const STEM_DIVS = 7;

const ISOLATED_ID = 'event.zimmerman.michael_birth.1869-10-25'; // Mainhardt; isolated on the zimmerman plate
const COINCIDENT_PAIRS = [
  ['event.doyle_zimmerman.birth.1930-04-12', 'event.mcclelland.dorsey_burial_selden.1904'],
  ['event.bill_dible.birth.1933-06-02', 'event.donna_connelly.birth.1935-04-24'],
  ['event.doyle_zimmerman.marriage.1954-06-14', 'event.evelyn_mundell.death.2023-04-15'],
];

let passed = 0;
function ok(label, cond, detail) {
  assert.ok(cond, label + (detail === undefined ? '' : ' :: ' + detail));
  passed += 1;
  console.log('PASS ' + label);
}

(async () => {
  // ---------- static source checks ----------
  // person.* ids contain dots (person.<surname>.<given>), so both this spec and
  // page code must address them via getElementById(...)/href="#...", never a
  // bare querySelector('#person.x') (the dot would be parsed as a class selector).
  const src = fs.readFileSync(FILE, 'utf8');
  ok('S1 no external scripts', !/<script[^>]*\ssrc=/.test(src));
  ok('S2 no external stylesheets', !/<link[^>]+rel="stylesheet"[^>]+href="http/.test(src));
  ok('S3 event data intact', src.includes('verifiedEventData') && src.includes('familyLinkData'));
  ok('S4 fonts embedded as data URIs', /@font-face/.test(src) && /data:font\/woff2;base64,/.test(src));
  ok('S5 leaflet fully removed', !/leaflet|unpkg|openstreetmap\.org\/\{z\}|tile\.openstreetmap/i.test(src));
  ok('S6 marriage corrected to 1954 everywhere', src.includes('event.doyle_zimmerman.marriage.1954-06-14') && !src.includes('1953-06-14'));
  ok('S7 Colby Free Press source cited', src.includes('Colby Free Press') && src.includes('Sacred Heart Catholic Church'));
  ok('S8 deploy stamp present', /<meta name="deploy-stamp" content="[0-9a-f]{12} \d{4}-\d{2}-\d{2}">/.test(src));
  // Payload budgets (treaty): set at measured+10% after the Track B
  // ledger batch (44 new source entries): total 276911, fonts 41783,
  // paths 19763 on 2026-07-08. TREATY MATH: remaining declared program
  // costs are ~21.6KB (Slate 2) + ~19.3KB (Slate 3) + W5/W6 (~5KB net
  // after the W5 stub-table retirement) -> projected ~323KB against the
  // hard 327,680 ceiling. S9 is a per-wave RATCHET (re-measured to
  // +10% at each landing per the documented procedure), so planned
  // waves will legitimately re-measure past this value; the ceiling is
  // the constraint that never moves. Margin is thin: every wave
  // declares its cost and looks for offsetting cuts. Peers bump
  // budgets only via a declared SPEC DELTA; total never exceeds 327680.
  ok('S9 total payload within budget', src.length < 304672, src.length);
  ok('S10 embedded fonts within budget',
    (src.match(/data:font\/woff2;base64,[A-Za-z0-9+\/=]+/g) || []).join('').length < 45153);
  ok('S11 baked path constants within budget',
    (src.match(/const \w+_D = "[^"]*"/g) || []).join('').length < 21739);
  ok('S12 generated-region marker pairs present',
    ['basemap-proj', 'basemap-paths'].every((tag) =>
      src.split('// BEGIN GENERATED ' + tag).length === 2 &&
      src.split('// END GENERATED ' + tag).length === 2));

  // ---------- browser ----------
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });

  const externalRequests = [];
  const consoleErrors = [];
  const pageErrors = [];
  await page.route('**/*', (route) => {
    const u = route.request().url();
    if (u.startsWith('file://')) return route.continue();
    externalRequests.push(u);
    return route.abort();
  });
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => pageErrors.push(String(e)));

  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForTimeout(800);

  ok('B1 zero external requests', externalRequests.length === 0, externalRequests.join(', '));

  const plates = await page.evaluate(() => {
    const out = {};
    document.querySelectorAll('figure.plate svg').forEach((svg) => {
      out[svg.id] = {
        visible: svg.getBoundingClientRect().width > 200 && getComputedStyle(svg).display !== 'none',
        markers: svg.querySelectorAll('g.event-marker[data-event-id]').length,
        edges: svg.querySelectorAll('path.family-link[data-link-id]').length,
        guests: svg.querySelectorAll('g.event-marker.guest').length,
        baseDrawn: (svg.querySelector('.layer-land path, .layer-borders path')?.getAttribute('d') || '').length > 200,
      };
    });
    out._distinctLinks = new Set([...document.querySelectorAll('path.family-link')].map((p) => p.dataset.linkId)).size;
    out._details = document.querySelectorAll('figure.plate .plate-detail').length;
    out._keyboardReady = [...document.querySelectorAll('g.event-marker')].every(
      (g) => g.getAttribute('tabindex') === '0' && (g.getAttribute('aria-label') || '').length > 3);
    out._nav = document.querySelectorAll('nav a[href^="#"]').length;
    return out;
  });
  for (const [id, expect] of Object.entries(PLATE_EXPECT)) {
    const p = plates[id];
    assert.ok(p, 'missing plate ' + id);
    assert.ok(p.visible, id + ' not visible');
    assert.equal(p.markers, expect.markers, id + ' markers');
    assert.equal(p.edges, expect.edges, id + ' edges');
    if (expect.guests !== undefined) assert.equal(p.guests, expect.guests, id + ' guests');
    assert.ok(p.baseDrawn, id + ' basemap empty');
  }
  ok('B2 all five plates render with expected markers/edges/guests', true);
  ok('B3 ten distinct links across plates', plates._distinctLinks === LINK_TOTAL, plates._distinctLinks);
  ok('B4 detail strip per plate', plates._details === 5, plates._details);
  ok('B5 markers keyboard-ready', plates._keyboardReady);
  ok('B6 nav has jump links', plates._nav >= 5, plates._nav);
  ok('B7 no leftover sidebar/chips/toggle', await page.evaluate(() =>
    !document.querySelector('#map-sidebar, .anchor-chip, button[data-view], .sidebar-tabs')));

  // land/water polarity: continents must be filled land, open ocean must expose the water rect
  const polarity = await page.evaluate(() => {
    const svg = document.querySelector('#map-line-zimmerman');
    svg.scrollIntoView({ block: 'center' });
    const vb = svg.viewBox.baseVal;
    const r = svg.getBoundingClientRect();
    const scale = Math.min(r.width / vb.width, r.height / vb.height);
    const ox = r.left + (r.width - vb.width * scale) / 2 - vb.x * scale;
    const oy = r.top + (r.height - vb.height * scale) / 2 - vb.y * scale;
    const d = Math.PI / 180;
    const p1 = MIG_PROJ.p1 * d, p2 = MIG_PROJ.p2 * d, lon0 = MIG_PROJ.lon0 * d;
    const n = Math.log(Math.cos(p1) / Math.cos(p2)) /
      Math.log(Math.tan(Math.PI / 4 + p2 / 2) / Math.tan(Math.PI / 4 + p1 / 2));
    const f = Math.cos(p1) * Math.tan(Math.PI / 4 + p1 / 2) ** n / n;
    const rho0 = f / Math.tan(Math.PI / 4 + 40 * d / 2) ** n;
    const proj = (lon, lat) => {
      const rho = f / Math.tan(Math.PI / 4 + lat * d / 2) ** n;
      const th = n * (lon * d - lon0);
      return [(rho * Math.sin(th) - MIG_PROJ.xMin) * MIG_PROJ.s,
        (MIG_PROJ.yMax - (rho0 - rho * Math.cos(th))) * MIG_PROJ.s];
    };
    const hit = (lon, lat) => {
      const [ux, uy] = proj(lon, lat);
      const el = document.elementFromPoint(ox + ux * scale, oy + uy * scale);
      if (!el) return 'none';
      if (el.classList.contains('map-water')) return 'water';
      if (el.tagName.toLowerCase() === 'svg' || el.classList.contains('map-neatline')) return 'paper';
      if (el.closest('.layer-land')) return 'land';
      return el.getAttribute('class') || el.tagName;
    };
    return {
      atlantic: hit(-38, 43.7),
      france: hit(2, 47),
      gulf: hit(-89, 26.8),
      germany: hit(12.6, 52.4),
      bandMid: hit(-35, 55.2),
      bandWest: hit(-52, 55.6),
      polandInterior: hit(16, 53.1),
      germanyEast: hit(13.2, 52.9),
    };
  });
  ok('B8 ocean exposes water rect', polarity.atlantic === 'water' && polarity.gulf === 'water',
    JSON.stringify(polarity));
  ok('B8b nothing painted above the top parallel', polarity.bandMid === 'paper' && polarity.bandWest === 'paper',
    JSON.stringify(polarity));
  ok('B9 continents filled as land', polarity.france === 'land' && polarity.germany === 'land',
    JSON.stringify(polarity));
  ok('B9b no water slash through Poland', polarity.polandInterior === 'land' && polarity.germanyEast === 'land',
    JSON.stringify(polarity));

  // ---------- content preservation ----------
  const content = await page.evaluate(() => {
    const h2s = [...document.querySelectorAll('h2')].map((h) => h.textContent.trim());
    const sec = [...document.querySelectorAll('section')].find((s) =>
      s.querySelector('h2') && s.querySelector('h2').textContent.trim() === 'Source Ledger');
    const lis = sec ? [...sec.querySelectorAll('li')] : [];
    return {
      h2s,
      sourceCount: lis.length,
      sourcesWithAnchor: lis.filter((li) => li.querySelector('a[href]')).length,
      groups: sec ? sec.querySelectorAll('details').length : 0,
      firstOpen: sec ? !!sec.querySelector('details[open]') : false,
      persons: document.querySelectorAll('.person').length,
      personWithoutIds: document.querySelectorAll('.person:not([id])').length,
      personIds: [...document.querySelectorAll('.person[id^="person."]')].map((el) => el.id),
      breadth: document.body.textContent.includes('The goal here is breadth plus honesty'),
      geojsonLink: !!document.querySelector('a[href="ancestry_geospatial.geojson"]'),
    };
  });
  for (const h of ['Doyle Julius Zimmerman Branches', 'Evelyn Delores Mundell Zimmerman Branches',
    'William J. "Bill" Dible Branches', 'Donna Lea Connelly Dible Branches',
    'The Docket', 'Index of Names', 'Source Ledger'])
    assert.ok(content.h2s.includes(h), 'missing h2: ' + h);
  ok('C1 all section headings present', true);
  ok('C2 source ledger count matches', content.sourceCount === SOURCE_ITEMS, content.sourceCount);
  ok('C3 every source has a link', content.sourcesWithAnchor === SOURCE_ITEMS, content.sourcesWithAnchor);
  ok('C4 sources grouped, first open', content.groups >= 5 && content.firstOpen, content.groups);
  ok('C5 person entry count matches', content.persons === PERSON_DIVS, content.persons);
  const idRe = /^person\.[a-z0-9_.]+$/;
  ok('C8 person ids stamped and unique',
    content.personIds.length === PERSON_IDS &&
    content.personWithoutIds === 0 &&
    new Set(content.personIds).size === PERSON_IDS &&
    content.personIds.every((id) => idRe.test(id) && (id.slice('person.'.length).match(/\./g) || []).length <= 1),
    JSON.stringify({ ids: content.personIds.length, bare: content.personWithoutIds }));
  ok('C6 method note preserved', content.breadth);
  ok('C7 geojson link preserved', content.geojsonLink);
  const brokenInternalLinks = await page.evaluate(() =>
    [...document.querySelectorAll('a[href]')]
      .map((a) => a.getAttribute('href'))
      .filter((href) => {
        const resolvedURL = new URL(href, location.href);
        return resolvedURL.pathname === location.pathname &&
          resolvedURL.hash.length > 1 &&
          !document.getElementById(decodeURIComponent(resolvedURL.hash.slice(1)));
      }));
  ok('C9 internal links resolve', brokenInternalLinks.length === 0, brokenInternalLinks.join(', '));
  const stemCheck = await page.evaluate((stemDivs) => {
    const expected = [
      { href: '#person.zodrow.cecilia', tagClass: 'documented', tagText: 'Documented' },
      { href: '#person.zodrow.cecilia', tagClass: 'documented', tagText: 'Documented' },
      { href: '#person.nauer.elizabeth', tagClass: 'strong', tagText: 'Strong lead' },
      { href: '#person.clemans.marjorie', tagClass: 'documented', tagText: 'Documented' },
      { href: '#person.clemans.marjorie', tagClass: 'documented', tagText: 'Documented' },
      { href: '#person.long.almeda', tagClass: 'documented', tagText: 'Documented' },
      { href: '#person.claar.martha', tagClass: 'documented', tagText: 'Documented' },
    ];
    const stems = [...document.querySelectorAll('.stem')];
    const details = stems.map((stem) => {
      const links = [...stem.querySelectorAll('a[href]')];
      const tags = [...stem.querySelectorAll('.tag')];
      const href = links[0]?.getAttribute('href') || '';
      const targetId = href.startsWith('#') ? decodeURIComponent(href.slice(1)) : '';
      const tag = tags[0] || null;
      const tagClasses = tag ? [...tag.classList].filter((c) => c !== 'tag') : [];
      // confidence class -> visible text -> stem border-left encoding must all agree
      const borderFor = { documented: 'solid', strong: 'double', lead: 'dashed', open: 'dotted' };
      return {
        text: stem.textContent.trim(),
        linkCount: links.length,
        tagCount: tags.length,
        href,
        targetExists: !!targetId && !!document.getElementById(targetId),
        tagClass: tagClasses.length === 1 ? tagClasses[0] : `MULTI:${tagClasses.join('+')}`,
        tagText: tag ? tag.textContent.trim() : '',
        borderStyle: getComputedStyle(stem).borderLeftStyle,
        borderExpected: borderFor[tagClasses[0]] || 'dotted',
      };
    });
    const failures = [];
    if (stems.length !== stemDivs) failures.push(`stem count ${stems.length}`);
    details.forEach((d, i) => {
      const e = expected[i];
      if (!e) failures.push(`unexpected stem ${i + 1}`);
      else if (d.linkCount !== 1 || d.tagCount !== 1 || !d.targetExists ||
        d.href !== e.href || d.tagClass !== e.tagClass || d.tagText !== e.tagText ||
        d.borderStyle !== d.borderExpected) {
        failures.push(`stem ${i + 1}: ${JSON.stringify(d)}`);
      }
    });
    return { pass: failures.length === 0, details, failures };
  }, STEM_DIVS);
  ok('C10 descent stems resolve and carry expected chain tags',
    stemCheck.pass, JSON.stringify(stemCheck.failures.length ? stemCheck.failures : stemCheck.details));
  const chartCheck = await page.evaluate(() => {
    const charts = [...document.querySelectorAll('figure.chart svg')].map((svg) => {
      const broken = [...svg.querySelectorAll('a[href]')]
        .map((a) => a.getAttribute('href'))
        .filter((href) => !href || !href.startsWith('#') || !document.getElementById(decodeURIComponent(href.slice(1))));
      return {
        id: svg.closest('figure.chart').id,
        cells: svg.querySelectorAll('g.pc[data-ah]').length,
        broken,
      };
    });
    return { charts };
  });
  ok('C11 pedigree charts render 63 cells each and links resolve',
    chartCheck.charts.length === 4 &&
    chartCheck.charts.every((c) => c.cells === 63 && c.broken.length === 0),
    JSON.stringify(chartCheck));
  const nameIndex = await page.evaluate(() => {
    const sec = document.getElementById('index-of-names');
    if (!sec) return { exists: false };
    const links = [...sec.querySelectorAll('li a[href]')];
    const names = links.map((a) => a.textContent.trim());
    const sorted = [...names].sort((a, b) => a.localeCompare(b));
    const letters = [...sec.querySelectorAll('.index-letter')].map((li) => li.textContent.trim());
    const expectedLetters = [...new Set(names.map((n) => n.split(',')[0].trim()[0].toUpperCase()))];
    const broken = links
      .map((a) => a.getAttribute('href'))
      .filter((href) => !href || !href.startsWith('#') || !document.getElementById(decodeURIComponent(href.slice(1))));
    const registryPeople = JSON.parse(document.getElementById('people-index').textContent)
      .people.filter((p) => p.k !== 'slot').length;
    return {
      exists: true,
      entries: links.length,
      registryPeople,
      ordered: names.every((n, i) => n === sorted[i]),
      grouped: letters.join('|') === expectedLetters.join('|'),
      broken: broken.length,
    };
  });
  ok('C12 Index of Names exists, is grouped, ordered, and linked',
    nameIndex.exists && nameIndex.entries >= nameIndex.registryPeople &&
    nameIndex.ordered && nameIndex.grouped && nameIndex.broken === 0,
    JSON.stringify(nameIndex));

  // ---------- theme ----------
  const bgFor = async (scheme, theme) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.evaluate((t) => {
      if (t) document.documentElement.dataset.theme = t;
      else delete document.documentElement.dataset.theme;
    }, theme);
    await page.waitForTimeout(80);
    return page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  };
  const lightDefault = await bgFor('light', null);
  const darkDefault = await bgFor('dark', null);
  const lightForced = await bgFor('dark', 'light');
  const darkForced = await bgFor('light', 'dark');
  ok('T1 dark media theme differs', lightDefault !== darkDefault, lightDefault + ' vs ' + darkDefault);
  ok('T2 data-theme=light beats dark media', lightForced === lightDefault, lightForced);
  ok('T3 data-theme=dark beats light media', darkForced === darkDefault, darkForced);
  await bgFor('light', null);

  // ---------- interactions (zimmerman line plate) ----------
  const marker = page.locator(`#map-line-zimmerman g.event-marker[data-event-id="${ISOLATED_ID}"]`);
  await marker.click({ force: true });
  await page.waitForTimeout(120);
  let detail = await page.locator('#detail-zimmerman').textContent();
  ok('I1 click pins detail strip', detail.includes('Michael John Zimmerman'), detail.slice(0, 80));
  ok('I2 pinned class applied', await marker.evaluate((g) => g.classList.contains('pinned')));

  await page.keyboard.press('Escape');
  await page.waitForTimeout(120);
  ok('I3 Escape clears pin', !(await marker.evaluate((g) => g.classList.contains('pinned'))));

  await marker.click({ force: true });
  await page.waitForTimeout(120);
  await page.locator('#map-line-zimmerman').click({ position: { x: 8, y: 8 }, force: true });
  await page.waitForTimeout(120);
  ok('I4 click-away clears pin', !(await marker.evaluate((g) => g.classList.contains('pinned'))));

  await marker.evaluate((g) => g.focus());
  await page.keyboard.press('Enter');
  await page.waitForTimeout(120);
  ok('I5 Enter pins focused marker', await marker.evaluate((g) => g.classList.contains('pinned')));
  await page.keyboard.press('Escape');

  // hover bubble over the point: date + what the event is
  const mbox = await marker.boundingBox();
  await page.mouse.move(mbox.x + mbox.width / 2, mbox.y + mbox.height / 2);
  await page.waitForTimeout(200);
  const bubble = await page.evaluate(() => {
    const b = document.querySelector('#map-line-zimmerman').closest('figure.plate').querySelector('.map-bubble');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { text: b.textContent, visible: getComputedStyle(b).opacity !== '0' && r.width > 40 };
  });
  ok('I8 hover shows date bubble over point',
    !!bubble && bubble.visible && bubble.text.includes('1869-10-25') &&
    bubble.text.includes('Michael John Zimmerman') && /birth/i.test(bubble.text),
    bubble && bubble.text.slice(0, 80));
  await page.mouse.move(5, 5);
  await page.waitForTimeout(200);
  ok('I9 bubble hides on leave', await page.evaluate(() => {
    const b = document.querySelector('#map-line-zimmerman').closest('figure.plate').querySelector('.map-bubble');
    return !b || getComputedStyle(b).opacity === '0' || b.hidden;
  }));
  await marker.evaluate((g) => { g.blur(); g.focus(); });
  await page.waitForTimeout(200);
  ok('I10 bubble shows on keyboard focus', await page.evaluate(() => {
    const b = document.querySelector('#map-line-zimmerman').closest('figure.plate').querySelector('.map-bubble');
    return !!b && getComputedStyle(b).opacity !== '0' && !b.hidden;
  }));
  await page.keyboard.press('Escape');
  await page.evaluate(() => document.activeElement.blur());

  // guest event participates on the mundell plate
  const guest = page.locator('#map-line-mundell g.event-marker.guest').first();
  await guest.click({ force: true });
  await page.waitForTimeout(120);
  detail = await page.locator('#detail-mundell').textContent();
  ok('I6 guest marker pins on host plate', detail.length > 20 && !detail.includes('Hover'), detail.slice(0, 60));
  await page.keyboard.press('Escape');

  // evidence ties are undirected: no arrowhead, no jargon label
  const evidence = await page.evaluate(() => {
    const path = document.querySelector(
      '#map-line-zimmerman path.family-link[data-link-id="link.john_paul_household_to_michael"]');
    const arrows = [...document.querySelectorAll('path.family-link')]
      .filter((p) => p.dataset.linkId !== 'link.john_paul_household_to_michael' && !p.getAttribute('marker-end'));
    return {
      exists: !!path,
      noArrow: path ? !path.getAttribute('marker-end') : false,
      othersArrowed: arrows.length === 0,
      noJargon: !document.body.textContent.includes('anchors Michael'),
    };
  });
  ok('I11 evidence tie has no arrowhead', evidence.exists && evidence.noArrow, JSON.stringify(evidence));
  ok('I12 directed links keep arrowheads', evidence.othersArrowed);
  ok('I13 anchoring jargon replaced', evidence.noJargon);

  // coincident separation on the convergence plate
  for (const [a, b] of COINCIDENT_PAIRS) {
    const d = await page.evaluate(([ida, idb]) => {
      const svg = document.querySelector('#map-convergence');
      const ra = svg.querySelector(`g.event-marker[data-event-id="${ida}"]`).getBoundingClientRect();
      const rb = svg.querySelector(`g.event-marker[data-event-id="${idb}"]`).getBoundingClientRect();
      const cx = (r) => [r.left + r.width / 2, r.top + r.height / 2];
      const [ax, ay] = cx(ra); const [bx, by] = cx(rb);
      return Math.hypot(ax - bx, ay - by);
    }, [a, b]);
    assert.ok(d >= 4, `coincident pair ${a} / ${b} separated only ${d}px`);
  }
  ok('I7 coincident markers separated on convergence plate', true);

  // ---------- layout budgets ----------
  const desktop = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth,
    scrollH: document.documentElement.scrollHeight,
  }));
  ok('L1 no horizontal scroll desktop', desktop.scrollW <= 1441, desktop.scrollW);
  // Prior single-map layout measured 16,095px; four user-requested line plates add
  // bounded map figures. Budget: still >=19% under the original 23,000px page.
  // Guards against layout regressions (dead voids, letterboxing), not research prose growth.
  // Content-driven height guard, PLATFORM-AWARE: Ubuntu CI renders ~2.5% taller
  // than macOS (27,383 vs 26,703 after the Cecilia correction) and the delta grows
  // with page height. Budget = larger platform's measure + 500. Re-measure
  // procedure: local measure + 1,200 (covers CI drift + headroom), confirm on the
  // next CI run. Prior local measures: 19,700 pre-W2, 23,511 post-W2, 26,132
  // post-W4, 26,703 post-correction.
  ok('L2 page height within layout budget (<27883)', desktop.scrollH < 27883, desktop.scrollH);

  for (const [w, h] of [[320, 700], [390, 844], [768, 1024], [1024, 768]]) {
    await page.setViewportSize({ width: w, height: h });
    await page.waitForTimeout(350);
    const vp = await page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth,
      convVisible: document.querySelector('#map-convergence').getBoundingClientRect().width > 180,
      navVisible: document.querySelector('nav').getBoundingClientRect().height > 10,
      h1Fits: document.querySelector('h1').getBoundingClientRect().width <= document.documentElement.clientWidth,
    }));
    assert.ok(vp.scrollW <= w + 1, `hscroll at ${w}px: ${vp.scrollW}`);
    assert.ok(vp.convVisible && vp.navVisible && vp.h1Fits, `layout broken at ${w}px: ${JSON.stringify(vp)}`);
  }
  ok('L3 no horizontal scroll at 320/390/768/1024', true);
  ok('L4 plates, nav, and title usable across viewports', true);

  // plate aspect matches its viewBox crop (letterbox regression guard)
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(350);
  const aspects = await page.evaluate(() =>
    [...document.querySelectorAll('figure.plate svg')].map((svg) => {
      const vb = svg.viewBox.baseVal;
      const r = svg.getBoundingClientRect();
      return { id: svg.id, want: vb.width / vb.height, got: r.width / r.height };
    }));
  for (const a of aspects)
    assert.ok(Math.abs(a.got - a.want) / a.want < 0.05, `letterboxed plate ${a.id}: ${JSON.stringify(a)}`);
  ok('L5 plate elements match crop aspect (no letterbox)', true);

  // cameos: committed files resolve, accessible, credited
  const cameos = await page.evaluate(async () => {
    const imgs = [...document.querySelectorAll('.cameo img')];
    await Promise.all(imgs.map((img) => img.complete ? 0 : new Promise((res) => {
      img.addEventListener('load', res);
      img.addEventListener('error', res);
    })));
    return imgs.map((img) => ({
      loaded: img.naturalWidth > 0,
      alt: (img.getAttribute('alt') || '').length > 3,
      lazy: img.getAttribute('loading') === 'lazy',
      sized: !!img.getAttribute('width') && !!img.getAttribute('height'),
      credited: !!img.closest('.cameo').querySelector('a[href]'),
    }));
  });
  ok('L6 at least one portrait cameo present', cameos.length >= 1, cameos.length);
  ok('L7 every cameo loads, has alt/lazy/size/credit',
    cameos.every((c) => c.loaded && c.alt && c.lazy && c.sized && c.credited),
    JSON.stringify(cameos.filter((c) => !(c.loaded && c.alt && c.lazy && c.sized && c.credited))));

  ok('E1 no console errors', consoleErrors.length === 0, consoleErrors.join(' | '));
  ok('E2 no page errors', pageErrors.length === 0, pageErrors.join(' | '));
  await browser.close();

  // touch context: tap pins the record card but no hover bubble appears
  const touchBrowser = await chromium.launch({ headless: true });
  const touchCtx = await touchBrowser.newContext({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  const tpage = await touchCtx.newPage();
  await tpage.goto(URL, { waitUntil: 'load' });
  await tpage.waitForTimeout(700);
  const tmarker = tpage.locator(`#map-line-zimmerman g.event-marker[data-event-id="${ISOLATED_ID}"]`);
  await tmarker.scrollIntoViewIfNeeded();
  await tpage.waitForTimeout(400);
  await tmarker.tap();
  await tpage.waitForTimeout(250);
  const touch = await tpage.evaluate(() => ({
    pinned: !!document.querySelector('#map-line-zimmerman .pinned'),
    detail: document.querySelector('#detail-zimmerman').textContent,
    bubbleShown: !!document.querySelector('#map-line-zimmerman')
      .closest('figure.plate').querySelector('.map-bubble.show'),
  }));
  ok('T4 tap pins record card on touch', touch.pinned && touch.detail.includes('Michael'),
    touch.detail.slice(0, 60));
  ok('T5 no hover bubble on touch devices', !touch.bubbleShown);
  await touchBrowser.close();

  console.log(`\nALL ${passed} CHECKS PASSED`);
})();
