---
id: trace.2026-07-08.mainhardt-dible-negatives-validation
title: "Mainhardt and Dible Origin Negatives Validation"
date: 2026-07-08
status: resolved
confidence: strong
case_refs: ["case.02", "case.11"]
person_refs: ["person.dible.jacob", "person.dible.john_albert", "person.zimmerman.john_paul"]
evidence_refs: ["ev.ancestry.1866-dible-will"]
source_refs: ["src.dad-bremen-emigrant-search.e1c6671c", "src.genealogie-mainhardt-database.05a17439", "src.history-of-the-devilbiss-family-in-the-united-states.69241716", "src.johann-jacob-dreibelbis-wikitree.9e7389b3", "src.pa-archives-3rd-series-vol-22.5842163a"]
geo_refs: ["target.dible.early_pennsylvania", "target.zimmerman.mainhardt_archion"]
outcome: "The Mainhardt database weakens the locality claim, the emigration search remains open, and the Dreibelbis and DeVilbiss pedigree grafts are disconfirmed."
next_action: "Pull original Mainhardt or United States Heimat records for Zimmerman and Westmoreland deeds, tax, probate, and church records for Dible."
---

# Mainhardt + Dible-origin negatives: validation (2026-07-08)

Independent validation of the two load-bearing negative/disconfirming clusters from
the frontier intake (`research/frontier-intake/13-zinkle.md`, `03-dible-origin.md`;
research/archive/program-board-2026-07-08.md 3.13 and 3.3). A validation agent re-ran every query and re-fetched every
text itself on 2026-07-08; the zeros below are that agent's own results, not
inherited claims. All five verdicts: CONFIRMED.

## 1. The Mainhardt negative (case.02) — CONFIRMED

Live substring searches on the free, no-login Genealogie Mainhardt database
(personen.genealogie-mainhardt.de), each returning the German no-results banner
("Keine Suchergebnisse fuer Nachname enthaelt ..."):
Zimmermann 0 · Zink 0 · Zinkl 0 · Zinkel 0 · Zinckel 0.

The only Zink-family surname in the database is spelled **Zinck**: exactly two
persons, Hans Zinck (I30160) and Margaretha Zinck (I30161, b. ~1552, Baeumlesfeld)
— three centuries too early and married out. Query subtlety worth preserving: a
"contains Zink" search does NOT surface them because "Zinck" does not contain the
substring "Zink"; both the zero and the 1552 pair are true simultaneously.

Coverage density proof: a place search for Wuerttemberger Hof returns 205 birth
records ("Treffer 1 bis 50 von 205") plus 86 deaths at that hamlet alone. One
caveat vs. the intake file: the "~30,000 persons" database total is not quotable
from any stats page (404); it is only corroborated indirectly by person-id numbering
(I30161). Cite the 205-births figure, not the 30k figure.

Bearing: with that density at the exact hamlet, total silence on Zimmermann/Zink*
is strong evidence AGAINST a long-rooted Wuerttemberger Hof/Mainhardt origin, and
consistent with the 1880 census "Bavaria". The FamilySearch "Wuerttemberger Hof"
locality tag should be treated as an unconfirmed indexer inference pending an
actual Mainhardt church-book entry.

## 2. The DAD correction (case.02) — CONFIRMED

dad-recherche.de/hmb/search.asp, surname Zimmermann, 1872-1880:
> "Ihre Suche ergab 656 Datensaetze, es koennen online jedoch nur 100 angezeigt werden."
The Deutsche Auswanderer-Datenbank does cover the window; the earlier zero-hit was
a query artifact. The emigration search is OPEN, not closed.

## 3. Dreibelbis disconfirmation (case.11) — CONFIRMED

Via WikiTree Dreibelbis-13 (direct fetch 403'd behind AWS WAF; r.jina.ai proxy
worked), quoting Annette Burgert's *Palatine Origins of Some Pennsylvania Pioneers*:
Johann Jacob Dreibelbis's 1761 Berks County will names seven children — Abraham,
Martin, Jacob, Mary Elisabeth, Mary Magdalene, Catharine, Philebena — none a
Westmoreland migrant or Dible. Naturalized Philadelphia 24 Sep 1760. The WikiTree
Dreibelbis index (147 profiles at fetch time) holds no Dible descendant.

## 4. DeVilbiss disconfirmation (case.11) — CONFIRMED

*History of the DeVilbiss Family in the United States of America; 200 years*
(archive.org/details/historyofdevilbi00devi), full text downloaded and grepped:
Casper Devilbiss's will (written 16 Mar 1777, probated 6 Apr 1777, Frederick Co MD,
certified copy quoted in the book) names George Devilbiss, John Devilbiss, Casper
Devilbiss, Ann Ramsbergh, Susannah Ramsbergh, Barbarah Fleming (wife Anne). No
Dible. A grep for "dible" across the entire book: zero occurrences.

## 5. The 1783 Westmoreland tax anchor — CONFIRMED

PA Archives 3rd series vol. 22 (archive.org/details/returnsoftaxable00egle), full
text grepped: "Dible, Jacob, 3 4 3" under the township header printed "HUNTINGTON
TOWNSHIP" (print variant of Huntingdon), inside "COUNTY OF WESTMORELAND—1783".
The 1786 Westmoreland section contains no Dible; this 1783 line is the ONLY
Dible-surname occurrence in the ~120k-line volume ("William Dibley" elsewhere is a
different surname). Earliest hard county trace of the surname.

## Docket wording (for Slate 1 W5 to consume verbatim)

**case.02** — downgrade the Mainhardt hypothesis: the Mainhardt database negative
(with the 205-births density argument and the Zinck-spelling subtlety), the
FamilySearch locality tag as indexer inference, and the DAD as an open live
instrument (656 Zimmermann emigrants 1872-1880).

**case.11** — record BOTH German grafts as primary-level disconfirmed (Dreibelbis
1761 will; DeVilbiss 1777 will + zero "Dible" spellings in the family history),
move both to the negative-evidence register, and reframe the case around what
stands: the 1890 Gresham Cyclopedia "Diblebiss" family tradition and the 1783
Huntingdon Township tax appearance as the earliest documentary anchor.

## Landing queue

- Ledger entries: Genealogie Mainhardt database, DAD (dad-recherche.de/hmb),
  DeVilbiss family history, PA Archives 3rd ser. vol. 22, WikiTree Dreibelbis-13
  (as compiled-tier carrier of the Burgert quotes).
- Negative-evidence register entries (dated 2026-07-08): Mainhardt zero-hits;
  Dreibelbis disconfirmation; DeVilbiss disconfirmation.
- case.02 and case.11 bodies per the wording above when the Docket lands (A5).
