# Frontier intake index

Raw-but-organized output of the 60-agent frontier research workflow of 2026-07-08
(three waves of twenty Sonnet agents, one per topic per wave, each wave building on
the last). Corpus: 963 findings and 276 search frames across the twenty topic files
below. No two findings were verbatim duplicates (each wave wrote its claims fresh),
so deduplication here means structure, not deletion: findings are grouped under their
529 unique source URLs, each claim is tagged with the wave(s) that reported it, and
201 of those URL groups carry multiple claims -- 86 of them corroborated by more than
one wave (the strongest intake signal; start there). Every topic file carries the full
verbatim wave syntheses, so these files are the complete durable record of the sweep
-- no other artifact is needed to act on it.

## Standing rules for consuming this directory

1. NOTHING here is validated. Before any claim lands in index.html, the geojson, or a
   reasoning trace, an agent must independently re-fetch the cited source and match the
   quote verbatim (the practiced fetch + quote-match protocol). Agents have been caught
   mislabeling sources before (see the avatar-alt portrait incident in the repo history).
2. Confidence tiers are the REPORTING agent's own grade of its source access:
   verified-primary (agent fetched a primary or near-primary record and quotes it),
   verified-index (agent fetched an index/derivative), compiled (trees, unverified
   chains -- treat as hearsay), speculative (hypothesis, clearly flagged).
3. Validated facts land through the Docket (case.NN) and person rows; corrections to
   already-landed content go through the corrigenda list; searched-and-not-found results
   go to the negative-evidence register. Search frames graduate into
   research/search-frames/<case-id>/ once their docket case exists.
4. This directory is deliberately NOT scanned by tools/check_refs.py: raw intake may
   mention ids that do not resolve yet. Do not add id-bearing files here expecting
   validation.
5. Sensitive-material rule: Medical Lake (file 16) is a psychiatric-hospital town.
   Document only recorded fact, with dignity. No living people, ever.

## Topic files

| file | topic | line | docket | findings (uniq/raw) | frames (uniq/raw) |
|---|---|---|---|---|---|
| 01-hawkeye.md | Hawkeye and the Rexford corner | Dible + Connelly (shared geography) | case.13, case.17 (narrative context for both branches) | 41/41 | 13/13 |
| 02-dible-armstrong-pa.md | Dible in Armstrong County: Zephaniah, Moore, Heckman | Dible (Bill's paternal line) | case.10 (Catherine Moore's dates/parents), case.11 (compiled immigrant layers) | 49/49 | 15/15 |
| 03-dible-origin.md | Dible origin: Dreibelbis and the German hypothesis | Dible (Bill's paternal line) | case.11 | 44/44 | 9/9 |
| 04-harry-julia-dible.md | Harry and Julia: two Dibles marry at Trenton | Dible (Bill's paternal line) | case.10, case.11 (no dedicated case; candidate for a new one) | 59/59 | 13/13 |
| 05-haden.md | Haden and Reed: Albemarle to Cumberland County | Dible (via Elizabeth J. Haden Dible) | case.12 | 45/45 | 14/14 |
| 06-long.md | Long: Pike County back to Carolina | Dible (Bill's maternal line) | case.13, case.20 (CLOSED - generation slip corrected) | 47/47 | 17/17 |
| 07-mcclelland-love.md | McClelland, Hoge, and Love | Dible (Bill's maternal line) | case.13 | 55/55 | 15/15 |
| 08-mundell-origin.md | Mundell origin above Harvey | Mundell (Evelyn's paternal line) | no dedicated case yet -- candidate new case at intake; Harvey's dead FS profile is in the negative-evidence register | 58/58 | 14/14 |
| 09-cantwell.md | Cantwell: Sarah Alice's people | Mundell (Evelyn's paternal line) | case.09 | 63/63 | 13/13 |
| 10-rust-rupert.md | Rust and Rupert: the Reamsville cluster | Mundell (Evelyn's paternal line) | case.05 (one woman or three), case.06 (her parents) | 41/41 | 16/16 |
| 11-clemans-flaherty.md | Clemans and Flaherty: St. Louis 1921 | Mundell (Evelyn's maternal line) | case.07, case.08 | 45/45 | 14/14 |
| 12-adolph-winona.md | Adolph and Winona: Frances's second family | Mundell (Evelyn's upbringing) | case.05 | 44/44 | 15/15 |
| 13-zinkle.md | Zinkle and the Mainhardt problem | Zimmerman (Doyle's paternal line) | case.02 | 47/47 | 12/12 |
| 14-zimmerman-community.md | The Zimmerman colony chain: Norfolk to Selden | Zimmerman (Doyle's paternal line) | case.02, case.03 | 41/41 | 15/15 |
| 15-grams-rolof.md | Grams and Rosa Rolof | Zimmerman (Doyle's maternal / Zodrow line) | case.01 | 39/39 | 13/13 |
| 16-zodrow-west.md | Zodrow west: Idaho, Spokane, Medical Lake | Zimmerman (Doyle's maternal / Zodrow line) | case.01, case.03 context | 68/68 | 15/15 |
| 17-koeberger.md | Koeberger: Ontario marriage, Bavarian origin | Zimmerman (Nauer side) | case.04 | 38/38 | 11/11 |
| 18-nauer.md | Nauer: Ontario to Kansas, Palatinate garble | Zimmerman (Nauer side) | case.04 | 42/42 | 13/13 |
| 19-connelly-durham-ford-staples.md | Connelly, Durham, Ford, Staples | Connelly (Donna's paternal side) | case.14, case.15, case.16 | 39/39 | 14/14 |
| 20-claar-colony.md | Claar: Bedford colony to Canton Bern | Connelly (Donna's maternal line) | case.17 | 58/58 | 15/15 |

## Docket key (from the Slate 1 plan, for orientation)

- case.01 The Sabanka problem: John Zodrow's birthplace; Zodrow/Grams/Baier origins -- OPEN
- case.02 Parents of John Paul Zimmerman and Catherine Zinkle: the Mainhardt registers -- NEEDS PULL
- case.03 Leonard-to-Michael hardening; Doyle's missing April 2005 obituary -- NEEDS PULL
- case.04 Nauer/Koeberger: Lorenz+Dorothea lead; Meyer vs. Wand; the 1871/1872 stone year -- IN CONFLICT
- case.05 Frances Rust / Frances Adolph / Frances Strawn: one woman or three? -- OPEN
- case.06 Mary Frances Rust's parents: the John F. Rust + Ethel Rupert Reamsville cluster -- OPEN
- case.07 Marjorie Clemans's parentage; the Indiana Marjorie Opal Clemans collision -- OPEN
- case.08 The Leora Young/Rogers household question -- OPEN
- case.09 Sarah Alice Cantwell's maternal line (Coshocton/Iowa) -- OPEN
- case.10 Catherine Moore: conflicting vital dates and unknown parents -- IN CONFLICT
- case.11 Compiled Dible/Heckman immigrant layers: Allshouse, Otterman, Dreibelbis, Boedigheim -- OPEN
- case.12 Haden/Reed: the Cumberland County chain and Sophia's parents -- OPEN
- case.13 Long/Sleight/McClelland/Love: hardening the Gen 5-6 compiled layer -- OPEN
- case.14 Parents of James Connelly -- OPEN
- case.15 David Monroe Durham: one man or two (1832-1897 vs. 1829-1887)? -- IN CONFLICT
- case.16 John Laborn Ford's father (John Laborn Sr. vs. Levi); the 1840 vs. 1842 marriage -- IN CONFLICT
- case.17 Hoyle vs. Hogle: the 1895 Decatur County original marriage record -- NEEDS PULL
- case.18 The 1953/1954 wedding date -- CLOSED (verdict 14 Jun 1954)
- case.19 Jule vs. Julius -- CLOSED (verdict Julius, family testimony)
- case.20 The Rev. Robert Long generation slip -- CLOSED (corrected Jul 2026)

