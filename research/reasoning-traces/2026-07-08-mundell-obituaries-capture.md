---
id: trace.2026-07-08.mundell-obituaries-capture
title: "Mundell and Cantwell Obituaries Real Browser Capture"
date: 2026-07-08
status: resolved
confidence: strong
case_refs: ["case.09", "case.22"]
person_refs: ["person.cantwell.barnabas", "person.mundell.harvey", "person.mundell.john", "person.mundell.john_pryor"]
evidence_refs: []
source_refs: ["src.john-pryor-mundell-find-a-grave.e1163e68", "src.rev-john-w-mundell-find-a-grave.737a9312", "src.sarah-alice-cantwell-mundell-find-a-grave.ee2b20da", "src.sarah-jane-mundell-wilcox-find-a-grave.f8ed8caa"]
geo_refs: ["event.mundell.harvey_birth.1837-04", "event.mundell.harvey_death.1911-03-26", "path.mundell", "target.mundell.cantwell_coshocton"]
outcome: "The obituary transcriptions establish the sibling and migration cluster and a Henry County Cantwell anchor, but they do not prove Harvey's parents or the deeper Cantwell line."
next_action: "Obtain original household, marriage, probate, deed, or church records for Harvey Mundell and Sarah Alice Cantwell's parent-child links."
---

# Mundell + Cantwell obituaries: real-browser capture (2026-07-08)

The four Find a Grave pages that blocked every scripted fetch (curl, mirrors,
reader proxies) were captured verbatim with a real Chrome instance driven by
Playwright. Tier note: these are obituary TRANSCRIPTIONS hosted on memorials —
verified-index; the underlying newspapers are the primaries and are named per
item. Full verbatim texts below are the evidence of record for quoting.

## 1. Sarah Jane (Mundell) Wilcox — memorial 43238060
The Chariton Herald-Patriot (Chariton, Iowa), 26 Mar 1931:
> "Sarah Jane Mundell, daughter of John and Deborah Ann Mundell, was born May 8,
> 1846, in Clinton county, Indiana ... She came with her parents to Lucas county,
> Iowa, in 1852 during the pioneer days ... three brothers, Johnny and Steve
> Mundell, of Princeton, Missouri, and Garret Mundell, of Kansas."
Structured fields: b. 8 May 1846 Clinton Co IN; d. 14 Mar 1931 Lucas Co IA;
Rose Hill Cemetery. (The editor header "Daughter of John Mundell and Deborah Ann
Elmore" supplies the ELMORE maiden name — editor-tier, not obituary text.)

## 2. Rev. John W. Mundell — memorial 20680003
The Cainsville News (Cainsville, Missouri), 19 May 1949, p. 1:
> "John W. Mundell, son of John and Deborah Mundell, was born Nov. 13, 1860, in
> Lucas County, Iowa ... He was the youngest of 11 children; all others preceded
> him in death. One brother died at 11 years of age, all other brothers and
> sisters lived to be in their late seventies and eighties, and one brother was
> past 91. ... He and his brother Steve drove an ox team..."

## 3. Sarah Alice (Cantwell) Mundell — memorial 259688013
Payne County News (Stillwater, Okla.), 10 Feb 1939:
> "Mrs. Mundell was a native of Iowa but moved when quite young to Hastings,
> Neb., where in 1885 she was married to John P. Mundell, who preceded her in
> death April 10, 1938. Eleven children were born to this union, five of whom
> survive ... Mrs. Nellie Post, Sapulpa; Mrs. Maude Tucker, Smith's Center,
> Kans.; Thomas S. Mundell, San Francisco, Calif.; Mrs. Velma Cantner, Troup,
> Tex.; Mrs. Thelma Hileman, Farmersville, Calif. ... Mrs. Mundell was the last
> survivor of her father's family."
Structured fields: b. 15 Jan 1864, Mount Pleasant, Henry County, Iowa — a
concrete Henry County anchor for the case.09 Cantwell-Iowa frame.

## 4. John Pryor Mundell — memorial 157801034 (located via site search)
Payne County News, 15 Apr 1938: short notice, names NO parents ("J.P. Mundell,
77, died early Sunday... pioneer farmer"). Structured fields: b. 18 Oct 1861,
**Sheridan, Poweshiek County, Iowa**; d. 10 Apr 1938 Glencoe; Glencoe Cemetery
("One stone ... only initials. J.P., J.R., S.A., and W.W.").

## What this establishes — and what it does not

- John Mundell + Deborah [Ann] (Elmore per editor-tier) Mundell are DIRECTLY
  documented as parents of Sarah Jane (b. 1846) and John W. (b. 1860), with an
  ELEVEN-child sibling set, Clinton County IN origin, and the 1852 migration to
  Lucas County IA — the sibling-set frame Harvey (b. Apr 1837, enlisted from
  Lucas County) must be tested against. Harvey's membership remains a compiled
  census inference; these obituaries constrain but do not close it.
- Chronology guard: John W. (b. Nov 1860) being "the youngest of 11" means
  anyone born later cannot belong to that sibling set. John Pryor (b. Oct 1861,
  Poweshiek Co) is therefore NOT a child of John + Deborah — consistent with our
  chain, where John Pryor is HARVEY's son. His Poweshiek birthplace is a new
  Iowa waypoint for the Harvey household between Lucas County records.
- Sarah Alice's Henry County IA birth (1864) and "last survivor of her father's
  family" feed case.09.

## Landing queue

- Ledger entries: the four memorials (obituary carriers), each cited with its
  newspaper name and date.
- Walter's grandparents' row context + the future Mundell-origin case: the
  sibling-set frame and the 1852 migration, with Harvey's membership explicitly
  marked compiled.
- case.09: Sarah Alice's 1864 Henry County birth and the 1885 Hastings marriage.
- John Pryor's row: b. 18 Oct 1861 Poweshiek County (memorial fields tier),
  d. 10 Apr 1938 Glencoe.
