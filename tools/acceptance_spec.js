// Acceptance spec for index.html: self-containment, per-line map plates, content
// preservation, themes, interactions, responsiveness, and portrait cameos.
// Run from any directory with playwright installed:  node tools/acceptance_spec.js
// (or via npx: npm exec --package=playwright -- node tools/acceptance_spec.js)

const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');

const path = require('node:path');
const ROOT = path.join(__dirname, '..');
const FILE = path.join(ROOT, 'index.html');
const URL = 'file://' + FILE;

// Derived from verifiedEventData/familyLinkData + plate rules:
// line plate = events of that anchor + links of that anchor or referencing them
// (referenced non-own events render as guests); convergence = Kansas-window subset.
const PLATE_EXPECT = {
  'map-convergence': { markers: 17, edges: 6 },
  'map-line-zimmerman': { markers: 14, edges: 6, guests: 1 },
  'map-line-mundell': { markers: 7, edges: 2, guests: 2 },
  'map-line-dible': { markers: 9, edges: 3, guests: 0 },
  'map-line-connelly': { markers: 8, edges: 4, guests: 0 },
};
const ROUTE_EXPECT = {
  'map-convergence': { routes: 7, paths: 9, solidPaths: 9, conjecturalPaths: 0 },
  'map-line-zimmerman': { routes: 3, paths: 4, solidPaths: 3, conjecturalPaths: 1 },
  'map-line-mundell': { routes: 2, paths: 3, solidPaths: 2, conjecturalPaths: 1 },
  'map-line-dible': { routes: 3, paths: 7, solidPaths: 2, conjecturalPaths: 5 },
  'map-line-connelly': { routes: 2, paths: 3, solidPaths: 2, conjecturalPaths: 1 },
};
const MAP_ACCESSIBLE_NAMES = {
  'map-convergence': 'Northwest Kansas convergence map of all four family lines',
  'map-line-zimmerman': 'Doyle Julius Zimmerman Branches event map',
  'map-line-mundell': 'Evelyn Delores Mundell Zimmerman Branches event map',
  'map-line-dible': 'William J. "Bill" Dible Branches event map',
  'map-line-connelly': 'Donna Lea Connelly Dible Branches event map',
};
const LINK_TOTAL = 10;
const SOURCE_ITEMS = 178;
const PERSON_DIVS = 73;
const PERSON_IDS = 73;
const STEM_DIVS = 7;
const CASE_ARTICLES = 23, CORRIGENDA_ITEMS = 4, NEGATIVE_REGISTER_ITEMS = 11;

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
  const srcBytes = Buffer.byteLength(src, 'utf8');
  // Shared same-origin assets (extracted 2026-07-10 for the five-page split):
  // pages may reference ONLY these relative files; anything else is external.
  const fontsCss = fs.readFileSync(path.join(ROOT, 'assets', 'fonts.css'), 'utf8');
  const siteCss = fs.readFileSync(path.join(ROOT, 'assets', 'site.css'), 'utf8');
  const appJs = fs.readFileSync(path.join(ROOT, 'assets', 'app.js'), 'utf8');
  const scriptSrcs = [...src.matchAll(/<script[^>]*\ssrc="([^"]+)"/g)].map((m) => m[1]);
  ok('S1 scripts are same-origin assets only',
    scriptSrcs.length === 1 && scriptSrcs[0] === 'assets/app.js', scriptSrcs);
  const styleHrefs = [...src.matchAll(/<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"/g)].map((m) => m[1]);
  ok('S2 stylesheets are same-origin assets only',
    styleHrefs.length === 2 &&
    styleHrefs.every((href) => href.startsWith('assets/')), styleHrefs);
  ok('S3 event data intact', appJs.includes('verifiedEventData') && appJs.includes('familyLinkData'));
  ok('S4 fonts embedded as data URIs', /@font-face/.test(fontsCss) && /data:font\/woff2;base64,/.test(fontsCss));
  ok('S5 leaflet fully removed', ![src, siteCss, appJs].some((body) => /leaflet|unpkg|openstreetmap\.org\/\{z\}|tile\.openstreetmap/i.test(body)));
  ok('S6 marriage corrected to 1954 everywhere', appJs.includes('event.doyle_zimmerman.marriage.1954-06-14') && !src.includes('1953-06-14') && !appJs.includes('1953-06-14'));
  ok('S7 Colby Free Press source cited', src.includes('Colby Free Press') && src.includes('Sacred Heart Catholic Church'));
  ok('S8 deploy stamp present', /<meta name="deploy-stamp" content="[0-9a-f]{12} \d{4}-\d{2}-\d{2}">/.test(src));
  // Payload budgets (treaty): set at measured+10% after the Track B
  // Track B close (case absorptions): total 304856, fonts 41783,
  // paths 19763 on 2026-07-08; route layer moved S11 to 22642, budget
  // reset to measured+10% = 24910. TREATY MATH: remaining declared program
  // costs are ~21.6KB (Slate 2) + ~19.3KB (Slate 3) + W5/W6 (~5KB net
  // after the W5 stub-table retirement) -> projected ~323KB against the
  // hard 358,400 ceiling. The 2026-07-09 family-core hard cutover deliberately
  // replaces combined couple labels with 117 individual name records and 18
  // explicit gaps; that reviewed projection moves the hard ceiling to 384,000.
  // S9 is otherwise a per-wave RATCHET (re-measured to
  // +10% at each landing per the documented procedure), so planned
  // waves will legitimately re-measure past this value; the ceiling is
  // the constraint that never moves. Margin is thin: every wave
  // declares its cost and looks for offsetting cuts. Peers bump
  // budgets only via a declared SPEC DELTA; total never exceeds 384000
  // (family-core ruling 2026-07-09; prior owner ceiling 358400).
  // SPEC DELTA 2026-07-10 (owner-approved five-page split, P2): assets
  // extracted; the ceiling now covers page + shared assets together.
  const assetBytes = Buffer.byteLength(fontsCss + siteCss + appJs, 'utf8');
  ok('S9 total payload within owner ceiling', srcBytes + assetBytes <= 384000,
    { page: srcBytes, assets: assetBytes });
  ok('S10 embedded fonts within budget',
    (fontsCss.match(/data:font\/woff2;base64,[A-Za-z0-9+\/=]+/g) || []).join('').length < 45153);
  ok('S11 baked path constants within budget',
    ((appJs.match(/const \w+_D = "[^"]*"/g) || []).join('') +
      (appJs.match(/const ROUTES_(?:MIG|KS) = \{[^\n]*\};/g) || []).join('')).length < 24910);
  ok('S12 generated-region marker pairs present',
    ['basemap-proj', 'basemap-paths', 'basemap-routes'].every((tag) =>
      appJs.split('// BEGIN GENERATED ' + tag).length === 2 &&
      appJs.split('// END GENERATED ' + tag).length === 2));
  ok('S13 route metadata declares 7 lineage and 3 conjectural routes',
    (appJs.match(/id:"route\./g) || []).length === 10 &&
    (appJs.match(/grade:"solid"/g) || []).length === 7 &&
    (appJs.match(/grade:"conjectural"/g) || []).length === 3);
  ok('S14 Slate 3 reader sections present',
    ['id="foreword"', 'id="stories"', 'id="album"', 'id="wanted"', 'class="colophon"']
      .every((token) => src.includes(token)));
  ok('S15 story cards target live person ids',
    (src.match(/class="story-card/g) || []).length === 6 &&
    ['#person.doyle_zimmerman', '#person.bill_dible', '#person.mundell.walter',
      '#person.zodrow.john', '#person.zimmerman.michael'].every((href) => src.includes(`href="${href}"`)));
  ok('S16 context stamps and asides present',
    (src.match(/class="[^"]*context-aside/g) || []).length === 2 &&
    (src.match(/class="tag context"/g) || []).length === 3 &&
    src.includes('Historical background around the family'));
  ok('S17 album plate uses existing ten-image plate VII layout',
    (src.match(/class="album-item/g) || []).length === 10 &&
    src.includes('class="plate album-plate"') &&
    src.includes('<span class="plate-no">Plate VII.</span>'));
  ok('S18 print stylesheet covers keepsake rules',
    siteCss.includes('section.sheet[id^="branch-"], #album, #docket, #index-of-names, #sources') &&
    siteCss.includes('.plate-key { columns: 2; break-inside: avoid; }') &&
    siteCss.includes('figure.plate:not(.revealed)') &&
    siteCss.includes('.tag::before { content: "["; }') &&
    siteCss.includes('.tag::after { content: "]"; }'));
  ok('S19 nav tools expose scale and print controls',
    src.includes('class="nav-tools"') &&
    (src.match(/class="tool scale-btn"/g) || []).length === 3 &&
    src.includes('id="print-btn"') &&
    appJs.includes('localStorage.getItem("zd-scale")') &&
    appJs.includes('window.print()'));
  const publicContentFiles = execFileSync('git', [
    'ls-files', '-z', '--cached', '--others', '--exclude-standard', '--',
    'index.html', 'assets', 'ancestry_geospatial.geojson', 'README.md', 'TODO.md', 'research',
  ], { cwd: ROOT, encoding: 'utf8' }).split('\0').filter(Boolean)
    .filter((relative) => fs.existsSync(path.join(ROOT, relative)));
  const ssnShape = /(^|[^0-9])[0-9]{3}-[0-9]{2}-[0-9]{4}(?![0-9])/m;
  const ssnShapeFiles = publicContentFiles.filter((relative) =>
    ssnShape.test(fs.readFileSync(path.join(ROOT, relative), 'utf8')));
  ok('S20 public research and product content contains no SSN-shaped text',
    ssnShapeFiles.length === 0, ssnShapeFiles.join(', '));
  const plateKeyBlocks = [...src.matchAll(/<!-- BEGIN plate-key:([a-z]+) -->[\s\S]*?<!-- END -->/g)]
    .map((m) => m[1]);
  ok('K1 five generated plate-key regions present',
    plateKeyBlocks.join('|') === 'convergence|zimmerman|mundell|dible|connelly');

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
        accessibleName: svg.getAttribute('aria-label') || '',
        markers: svg.querySelectorAll('g.event-marker[data-event-id]').length,
        edges: svg.querySelectorAll('path.family-link[data-link-id]').length,
        guests: svg.querySelectorAll('g.event-marker.guest').length,
        routes: new Set([...svg.querySelectorAll('path.route-line[data-route-id]')].map((p) => p.dataset.routeId)).size,
        routePaths: svg.querySelectorAll('path.route-line[data-route-id]').length,
        solidRoutePaths: svg.querySelectorAll('path.route-line[data-route-id]:not(.conjectural)').length,
        conjecturalRoutePaths: svg.querySelectorAll('path.route-line[data-route-id].conjectural').length,
        routesPointerNone: [...svg.querySelectorAll('path.route-line[data-route-id]')].every(
          (p) => getComputedStyle(p).pointerEvents === 'none'),
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
  const mapAccessibleNames = Object.fromEntries(Object.keys(MAP_ACCESSIBLE_NAMES)
    .map((id) => [id, plates[id]?.accessibleName || '']));
  ok('B2a all five map SVGs have complete accessible names',
    Object.entries(MAP_ACCESSIBLE_NAMES).every(([id, expected]) =>
      mapAccessibleNames[id] === expected), JSON.stringify(mapAccessibleNames));
  const keyAudit = await page.evaluate(() => PLATES.map((cfg) => {
    const data = plateData(cfg);
    const expected = data.events.map((e) => e.id);
    const fig = document.getElementById(cfg.svgId).closest('figure');
    const rows = [...fig.querySelectorAll('.plate-key [data-e]')];
    return {
      key: cfg.key,
      expected,
      actual: rows.map((row) => row.dataset.e),
      keyNos: rows.map((row) => row.querySelector('b')?.textContent.trim() || ''),
      markerNos: [...document.getElementById(cfg.svgId).querySelectorAll('g.event-marker .marker-no')]
        .map((node) => node.textContent.trim()),
    };
  }));
  ok('K2 static plate keys match computed order and count', keyAudit.every((plate) =>
    JSON.stringify(plate.actual) === JSON.stringify(plate.expected) &&
    plate.keyNos.join('|') === plate.expected.map((_, i) => String(i + 1)).join('|')),
    JSON.stringify(keyAudit));
  ok('N1 marker numerals are present and unique per plate', keyAudit.every((plate) =>
    plate.markerNos.join('|') === plate.expected.map((_, i) => String(i + 1)).join('|')),
    JSON.stringify(keyAudit));
  for (const [id, expect] of Object.entries(ROUTE_EXPECT)) {
    const p = plates[id];
    assert.equal(p.routes, expect.routes, id + ' distinct route ids');
    assert.equal(p.routePaths, expect.paths, id + ' route paths');
    assert.equal(p.solidRoutePaths, expect.solidPaths, id + ' solid route paths');
    assert.equal(p.conjecturalRoutePaths, expect.conjecturalPaths, id + ' conjectural route paths');
  }
  ok('R1 route path counts by style match each affected plate', true);
  ok('R2 conjectural route paths are dashed only off convergence',
    plates['map-convergence'].conjecturalRoutePaths === 0 &&
    ['map-line-zimmerman', 'map-line-mundell', 'map-line-dible', 'map-line-connelly']
      .every((id) => plates[id].conjecturalRoutePaths > 0));
  ok('P1 routes are noninteractive', Object.keys(ROUTE_EXPECT).every((id) => plates[id].routesPointerNone));
  const mapPlateCartouches = await page.evaluate(() => [...document.querySelectorAll('figure.plate')]
    .filter((fig) => fig.querySelector('svg')).map((fig) => ({
    no: fig.querySelector('.plate-no')?.textContent.trim() || '',
    title: fig.querySelector('.plate-title')?.textContent.trim() || '',
    imprint: fig.querySelector('.plate-imprint')?.textContent.trim() || '',
    sub: fig.querySelector('.plate-sub')?.textContent.trim() || '',
    h2: fig.closest('section')?.querySelector('h2')?.textContent.trim() || '',
    scaleBars: fig.querySelectorAll('.plate-scalebar').length,
    scaleLabel: fig.querySelector('.plate-scalebar text')?.textContent.trim() || '',
    cornerNo: fig.querySelector('.plate-corner-no')?.textContent.trim() || '',
  })));
  const allPlateNos = await page.evaluate(() => [...document.querySelectorAll('figure.plate .plate-no')]
    .map((n) => n.textContent.trim()));
  ok('SB1 scale bars carry reference-latitude labels', mapPlateCartouches.length === 5 &&
    mapPlateCartouches.every((p) => p.scaleBars === 1 && /LAT\. 40°(?: N|27[′'] N)$/.test(p.scaleLabel)),
    JSON.stringify(mapPlateCartouches));
  ok('RN1 plate numerals are cartouche-only and document-ordered',
    allPlateNos.join('|') === 'Plate II.|Plate III.|Plate IV.|Plate V.|Plate VI.|Plate VII.' &&
    mapPlateCartouches.map((p) => p.cornerNo).join('|') === 'PL. II.|PL. III.|PL. IV.|PL. V.|PL. VI.' &&
    mapPlateCartouches.every((p) => p.title && p.imprint && p.sub && !/\bPlate [IVX]+\b/.test(p.h2)),
    JSON.stringify({ allPlateNos, mapPlateCartouches }));
  const removes = await page.evaluate(() => {
    const table = document.querySelector('.ledger-table table');
    const rows = table ? [...table.querySelectorAll('tbody tr')] : [];
    return {
      caption: document.querySelector('.ledger-table figcaption')?.textContent.trim() || '',
      rows: rows.length,
      conjectural: rows.filter((r) => r.classList.contains('conjectural')).length,
      text: table?.textContent || '',
    };
  });
  ok('TL1 Table of Removes has planned rows and figures',
    removes.caption.startsWith('Table of Removes') && removes.rows === 11 && removes.conjectural === 4 &&
    ['8,158', '10,779', '~9,100', '2,216', '1921-2023'].every((token) => removes.text.includes(token)),
    JSON.stringify(removes));
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
    const evidenceRows = [...document.querySelectorAll('.person')].filter((row) =>
      row.querySelector('.person-head .tag.documented, .person-head .tag.strong'));
    const evidenceRowsWithoutCitation = evidenceRows
      .filter((row) => !row.querySelector('a.cite[href^="#s"]'))
      .map((row) => row.id);
    return {
      h2s,
      sourceCount: lis.length,
      sourcesWithAnchor: lis.filter((li) => li.querySelector('a[href]')).length,
      groups: sec ? sec.querySelectorAll('details').length : 0,
      firstOpen: sec ? !!sec.querySelector('details[open]') : false,
      persons: document.querySelectorAll('.person').length,
      personWithoutIds: document.querySelectorAll('.person:not([id])').length,
      personIds: [...document.querySelectorAll('.person[id^="person."], .person[id^="gap."]')]
        .map((el) => el.id),
      breadth: document.body.textContent.includes('The goal here is breadth plus honesty'),
      geojsonLink: !!document.querySelector('a[href="ancestry_geospatial.geojson"]'),
      evidenceRows: evidenceRows.length,
      evidenceRowsWithoutCitation,
    };
  });
  for (const h of ['Doyle Julius Zimmerman Branches', 'Evelyn Delores Mundell Zimmerman Branches',
    'William J. "Bill" Dible Branches', 'Donna Lea Connelly Dible Branches',
    'Six Stories The Records Tell', 'Family Album', 'Wanted: Family Papers',
    'The Docket', 'Index of Names', 'Source Ledger'])
    assert.ok(content.h2s.includes(h), 'missing h2: ' + h);
  ok('C1 all section headings present', true);
  ok('C2 source ledger count matches', content.sourceCount === SOURCE_ITEMS, content.sourceCount);
  ok('C3 every source has a link', content.sourcesWithAnchor === SOURCE_ITEMS, content.sourcesWithAnchor);
  ok('C4 sources grouped, first open', content.groups >= 5 && content.firstOpen, content.groups);
  ok('C5 person entry count matches', content.persons === PERSON_DIVS, content.persons);
  const idRe = /^(?:person|gap)\.[a-z0-9]+(?:[._-][a-z0-9]+)*$/;
  ok('C8 family rows have canonical person or gap ids',
    content.personIds.length === PERSON_IDS &&
    content.personWithoutIds === 0 &&
    new Set(content.personIds).size === PERSON_IDS &&
    content.personIds.every((id) => idRe.test(id)),
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
  const citationContract = await page.evaluate((sourceItems) => {
    const sec = [...document.querySelectorAll('section')].find((s) =>
      s.querySelector('h2') && s.querySelector('h2').textContent.trim() === 'Source Ledger');
    const ledgerLis = sec ? [...sec.querySelectorAll('li')] : [];
    const scodes = ledgerLis.map((li) => li.querySelector(':scope > .scode')?.textContent.trim() || '');
    const allCiteLinks = [...document.querySelectorAll('a.cite[href]')];
    const citeLinks = allCiteLinks.filter((a) => /^#s[1-9]\d*$/.test(a.getAttribute('href') || ''));
    const failures = [];
    const phaseRows = new Set();
    citeLinks.forEach((a) => {
      const targetId = decodeURIComponent(a.hash.slice(1));
      const li = document.getElementById(targetId);
      const code = li?.querySelector(':scope > .scode')?.textContent.trim();
      const row = a.closest('.person[id]');
      if (!li || li.tagName !== 'LI' || !code ||
        code !== li.id || targetId !== li.id || targetId !== a.textContent.trim()) failures.push(a.outerHTML);
      if (row) phaseRows.add(row.id);
    });
    return {
      ledgerIds: ledgerLis.filter((li, i) => li.id === `s${i + 1}`).length,
      scodeCount: scodes.filter(Boolean).length,
      sequential: scodes.length === sourceItems &&
        scodes.every((code, i) => code === `s${i + 1}` && ledgerLis[i]?.id === code),
      pinned: scodes.slice(0, 4).join('|'),
      chips: citeLinks.length,
      phaseRows: phaseRows.size,
      badCites: allCiteLinks.length - citeLinks.length,
      failures,
    };
  }, SOURCE_ITEMS);
  ok('C14 citation chips target coded ledger rows',
    citationContract.ledgerIds === SOURCE_ITEMS &&
    citationContract.scodeCount === SOURCE_ITEMS &&
    citationContract.sequential &&
    citationContract.pinned === 's1|s2|s3|s4' &&
    citationContract.phaseRows >= 22 &&
    citationContract.chips >= 22 && citationContract.chips <= 100 &&
    citationContract.badCites === 0 &&
    citationContract.failures.length === 0,
    JSON.stringify(citationContract));
  ok('C14a every documented or strong person row cites the Source Ledger',
    content.evidenceRows === 39 && content.evidenceRowsWithoutCitation.length === 0,
    JSON.stringify(content.evidenceRowsWithoutCitation));
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
      .people.filter((p) => p.k === 'person').length;
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
  const docketCheck = await page.evaluate(({ c, r, n }) => {
    const s = document.getElementById('docket'), f = [];
    if (!s) return ['missing docket'];
    const a = [...s.querySelectorAll(':scope>div[id^="case."]')], statuses = '|OPEN|IN CONFLICT|NEEDS PULL|CLOSED|';
    if (a.length !== c) f.push(`case count ${a.length}`);
    for (const x of a) {
      const h = x.querySelector(':scope>div:first-child'), b = x.querySelector(':scope>p'),
        q = x.querySelector(':scope>div:last-child'), t = h?.querySelector('b:last-child')?.textContent.trim();
      if (!/^case\.\d{2}$/.test(x.id) || !h?.querySelector('b:first-child') || !h.querySelector('h3') ||
        !statuses.includes(`|${t}|`) || !b?.textContent.trim() || !q?.textContent.trim() ||
        [...(q?.querySelectorAll('a[href^="#"]') || [])].some((l) =>
          !document.getElementById(decodeURIComponent(l.hash.slice(1)))))
        f.push(x.id || 'case without id');
    }
    if (s.querySelectorAll(':scope>ul:nth-of-type(1) li').length < r) f.push('corrigenda count');
    if (s.querySelectorAll(':scope>ul:nth-of-type(2) li').length < n) f.push('negative-register count');
    return f;
  }, { c: CASE_ARTICLES, r: CORRIGENDA_ITEMS, n: NEGATIVE_REGISTER_ITEMS });
  ok('C13 docket has 23 structured cases plus registers', docketCheck.length === 0, JSON.stringify(docketCheck));

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
  // post-W4, 26,703 post-correction, 29,725 post-W5 Docket, 31,108 post-plate-keys, 36,462 post-Slate-3 reader layer, 37,742 post-Mundell/Clemans intake, 40,935 post family-card air pass (owner-approved keepsake readability: line-height 1.62, card padding, grid gaps).
  ok('L2 page height within layout budget (<42135)', desktop.scrollH < 42135, desktop.scrollH);

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
