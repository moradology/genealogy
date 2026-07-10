
    function initScale() {
      const root = document.documentElement;
      const buttons = document.querySelectorAll(".scale-btn");
      const hasStorage = "localStorage" in window && window.localStorage !== null;
      function apply(v) {
        if (v === "1" || v === "2") root.dataset.scale = v;
        else delete root.dataset.scale;
        buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.scale === (v || "0"))));
      }
      apply(hasStorage ? localStorage.getItem("zd-scale") : null);
      buttons.forEach((btn) => btn.addEventListener("click", () => {
        apply(btn.dataset.scale);
        if (hasStorage) localStorage.setItem("zd-scale", btn.dataset.scale);
      }));
    }
    function initPrint() {
      document.getElementById("print-btn").addEventListener("click", () => window.print());
      window.addEventListener("beforeprint", () => {
        document.querySelectorAll("#sources details").forEach((d) => {
          d.dataset.wasOpen = d.open ? "1" : "";
          d.open = true;
        });
      });
      window.addEventListener("afterprint", () => {
        document.querySelectorAll("#sources details").forEach((d) => {
          d.open = d.dataset.wasOpen === "1";
        });
      });
    }
    initScale();
    initPrint();
  
;

    const verifiedEventData = [
      {"id":"event.durham.david_birth.1832-12-28","date":"1832-12-28","sort":"1832-12-28","person":"David Monroe Durham","type":"birth","place":"North Carolina","anchor":"Donna Lea Connelly Dible","confidence":"strong","coords":[-79.0392919,35.6729639]},
      {"id":"event.claar.henry_birth.1838-12-31","date":"1838-12-31","sort":"1838-12-31","person":"Henry Claar","type":"birth","place":"Jackson County, Ohio","anchor":"Donna Lea Connelly Dible","confidence":"strong","coords":[-82.6089043,39.0131871]},
      {"id":"event.zodrow.antonette_grams_birth.1846-05-23","date":"1846-05-23","sort":"1846-05-23","person":"Antonia/Antonette Grams Zodrow","type":"birth","place":"Prussia, today Poland","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[19.1451,51.9194]},
      {"id":"event.long.robert_ann_marriage.1857-02-19","date":"1857-02-19","sort":"1857-02-19","person":"Robert Nelson Long","type":"marriage","place":"Griggsville Township, Pike County, Illinois","anchor":"William J. Dible","confidence":"strong","coords":[-90.7245722,39.7089362]},
      {"id":"event.durham.david_virginia_marriage.1857-08-19","date":"1857-08-19","sort":"1857-08-19","person":"David Monroe Durham","type":"marriage","place":"Menard County, Illinois","anchor":"Donna Lea Connelly Dible","confidence":"strong","coords":[-89.7858065,40.0166667]},
      {"id":"event.zimmerman.michael_birth.1869-10-25","date":"1869-10-25","sort":"1869-10-25","person":"Michael John Zimmerman Sr.","type":"birth","place":"Wuerttemberger Hof, Mainhardt, Baden-Wuerttemberg","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[9.5830848,49.064658]},
      {"id":"event.nauer.elizabeth_birth.1872-04-07","date":"1872-04-07","sort":"1872-04-07","person":"Elizabeth Catherine Nauer Zimmerman","type":"birth","place":"Waterloo, Ontario","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-80.5222961,43.4652699]},
      {"id":"event.mcclelland.cora_birth.1872-12-08","date":"1872-12-08","sort":"1872-12-08","person":"Cora Ellie McClellan Long","type":"birth","place":"Fairfield, Jefferson County, Iowa","anchor":"William J. Dible","confidence":"strong","coords":[-91.9629664,41.008632]},
      {"id":"event.zimmerman.john_paul_household.1880","date":"1880","sort":"1880-06-01","person":"John Paul Zimmerman","type":"household","place":"Norfolk, Madison County, Nebraska","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-97.4169964,42.0283379]},
      {"id":"event.zimmerman.michael_elizabeth_marriage.1895-11-19","date":"1895-11-19","sort":"1895-11-19","person":"Michael John Zimmerman Sr.","type":"marriage","place":"Cawker City, Mitchell County, Kansas","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-98.433672,39.51251]},
      {"id":"event.dible.harry_julia_marriage.1896-06-10","date":"1896-06-10","sort":"1896-06-10","person":"Harry H. Dible","type":"marriage","place":"Trenton, Hitchcock County, Nebraska","anchor":"William J. Dible","confidence":"strong","coords":[-101.0131604,40.1757537]},
      {"id":"event.durham.david_death.1897-08-24","date":"1897-08-24","sort":"1897-08-24","person":"David Monroe Durham","type":"death","place":"Nebo, Hopkins County, Kentucky","anchor":"Donna Lea Connelly Dible","confidence":"strong","coords":[-87.6427843,37.383656]},
      {"id":"event.mcclelland.dorsey_burial_selden.1904","date":"1904-05-19","sort":"1904-05-19","person":"Dorsey Overturf McClelland","type":"death_or_burial","place":"Selden Cemetery, Selden, Sheridan County, Kansas","anchor":"William J. Dible","confidence":"strong","coords":[-100.567644,39.540837]},
      {"id":"event.nauer.catherina_koeberger_death.1906-02-01","date":"1906-02-01","sort":"1906-02-01","person":"Catherina Marie Koeberger Nauer","type":"death_or_burial","place":"Saint Joseph Cemetery, New Almelo, Norton County, Kansas","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-100.1179098,39.5941707]},
      {"id":"event.zodrow.john_death.1915-03-15","date":"1915-03-15","sort":"1915-03-15","person":"John Zodrow","type":"death_or_burial","place":"Leoville, Decatur County, Kansas","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-100.4609753,39.5816708]},
      {"id":"event.claar.henry_death.1915-12-28","date":"1915-12-28","sort":"1915-12-28","person":"Henry Claar","type":"death","place":"Topeka, Kansas","anchor":"Donna Lea Connelly Dible","confidence":"strong","coords":[-95.677556,39.049011]},
      {"id":"event.long.ray_almeda_marriage.1922","date":"1922","sort":"1922-01-01","person":"Almeda Ora Long Dible","type":"marriage","place":"Jackson County, Kansas","anchor":"William J. Dible","confidence":"documented","coords":[-95.8159647,39.4030917]},
      {"id":"event.doyle_zimmerman.birth.1930-04-12","date":"1930-04-12","sort":"1930-04-12","person":"Doyle Julius Zimmerman","type":"birth","place":"Selden, Sheridan County, Kansas","anchor":"Doyle Julius Zimmerman","confidence":"documented","coords":[-100.567644,39.540837]},
      {"id":"event.bill_dible.birth.1933-06-02","date":"1933-06-02","sort":"1933-06-02","person":"William J. \"Bill\" Dible","type":"birth","place":"Rexford, Thomas County, Kansas","anchor":"William J. Dible","confidence":"documented","coords":[-100.743482,39.471671]},
      {"id":"event.zodrow.antonette_grams_death.1934-08-01","date":"1934-08-01","sort":"1934-08-01","person":"Antonia/Antonette Grams Zodrow","type":"death","place":"Dresden, Decatur County, Kansas","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-100.4192737,39.6223582]},
      {"id":"event.evelyn_mundell.birth.1935-01-16","date":"1935-01-16","sort":"1935-01-16","person":"Evelyn Delores Mundell Zimmerman","type":"birth","place":"Flagler, Kit Carson County, Colorado","anchor":"Evelyn Delores Mundell Zimmerman","confidence":"documented","coords":[-103.067158,39.2930463]},
      {"id":"event.donna_connelly.birth.1935-04-24","date":"1935-04-24","sort":"1935-04-24","person":"Donna Lea Connelly Dible","type":"birth","place":"Rexford, Thomas County, Kansas","anchor":"Donna Lea Connelly Dible","confidence":"documented","coords":[-100.743482,39.471671]},
      {"id":"event.mcclelland.cora_death.1952-03-19","date":"1952-03-19","sort":"1952-03-19","person":"Cora Ellie McClellan Long","type":"death","place":"Manhattan, Riley County, Kansas","anchor":"William J. Dible","confidence":"strong","coords":[-96.5716694,39.1836082]},
      {"id":"event.doyle_zimmerman.marriage.1954-06-14","date":"1954-06-14","sort":"1954-06-14","person":"Doyle Julius Zimmerman","type":"marriage","place":"Sacred Heart Catholic Church, Colby, Thomas County, Kansas","anchor":"Doyle Julius Zimmerman","confidence":"documented","coords":[-101.0526881,39.3959655]},
      {"id":"event.bill_dible.death.2022-08-09","date":"2022-08-09","sort":"2022-08-09","person":"William J. \"Bill\" Dible","type":"death","place":"Lee County, Florida","anchor":"William J. Dible","confidence":"documented","coords":[-81.8823135,26.5999265]},
      {"id":"event.donna_connelly.death.2022-12-20","date":"2022-12-20","sort":"2022-12-20","person":"Donna Lea Connelly Dible","type":"death","place":"Bonita Springs, Lee County, Florida","anchor":"Donna Lea Connelly Dible","confidence":"documented","coords":[-81.7786972,26.339806]},
      {"id":"event.evelyn_mundell.death.2023-04-15","date":"2023-04-15","sort":"2023-04-15","person":"Evelyn Delores Mundell Zimmerman","type":"death","place":"Colby, Thomas County, Kansas","anchor":"Evelyn Delores Mundell Zimmerman","confidence":"documented","coords":[-101.0526881,39.3959655]},
      {"id":"event.zimmerman.john_paul_birth.1842-03-09","date":"1842-03-09","sort":"1842-03-09","person":"John Paul Zimmerman","type":"birth","place":"Bavaria, Germany","anchor":"Doyle Julius Zimmerman","confidence":"lead","coords":[11.497889,48.790447]},
      {"id":"event.mundell.homer_marriage.1933-06-19","date":"1933-06-19","sort":"1933-06-19","person":"Homer Clair Mundell","type":"marriage","place":"Akron, Washington County, Colorado","anchor":"Evelyn Delores Mundell Zimmerman","confidence":"documented","coords":[-103.214725,40.161638]},
      {"id":"event.mundell.homer_marriage.1956-02-06","date":"1956-02-06","sort":"1956-02-06","person":"Homer Clair Mundell","type":"marriage","place":"Colorado Springs, El Paso County, Colorado","anchor":"Evelyn Delores Mundell Zimmerman","confidence":"documented","coords":[-104.821363,38.833882]},
      {"id":"event.mundell.homer_residence.1930","date":"1930","sort":"1930-01-01","person":"Homer Clair Mundell","type":"residence","place":"Cloverly, Big Horn County, Wyoming","anchor":"Evelyn Delores Mundell Zimmerman","confidence":"documented","coords":[-108.55,44.94]},
      {"id":"event.zodrow.julius_death.1959-03-13","date":"1959-03-13","sort":"1959-03-13","person":"Julius Henry Zodrow","type":"death","place":"Medical Lake, Spokane County, Washington","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-117.703,47.573]},
      {"id":"event.zodrow.ernestina_death.1940-05-14","date":"1940-05-14","sort":"1940-05-14","person":"Ernestina Baier Zodrow","type":"death","place":"Chewelah, Stevens County, Washington","anchor":"Doyle Julius Zimmerman","confidence":"strong","coords":[-117.715,48.276]},
      {"id":"event.long.jf_marriage.1826-02-23","date":"1826-02-23","sort":"1826-02-23","person":"John Franklin Long + Sally A. Patton","type":"marriage","place":"Vanderburgh County, Indiana","anchor":"William J. Dible","confidence":"lead","coords":[-87.583,38.025]},
      {"id":"event.claar.swiss_origin.1700","date":"1700s","sort":"1700-01-01","person":"Claar family, Canton Bern (lead)","type":"european_origin_hypothesis","place":"Canton Bern, Switzerland","anchor":"Donna Lea Connelly Dible","confidence":"lead","coords":[7.45,46.95]}
    ];

    const familyLinkData = [
      {
        id: "link.zimmerman_nauer_births_to_union",
        anchor: "Doyle Julius Zimmerman",
        from: ["event.zimmerman.michael_birth.1869-10-25", "event.nauer.elizabeth_birth.1872-04-07"],
        to: "event.zimmerman.michael_elizabeth_marriage.1895-11-19",
        kind: "couple convergence",
        label: "Michael Zimmerman and Elizabeth Nauer converge at Cawker City"
      },
      {
        id: "link.zimmerman_nauer_union_to_doyle",
        anchor: "Doyle Julius Zimmerman",
        from: ["event.zimmerman.michael_elizabeth_marriage.1895-11-19"],
        to: "event.doyle_zimmerman.birth.1930-04-12",
        kind: "descendant path",
        label: "Michael and Elizabeth's line runs through Leonard Henry Zimmerman to Doyle"
      },
      {
        id: "link.doyle_evelyn_births_to_union",
        anchor: "Doyle Julius Zimmerman",
        from: ["event.doyle_zimmerman.birth.1930-04-12", "event.evelyn_mundell.birth.1935-01-16"],
        to: "event.doyle_zimmerman.marriage.1954-06-14",
        kind: "couple convergence",
        label: "Doyle Zimmerman and Evelyn Mundell converge at Colby"
      },
      {
        id: "link.john_paul_household_to_michael",
        anchor: "Doyle Julius Zimmerman",
        from: ["event.zimmerman.john_paul_household.1880"],
        to: "event.zimmerman.michael_birth.1869-10-25",
        kind: "parent evidence",
        label: "The 1880 Norfolk household record ties Michael to his parents, John Paul and Catherine"
      },
      {
        id: "link.dible_union_to_bill",
        anchor: "William J. Dible",
        from: ["event.long.ray_almeda_marriage.1922"],
        to: "event.bill_dible.birth.1933-06-02",
        kind: "parents to child",
        label: "Ray Dible and Almeda Long produce Bill Dible"
      },
      {
        id: "link.harry_julia_to_bill",
        anchor: "William J. Dible",
        from: ["event.dible.harry_julia_marriage.1896-06-10"],
        to: "event.bill_dible.birth.1933-06-02",
        kind: "descendant path",
        label: "Harry and Julia Dible's line runs through Ray Hershel Dible to Bill"
      },
      {
        id: "link.long_sleight_to_almeda",
        anchor: "William J. Dible",
        from: ["event.long.robert_ann_marriage.1857-02-19"],
        to: "event.long.ray_almeda_marriage.1922",
        kind: "descendant path",
        label: "Robert Long and Ann Sleight's line runs down to Almeda Long"
      },
      {
        id: "link.durham_birth_to_union",
        anchor: "Donna Lea Connelly Dible",
        from: ["event.durham.david_birth.1832-12-28"],
        to: "event.durham.david_virginia_marriage.1857-08-19",
        kind: "individual to union",
        label: "David Monroe Durham moves into the Durham/Ford union"
      },
      {
        id: "link.durham_ford_to_donna",
        anchor: "Donna Lea Connelly Dible",
        from: ["event.durham.david_virginia_marriage.1857-08-19"],
        to: "event.donna_connelly.birth.1935-04-24",
        kind: "descendant path",
        label: "David Durham and Virginia Ford's line runs through America and Chester to Donna"
      },
      {
        id: "link.claar_to_donna",
        anchor: "Donna Lea Connelly Dible",
        from: ["event.claar.henry_birth.1838-12-31", "event.claar.henry_death.1915-12-28"],
        to: "event.donna_connelly.birth.1935-04-24",
        kind: "descendant path",
        label: "Henry Claar's line runs through Samuel and Martha to Donna"
      }
    ];
// BEGIN GENERATED basemap-proj -- regenerate with: uv run tools/build_basemap.py --write
// Basemap generated from Natural Earth (public domain) via build_basemap.py.
const MIG_VIEW = { w: 1000, h: 397.1 };
const KS_VIEW = { w: 1000, h: 598.6 };
const MIG_PROJ = { p1: 30, p2: 50, lon0: -42, xMin: -0.955457, yMax: 0.480234, s: 523.309669 };
const KS_PROJ = { lonMin: -103.5, latMax: 42.5, k: 0.760972, s: 146.012007, lonMax: -94.5, latMin: 38.4 };
const MIG_WINDOW = { lonMin: -106, latMin: 24, lonMax: 22, latMax: 54.5 };
// END GENERATED basemap-proj

function migFmt(v) {
  const r = Math.round(v * 10) / 10;
  return Number.isInteger(r) ? String(r) : r.toFixed(1);
}

function computeFanPath(project) {
  const w = MIG_WINDOW;
  const steps = 240;
  const pts = [];
  for (let i = 0; i <= steps; i += 1) pts.push(project(w.lonMin + (w.lonMax - w.lonMin) * i / steps, w.latMin));
  for (let i = 0; i <= steps; i += 1) pts.push(project(w.lonMax, w.latMin + (w.latMax - w.latMin) * i / steps));
  for (let i = 0; i <= steps; i += 1) pts.push(project(w.lonMax - (w.lonMax - w.lonMin) * i / steps, w.latMax));
  for (let i = 0; i <= steps; i += 1) pts.push(project(w.lonMin, w.latMax - (w.latMax - w.latMin) * i / steps));
  return "M" + pts.map((pt) => migFmt(pt[0]) + " " + migFmt(pt[1])).join("L") + "Z";
}

function computeGraticulePath(project) {
  const w = MIG_WINDOW;
  const inside = (pt) => pt[0] >= 0 && pt[0] <= MIG_VIEW.w && pt[1] >= 0 && pt[1] <= MIG_VIEW.h;
  const chains = [];
  const collect = (pts) => {
    let current = [];
    pts.forEach((pt) => {
      if (inside(pt)) current.push(pt);
      else {
        if (current.length > 1) chains.push(current);
        current = [];
      }
    });
    if (current.length > 1) chains.push(current);
  };
  for (let lon = -100; lon < 30; lon += 10) {
    const pts = [];
    for (let i = 0; i <= 60; i += 1) pts.push(project(lon, w.latMin + (w.latMax - w.latMin) * i / 60));
    collect(pts);
  }
  for (let lat = 30; lat < 60; lat += 10) {
    const pts = [];
    for (let i = 0; i <= 120; i += 1) pts.push(project(w.lonMin + (w.lonMax - w.lonMin) * i / 120, lat));
    collect(pts);
  }
  return chains.map((chain) =>
    "M" + chain.map((pt) => migFmt(pt[0]) + " " + migFmt(pt[1])).join("L")
  ).join("");
}

// BEGIN GENERATED basemap-paths -- regenerate with: uv run tools/build_basemap.py --write
const MIGRATION_LAND_D = "M765.4 312.7l5.9 15.3l-25.8 9.1l8.2 22.4l-7.3 3.4l-0.5 5.2l5.9 12.4l-32.9 10.3l-1 3.6l-0.7 -4l18.9 -6.5l2.1 -8.7l-1.3 -13.2l8 -13.3l-0.1 -12.4l2.2 -1.5l0.1 -7.7l12.9 -4.5l1.7 -2.9l4.6 -2.1l-2 -4.5l1.2 -0.5ZM267.9 -12l-12.6 14.6l5.2 5.3l-4.8 16l7.1 2.2l6.1 8.4l3.7 11.4l7.6 11.6l12.4 7.9l-4.3 6.9l-2.6 9.1l-0.8 11.1l4 11.5l5.2 -0.9l6.6 -7.4l3.3 -14.5l-1.5 -6l9.6 -0.5l8.1 -3.7l5.2 -4.9l2 -6l-0.1 -8.8l-2.7 -9l9.3 -7l6.1 -23.5l3.8 -0.8l10.2 8l4.5 -1.1l6.3 11.8l0.1 4l7.7 3.3l-4.8 19.8l3.9 2.8l1.8 6.4l8.4 -3.1l11.5 -12.5l7.8 34.9l-3.3 5.3l9.3 12.9l7.9 4l2.9 3.5l0.8 8.1l4 1.9l1.6 3.8l-1.2 10.3l-9.2 5.3l-9.9 1.5l-8.6 6l-10 -0.6l-26.2 -8.1l-6.5 4.9l-8.4 1.7l-21.3 14.5l5.5 0.3l13 -8.4l14.2 -3.7l8.8 1.5l4 5.7l-7.1 4.5l-0.4 17.1l6.8 6.4l10.4 1.1l8.3 -8.6l-0.9 6.5l3.3 4l-8.9 4.2l-22.1 4l-8.7 4.4l-4.6 -1.9l1.8 -7.4l12.7 -4.3l-17 -3.2l-2.5 -6.1l3.5 -11.8l-1.9 -3.3l-4.4 0.3l-1.2 -2.9l-14 14.4l-5.1 0.2l-1.3 1.9l-20.2 -7.3l-16.3 6.8l-11.4 -4.8l-3.3 0.1l-0.8 5.6l-27.2 -0.9l-1 -4.5l11.8 -9.2l4.7 -15.6l-4 -6.7l1.4 -1.1l-1.9 -2.2l0.2 -3.9l-2.9 -0.7l0.4 -4.5l-12.6 -21.5l-6 -0.5l-6.9 -6.8l-4.8 -1.6l-11 -12.9l1.2 -7.1l-1.7 -1.1l-2 2.9l-42.3 -32.1l-26.6 -24l-31.8 -33.6ZM316.1 -0.8l5.1 -2.5l5.5 2.8l-8.1 4.2l-2.8 -1.7l0.3 -2.8ZM329.6 9.8l2.8 -1.9l1.6 1l0.2 2.3l-3.8 4l-1.5 -1.6l0.6 -3.7ZM422.3 142.9l-9.1 12.5l4.3 -2.4l3.6 2.5l-2.5 2.8l4.8 3.3l3 -1.8l5.5 3.6l-2.7 6.4l4.4 -1l1.4 10.7l-3.6 7.6l-6.6 -2.3l2.3 -7.2l-1.5 -1.4l-8.2 6.8l-3.6 -0.9l5 -3.5l-5.5 -3.1l-18.2 -3l-0.4 -2.8l4.3 -2.4l-2.1 -2.9l6 -4.4l8.6 -13.2l9.8 -6.9l2.6 0.8l-1.5 2.3ZM414.2 -12l6.1 2.3l-2.9 6.7l-9.9 9.7l-4 -5.5l-3.7 -11.2l-5.5 -0.3l-2.2 5.4l7.9 16l0.2 10.3l-3.3 6.5l-13.2 -14.9l6.4 17l-0.2 3.5l-10.8 -7.3l-7.5 -8.4l-3.5 -6.3l2.4 -2.1l-8.6 -13.8l-1 2.7l-12.2 -3.2l-2 -4.6l2.4 -2.5l19.1 1.6l-0 -1.6ZM368.9 145.3l9.1 3.8l4.8 6.8l-9.7 -5.1l-4.3 -5.5ZM365.5 171.1l1 4.8l9.8 3.3l-6.2 2.9l-6.8 -5.6l-0.8 -3.3l3 -2.1ZM100.4 -12l31.8 33.6l26.6 24l42.3 32.1l2 -2.9l1.7 1.1l-1.2 7.1l11 12.9l4.8 1.6l6.9 6.8l6 0.5l12.6 21.5l-0.4 4.5l2.9 0.7l-0.2 3.9l1.9 2.2l-1.4 1.1l4 6.7l-4.7 15.6l-11.8 9.2l1 4.5l27.2 0.9l0.8 -5.6l3.3 -0.1l11.4 4.8l16.3 -6.8l20.2 7.3l1.3 -1.9l5.1 -0.2l14 -14.4l1.2 2.9l4.4 -0.3l1.9 3.3l-3.5 11.8l2.8 9.2l-22.4 3.7l-6.7 5.6l-1.6 4.5l0.6 5.2l2.6 1.1l0.4 -3.3l1.3 2.5l-1.3 2.3l-26 -2.4l9.9 1.8l1.3 2.3l-9.9 -0.7l-3.5 -2.5l-2.8 1.6l1.7 1.1l-3.7 5.5l-7.2 4.6l-2.2 -6.3l-0.5 10.4l-9.8 7.6l3.9 -5.4l-2.1 -4.5l2.1 -7.2l-2.7 3.1l-0.8 5.9l-3.8 -3.1l3.4 4.5l-2.9 8.1l1.7 1.4l-2.9 11.9l-6.9 4.5l-8.1 -0.5l-6.6 3l-3.7 -1l-28.4 11.2l-3.9 5.3l-1.5 6.3l-3 30.5l-4.7 8.7l-4.3 4.3l-2.8 0l-3.3 -2.8l-1.9 -16.6l0.2 -11.8l4.2 -4.7l-1.9 -15.1l-2.1 -2.7l-9 -0l-5.7 -11l-22.9 -10.6l-1.5 8.4l-1.9 0.3l-1.9 -2.7l-3.5 -0.1l-4.8 -3.3l-2.5 -7.2l-6.5 -2.7l-3.7 -4.9l-11.2 -4.1l-24.8 1.2l-7.7 7.4l-2.8 7.3l-2.8 -1.7l-7.1 -11.3l3.2 -11.1l1.1 -20.5l-2.1 -6.3l-5.2 -3.9l-8.5 2.4l-3.3 -6.4l-1.4 -4.8l2.9 -10.4l-2 -15.1l-9.9 -9l-2.6 2.7l-15.7 -14.9l-12.6 -28.5l1.8 -0.7l-13.6 -12.5l2.6 -4l0.7 -7.1l-1.5 -3.4l1.4 -2.3l-6 -15.4l3.3 -3.8l2.6 -11.2l7.9 -13.6l3.1 -13.2l5.3 -5.2l1.7 -5.9l12.9 -8.1l4.3 -5.8l6.5 -2.4ZM1012 330.6l-5.1 3.5l-3.8 -5.2l-5.4 -0.6l-4.3 -12.9l4.1 -14.5l-7.2 -10.4l-9.9 -22.1l-11 -2.6l-10.5 -10.4l3.9 -9.3l49.1 -10.3ZM237.8 393.2l-2.8 8.4l-2.6 0.8l0.2 5.9l-14.5 -7l-4.6 0.2l-3.5 -4.5l1.9 -2.6l13.6 7.3l3.8 -0.9l-2.5 -5.3l1.3 -3.4l-4.8 -3.4l2.8 -1.8l11.8 6.3ZM232.6 408.4l-0.2 -5.9l2.6 -0.8l4.4 -9.6l13.2 6.8l0.5 3.7l4.8 1.3l-1.1 2.6l4.4 2.5l-28.6 -0.7ZM820.6 -1.4l-13.2 10.2l-1.7 -3.9l3.7 -7.1l8 -2.9l3.2 3.8ZM918.9 7.8l-0.6 -2.7l6 -3.4l7 -0.5l3.7 -5.3l1.7 3l-3.3 6.4l-1.7 10l-3.7 1.5l-2.3 -3.9l-6.6 3.5l1.2 -8.5l-1.4 0ZM204 308.6l8.7 3.3l-0.7 2.3l-8.9 -2.2l0.9 -3.4ZM213.9 310.4l4.4 6.4l-3.9 5.5l-1 -1.7l2 -4.4l-1.6 -5.8ZM204.1 324.6l2.2 1.3l-2.4 13.3l-2.1 -0.4l-1.7 -9.5l4 -4.7ZM744.4 -12l2.3 14.4l-6 -3l-2.1 14.6l-4.5 5.4l-8.4 -0.6l-19.4 -26.5l0.2 -4.4ZM536.5 -12l-4.8 11.7l-8.3 7.8l-14.2 5.9l-3.5 6.3l-2.1 13.6l-7.3 7.9l1.8 7.7l-4.7 17.5l-6.8 0.4l-6.7 -8.2l-9.4 -0.6l-4.1 -5.7l-2.3 -9.8l-6.5 -13l-1 -15.7l-4.6 -10l2.4 -7.3l-2.2 -4l2.2 -4.6ZM-8.4 89.4l13.6 12.5l-1.8 0.7l12.6 28.5l15.7 14.9l2.6 -2.7l9.9 9l2 15.1l-2.9 10.4l4.7 11.1l8.5 -2.4l5.2 3.9l2.1 6.3l-1.1 20.5l-3.2 11.1l7.1 11.3l2.8 1.7l-12.5 9.3l-11.3 13l-5.2 17.4l-0.5 20.8l6.5 7.6l0.9 5.5l26.9 9l7 -0.3l12.3 -11.7l15.6 3.8l11.6 6.1l0.9 2.8l-2.5 3.8l-11.6 6.6l0.6 2.3l-8.9 8.3l-0.8 -3.3l-3.3 -1.6l-5.8 3.4l-17.3 -9.6l-2.9 4.6l-3.6 -2.2l3.7 11.9l-1.9 2.7l-10.3 -6.3l-8.1 4.3l0.2 2.3l-3.9 3.7l-5.6 -20.1l-5 -6.4l-17.5 -5.6l-23.2 -35.7l-3.4 -11.9l-2.6 -2.6l0 -41.4l3.3 -9.5l1.5 -17.5l-0.5 -18.2l-2.7 -7.7l0.4 -2.7l4.9 -3.3l-1.9 -11.1l3 -6l-2.6 -3.6l0.6 -12.6l6.8 -17l2.6 -2.3l-4.5 -13.1l-3.5 1.6l-7.3 11.5l0 -24l3.6 -7ZM79.7 409.1l-5.1 -17.1l1.7 -0.8l0.7 2.1l3.8 0.9l3.5 -0.8l2.2 -4.4l3.8 1.9l3.1 -1.3l1.5 3.1l11.9 -4.4l3.2 3.6l12.7 2.3l-11.8 14.9ZM122.7 394.2l-12.7 -2.3l-3.2 -3.6l-11.9 4.4l-1.5 -3.1l-3.1 1.3l-3.8 -1.9l-2.2 4.4l-6.3 -0.3l0.1 -3.5l-2.1 -2.2l1.9 -4.7l-5.6 -2.7l-4.1 -9.1l4.8 -4.5l14.2 -0.8l7.7 5.5l8.6 1.9l8.4 4.6l4.4 4.1l6.6 12.6ZM68.1 370.8l4.1 9.1l4.3 1.1l2 3.2l-4.6 4.6l-7.3 -5.5l-8 -10.2l9.6 -2.2ZM45.2 355.5l3.9 -3.7l-0.2 -2.3l8.1 -4.3l10.3 6.3l1.9 -2.7l-3.7 -11.9l3.6 2.2l2.9 -4.6l14.6 8.9l-10.2 15.7l7.4 6.1l-10.9 1.2l-4.8 4.5l-9.6 2.2l-8.3 -7.3l-4.9 -10.2ZM86.6 343.3l1.8 -1.1l0.9 1.8l5.8 -3.4l2.4 2.9l-10.8 14.1l-7.8 2.7l-2.4 -1.4l10.2 -15.7ZM771.7 90.1l3.6 0.6l8.2 -3.1l3.5 12.8l-0.6 2.2l-2.8 0.8l1.4 1.9l-1.2 6.7l2 3.6l1.8 -2.8l3.9 2.3l4.5 4.2l-0.4 3.5l5.1 5.1l3.6 -0.9l1.4 3.7l-2.4 7.4l-12.4 4.5l-6.9 7.3l2 5.1l-6.2 4.7l-8.5 -0.1l-1.2 2.8l-12.7 1.8l-3.9 -2l0.6 -6.3l-6.9 -16.7l-16 -7.9l-9.9 0.7l-3.3 -5.8l6.2 -5l10.1 -2.2l-6.2 -8.4l6.7 1l8.9 -12.6l-2 -7.4l3.5 -4l2.3 2.4l2.4 -1.2l9.8 3.6l2.3 -2.1l9.5 -0.1ZM818.1 134.1l1.7 -5.2l5.2 5.8l2 7l-3.6 0.1l-4.6 -4.3l-0.7 -3.5ZM184.1 385.1l5.3 3.2l4 7l-9.2 -1.9l-4.1 -3.4l-3.4 -5.3l1.9 -1.6l5.6 2ZM164.7 327.2l12.5 6.8l6 6.3l1.7 4.6l7.9 2.3l9.9 17.6l6.9 4.7l-1.6 2.2l5.9 2.8l4.9 6l-1.8 1.7l-6 -1l-23.5 -8.9l7.6 -2.6l-7.4 -6.5l-1.5 -9.5l-4.7 -1.7l-8 -8.6l-9.7 -6.2l-1.9 -3l4 -0.7l-7.4 -4.2l-7.8 1.6l-3.3 -1.5l-2.2 1.5l-7.2 -3.6l13.1 -2.7l13.4 2.5ZM833.4 409.1l1.5 -0.6l-0.8 -7.1l-2 -0.5l-40.3 -72l11.8 -5.3l70.5 11.1l4 2.9l10.6 -0.9l3.1 5.3l8.3 -5.8l11.1 19.3l-1.2 8.2l2.3 5.6l-17.5 12.4l-1.5 4.7l-10.6 6l-3 -0.6l-4 3.6l-6.2 7.6l-2.1 6.2ZM717.9 394.5l1 -3.6l32.9 -10.3l-5.9 -12.4l0.5 -5.2l7.3 -3.4l-8.2 -22.4l25.8 -9.1l-5.1 -13l37.5 8.6l-11.8 5.3l40.3 72l2 0.5l0.8 7.1l-105.5 0.6l-2.5 -8.3l-9.1 -6.3ZM959 255.4l10.5 10.4l11 2.6l9.9 22.1l7.2 10.4l-4.1 14.5l4.3 12.9l5.4 0.6l3.8 5.2l5.1 -3.5l0 10.2l-11.3 -4.8l-2.1 1l-3 8.9l-12.5 4.4l-6.4 5.6l-2.4 6.7l-4 2.9l-12.7 2l-2.6 4.5l-4.3 2.5l-5.1 -1.3l-10.2 1.8l-8.4 6.2l0.1 13.7l3.8 8.1l-9.4 -1.4l-3.1 1.7l-1.5 4.2l-3.1 -6.1l-11 3.3l-2.5 -4.1l-7.8 -3.2l-4.7 -8l5.2 -3.2l1.5 -4.7l17.5 -12.4l-2.3 -5.6l1.2 -8.2l-11.1 -19.3l8.8 -10.1l26.9 -60.9l13.4 -4.6l7 1.3l2.9 -6.5ZM935.8 409.1l-3.4 -2.8l-5.1 -11.3l-0.1 -13.7l8.4 -6.2l10.2 -1.8l5.1 1.3l4.3 -2.5l2.6 -4.5l12.7 -2l4 -2.9l2.4 -6.7l6.4 -5.6l12.5 -4.4l3 -8.9l2.1 -1l11.3 4.8l0 68.3ZM867.3 409.1l2.1 -6.2l6.2 -7.6l4 -3.6l3 0.6l5.4 -2.8l4.7 8l7.8 3.2l2.5 4.1l11 -3.3l2.9 7.6ZM883.2 224.5l-11.7 -11.9l-15.3 -3.6l-4.2 -5.4l1.2 -6.7l-9.4 -18.5l4.6 -7.3l4.8 -1.9l2.4 3.9l3.2 -6.2l1.4 1.1l-0.5 5.7l2.3 3.5l3.4 0.4l3.6 7l-1.5 6.5l3.9 3.3l3.3 -2l4 2.5l3.2 -0.5l3.6 6l-4.4 13.9l4.3 6.3l-2 3.9ZM766.1 315l-4.8 -12.4l9.4 -11.1l11.7 -9.2l0.9 -5.4l6.9 -7.1l-2.5 -6.3l3.7 -2.6l1.7 -4.5l8.4 -5.8l-0.3 -3.8l-2.7 -0.8l-14.4 -16.2l4.2 -7.5l6.4 -5l7.3 -11.1l20 -13.8l3.8 -0.7l4 -6.5l14 -6.9l9.4 18.5l-1.2 6.7l4.2 5.4l15.3 3.6l18.3 17.2l14.2 22.7l-0.6 5l7.8 2.9l7.8 5.8l2.3 -3.6l8 -0.2l6.4 2.7l-26.9 60.9l-8.8 10.1l-8.3 5.8l-3.1 -5.3l-10.6 0.9l-4 -2.9l-70.5 -11.1l-37.5 -8.6ZM1012 58.9l-4.1 1.7l-5.8 -3.9l-2.3 -9.3l-3.7 -3.5l2.8 -0.7l3 -7.8l7.3 -6.7l2.6 -9.1ZM746.6 2.4l-2.3 -14.4l27.1 0l10.4 21.1l-5.6 3.1l2 7.7l-4.7 4l-26.9 -21.5ZM871 -12l-5.3 5l-2.6 -0.4l-0.3 2.7l-16.5 10l-5.4 9.2l-7 -4.9l1.2 -3.7l-8.9 -7.2l3.9 -3.5l1.6 -7.2ZM927 -12l-3.1 4.5l-0.9 6.3l3.9 2.9l-8.7 3.4l0.6 2.7l-9.5 5.7l-2.8 -2l-3.1 5l3.5 13.2l-3.1 1l-1 3.2l-3.2 0.9l-3.4 -8.8l5.1 -5.1l-11.3 -2.5l-1.9 -2.5l-3.7 0.3l-7.1 2.7l-7 16l-3.6 0.3l-6.3 4.4l-0.7 3.2l-6.1 -1.2l-1.9 -6.4l1.3 -0.5l-3.9 -2l-1.1 -9.2l1.4 -2.7l-8.8 -6.3l5.4 -9.2l16.5 -10l0.3 -2.7l2.6 0.4l5.3 -5ZM826.2 -1.3l8.9 7.2l-1.2 3.7l14.5 8.9l1 14.3l3.9 2l-7.9 1.6l-6.5 8.6l-4.4 -0.6l-1.1 2.5l-5.6 -2l-3.7 2.3l-2.2 -1.9l-3.8 1.7l0.8 2.4l-3.7 0.4l-1.2 -2.2l-3.9 2l-4 -0.7l-14.6 -10.7l-0.2 -2.9l-3.8 -3l1.4 -4.4l7.5 -15.2l5.2 -2.1l1.7 1.5l17.3 -13.4l5.6 0.1ZM831.8 63.4l1.9 3.2l-2.7 2.1l2.1 0.8l1.9 7.8l-5.5 7l-13.2 5.8l-2.9 -1.8l-4.1 4.8l0.4 1.8l-9.8 2.7l-1.5 -3.6l1.3 -1.4l4 0.4l-0.6 -2.5l7.3 -6.5l5.2 -1l-4.6 -5.9l0.4 -6.8l5.3 -0.3l1.8 -6.8l5.4 -0.6l1.9 -2.1l3.2 -0.3l2.7 3.3ZM853.8 41.6l6.1 1.2l-1.5 3.9l3.1 13.6l-6 6.8l-3.2 7.4l-5.1 1.9l-12 -0.9l-2 -5.9l-2.1 -0.8l2.7 -2.1l-1.9 -3.2l6.2 -0.7l8.7 -17.4l6.7 -2.1l0.4 -1.5ZM875.2 24.3l2.3 -5.4l7.1 -2.7l14.7 3.6l2.1 1l-0.7 1.7l-4.5 3.5l3.4 8.8l-9 -7.9l-15.6 -2.6ZM899.7 34.8l7.3 -5l1.8 1.5l-0.7 3.6l-2 0.8l6.5 8.9l-9 3.1l-4.7 10.7l-13.4 10.7l-5.8 -1.9l0.1 -2.1l-1.9 0.2l-0.2 2.9l-4.5 0.5l-2.8 -2.5l-4.3 0.9l-7.3 -2.2l2.7 -4.6l-3.1 -13.6l2.2 -7.1l6.3 -4.4l3.6 -0.3l4.7 -10.5l15.6 2.6l9 7.9ZM787.5 32.2l3.8 3l0.2 2.9l14.6 10.7l-3.3 2.4l-5.2 13.3l5.1 4.4l8.8 1.2l-0.4 6.8l4.6 5.9l-5.2 1l-7.3 6.5l0.6 2.5l-12.2 2.3l0 2.3l-4.4 2.7l-3.5 -12.8l-8.2 3.1l-3.6 -0.6l-3.9 -4.8l-8.4 -13.4l2.9 -1.8l-0.6 -3.7l-5.9 -12.3l3.6 -2.9l2 1.2l0.7 -5.9l-6 -6.6l4.1 -1.2l2.1 -3.1l2.1 2.9l5.7 -1.2l1.8 2.8l4.6 -8.4l10.9 0.3ZM881.7 67.5l3.9 1.5l13.4 -10.7l4.7 -10.7l9 -3.1l3.1 11.3l5.2 2.1l-4.9 3.2l-2.9 6.8l3.1 3.3l-3.9 4.9l-5.6 1l-2.3 5.5l-3.9 3.2l-4.3 -4.1l-4.4 0.1l-2.4 -8.6l-5 -0.8l-2.8 -4.7ZM954.9 109.3l1.2 2.6l-7.2 7.9l-1 -1.1l-7.8 4.8l-1.6 -3.7l5 -0.5l8.2 -7.6l1 1.3l2.1 -3.6ZM900.5 85.7l3.9 -3.2l2.3 -5.5l5.6 -1l3.9 -4.9l-3.1 -3.3l4 -0.6l2 7.3l-6.3 4.5l-4.5 7.3l6.9 0.5l-4.4 6l-5.8 -1l0.4 2.3l10.1 3.8l-0.6 3.2l10 0l3.5 3.7l-6.5 2.7l4.6 2l-2.7 3.7l7.4 4.1l-3.5 3.3l-7 1l-11.6 -7.4l-12.8 -4.6l-2.6 -12.2l6.9 -12ZM1012 19.6l-2.6 9.1l-7.3 6.7l-3 7.8l-2.8 0.7l3.7 3.5l0.6 5.5l-4.9 -0.5l-0.9 -4.3l-2.2 3.9l-5.5 3.3l0.7 7.2l-6.5 9l-7.5 1.1l-5.5 5.5l1.6 3.8l-2.7 4.4l-8.3 1.7l-5.4 5.7l-9.3 -3.4l-7.2 0.1l-2.4 -7.4l-6.2 0l-0.6 -11.5l7.2 -7.7l-2.9 -6.8l9.7 -8.6l1.2 -9.9l3.3 -7.5l7.1 -8.5l21.1 -10.4l7.9 -11.3l1 -9.2l2.2 -3.5l23.4 0l3.4 1.5ZM913.1 67.9l2.9 -6.8l4.9 -3.2l3 1.9l6.2 -2.2l0.7 2.4l-5.3 6.1l-0.8 11.5l-5.7 -2.9l-2 -7.3l-4 0.6ZM893.6 97.7l2.6 12.2l-7.5 -1l-7.7 -10.7l-3.9 -2.3l-0.6 -5.2l6.7 -0.1l7 7.4l3.6 -0.2ZM838.9 76.5l8.3 -0.2l5.1 -1.9l1 -2.5l6.6 2.4l0.3 4.2l-12.1 5.4l-2.2 4.3l-3.1 -0.2l1.2 3.8l19.8 5l6.7 -1l0.4 1.6l-18.3 2.7l-8.4 -2l0.6 -1.3l-6.5 -3.6l-4.1 1.3l0.7 4.3l-3.3 -1.3l-1.6 -2.9l3.7 -2.4l0 -1.9l4.7 -1.5l-2.1 -7.3l2.5 -4.9ZM798.5 94.1l1.5 3.6l6 -1.7l1.7 3.4l-1.4 2.8l-4.5 1.6l0.9 3.8l-4 1.2l-3.7 6.4l-7.2 -2.5l-1.8 2.8l-2 -3.6l1.2 -6.7l-1.4 -1.9l7.9 -5.7l-0 -2.3l7 -1.2ZM767.9 85.4l3.9 4.8l-1.4 1l-1.5 0l-2.1 -4.7l1.1 -1.1ZM765.2 79.7l3.6 11.4l-6.6 -1l-2.3 2.1l-9.8 -3.6l-2.4 1.2l-2.3 -2.4l10.8 -9.6l9 1.8ZM756 56.5l5.8 10l0.6 3.7l-2.9 1.8l5.8 7.7l-9 -1.8l-3.6 4.3l-4 1.4l1.3 -3.6l-2.5 -14.2l4.5 -7.2l4 -2.2ZM715.8 193.8l3.5 -5.2l3.2 3.5l8 -4.2l3.5 3.4l-1.9 3.5l3.5 12.2l-2.5 1.8l4.6 3.9l0.5 6.2l3.3 1.5l-1.1 6.8l1.7 2.5l-1.8 3.3l-7.1 2.5l-4.2 -11.9l-3.2 0.4l-2.8 -2.6l-1.7 -18.9l-5.3 -8.7ZM742 229.7l-1.7 -2.5l1.1 -6.8l-3.3 -1.5l-0.5 -6.2l-4.6 -3.9l2.5 -1.8l-3.5 -12.2l1.9 -3.5l-3.5 -3.4l-8 4.2l-3.2 -3.5l-3.5 5.2l-2 -6.1l-3.9 -2.7l6.2 -9.4l23 -6.5l14.4 -7l3.9 2l12.7 -1.8l1.2 -2.8l8.5 0.1l6.2 -4.7l2.9 4.4l-2.7 8.3l-6.8 5.8l0.4 17.1l4.8 3.3l-1.8 5.4l1.3 5.9l-4 4l-1.5 8.5l-14.6 6.8l-4 9l-3.6 0.7l-7.6 -5.7l-6.7 1.3ZM690.5 86.3l3.4 5.7l-0.7 9.2l-7.3 8.8l-8 1.6l0.8 -10.6l-6.1 -7.7l6.4 -15l3.8 9.2l7.6 -1.2ZM806 96l3.8 -1l-0.4 -1.8l4.1 -4.8l2.9 1.8l8.6 -3.3l5.6 6.2l-4.8 1.9l-2.3 5.6l3.7 6l4.4 2.5l7.6 0.1l7.1 4.1l10.3 1.4l4.1 -3.2l2.5 0.6l-0.4 2.6l12.4 -2.1l9.1 0.9l1 3.3l-5.6 -0.9l-5.6 2.5l1.3 6.4l6 -0.5l2.3 4.2l-2 2.2l1.7 8.4l-1.9 2.3l-3.4 -9.4l-9.8 -4.8l-15.9 -1l-4.4 2.4l-15 -1.6l-6.6 -1.8l-6.7 -6.3l-9.3 1.3l-4.7 10.2l-1.4 -3.7l-3.6 0.9l-5.1 -5.1l0.4 -3.5l-4.5 -4.2l3.3 0.2l3.7 -6.4l4 -1.2l-0.9 -3.8l4.5 -1.6l1.4 -2.8l-1.7 -3.4ZM874.9 143.8l3.8 -3.9l6.3 13.4l-20.8 4l-1.9 -4.3l12.5 -9.2ZM826.3 147.3l1.3 -4.2l6.9 3.1l5.7 10.5l-3 1.3l-0.8 4.1l-3.5 -0.6l-10.2 -12.5l3.4 -1.6ZM762.3 35.9l-2.1 3.1l-4.1 1.2l-4.6 -3.2l-5.3 -8l-0.9 -5.8l3.5 -2.9l2 -7.7l3 7.5l2 1.8l3.1 -0.4l-0.4 11.4l3.7 3ZM767.1 19.9l4.1 2.9l1.7 8l-7.6 -1.2l-2.8 -2.8l4.6 -6.9ZM690.5 86.3l-7.6 1.2l-3.8 -9.2l4 -2.1l7.6 3l-0.1 7ZM707.9 83.3l-1.6 -5.2l-5.8 -3.7l-6.6 1.2l-2.2 -1.8l0.1 -4.6l-2.6 -1.7l-0.8 5.2l-3.9 -8.2l-4.3 -3.4l-2.2 -9.7l0.5 -8.6l9 -4.2l-0.6 11.6l9.2 -5.7l2.2 7.5l-0.6 9.6l5.2 -1.8l9.9 8.5l4 -0.3l10.9 10.4l6.8 -1.6l2.2 5.5l-1.3 3.7l4.2 3.1l-2.4 6.7l-14.7 10.1l-3.2 -0.5l-1.7 5.5l-5.3 1.3l-2.3 4.9l-3.6 -0.4l3.9 -12.2l3.8 -3.9l-8.8 2.3l-2.9 -2.7l4.2 -5l-4.8 -3.3l-1.5 -6l7.8 -2.7ZM611.1 -12l0.8 4.7l6.7 5.1l-2.9 9l-13.3 12.9l-6 0.1l-12.7 -0.2l3.2 -5.3l-10.2 -2.8l7 -3.5l-0.8 -2.9l-9.1 -0.5l1.4 -7.1l5.8 -2.8l7.9 5.2l4.7 -6.9l5.8 1.4l4.5 -6.5ZM825.1 86.8l4.6 -2.5l5.5 -8.9l3.7 1.1l-2.5 4.9l2.1 7.3l-4.7 1.5l-0 1.9l-3.7 2.4l0.7 -1.5l-5.6 -6.2ZM852 35.2l1.5 7.9l-6.7 2.1l-8.7 17.4l-6.2 0.7l-3.3 -5.4l3.2 -3.5l-0.3 -6.7l3.1 -3.4l4.4 0.6l6.5 -8.6l6.6 -1.1ZM806.1 48.9l4 0.7l3.9 -2l1.2 2.2l3.7 -0.4l-0.8 -2.4l3.8 -1.7l2.2 1.9l3.7 -2.3l4.9 1.8l-3.7 13.5l-10.6 3l-1.8 6.8l-14.1 -1l-5.1 -4.4l5.2 -13.3l3.3 -2.4ZM988.8 76l-0.6 -2.7l3.6 -3.9l2.3 -6.8l-0.3 6.3l1.6 0.7l-6.6 6.4ZM988.8 76l7.3 -6.1l-2.3 8.1l-3.3 1.9l-3.9 -1.1l2.1 -2.8ZM784.2 229.9l14.4 16.2l2.7 0.8l0.3 3.8l-8.4 5.8l-1.7 4.5l-3.7 2.6l2.5 6.3l-6.9 7.1l-0.9 5.4l-11.7 9.2l-9.4 11.1l4.9 15.1l-4.6 2.1l-1.7 2.9l-12.9 4.5l-0.1 7.7l-2.2 1.5l0.1 12.4l-8 13.3l1.3 13.2l-2.1 8.7l-18.9 6.5l-0.8 -4.3l3.8 -8.9l-1.4 -2.9l0.9 -7.2l5.1 -9.3l0.3 -17l4.2 -4.9l2 -10.6l2.8 -4.8l6.8 -3.4l10.3 -21.2l-5.9 -9.9l-0.8 -13.2l2.3 -7.5l9.2 -12.2l0.9 -16.6l5 -2.1l5.6 1.7l16.8 -6.2ZM1012 183.8l-26.3 -27.9l-6.8 -3.7l-2.4 -5.5l-3.5 -2l-0.9 -5.1l7.3 -7.2l17.9 -8.7l2.4 -10.4l4.1 -5.5l4.6 -3.3l3.6 1.1ZM1012 235.7l-49.1 10.3l-6.7 15.8l-7 -1.3l-13.4 4.6l-6.4 -2.7l-8 0.2l-2.3 3.6l-7.8 -5.8l-7.8 -2.9l0.6 -5l-11.4 -19.4l-9.3 -8.6l2 -3.9l-4.3 -6.3l4.4 -13.9l-3.6 -6l27.9 -10.3l7.8 4.3l27 -8.5l1.6 -9.9l-5.9 -4.2l0.5 -11.8l3.2 -4.4l9 -5.4l4.7 1.3l11.3 -6.8l3.4 0.9l0.9 5.1l3.5 2l2.4 5.5l6.8 3.7l26.3 27.9ZM870.5 95.8l-6.7 1l-11.9 -2.3l-7.9 -2.8l-1.2 -3.8l3.1 0.2l2.2 -4.3l13.8 -6.9l1.3 4.1l4.6 0.7l2 3.9l-1.7 5.7l2.4 4.5ZM891.8 81.6l4.4 -0.1l4.3 4.1l-6.9 12l-3.6 0.2l-3.2 -2.3l-1.6 -5l6.5 -8.9ZM853.3 71.9l2.2 -4.9l3.3 -2.2l7.3 2.2l4.3 -0.9l2.8 2.5l4.5 -0.5l0.2 -2.9l1.9 -0.2l2 5.1l7.6 2.8l2.4 8.6l-3.6 4l-1.6 -3.8l-8.3 0.1l-0.1 5.5l-9.3 -0.5l-1.1 -5.2l-4.6 -0.7l-1.3 -4.1l-1.8 1.5l-0.3 -4.2l-6.6 -2.4ZM878.6 89.8l-0.9 1.8l-1.4 -1l0.6 5.2l2.2 1.9l-8.2 -0.3l-2.8 -6.1l0.7 -4.4l9.3 -0.4l0.4 3.3ZM885.5 92.6l-6.9 -2.8l-0.2 -7.9l8.3 -0.1l1.6 3.8l-2.7 7Z";
const MIGRATION_BORDERS_D = "M284.3 198.9l-2.3 -7.1l-26.9 -11.4l0.9 -2M222.1 132.3l0.9 -8.9l-9.4 -11.5M194.6 132.8l1.7 -3.5l-4.2 -11.6l4 -7.4l5.3 -0.8l2.7 -4.3l1.6 0.5M245.3 189.3l5 -10.7M223.4 168.1l8.1 4M302.1 205.8l2.4 -5.8M293.9 195.8l-4.4 8.6M172.1 192.8l-3.3 3.1M140.9 172.6l2.3 -3.4M248.4 199.8l-6.6 -3l3.5 -7.5M223.7 201.2l3 -0.2l2.7 -3.1l1.1 1.5l1.5 -2l7.2 -1.1l6 -7M173.7 209.4l-13.2 -8M193.2 142.4l16.2 9.6M178.5 156l-2.6 6.4l1.4 4.5l-1.1 3.1l2.3 2.9l-3.6 3.1l2.4 7.2l-1.9 5.5l1.2 2M145.2 213.4l-2 6.3l-10.3 7.1l12 7.7l-2.2 2.2l-0.7 5M36.9 79.2l25.4 25.3M198.6 223.1l5 -2.5l14.4 1l4.3 -2.7M206.8 227.4l11.1 3.5l3.6 2.4l-0.1 2.8l7.4 3.5l4.2 11.2M287.9 204.1l-3.6 -5.2M284.3 198.9l-5.3 3.8l1 5.7l-5.4 1.7M154.3 144.1l0.3 -6.2M166.1 113.9l9.3 -14.3l-0.2 -2.7l3.6 -1.8M160.8 121.4l-2.6 -5.8l-6.1 -6.2l-28.2 -22.3M168.8 195.9l-8.3 5.5M140.9 172.6l27.2 18.2l-3.3 2.6l4.1 2.5M127.1 195l13.7 -22.4M145.2 213.4l3 -5.5l12.3 -6.4M145.2 213.4l-18.6 -11.9M173.7 209.4l16.4 9.2M173.7 209.4l-22.5 35.3M307.3 205.9l-0.1 -5.1l-2.7 -0.8M297.4 190.5l-3.5 5.3M293.9 195.8l10.5 4.2M94.9 133.2l-2.8 3.5M62.3 104.5l-35.1 37.3M83.5 62.4l-6.2 6.2l9.6 9.6M112.4 100.8l11.5 -13.8M135.6 72.9l-11.7 14.2M75 0.3l8.5 9.7M178.7 95.1l12.3 -24.5M141.2 66.8l37.6 28.3M198.6 223.1l-8.5 -4.5M206.8 227.4l-2.9 1.3l5.7 19.8l-0.9 8.6l1.5 1.6M198.6 223.1l8.2 4.2M177.2 252.9l2.5 -6.6l3.6 -3.2l6.7 -24.4M260.6 214.3l-0 -1.4M271.9 209.8l-23.5 -10M258.1 208l-2 -4.3l-9.6 0.3l1.9 -4.1M62.3 104.5l24.7 -26.2M94.9 133.2l5.4 4.4M117.2 116.5l5.7 -7l-10.5 -8.6M94.9 133.2l-32.6 -28.8M112.4 100.8l-25.4 -22.6M211.8 161l11.6 7.1M212.5 188.6l10.8 -20.4M207.5 159.2l-13.1 23.3l-7.4 5.3M194.6 132.8l-2.6 6.3l1.2 3.4M194.6 132.8l-28.5 -18.8M154.6 138l23.2 15l0.7 3.1M193.2 142.4l0.9 4.8l-1.6 1.9l-2.8 1.4l-3.8 -1.2l-1.5 3.4l-5.9 3.3M154.6 138l6.2 -16.6M160.8 121.4l5.3 -7.4M266.5 225l2.3 0.1M260.6 214.3l-0 -1.4M209.5 212.4l12.9 6.5M258.1 208l-1.4 1.2l-2.3 -3.6l-9 5.3l-2.3 -2.1l-9.5 6.9l-8.8 -1.7l-0.7 -3.7M222.3 218.9l38.4 17.2M260.6 212.9l-2.5 -4.9M260.6 214.3l-3.3 2.5l1.8 2.2M297.4 190.5l6.7 -19.3M302.5 192.5l-5.1 -2M127.1 195l-2.9 -5.3l-12.6 -7l-10.1 -12.6l-3 -6l10.6 -13.9l-17 -13.5M126.6 201.5l-5 8.3l-1 8.7l-9.3 9.1M127.1 195l2.7 2.4l-3.2 4M92.1 136.7l-25.8 31.4l-21.2 -18.2l-0.8 2.3M141.2 66.8l-5.6 6.1M99.2 46.2l3.5 -3.4l32.9 30.1M141.2 66.8l17.5 -21.4M177.2 252.9l-18.2 -9.3l0 3.3l-2.4 2.2M200.7 267.3l-3.5 -2.3l-2.7 3.1l0.2 -1.7l-17.6 -10.9l0.1 -2.7M212.5 188.6l5.1 7.7l5.3 2.2l0.7 2.7M209.5 212.4l-37.4 -19.6M176.6 190.8l-1.3 2l-3.3 0.1M223.7 201.2l-1.3 5.5l1.8 3.6M187 187.8l-5.4 4l-3.7 -2.8l-1.3 1.8M212.5 188.6l-1.5 2.5l-3.7 -1.4l-7.3 3.9l-0.8 -2.5l-3.1 1.5l-9.1 -4.7M209.5 212.4l14.7 -2.1M154.3 144.1l1.4 2.4l-2.3 2l0.6 4.8l-10.9 15.9M143.2 169.2l-43 -31.6M154.3 144.1l-37.2 -27.6M100.2 137.6l16.9 -21.1M274.6 210.2l-2.7 -0.4M274.6 210.2l-1.8 2.2M271.9 209.8l-3.8 10.8l4.4 1.7M36.9 79.2l32.6 -31M36.9 79.2l-7 5.6l-3.1 -3.2l-5.7 6.3M43 18.4l13 15M5.2 101.9l2.6 0.1l1.7 -4.3l8.9 -2.4l2.7 -7.4M43 18.4l-20.8 17.2l-1.2 52.4M83.5 10.1l1.9 -2.4M83.5 62.4l-14 -14.2M83.5 62.4l15.7 -16.2M83.5 10.1l-1 4.7l-10.8 3.3l-1.3 3.4l-14.5 11.9M99.2 46.2l-0 -2.9l-1.9 0.6l-7.1 -5l4.1 -13.2l-3.5 -1.9l8 -5.5l-1.3 -3.5l3.1 -12.2M69.5 48.2l-13.5 -14.8M314.9 193.3l-1.3 -3.1l5 -16.6M302.5 192.5l10.7 2.4M302.5 192.5l2.9 -6.5l4.6 -5.8l3 -0.5l2.1 -4.4";
const MIGRATION_LAKES_D = "M209.8 28.2l6.6 0.2l-3.6 7.9l-5.1 19.3l-3 5.8l-3.6 0.2l3.2 -9.5l0.3 -19.4l5.2 -4.4ZM263.9 172l-4.1 -2.2l5.3 -2.2l10.2 1.7l2 2.7l4.8 -1.5l1.2 2.7l-1 3.4l-5.7 0.9l-9.3 -5.1l-3.6 -0.3ZM235.1 170.1l3 2.1l9.4 -1.4l4.9 2.8l11.3 1.1l-7.7 3.4l-14 0.4l-7.7 -2.9l-2.9 -3.5l3.6 -2.1ZM224.5 103.3l11.6 -3l7.5 6.5l-0 7.2l5.4 4.4l-2.2 1.8l0.9 3.5l-2.5 2.6l1.8 2.2l-2.6 2.1l-1.5 -1.2l0 -2.9l-11.6 -3.1l-4.6 -7.9l4.1 -3.2l-17.3 -0.6l-1.6 -4.6l-6.3 -1.7l11.9 -2.9l6.9 0.6ZM191 302.7l-1.6 -1.1l1.1 -2l1.5 1.1l-1.1 2ZM203.4 32.7l-3.6 -4.6l0.6 -2.4l5.6 -3.9l1 0.9l-2.4 1.5l1.3 1.1l-3.5 3l1.9 3.5l-0.8 1ZM73.9 61.3l-3.1 3.2l-0.6 -4.2l2.3 -4.1l1.4 5.1ZM264.7 149.2l0.9 8l-3.1 1.9l-4.2 -3.3l-0.5 -6.4l-1.7 5.5l-4.9 3.2l-3.1 6l-5.1 0.8l2.6 -8.7l-1.7 -1.9l-6.5 1.1l0.7 -2.2l4.8 -1.6l3.7 -7.3l-6.5 -9.3l7 1.4l-1.1 -4.6l1.7 -0.6l0.2 2.3l16.4 12.4l0.7 3.4ZM237.5 131.2l3.9 3.2l-8.7 6.7l0.9 -2.9l-3.3 0.7l-6.4 5l-5.9 14.3l-6.3 3l-4.1 -1.1l0.5 -5.8l3.8 -8.1l14.2 -13l-7.8 2.3l-0.2 -1.4l9.9 -4.8l9.3 2.1Z";
const KANSAS_BORDERS_D = "M163.9 364.9l-0.1 -145.9l-138.7 -0M164.6 583.9l-0.6 -219M905.9 364.8l-742 0.1M986.2 498.5l0.2 95.1M986.4 492.9l-0.2 5.6M859.4 277.2l139.9 -1M905.9 364.8l25.6 18.9l6.7 0.2l7.9 -3l6 4.3l4.1 11.6l-0.6 5.9l-5.2 0.2l-6.5 7l-7.8 13.8l1.9 12.9l11.7 12.1l7.8 12.2l3.9 12.3l7.7 9.5l17.3 10.2M859.4 277.2l2.8 4.5l6.1 15.3l2.6 15.1l6.1 9.8l9.5 4.5l6.4 9.7l3.3 14.9l8 12.5l1.8 1.3M790.7 12l3.1 23l6.8 18.6l10.4 14.1l5.2 10.3l0 6.5l2.5 7l5 7.5l2 12.7l-1 18l2.1 9.6l5.2 1.2l2.3 2.5l-0.7 3.9l1.8 2.9l4.2 1.9l1.2 5.2l-1.9 8.5l1.5 5.3l4.9 2.2l0.9 4.2l-3.1 6.2l0.5 4.9l4 3.5l2.7 15.7l1.4 27.9l-0.5 16.3l-2.3 4.8l3.7 10.1l6.8 10.9";
// END GENERATED basemap-paths
// BEGIN GENERATED basemap-routes -- regenerate with: uv run tools/build_basemap.py --write
const ROUTE_META = [ {id:"route.zimmerman_surname",anchor:"zimmerman",grade:"solid",plates:["convergence","zimmerman"]}, {id:"route.nauer",anchor:"zimmerman",grade:"solid",plates:["convergence","zimmerman"]}, {id:"route.nauer_candidate",anchor:"zimmerman",grade:"conjectural",plates:["zimmerman"]}, {id:"route.mundell_rust",anchor:"mundell",grade:"solid",plates:["convergence","mundell"]}, {id:"route.rust_candidate",anchor:"mundell",grade:"conjectural",plates:["mundell"]}, {id:"route.dible_surname",anchor:"dible",grade:"solid",plates:["convergence","dible"]}, {id:"route.long_sleight",anchor:"dible",grade:"solid",plates:["convergence","dible"]}, {id:"route.mcclelland_love",anchor:"dible",grade:"conjectural",plates:["dible"]}, {id:"route.connelly_durham",anchor:"connelly",grade:"solid",plates:["convergence","connelly"]}, {id:"route.claar_stropes",anchor:"connelly",grade:"solid",plates:["convergence","connelly"]} ];
const ROUTES_MIG = {"route.zimmerman_surname":[{d:"M790.7 82.4l-78.4 -8.6l-8.3 0.1"},{d:"M330.5 88.5l-24.1 2.1l-77.3 14.7l-75.9 15.7l-18.9 14.2l-11.6 -9.1l-3.5 -1"}],"route.nauer":[{d:"M256 166.3l-121.7 -31l-8.9 -7.6l-2.8 -1.5"}],"route.nauer_candidate":[{d:"M255 166.5l-0.8 -6.7l1.8 6.5l-121.7 -31",c:1,q:[255,166.5]}],"route.mundell_rust":[{d:"M207.6 173.7l-39.4 -31.3l-34.4 -10.6l-52.3 -16"},{d:"M85.6 111.2l22.1 5.8l8.6 9.6l2.9 -1.5"}],"route.rust_candidate":[{d:"M128.7 126.2l5 5.6l-17.5 -5.3l19.6 10.4",c:1,q:[128.7,126.2]}],"route.dible_surname":[{d:"M787.3 80.1l-68 6.2l-67.2 8.3",c:1},{d:"M514.2 119.3l-67 15.9l-65.9 17.7l-129 38.2l-128.6 -71.4",c:1},{d:"M123.7 119.7l-2.4 6.1l29.2 86.8l31 87.5"}],"route.long_sleight":[{d:"M723.1 78.1l-43.6 6.5",c:1},{d:"M488.4 119.3l-41.4 8.8l-66.6 18.6l-194.7 60.4",c:1},{d:"M185.7 207.1l-6.1 -43.5l-31.1 -17l-27.2 -20.8"}],"route.mcclelland_love":[{d:"M247.5 195.7l-3.3 0.9l-13.1 -2.6l0.1 -0.4l-100.2 -56.9l-8.4 -10.6l25.9 20.5l-27.2 -20.8",c:1,q:[247.5,195.7]}],"route.connelly_durham":[{d:"M245.2 224l-8.2 3.5l-31.8 -10.8l-15.3 -20.8l-0.2 -0.2l-3.2 -31.1l1.1 28l-66.3 -66.8l29.1 88l30.9 88.8"}],"route.claar_stropes":[{d:"M255.5 200l-29.5 -3.7",c:1},{d:"M226 196.3l-101.6 -72l23.1 25.5l-26.2 -24"}]};
const ROUTES_KS = {"route.zimmerman_surname":[{d:"M741.2 0l-65.3 68.9l-57.6 183.5l-55.4 183.8l-118.5 -2.8l-118.6 -1.4l-53.9 21.2"}],"route.nauer":[{d:"M1000 267.8l-83.3 30l-119 44.7l-117.9 46.1l-116.8 47.5l-187.1 -11.9l-50 7.8"}],"route.nauer_candidate":[{d:"M1000 267.8l-83.3 30l-119 44.7l-117.9 46.1l-116.8 47.5",c:1,q:[1000,267.8]}],"route.mundell_rust":[{d:"M1000 240.6l-61.3 18.3l-139.6 44.2l-138.3 46.1l-137 48l-142.1 41.2l-141 43.2l-139.7 45.2l-101 34.4"},{d:"M0 486.8l48.1 -18.6l202.5 33.8l21.4 -48.8"}],"route.rust_candidate":[{d:"M404.5 373.3l119.4 24l-137.4 51.4l-136 53.3l173.9 -30.3l174.9 -27.3",c:1,q:[404.5,373.3]}],"route.dible_surname":[{d:"M1000 250.1l-131.6 12.1l-148.9 15.9l-148.3 18.2l-147.8 20.4l-147.1 22.6",c:1},{d:"M276.3 339.4l30 102.8l150.6 103.8l73.3 52.7"}],"route.long_sleight":[{d:"M1000 437.5l-146.2 14.7l-136.7 -5.3l-136.9 -3.5l-136.9 -1.6l-137 0.3"}],"route.mcclelland_love":[{d:"M1000 439.7l-122.5 10l-114.6 10.8l-114.4 12.1l-114.1 13.5l-104 -27.6l-104.6 -26.5l132.2 2.4l132.1 4.1l131.9 5.9l131.8 7.7l-136.7 -5.3l-136.9 -3.5l-136.9 -1.6l-137 0.3",c:1,q:[1000,439.7]}],"route.connelly_durham":[{d:"M1000 559l-138.2 -27.6l-184.1 -33.2l-185.2 -29.7l-186.2 -26.2l151.8 106l69.3 50.4"}],"route.claar_stropes":[{d:"M1000 386l-168.9 -3l-125.3 -0.2l-125.3 1.3l-125.2 2.9l-125.1 4.5l135.8 25.3l135.1 27.2l134.4 29l133.6 30.8l-140.1 -18.4l-140.5 -16.4l-141 -14.4l-141.3 -12.4"}]};
// SCALE_UPK is svg units per km at the plate reference latitude.
const SCALE_UPK = { migration: 0.080889, kansas: 1.313116 };
// END GENERATED basemap-routes

    const SVG_NS = "http://www.w3.org/2000/svg";

    const anchorSlug = {
      "Doyle Julius Zimmerman": "zimmerman",
      "Evelyn Delores Mundell Zimmerman": "mundell",
      "William J. Dible": "dible",
      "Donna Lea Connelly Dible": "connelly"
    };
    const anchorShort = {
      "Doyle Julius Zimmerman": "Zimmerman",
      "Evelyn Delores Mundell Zimmerman": "Mundell",
      "William J. Dible": "Dible",
      "Donna Lea Connelly Dible": "Connelly"
    };

    const PLATES = [
      { key: "convergence", svgId: "map-convergence", detailId: "detail-convergence", base: "kansas", anchor: null, numeralNudges: {"event.zodrow.antonette_grams_death.1934-08-01": Math.PI, "event.zodrow.john_death.1915-03-15": Math.PI / 2} },
      { key: "zimmerman", svgId: "map-line-zimmerman", detailId: "detail-zimmerman", base: "migration", anchor: "Doyle Julius Zimmerman" },
      { key: "mundell", svgId: "map-line-mundell", detailId: "detail-mundell", base: "kansas", anchor: "Evelyn Delores Mundell Zimmerman" },
      { key: "dible", svgId: "map-line-dible", detailId: "detail-dible", base: "migration", anchor: "William J. Dible" },
      { key: "connelly", svgId: "map-line-connelly", detailId: "detail-connelly", base: "migration", anchor: "Donna Lea Connelly Dible" }
    ];
    const PLATE_ROMANS = ["II", "III", "IV", "V", "VI"];

    function projectMigration(lon, lat) {
      const d = Math.PI / 180;
      const p1 = MIG_PROJ.p1 * d, p2 = MIG_PROJ.p2 * d, lon0 = MIG_PROJ.lon0 * d;
      const n = Math.log(Math.cos(p1) / Math.cos(p2)) /
        Math.log(Math.tan(Math.PI / 4 + p2 / 2) / Math.tan(Math.PI / 4 + p1 / 2));
      const f = Math.cos(p1) * Math.tan(Math.PI / 4 + p1 / 2) ** n / n;
      const rho0 = f / Math.tan(Math.PI / 4 + 40 * d / 2) ** n;
      const rho = f / Math.tan(Math.PI / 4 + lat * d / 2) ** n;
      const theta = n * (lon * d - lon0);
      const x = rho * Math.sin(theta);
      const y = rho0 - rho * Math.cos(theta);
      return [(x - MIG_PROJ.xMin) * MIG_PROJ.s, (MIG_PROJ.yMax - y) * MIG_PROJ.s];
    }

    function projectKansas(lon, lat) {
      return [(lon - KS_PROJ.lonMin) * KS_PROJ.k * KS_PROJ.s, (KS_PROJ.latMax - lat) * KS_PROJ.s];
    }

    function baseInfo(base) {
      if (base === "kansas") return { dims: KS_VIEW, project: projectKansas };
      return { dims: MIG_VIEW, project: projectMigration };
    }

    function inKansas(event) {
      const [lon, lat] = event.coords;
      return lon >= KS_PROJ.lonMin && lon <= KS_PROJ.lonMax &&
        lat >= KS_PROJ.latMin && lat <= KS_PROJ.latMax;
    }

    function typeLabel(event) {
      return event.type.replaceAll("_", " ");
    }
    function compareEvents(a, b) {
      return a.sort < b.sort ? -1 : a.sort > b.sort ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
    }

    function kindLabel(kind) {
      const labels = {
        "couple convergence": "paths converge",
        "descendant path": "line of descent",
        "parents to child": "parents to child",
        "individual to union": "into the union",
        "parent evidence": "evidence tie, no direction"
      };
      return labels[kind] || kind;
    }

    function eventMeaning(event) {
      const person = event.person;
      const meanings = {
        birth: `Birth of ${person}`,
        death: `Death of ${person}`,
        marriage: `Marriage of ${person}`,
        household: `Census household of ${person}`,
        death_or_burial: `Death or burial of ${person}`
      };
      return meanings[event.type] || `${typeLabel(event)} record for ${person}`;
    }

    function plateData(cfg) {
      if (!cfg.anchor) {
        const events = verifiedEventData.filter(inKansas);
        const own = new Set(events.map((e) => e.id));
        const links = familyLinkData;
        return { events: events.sort(compareEvents), guestIds: new Set(), links, present: own };
      }
      const own = verifiedEventData.filter((e) => e.anchor === cfg.anchor);
      const ownIds = new Set(own.map((e) => e.id));
      const links = familyLinkData.filter((link) =>
        link.anchor === cfg.anchor ||
        link.from.some((id) => ownIds.has(id)) || ownIds.has(link.to));
      const wanted = new Set(ownIds);
      links.forEach((link) => [...link.from, link.to].forEach((id) => wanted.add(id)));
      const events = verifiedEventData.filter((e) => wanted.has(e.id));
      const guestIds = new Set(events.filter((e) => !ownIds.has(e.id)).map((e) => e.id));
      return { events: events.sort(compareEvents), guestIds, links, present: wanted };
    }

    function fitViewBox(points, base, cfg) {
      const { dims } = baseInfo(base);
      if (!cfg.anchor) return { x: 0, y: 0, w: dims.w, h: dims.h };
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      points.forEach(([x, y]) => {
        minX = Math.min(minX, x); maxX = Math.max(maxX, x);
        minY = Math.min(minY, y); maxY = Math.max(maxY, y);
      });
      const pad = Math.max(maxX - minX, maxY - minY) * 0.16 + 14;
      let x0 = minX - pad, x1 = maxX + pad, y0 = minY - pad, y1 = maxY + pad;
      const minW = base === "kansas" ? 360 : 420;
      if (x1 - x0 < minW) {
        const cx = (x0 + x1) / 2;
        x0 = cx - minW / 2; x1 = cx + minW / 2;
      }
      let w = x1 - x0, h = y1 - y0;
      if (w / h > 3) {
        const cy = (y0 + y1) / 2;
        h = w / 3; y0 = cy - h / 2; y1 = cy + h / 2;
      } else if (w / h < 1.9) {
        const cx = (x0 + x1) / 2;
        w = h * 1.9; x0 = cx - w / 2; x1 = cx + w / 2;
      }
      x0 = Math.max(0, Math.min(x0, dims.w - w));
      y0 = Math.max(0, Math.min(y0, dims.h - h));
      w = Math.min(w, dims.w - x0);
      h = Math.min(h, dims.h - y0);
      return { x: x0, y: y0, w, h };
    }

    function displayPoints(events, project, offset) {
      const groups = new Map();
      events.forEach((event) => {
        const key = event.coords.join(",");
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(event);
      });
      const points = new Map();
      groups.forEach((members) => {
        members.sort(compareEvents);
        members.forEach((event, i) => {
          const [x, y] = project(event.coords[0], event.coords[1]);
          if (members.length === 1) {
            points.set(event.id, [x, y, null]);
            return;
          }
          const angle = Math.PI * 2 * i / members.length + Math.PI / 4;
          points.set(event.id, [x + Math.cos(angle) * offset, y + Math.sin(angle) * offset, angle]);
        });
      });
      return points;
    }

    function bezierFor(a, b, bowCap, trim) {
      const [ax, ay] = a;
      const [bx, by] = b;
      const dx = bx - ax, dy = by - ay;
      const len = Math.hypot(dx, dy) || 1;
      let px = -dy / len, py = dx / len;
      if (py > 0) { px = -px; py = -py; }
      const bow = Math.min(len * 0.22, bowCap);
      const cx = ax + dx / 2 + px * bow;
      const cy = ay + dy / 2 + py * bow;
      const ua = [cx - ax, cy - ay], la = Math.hypot(ua[0], ua[1]) || 1;
      const ub = [cx - bx, cy - by], lb = Math.hypot(ub[0], ub[1]) || 1;
      const a2 = [ax + ua[0] / la * trim, ay + ua[1] / la * trim];
      const b2 = [bx + ub[0] / lb * (trim * 1.4), by + ub[1] / lb * (trim * 1.4)];
      const f = (v) => Math.round(v * 10) / 10;
      return `M${f(a2[0])} ${f(a2[1])}Q${f(cx)} ${f(cy)} ${f(b2[0])} ${f(b2[1])}`;
    }

    let defsEmitted = false;
    let plateSeq = 0;
    const MIGRATION_FAN_D = computeFanPath(projectMigration);
    const MIGRATION_GRATICULE_D = computeGraticulePath(projectMigration);
    function markerDefs() {
      if (defsEmitted) return "";
      defsEmitted = true;
      return "<defs>" + Object.values(anchorSlug).map((slug) =>
        `<marker id="arrow-${slug}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">` +
        `<path d="M0 0.6L7.6 4L0 7.4z" class="arrowhead anchor-${slug}"></path></marker>`
      ).join("") + "</defs>";
    }

    function basemapMarkup(base, withLabels) {
      if (base === "kansas") {
        const labels = !withLabels ? "" : [
          ["KANSAS", -99.6, 38.78], ["NEBRASKA", -99.6, 41.95], ["COLORADO", -103.28, 40.9]
        ].map(([name, lon, lat]) => {
          const [x, y] = projectKansas(lon, lat);
          return `<text class="map-label" x="${x.toFixed(1)}" y="${y.toFixed(1)}">${name}</text>`;
        }).join("");
        return markerDefs() +
          `<rect class="map-land" x="0" y="0" width="${KS_VIEW.w}" height="${KS_VIEW.h}"></rect>` +
          `<g class="layer-borders"><path d="${KANSAS_BORDERS_D}"></path></g>` +
          `<g class="layer-labels">${labels}</g>` +
          `<g class="layer-routes"></g><g class="layer-links"></g><g class="layer-markers"></g>`;
      }
      const clipId = `fan-${plateSeq += 1}`;
      return markerDefs() +
        `<defs><clipPath id="${clipId}"><path d="${MIGRATION_FAN_D}"></path></clipPath></defs>` +
        `<g clip-path="url(#${clipId})">` +
        `<rect class="map-water" x="0" y="0" width="${MIG_VIEW.w}" height="${MIG_VIEW.h}"></rect>` +
        `<g class="layer-land"><path d="${MIGRATION_LAND_D}"></path></g>` +
        `<g class="layer-graticule"><path d="${MIGRATION_GRATICULE_D}"></path></g>` +
        `<g class="layer-lakes"><path d="${MIGRATION_LAKES_D}"></path></g>` +
        `<g class="layer-borders"><path d="${MIGRATION_BORDERS_D}"></path></g>` +
        `</g>` +
        `<path class="map-neatline" d="${MIGRATION_FAN_D}"></path>` +
        `<g class="layer-routes" clip-path="url(#${clipId})"></g><g class="layer-links"></g><g class="layer-markers"></g>`;
    }

    function routeDataFor(base) {
      return base === "kansas" ? ROUTES_KS : ROUTES_MIG;
    }

    function renderRoutes(layer, cfg, s) {
      if (!layer) return;
      const routes = routeDataFor(cfg.base);
      ROUTE_META.filter((route) => route.plates.includes(cfg.key)).forEach((route) => {
        (routes[route.id] || []).forEach((segment) => {
          if (!segment.d) return;
          const conjectural = cfg.key !== "convergence" && (segment.c || route.grade === "conjectural");
          const path = document.createElementNS(SVG_NS, "path");
          path.setAttribute("d", segment.d);
          path.setAttribute("class", `route-line anchor-${route.anchor}${conjectural ? " conjectural" : ""}`);
          path.dataset.routeId = route.id;
          if (conjectural) {
            path.setAttribute("stroke-dasharray", `${(3.2 * s).toFixed(2)} ${(3.4 * s).toFixed(2)}`);
          }
          layer.appendChild(path);
          if (conjectural && segment.q) {
            const label = document.createElementNS(SVG_NS, "text");
            label.setAttribute("class", `route-query anchor-${route.anchor}`);
            label.setAttribute("x", segment.q[0]);
            label.setAttribute("y", segment.q[1]);
            label.setAttribute("text-anchor", "middle");
            label.setAttribute("dominant-baseline", "central");
            label.textContent = "?";
            layer.appendChild(label);
          }
        });
      });
    }

    function eventDetailHtml(event, links) {
      const related = links.filter((l) => l.from.includes(event.id) || l.to === event.id);
      const linkList = related.length
        ? `<ul class="detail-links">${related.map((l) => `<li>${l.label}</li>`).join("")}</ul>`
        : "";
      return `<div class="detail-date">${event.date} · ${typeLabel(event)}</div>` +
        `<div class="detail-name">${event.person.replace(/"/g, "&quot;").replace(/</g, "&lt;")}</div>` +
        `<div class="detail-place">${event.place}</div>` +
        `<div class="detail-meta"><span class="tag ${event.confidence === "documented" ? "documented" : "strong"}">` +
        `${event.confidence === "documented" ? "Documented" : "Strong lead"}</span>` +
        `<span class="detail-anchor anchor-text-${anchorSlug[event.anchor]}">${anchorShort[event.anchor]} line</span></div>` +
        linkList;
    }

    function linkDetailHtml(link) {
      const eventLine = (id) => {
        const event = verifiedEventData.find((e) => e.id === id);
        if (!event) return "";
        return `<li>${event.date} · ${typeLabel(event)} · ${event.place}</li>`;
      };
      return `<div class="detail-date">${kindLabel(link.kind)}</div>` +
        `<div class="detail-name">${link.label}</div>` +
        `<ul class="detail-links">${link.from.map(eventLine).join("")}${eventLine(link.to)}</ul>` +
        `<div class="detail-meta"><span class="detail-anchor anchor-text-${anchorSlug[link.anchor]}">${anchorShort[link.anchor]} line</span></div>`;
    }

    function plateFurniture(svg, cfg, box, s) {
      const roman = PLATE_ROMANS[PLATES.indexOf(cfg)];
      const f = (v) => (Math.round(v * 10) / 10).toFixed(1);
      const x = box.x, y = box.y, w = box.w, h = box.h, i = 5 * s, a = 14 * s;
      const tick = `M${f(x + i)} ${f(y + i + a)}V${f(y + i)}H${f(x + i + a)}M${f(x + w - i - a)} ${f(y + i)}H${f(x + w - i)}V${f(y + i + a)}M${f(x + i)} ${f(y + h - i - a)}V${f(y + h - i)}H${f(x + i + a)}M${f(x + w - i - a)} ${f(y + h - i)}H${f(x + w - i)}V${f(y + h - i - a)}`;
      let km = 50;
      [100, 200, 500, 1000, 2000, 4000].forEach((v) => { if (v * SCALE_UPK[cfg.base] <= w * 0.22) km = v; });
      const bw = km * SCALE_UPK[cfg.base], bh = 3.5 * s, font = 10.5 * Math.max(s, 0.55);
      const label = `${km} KM · SCALE TRUE AT LAT. ${cfg.base === "kansas" ? "40°27' N" : "40° N"}`;
      const pad = 4 * s, backW = Math.max(bw, label.length * font * 0.58) + pad * 2, backH = bh + font + pad * 3;
      const bx = x + w - 12 * s - backW, by = y + h - 12 * s - backH, barX = bx + backW - pad - bw, barY = by + pad;
      const g = document.createElementNS(SVG_NS, "g");
      g.setAttribute("class", "plate-decor");
      g.innerHTML = `<path class="plate-tick" d="${tick}"></path><text class="plate-corner-no" x="${f(x + w - 9 * s)}" y="${f(y + 17 * s)}" text-anchor="end" font-size="${f(font)}">PL. ${roman}.</text><g class="plate-scalebar"><rect class="back" x="${f(bx)}" y="${f(by)}" width="${f(backW)}" height="${f(backH)}"></rect><rect class="bar-a" x="${f(barX)}" y="${f(barY)}" width="${f(bw / 2)}" height="${f(bh)}"></rect><rect class="bar-b" x="${f(barX + bw / 2)}" y="${f(barY)}" width="${f(bw / 2)}" height="${f(bh)}"></rect><path class="scale-tick" d="M${f(barX)} ${f(barY - 2 * s)}V${f(barY + bh + 2 * s)}M${f(barX + bw)} ${f(barY - 2 * s)}V${f(barY + bh + 2 * s)}"></path><text x="${f(bx + backW - pad)}" y="${f(by + backH - pad)}" text-anchor="end" font-size="${f(font)}">${label}</text></g>`;
      svg.appendChild(g);
    }

    function makePlate(cfg) {
      const svg = document.getElementById(cfg.svgId);
      const detail = document.getElementById(cfg.detailId);
      if (!svg || !detail) return;
      const figure = svg.closest("figure.plate");
      const { dims, project } = baseInfo(cfg.base);
      const data = plateData(cfg);
      const box = (() => {
        const pts = data.events.map((e) => project(e.coords[0], e.coords[1]));
        return fitViewBox(pts, cfg.base, cfg);
      })();
      const s = box.w / 1000;
      svg.setAttribute("viewBox", `${box.x.toFixed(1)} ${box.y.toFixed(1)} ${box.w.toFixed(1)} ${box.h.toFixed(1)}`);
      svg.style.setProperty("--plate-s", String(s));
      svg.style.aspectRatio = `${box.w.toFixed(1)} / ${box.h.toFixed(1)}`;
      svg.innerHTML = basemapMarkup(cfg.base, !cfg.anchor);

      const points = displayPoints(data.events, project, (cfg.base === "kansas" ? 9 : 5.5) * Math.max(s, 0.55));
      const routeLayer = svg.querySelector(".layer-routes");
      const linkLayer = svg.querySelector(".layer-links");
      const markerLayer = svg.querySelector(".layer-markers");
      const state = { pinnedId: null, hoverId: null };
      renderRoutes(routeLayer, cfg, s);

      data.links.forEach((link) => {
        link.from.forEach((fromId) => {
          if (!points.has(fromId) || !points.has(link.to)) return;
          const slug = anchorSlug[link.anchor];
          const path = document.createElementNS(SVG_NS, "path");
          path.setAttribute("d", bezierFor(points.get(fromId), points.get(link.to), 60 * s, 10 * s));
          path.setAttribute("class", `family-link anchor-${slug}`);
          path.dataset.linkId = link.id;
          if (link.kind === "parent evidence") {
            path.setAttribute("stroke-dasharray", `${(1.6 * s).toFixed(2)} ${(4.5 * s).toFixed(2)}`);
          } else {
            if (link.kind === "descendant path") {
              path.setAttribute("stroke-dasharray", `${(5 * s).toFixed(2)} ${(6 * s).toFixed(2)}`);
            }
            path.setAttribute("marker-end", `url(#arrow-${slug})`);
          }
          linkLayer.appendChild(path);
        });
      });

      const rBase = cfg.base === "kansas" ? 9 : 7;
      data.events.forEach((event) => {
        if (!points.has(event.id)) return;
        const guest = data.guestIds.has(event.id);
        const [x, y, fanAngle] = points.get(event.id);
        const g = document.createElementNS(SVG_NS, "g");
        g.setAttribute("class",
          `event-marker anchor-${anchorSlug[event.anchor]} conf-${event.confidence}${guest ? " guest" : ""}`);
        g.setAttribute("transform", `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
        g.setAttribute("tabindex", "0");
        g.setAttribute("role", "button");
        g.setAttribute("aria-label", `${event.date}, ${event.person}, ${typeLabel(event)}, ${event.place}`);
        g.dataset.eventId = event.id;
        const hit = document.createElementNS(SVG_NS, "circle");
        hit.setAttribute("class", "hit");
        hit.setAttribute("r", (15 * Math.max(s, 0.5)).toFixed(1));
        const dot = document.createElementNS(SVG_NS, "circle");
        dot.setAttribute("class", "dot");
        const r = (event.confidence === "documented" ? rBase : rBase - 1.5) * Math.max(s, 0.5) * (guest ? 0.85 : 1);
        dot.setAttribute("r", r.toFixed(1));
        g.appendChild(hit);
        g.appendChild(dot);
        const angle = cfg.numeralNudges?.[event.id] ?? fanAngle ?? 0;
        const no = document.createElementNS(SVG_NS, "text");
        const d = r + 4.5 * Math.max(s, 0.55), c = Math.cos(angle), m = Math.sin(angle);
        no.setAttribute("class", "marker-no");
        no.setAttribute("x", (c * d).toFixed(1));
        no.setAttribute("y", (m * d).toFixed(1));
        no.setAttribute("font-size", (10.5 * Math.max(s, 0.55)).toFixed(1));
        no.setAttribute("text-anchor", c > 0.35 ? "start" : c < -0.35 ? "end" : "middle");
        no.setAttribute("dominant-baseline", "central");
        no.textContent = data.events.indexOf(event) + 1;
        g.appendChild(no);
        markerLayer.appendChild(g);
      });
      plateFurniture(svg, cfg, box, s);

      const bubble = document.createElement("div");
      bubble.className = "map-bubble";
      figure.appendChild(bubble);

      function bubbleHtml(id) {
        if (id.startsWith("link.")) {
          const link = data.links.find((l) => l.id === id);
          if (!link) return "";
          return `<span class="bubble-date">${kindLabel(link.kind)}</span>` +
            `<span class="bubble-body">${link.label}</span>`;
        }
        const event = verifiedEventData.find((e) => e.id === id);
        if (!event) return "";
        return `<span class="bubble-date">${event.date} · ${typeLabel(event)}</span>` +
          `<span class="bubble-body">${eventMeaning(event).replace(/"/g, "&quot;").replace(/</g, "&lt;")}</span>` +
          `<span class="bubble-place">${event.place} · ${event.confidence === "documented" ? "documented" : "strong lead"}</span>`;
      }

      const hoverCapable = window.matchMedia("(hover: hover)").matches;

      function showBubbleAt(id, clientX, clientY) {
        if (!hoverCapable) return;
        const fig = figure.getBoundingClientRect();
        let x = clientX - fig.left;
        let y = clientY - fig.top;
        if (!id.startsWith("link.")) {
          const dot = svg.querySelector(`[data-event-id="${id}"] .dot`);
          if (dot) {
            const r = dot.getBoundingClientRect();
            x = r.left + r.width / 2 - fig.left;
            y = r.top - fig.top;
          }
        }
        bubble.innerHTML = bubbleHtml(id);
        bubble.classList.add("show");
        const half = bubble.offsetWidth / 2;
        bubble.style.left = `${Math.max(half + 6, Math.min(x, fig.width - half - 6))}px`;
        bubble.style.top = `${y}px`;
        bubble.style.transform = y < 86 ? "translate(-50%, 14px)" : "translate(-50%, calc(-100% - 12px))";
      }

      function hideBubble() {
        bubble.classList.remove("show");
      }

      function relatedIds(id) {
        const related = new Set([id]);
        if (id.startsWith("link.")) {
          const link = data.links.find((l) => l.id === id);
          if (link) [...link.from, link.to].forEach((eid) => related.add(eid));
          return related;
        }
        data.links.forEach((link) => {
          if (link.from.includes(id) || link.to === id) {
            related.add(link.id);
            [...link.from, link.to].forEach((eid) => related.add(eid));
          }
        });
        return related;
      }

      function render() {
        const focusId = state.pinnedId || state.hoverId;
        const related = focusId ? relatedIds(focusId) : null;
        svg.querySelectorAll("[data-event-id], [data-link-id]").forEach((el) => {
          const id = el.dataset.eventId || el.dataset.linkId;
          el.classList.toggle("pinned", id === state.pinnedId);
          el.classList.toggle("hovered", id === state.hoverId && id !== state.pinnedId);
          el.classList.toggle("related", !!related && related.has(id) && id !== focusId);
          el.classList.toggle("faded", !!related && !related.has(id));
        });
        if (!state.pinnedId) {
          detail.innerHTML = '<p class="detail-empty">Click a marker or arc to pin its record here. Hover for the date bubble.</p>';
          return;
        }
        if (state.pinnedId.startsWith("link.")) {
          const link = data.links.find((l) => l.id === state.pinnedId);
          detail.innerHTML = link ? linkDetailHtml(link) : "";
          return;
        }
        const event = verifiedEventData.find((e) => e.id === state.pinnedId);
        detail.innerHTML = event ? eventDetailHtml(event, data.links) : "";
      }

      function pick(e) {
        let best = null;
        let bestDistance = 16;
        svg.querySelectorAll("g.event-marker").forEach((g) => {
          const rect = g.querySelector(".dot").getBoundingClientRect();
          const distance = Math.hypot(
            e.clientX - (rect.left + rect.width / 2),
            e.clientY - (rect.top + rect.height / 2)
          );
          if (distance < bestDistance) {
            bestDistance = distance;
            best = g.dataset.eventId;
          }
        });
        if (best) return best;
        const el = e.target.closest("[data-link-id]");
        return el ? el.dataset.linkId : null;
      }

      svg.addEventListener("click", (e) => {
        const id = pick(e);
        state.pinnedId = id && id !== state.pinnedId ? id : null;
        render();
      });
      figure.querySelectorAll(".plate-key li").forEach((r)=>r.onclick=()=>{const id=r.dataset.e;state.pinnedId=id===state.pinnedId?null:id;render();});
      svg.addEventListener("mousemove", (e) => {
        const id = pick(e);
        if (id !== state.hoverId) {
          state.hoverId = id;
          render();
        }
        if (id) showBubbleAt(id, e.clientX, e.clientY);
        else hideBubble();
      });
      svg.addEventListener("mouseleave", () => {
        state.hoverId = null;
        hideBubble();
        render();
      });
      svg.addEventListener("focusin", (e) => {
        const g = e.target.closest("g.event-marker");
        if (!g) return;
        state.hoverId = g.dataset.eventId;
        render();
        const rect = g.querySelector(".dot").getBoundingClientRect();
        showBubbleAt(g.dataset.eventId, rect.left + rect.width / 2, rect.top);
      });
      svg.addEventListener("focusout", () => {
        state.hoverId = null;
        hideBubble();
        render();
      });
      svg.addEventListener("keydown", (e) => {
        if (e.key !== "Enter" && e.key !== " ") return;
        const g = e.target.closest("g.event-marker");
        if (!g) return;
        e.preventDefault();
        const id = g.dataset.eventId;
        state.pinnedId = id === state.pinnedId ? null : id;
        render();
      });
      document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape" || state.pinnedId === null) return;
        state.pinnedId = null;
        render();
      });

      render();
      return figure;
    }

    function revealPlates(figures) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduced || !("IntersectionObserver" in window)) {
        figures.forEach((f) => f.classList.add("revealed"));
        return;
      }
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("revealed");
          observer.unobserve(entry.target);
        });
      }, { threshold: 0.2 });
      figures.forEach((f) => observer.observe(f));
    }

    function initMaps() {
      const figures = PLATES.map(makePlate).filter(Boolean);
      revealPlates(figures);
    }

function initPedigrees(){const D=document,P=JSON.parse(D.getElementById("people-index").textContent).people,B={};for(const p of P)for(const n of p.ah||[])(B[p.a]||(B[p.a]={}))[n]=p;for(const a of"ZMDC"){const f=D.getElementById("chart-"+a.toLowerCase());if(!f)continue;let W=160,X=172,H=640,o={},s='<svg viewBox="0 0 1030 640">';for(let n=1;n<64;n++){let g=Math.log2(n)|0,i=n-(1<<g),q=H/(1<<g),h=Math.min(42,q-3),x=g*X,y=i*q+(q-h)/2;o[n]=[x,y,W,h]}for(let n=1;n<32;n++){let c=o[n],d=o[n*2],m=o[n*2+1],x=c[0]+W+6,y=c[1]+c[3]/2,u=d[1]+d[3]/2,v=m[1]+m[3]/2;s+='<path class=pl d="M'+(c[0]+W)+' '+y+'H'+x+'M'+x+' '+u+'V'+v+'M'+x+' '+u+'H'+d[0]+'M'+x+' '+v+'H'+m[0]+'"/>'}for(let n=1;n<64;n++){let r=o[n],p=B[a]&&B[a][n],x=r[0],y=r[1],h=r[3],z=h<20,b=p&&p.ah&&Math.max(...p.ah)-Math.min(...p.ah)>p.ah.length-1?' =':'',N=p&&p.n;let l=p?(z?(p.k=="gap"&&p.c?p.c:N.slice(0,16)+' '+a+'-'+n+b):N.slice(0,28)):'',m=p&&!z?(p.k=="gap"&&p.c?p.c:a+'-'+n+b):'',g='<g class="pc '+(p?p.t:'bare')+'" data-ah='+n+'><rect x='+x+' y='+y+' width='+W+' height='+h+'></rect><text '+(z?'class=pe ':'')+'x='+(x+4)+' y='+(y+(z?11:9))+'>'+l+'</text>'+(m?'<text class=pn x='+(x+4)+' y='+(y+18)+'>'+m+'</text>':'')+'</g>';s+=p?'<a href="#'+p.h+'">'+g+'</a>':g}f.insertAdjacentHTML('beforeend',s+'</svg>')}}
    initPedigrees();initMaps();
  