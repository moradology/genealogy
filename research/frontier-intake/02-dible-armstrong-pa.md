# Frontier intake 02: Dible in Armstrong County: Zephaniah, Moore, Heckman

Line: Dible (Bill's paternal line)
Docket: case.10 (Catherine Moore's dates/parents), case.11 (compiled immigrant layers)
Source: 60-agent frontier workflow, waves 1-3, 2026-07-08. RAW INTAKE -- see 00-index.md
for the validation protocol; nothing below may land in index.html without an
independent re-fetch and quote match.

## Where this sits in the tree

The Dible/Heckman/Moore layer sits above Harry and Julia Dible: Zephaniah Dible of Kiskiminetas Township, Armstrong County, PA, and wife Catherine Moore (her conflicting vital dates are case.10), plus John Albert Dible m. Catherine Heckman. Note the generational order of Zephaniah vs. John Albert is itself disputed between compiled sources: the workflow frame read John Albert as Zephaniah's son, while slate1's chart places Zephaniah at D-8/9 and John Albert at D-16/17=20/21 (Zephaniah's father, and father of John Heckman Dible too). Resolve before landing anything.

## Original frame given to the agents

> DIBLE DEEP PA: Zephaniah Dible of Kiskiminetas Township, Armstrong County, PA, and wife Catherine Moore (conflicting dates in compiled sources). Parents of John Albert Dibler/Dible (m. Catherine Heckman). Frame Armstrong/Westmoreland County records: probate, land, church (Lutheran/Reformed), cemeteries. Dibler/Deibel/Dible variants.

## Wave syntheses (verbatim from the agents)

### Wave 1

The existing page already treats 'Zephaniah Dible + Catherine Moore, Kiskiminetas Twp, Armstrong Co PA' as a strong lead with conflicting Catherine-Moore vital dates (Ancestry 1839-1864 vs WikiTree ~1834-1872) and names John Albert Dibler + Catherine Heckman as the parent couple. This pass surfaced three genuinely independent compiled sources that disagree on Zephaniah's mother: (1) FamilySearch/WikiTree (already known) say Catherine Heckman; (2) the 'Families by Velma Parsons' DIBLE.pdf traces Jacob Dible (1780-1872) m. Susannah Allshouse (1782-1835) -> son John Dible (1805-1866) m. Catherine Heckman (1805-1846), 'Both buried, Porter Cemetery, Bethel Twp,' but lists only four children (John, Margaret, Malinda, Belle) with NO Zephaniah; (3) the Allshouse family webGED (rootsweb) gives the same John Dible (1805 Franklin Twp, Westmoreland Co - 1866, son of Jacob Dible Esq. II and Susannah Allshouse) TWO wives -- Elizabeth Allshouse (children incl. Susanna, m. Andrew Jackson Allison at Congruity Presbyterian Church 1851) and an otherwise-unidentified 'Mrs. Barbara' (b.1809 Armstrong Co) -- and places Zephaniah (~1835) as Barbara's son. Critically, this same webGED independently records Zephaniah Dible marrying Catherine Moore (b.1839, Westmoreland Co) on 24 Mar 1859 in Westmoreland Co, PA -- a specific, dated, previously-uncited claim that corroborates the Ancestry 1839 birth year for Catherine. A period 1861 Kiskiminetas Twp landowner map (Pomeroy's map, free reproduction) shows a 'J. Dible' tract directly beside Lewis Heckman, S. Crosby (a fellow Apollo Presbyterian elder alongside John Dible per a county-history reproduction) and two more Heckman households, physically corroborating a Dible-Heckman neighborhood link even though it doesn't resolve the maternity conflict. Every congregation actually documented for this specific family (Apollo Presbyterian, Congruity Presbyterian, Spring Church Presbyterian for a Dible-Jr. line) is Presbyterian, not Lutheran/Reformed as the assignment assumed -- though Kiskiminetas Twp did have real Lutheran congregations (Boiling Spring Lutheran, Maysville Lutheran) worth checking. 'Porter Cemetery, Bethel Twp' resolves geographically to a Porter Cemetery on Ridge Rd, Vandergrift, tagged Armstrong County by BillionGraves (0 headstones indexed yet), which is a separate jurisdictional lead from Westmoreland's Bethel/Franklin (Murrysville) townships also named in these sources. FindAGrave and WikiTree were both bot-walled (Cloudflare/AWS WAF) against curl in this session and need a real browser pass. No original PA vital, probate, or land record was directly pulled this round -- everything above is compiled/index-tier except the map image and the county-history text.

### Wave 2

This wave verified several of wave 1's compiled leads by directly fetching the underlying Allshouse rootsweb webGED (not just describing it), confirming the 'Mrs. Barbara' vs Catherine Heckman maternity conflict with exact dates for Zephaniah's whole sibling group, and surfacing that his sister Mereyann married a Hezekiah Moore in 1853, six years before Zephaniah married Catherine Moore -- a concrete, testable hint that the two Moore spouses may be kin. It pushed the Allshouse collateral line back two further generations to a German immigrant (Henry Allshouse Sr., 1725 Althausen, Wuerttemberg - 1803 Easton, PA), surfaced a new, geographically tighter competing immigrant-surname theory (Divelbiss/Devilbiss of Harrison City, the same village Jacob Dible Esq II was born in, versus the previously-cited Dreibelbis of Berks Co), and resolved wave 1's Bethel Township jurisdictional ambiguity (it split from Allegheny Township only in 1878, so it is almost certainly Armstrong County's Bethel Twp, not a nonexistent Westmoreland one). Most significantly, a full-text search of the 1883 History of Armstrong County surfaced primary-tier material never cited before: an Elias Dibler Civil War muster-roll entry, a Philip Heckman 1822 land deed, an 1848 Lutheran church charter naming a Heckman and a Kepple trustee (the same Kepple surname that married into the Dible family in Westmoreland Co), and -- directly answering the assignment's Lutheran/Reformed church question -- Kiskiminetas Township's own Boiling Spring Presbyterian/Lutheran and Maysville Lutheran congregations, though no Dible/Heckman/Moore name appears in that chapter. WikiTree's surname-index page (unlike its individual profile pages, which remain hard-blocked by CAPTCHA on both curl and headless Playwright) yielded day-precise WikiTree profile IDs for Zephaniah and John Dible. Catherine Moore's own parentage and exact death date remain fully open; no original probate, land, or church record has yet been pulled for the family, only compiled/index-tier and one county-history source.

### Wave 3

This wave pushed the Dible/Heckman/Moore line by directly fetching primary and primary-adjacent sources rather than describing compiled trees: a real 1748 Philadelphia oath-of-allegiance ship list independently confirmed the Allshouse immigrant ancestor (Henry Althaus/Allshouse); FindAGrave and two county-history chapters (Beers 1883/1914, read via pa-roots.com) pinpointed three distinct Lutheran cemeteries/congregations tied to the Heckman, Kepple, and Dibler surnames in Bethel, Parks, and old Kiskiminetas Township/Apollo Borough -- directly answering the assignment's Lutheran-church question with named individuals (Frederick & Nancy Dibler, Christian & Elizabeth Kepple as 1859 Apollo Lutheran founders) instead of the prior wave's nameless Boiling Spring/Maysville mentions. It also corrected the Porter Cemetery jurisdiction (Parks Township, not Bethel) and found its single indexed Dible burial is a full generation earlier (Catherine, wife of 'John Dible,' d.1816) than previously assumed. Most significantly, using the Wayback Machine to bypass WikiTree's CAPTCHA (successfully reading Dible-18, Dible-6, and the DIBLE surname index in full for the first time), this wave discovered that WikiTree's own tree does NOT establish Zephaniah Dible's parents at all -- adding a fourth, blank data point to the three-way Catherine-Heckman-vs-Mrs.-Barbara conflict -- while separately yielding an entirely new, previously undocumented post-1859 migration trail for Zephaniah (Ohio River steamboat engineer, then Iowa, Sedgwick County KS, and Missouri mining, with a directly quoted 1895 KS census citation) and pushing the Allshouse ancestor chain, via WikiTree's compiled tree, three further generations into 1680s-1720s Germany (Wolfersheim, Saarland; unnamed Bavarian villages). The Albrecht Heckman 'ship Beulah 1753' immigration claim could not be corroborated in any searched Palatine passenger-list corpus and should be treated as unverified pending further search. Catherine Moore's parentage and Zephaniah's own death date/place remain the two most wide-open threads; a concrete Westmoreland County probate citation (Jacob Dible Sr., d.1872) surfaced as an unpulled next step.

## Findings (49 unique from 49 raw, grouped by source, best-verified first)

### https://billiongraves.com/cemetery/Porter-Cemetery/85968

- **[verified-index]** (w1, place) A Porter Cemetery (candidate for the Velma Parsons paper's 'Porter Cemetery, Bethel Twp') is located on Ridge Rd in Vandergrift and is catalogued under Armstrong County, not Westmoreland -- a jurisdictional clue for where to search burial records, though no headstones are yet indexed there.
  > 1231-1201 Ridge Rd, Vandergrift, Pennsylvania, 15690
- **[verified-primary]** (w2, other) Porter Cemetery (Ridge Rd, Vandergrift, tagged Armstrong County) remains completely unindexed on BillionGraves as of this session -- re-confirmed directly from the site's own live metadata rather than relying on wave 1's visual description, so this remains a genuine dead end pending an in-person survey.
  > "numRecords":0,"numImages":0

### https://ancestortracks.com/Armstrong%20Co,%201861/KiskiminetasTp,ArmCo.jpg

- **[verified-primary]** (w1, place) An 1861 landowner map of Kiskiminetas Township shows a 'J. Dible' tract sited directly among a cluster of Heckman-surname landowners (Lewis Heckman, Michael Heckman, Jacob Heckman) and next to S. Crosby (the fellow Apollo Presbyterian elder), physically corroborating a Dible-Heckman neighborhood tie in the exact township named in the task.
  > J. Dible

### http://www.searchforancestors.com/passengerlists/judith1748.html

- **[verified-primary]** (w3, migration) Henry Allshouse (the immigrant ancestor of Zephaniah Dible's grandmother Susannah Allshouse) appears as 'Henry Althaus' on the actual 1748 Philadelphia oath-of-allegiance passenger list for the ship Judith, Capt. James Tait -- directly corroborating the FindAGrave/WikiTree claim about his arrival.
  > Sept. 15, 1748. Foreigners imported in the ship Judith James Tait, Captain, from Rotterdam, last from Cowes... Conrad Hinkel Philip Knobel Augustus Eygenbrod Henry Althaus

### https://www.findagrave.com/memorial/29506509/catherine-dible

- **[verified-primary]** (w3, place) The 'Porter Cemetery' previously guessed to be in Bethel Township is actually in Parks Township, Armstrong County, and holds exactly one Dible burial: Catherine, wife of a 'John Dible,' who died in 1816 -- a full generation earlier than John Dible (1805-1866) m. Catherine Heckman.
  > Burial Porter Cemetery Parks Township, Armstrong County, Pennsylvania, USA ... Wife of John Dible. died age 40 Y; 8 M and 10 D.

### https://www.findagrave.com/memorial/42106564/philip-heckman

- **[verified-primary]** (w3, person) Philip Heckman (presumed father of Catherine Heckman) was born in Lancaster County, PA in 1770 -- not Germany -- and died in Armstrong County in 1839, buried at Bethel Lutheran Church Cemetery, Ford City.
  > Philip Heckman Birth 8 Jul 1770 Lancaster County, Pennsylvania, USA Death 25 Aug 1839 (aged 69) Armstrong County, Pennsylvania, USA Burial Bethel Lutheran Church Cemetery Ford City

### https://www.findagrave.com/memorial/43410689/ludwig-heckman

- **[verified-primary]** (w3, other) Highfield (St. Paul) Evangelical Lutheran Church Cemetery in Parks Township holds numerous Heckman and Kepple burials, including children of Philip Heckman and Esther Otterman -- a concrete Lutheran-church record set tying the Heckman and Kepple families to the same township as the Dible-linked Porter Cemetery.
  > Louis (baptized Ludwig), was son of Philip Heckman and Esther Otterman, grandson of Albrecht Heckman, immigrant from Boedigheim, Mosbach, Baden, Germany.
- **[speculative]** (w3, migration) The compiled claim that Albrecht Heckman (Philip Heckman's father) immigrated on a ship 'Beulah' landing 10 Sep 1753 could not be corroborated in any searched Philadelphia Palatine passenger-list index (Strassburger/Hinke mirrors, Rupp 1876) -- no ship named Beulah appears in the standard 1753 arrivals.
  > Albrecht emigrated to Pennsylvania aboard Ship Beulah, landing in Philadelphia 10 Sep 1753.

### https://www.findagrave.com/memorial/51396019/frederick-dibler

- **[verified-primary]** (w3, person) Frederick Dibler (1812-1886), a founding member of the Apollo Lutheran church, is buried at a third distinct Lutheran cemetery -- St. Michael's, Brick Church, Armstrong County -- widening the Dibler-Lutheran church footprint in the county.
  > Birth 27 Aug 1812 Death 5 Feb 1886 (aged 73) Burial Saint Michael's Lutheran Church Cemetery Brick Church, Armstrong County, Pennsylvania

### https://www.findagrave.com/memorial/135345825/samuel-dible

- **[verified-primary]** (w3, person) A documented Jacob Dible (1811-1886, likely John Dible's brother) married Rosannah Hall and is buried with their son Samuel Dible at Fairview Cemetery, Spring Church, Armstrong County -- a second confirmed Dible burial ground in the county distinct from Porter Cemetery.
  > Parents Jacob Dible 1811 - 1886 Rosannah Hall Dible 1815 - 1907

### https://en.wikipedia.org/wiki/Bethel_Township,_Armstrong_County,_Pennsylvania

- **[compiled]** (w1, place) Armstrong County itself has its own Bethel Township (distinct from Westmoreland's Bethel/Franklin-Murrysville area), so 'Bethel Twp' in the compiled Dible paper is ambiguous between two counties until an original record specifies which.
  > Bethel Township is a township in Armstrong County, Pennsylvania, United States.
- **[verified-index]** (w2, place) Bethel Township, Armstrong County (named in the Velma Parsons paper's 'Porter Cemetery, Bethel Twp' burial claim) was not established as a separate township until 1878, when it split off from the older Allegheny Township along with Gilpin and Parks Townships. Since John Dible died in 1866, any 'Bethel Township' burial reference necessarily uses a place-name created 12 years after his death, and no Westmoreland County township of that name appears to exist -- resolving wave 1's jurisdictional ambiguity in favor of Armstrong County.
  > Bethel Township was originally merged with the neighboring townships of Gilpin and Parks, known as Allegheny Township. In 1878, finding it was too large to manage and supervise, the three split and Bethel Township was incorporated.

### https://www.findagrave.com/memorial/135353288/anna-rose-richards

- **[verified-index]** (w1, place) Anna Rose Dible Richards (1875-1965) on Find a Grave is buried at Fairview Cemetery, Spring Church, Armstrong Co -- matching the Velma Parsons paper's Anna R. Dible (dau. of Samuel Dible & Nancy Cochran, m. Harry R. Richards, 'Live Spring Church'), an independent cross-check that validates the Parsons paper's accuracy for that collateral line.
  > citing Fairview Cemetery, Spring Church, Armstrong County, Pennsylvania

### https://archive.org/details/historyofarmstro01smit

- **[verified-index]** (w2, person) The 1883 published History of Armstrong County's Civil War muster rolls record a soldier under the 'Dibler' spelling variant: Elias Dibler, private, Co. B, 78th Pennsylvania Volunteer Infantry, mustered in Oct. 12, 1861, reported missing in action at the Battle of Stones River, TN, on Dec. 31, 1862 -- a new, dated primary-tier record tying the 'Dibler' variant specifically to Armstrong County in the same decade Zephaniah's family appears there.
  > Dibler, Elias, m. i. s. Oct. 12, 1861; missing in action at Stone River, Tenn., Dec. 31,1862.
- **[compiled]** (w2, date) The same county history's deed-chain summary for a tract in Allegheny Township, Armstrong County records a Philip Heckman land purchase dated Jan. 22, 1822 -- a genuine period land-record lead for the man FamilySearch names as Catherine Heckman's father.
  > he to John Sheaffer, May 17, 1817, he to Philip Heokman [Heckman], January 22, 1822. There was a conveyance from Heckman to Michael Fry, whose administrator, Peter Phillipi, conveyed it to Robert Morrison, September 19, 1836
- **[compiled]** (w2, other) The same county history records the 1848 incorporation charter of the Hebron Evangelical Lutheran Church at Leechburg (Allegheny Township, Armstrong Co, immediately adjoining Kiskiminetas Township) naming trustees Abraham Heckman and George Kepple -- the Kepple surname that had married into the Dible family in Westmoreland County six years earlier (Susan/Susannah Dible married John Kepple in 1843), suggesting a real kinship/migration corridor between the Franklin Twp Dible circle and this Armstrong County Lutheran congregation.
  > The trustees named in the charter, who were to continue until the election held on the last Saturday of March, 1850, were Rev. David Earhart, George Kepple, Jacob Trout, Thomas Van Tine, Abraham Heckman, Andrew Ashbaugh, Jr., and Samuel Shuster.
- **[verified-index]** (w2, place) The county history's dedicated Kiskiminetas Township chapter (Chapter X) directly names and dates the township's Lutheran congregations the assignment flagged as a gap: Boiling Spring Presbyterian Church (organized 1840) shared its first building with the Boiling Spring Lutheran Church near Rattling Run, and the separate Maysville Lutheran Church stood nearby; both Lutheran congregations belonged to the General Synod, with 54 and 38 members respectively as of 1883. No Dible, Heckman, Moore, or Crosby name appears anywhere in this chapter's text, so the family-to-congregation link is still unconfirmed.
  > The first church edifice, built jointly by the Presbyterian and Lutheran congregations, was a capacious frame structure, situated near Rattling run... Both of these last-mentioned churches belong to the General Synod.

### https://homepages.rootsweb.com/~allshous/Allshouse/wga16.html

- **[compiled]** (w1, relationship) An independently compiled genealogy (not previously cited on the site) gives an exact marriage date for Zephaniah Dible and Catherine Moore: 24 Mar 1859 in Westmoreland Co., PA, and gives Catherine's birth year as 1839, matching Ancestry's 1839 date rather than WikiTree's ~1834.
  > spouse: Moore, Catherine (1839 - ) - m. 24 MAR 1859 in Westmoreland Co., Pennsylvania
- **[compiled]** (w1, relationship) This same compiled genealogy names Zephaniah Dible's mother as an unidentified 'Mrs. Barbara' (b.1809, Armstrong Co PA), not Catherine Heckman as FamilySearch/WikiTree state -- a direct three-way conflict on Zephaniah's maternity.
  > father: Dible, John (1805 - 1866) mother: Dible, Mrs. Barbara (1809 - )
- **[compiled]** (w1, relationship) The same source gives John Dible's (Zephaniah's presumed father) own birthplace and parents: born 1805 in Franklin Township, Westmoreland Co PA, son of Jacob Dible Esq. II and Susannah Allshouse.
  > b. 1805 in Franklin Township, Westmoreland Co, PA father: Dible, Jacob Esquire Ii (1780 - 1872) mother: Allshouse, Susannah (1782 - 1835)
- **[compiled]** (w1, relationship) Susanna Dible (John Dible's daughter by Elizabeth Allshouse) married Andrew Jackson Allison at Congruity Presbyterian Church, Salem Twp, Westmoreland Co, on 21 Aug 1851 -- a second Presbyterian-congregation touchpoint for this Dible family cluster.
  > m. 21 AUG 1851 in Congruity Presbeterian Church, Salem, PA
- **[compiled]** (w2, relationship) Zephaniah Dible's full sibling group under his mother 'Mrs. Barbara' all married in Westmoreland Co, PA between 1853 and 1859, including a Dible-Moore marriage one generation before Zephaniah's own: his sister Mereyann Dible married Hezekiah Moore in 1853, six years before Zephaniah married Catherine Moore in the same county.
  > Dible, Mereyann (~1831 - )... spouse: Moore, Hezekiah (1827 - ) - m. 24 FEB 1853 in Westmoreland Co., Pennsylvania ... Dible, Zephaniah (~1835 - )... spouse: Moore, Catherine (1839 - ) - m. 24 MAR 1859 in Westmoreland Co., Pennsylvania
- **[compiled]** (w2, relationship) John Dible's first wife, Elizabeth Allshouse (d. before 1856, m. abt. 1827), appears to be a member of the same extended Allshouse family as John's own mother Susannah Allshouse -- suggesting an endogamous marriage inside the Allshouse clan one generation before Zephaniah.
  > spouse: Allshouse, Elizabeth (1806 - <1856) - m. ABT 1827 in of Westmoreland, Pennsylvania
- **[compiled]** (w2, other) Six of the seven children this database lists under John Dible + Elizabeth Allshouse (Elizabeth, Jane, Albert, William, Esther, Isabella) all carry the identical placeholder birth year 'estimated 1838,' a pattern typical of genealogy-software auto-estimated dates rather than documented individual births -- this whole half-sibling cluster's ages (and possibly some entries themselves) should be treated as low-confidence filler, not vetted data.
  > Dible, Elizabeth (*1838 - ) ... Dible, Jane (*1838 - ) ... Dible, Albert (*1838 - ) ... Dible, William (*1838 - ) ... Dible, Esther (*1838 - ) ... Dible, Isabella (*1838 - )

### https://www.familiesbyvelmaparsons.com/pdfs/DIBLE.pdf

- **[compiled]** (w1, relationship) A different compiled 'Dible Family' paper agrees John Dible (1805-1866) married Catherine Heckman (1805-1846) but lists only four children -- John, Margaret, Malinda, Belle -- with no Zephaniah among them, raising the possibility Zephaniah belongs to a different set of siblings or was simply omitted.
  > 5-1. John Dible. 5-2. Margaret Dible. 5-3. Malinda Dible. 5-4. Belle Dible.
- **[compiled]** (w1, place) The same paper states John Dible and Catherine Heckman were both buried at 'Porter Cemetery, Bethel Twp' -- a burial-place lead not previously captured on the site.
  > Both buried, Porter Cemetery, Bethel Twp.
- **[compiled]** (w1, relationship) Jacob Dible (1780-1872) married Susannah Allshouse (1782-1835) on 19 Jun 1802, per the same compiled paper -- giving a specific marriage date for the great-grandparent generation.
  > Married, 19 Jun 1802. Wife, Susannah ALLSHOUSE. 21 Dec 1782-25 Jan 1835.

### https://www.pa-roots.com/2025/08/13/apollo-presbyterian-church-kiskiminetas-township-armstrong-county-pennsylvania/

- **[compiled]** (w1, other) A John Dible (very likely the 1805-1866 John Dible, father of the disputed Zephaniah) served as an elder at Apollo Presbyterian Church in Kiskiminetas Township, Armstrong Co, during the 1830 - 1837 pastorate of Rev. Watson Hughes -- placing the family in Kiskiminetas Twp church life a generation earlier than previously documented, and indicating a Presbyterian rather than Lutheran/Reformed affiliation for this line.
  > Four elders were elected and ordained—William McGeary, Samuel Crosby, John Dible and James Chambers.

### https://www.pa-roots.com/2025/08/13/chapter-10-kiskiminetas-history-of-armstrong-county-pennsylvania-part1/

- **[compiled]** (w1, place) Kiskiminetas Township itself did contain actual Lutheran congregations (Boiling Spring Lutheran and Maysville Lutheran), so the task's Lutheran/Reformed premise is geographically plausible even though no direct Dible-Lutheran membership record has been found yet.
  > The Boiling Spring Lutheran church has a capacious frame edifice situated a few rods west of the Presbyterian church.

### https://ancestors.familysearch.org/en/L6LS-FR4/malinda-dible-londen-1839-1929

- **[compiled]** (w1, relationship) A FamilySearch public-tree profile for Malinda Dible Londen (1839-1929) -- matching the Velma Parsons paper's 'Malinda Dible' child of John Dible/Catherine Heckman -- names her father as 'John Albert Dibler,' the same compound name already used on the site's Gen 5 label, and places her in Burrell Township, Armstrong Co.
  > born on 15 December 1839 in Westmoreland, Pennsylvania, and her father was John Albert Dibler

### https://homepages.rootsweb.com/~allshous/Allshouse/wga31.html

- **[compiled]** (w2, date) In this same compiled database, Catherine Moore's own entry and her presumed brother-in-law Hezekiah Moore's entry carry no father/mother line at all, unlike every Dible/Allshouse entry around them -- this specific compiled tree simply does not attempt Catherine Moore's parentage.
  > Moore, Catherine (1839 - ) - female b. 1839 in Westmoreland Co., Pennsylvania spouse: Dible, Zephaniah (~1835 - ) - m. 24 MAR 1859 in Westmoreland Co., Pennsylvania

### https://www.findagrave.com/memorial/7454044/susanna-dible

- **[compiled]** (w2, place) Susannah Allshouse Dible (Jacob Dible Esq II's wife, Zephaniah's grandmother) has an actual Find A Grave memorial with plot-level burial detail at Murrysville Cemetery, Westmoreland County, PA -- a different, specific cemetery from the 'Porter Cemetery, Bethel Twp' claimed for the next generation (John Dible/Catherine Heckman) in the previously-cited Velma Parsons paper.
  > Cemetery Murrysville, Westmoreland County, Pennsylvania ... Plot Section: 12; Row: 2; Space: 3

### https://homepages.rootsweb.com/~allshous/Allshouse/wga5.html

- **[compiled]** (w2, person) Susannah Allshouse's own parents are documented as Henry Allshouse (1757-1836, b. Easton, Bucks Co PA) and Gertrude Truxell (1758-1819), married 1779 in Easton PA; pushing one generation further, Henry's father Henry Allshouse Sr. (1725-1803) was the immigrant, born in Althausen, Wuerttemberg, Germany, and died/was buried in Easton, Northampton Co, PA.
  > Allshouse, Henry (1725 - 1803) - male b. 4 OCT 1725 in Althausen, Wuertemburg, Germany d. 12 JUN 1803 in Easton, Norhampton Co, PA ... Burial - [place: Easton cemetery - common vault]

### https://www.wikitree.com/genealogy/Dible

- **[compiled]** (w2, date) A WikiTree surname-index page (distinct from the individual profile pages, which are blocked by a human-verification wall on both curl and headless-Playwright access) lists specific profiles for Zephaniah Dible (Dible-18, b. 1836, Westmoreland County) and his father John Dible (Dible-6), the latter with day-level precision not present in the older rootsweb webGED.
  > Zephaniah Dible 1836 Westmoreland County, Pennsylvania, United States ... John Dible 03 Jan 1805 Pennsylvania, USA - 28 Dec 1866 Pennsylvania

### https://www.pa-roots.com/2025/08/12/beers-historical-record-chapter-24-bethel-township/

- **[compiled]** (w3, other) Bethel Township, Armstrong County (which the predecessor wave flagged as a jurisdictional question) is literally named for the Bethel Evangelical Lutheran Church, organized 1846 with a second charter in 1848 -- matching the '1848 Lutheran church charter' the predecessor wave found in the county history.
  > Bethel Evangelical Lutheran Church was organized in 1846, under the pastorate of Rev. David Earhart of Leechburg.
- **[compiled]** (w3, place) A 'P. Heckman' (almost certainly Philip Heckman) is named as an early land-warrant holder/settler in the territory that became Bethel Township, Armstrong County.
  > John Elder, John Collier, David McKee, Peter Shaeffer, J. Heckman, P. Heckman, John Barrickman, James Beatty

### http://parkstwp.com/About.aspx

- **[compiled]** (w3, place) Parks Township, Armstrong County (formed 1878 alongside Bethel and Gilpin out of the old Allegheny Township) lists Heckman and Kepple among its early settler families, and names 'Porter's' among its old cemeteries -- directly matching the Porter Cemetery Dible burial found this session.
  > Early settlers included Stitt, Hill, Foster, Guthrie, Heckman, Altman, Shaner, Kepple, McIntire, Lanning, Kearney, Greenberry, Wilson, Painter, Girt, Wyant, Gourley, and Crosby.

### https://www.pa-roots.com/2025/08/12/beers-historical-record-chapter-15-apollo-borough/

- **[compiled]** (w3, relationship) The First Evangelical Lutheran Church of Apollo (organized 1859) directly answers the assignment's Lutheran-church question with named founding members Frederick Dibler and Nancy Dibler alongside Christian Kepple and Elizabeth Kepple.
  > Christian Kepple, Elizabeth Kepple, John Bair, Elizabeth Bair, Mary Martin, Frederick Dibler, Nancy Dibler, Bohemia Townsend
- **[compiled]** (w3, place) Apollo Borough -- site of the 1859 Dibler/Kepple Lutheran church -- was carved directly out of Kiskiminetas Township in 1848, geographically anchoring that church record inside the assignment's named township.
  > By act of Assembly March 15, 1848, Warren, then in the township of Kiskiminetas, was incorporated into the borough of Apollo.

### https://apollopahistory.com/apollo-history/churches/lutheran-church/

- **[compiled]** (w3, other) A modern local-history page independently corroborates Christian Kepple as a founding deacon/trustee of the Apollo Lutheran congregation.
  > James Fair and C. Kepple, deacons and trustees.

### https://www.wikitree.com/wiki/Dible-18

- **[compiled]** (w3, relationship) WikiTree's own profile for Zephaniah Dible does not establish his parents at all (shows 'Unknown Dible' and mother unknown), meaning the widely repeated 'John Albert Dibler + Catherine Heckman' parentage rests solely on Ancestry/FamilySearch/Velma-Parsons compiled trees and is not independently corroborated by WikiTree.
  > Son of Unknown Dible and [mother unknown] Brother of George F Dible Husband of Catherine (Moore) Dible
- **[compiled]** (w3, migration) Zephaniah Dible's WikiTree biography adds an entirely new post-Kiskiminetas migration trail never previously documented: Civil War-era Ohio River steamboat engineer, then Iowa (1869), then Sedgwick County, Kansas (1880-1896), then Missouri mining -- with a directly quoted 1895 Kansas State Census entry.
  > in 1869 removed to Iowa. He settled in Monroe county, near Albia, where he remained until he moved to Wapello county
- **[compiled]** (w3, date) WikiTree gives an exact marriage date for Zephaniah Dible and Catherine Moore -- 24 Mar 1859 -- not previously pinned to a specific day in either compiled source used in prior waves.
  > Husband of Catherine (Moore) Dible — married 24 Mar 1859 [location unknown]

### https://www.wikitree.com/wiki/Dible-6

- **[compiled]** (w3, relationship) WikiTree's John Dible (1805-1866) profile names his parents as Jacob Dible Sr. and Susannah Allshouse but lists his own spouse as unknown and only one child (Susannah Dible Allison) -- an independent tree that does not corroborate Catherine Heckman as his wife or Zephaniah as his son.
  > Son of Jacob Dible Sr. and Susannah (Allshouse) Dible ... [spouse(s) unknown] Father of Susannah (Dible) Allison
- **[compiled]** (w3, migration) WikiTree extends the Allshouse immigrant chain three further generations into 17th/18th-century Germany: Henry Allshouse's wife Susanna Drissel and Susannah Allshouse's maternal grandfather John Michael Troxell are both given named, dated German/colonial origins.
  > John Michael Troxell 25 Dec 1721 - 29 Sep 1772 Wolfersheim, Saarpfalz-Kreis, Saarland, Germany
- **[compiled]** (w3, other) John Dible's WikiTree profile cites a Westmoreland County, PA Register of Wills will-book index as a source, pointing to an unpulled original probate record for this family.
  > Will Books, 1773-1917; Will Indexes 1773-1918; Author: Westmoreland County (Pennsylvania). Register of Wills; Probate Place: Westmoreland, Pennsylvania

### https://www.wikitree.com/genealogy/DIBLE

- **[compiled]** (w3, person) WikiTree's Dible surname index reveals two entirely distinct people both named 'George F Dible' (one 1828-1904 Murrysville, Westmoreland Co; one 1841-1916 Union Co, Iowa) that had been conflated via identical 'Brother of George F Dible' sibling tags on different profiles, and confirms a large cluster of 'Dible' WikiTree profiles are an unrelated English (London/Kent/Hampshire) family that should not be mixed into this line.
  > George F Dible 21 Dec 1828 Franklin, Westmoreland, Pennsylvania, USA - 17 Mar 1904 Murrysville, Westmoreland, Pennsylvania, USA

### https://www.genealogy.com/ftm/p/r/e/Kim-M-Preston/GENE2-0006.html

- **[speculative]** (w2, person) A search-engine-surfaced compiled genealogy names a candidate father for Jacob Dible Esq II that is geographically far tighter than the previously-cited Dreibelbis (Berks Co) lead: 'Johan Jacob Diblebiss,' born 1743 in Monocacy, Frederick Co, MD, died 1820 in Harrison City, Westmoreland Co, PA -- the exact same village where Jacob Dible Esq II was born in 1780 -- son of Hans Michael Divelbiss and Barbara Hoffman, tying into the documented 'Devilbiss' immigrant family from Alsace (ship Britannia, 1731), a lineage genealogically distinct from the Dreibelbis family despite the similar-sounding surname. This could not be independently fetched and verbatim-quoted this session (genealogy.com and WorldConnect both returned 403/JS-shell to automation), so treat as speculative until a primary page is read directly.
  > N/A - search-snippet only, not independently fetched verbatim this session

### https://www.familysearch.org/en/search/catalog/1999196

- **[speculative]** (w2, other) FamilySearch's catalog confirms free, non-paywalled Armstrong County probate coverage spanning the relevant decades: Will Books (1805-1918) with an index to 1961, Orphans' Court Dockets (1817-1868) with an index to 1931, and Probate Records (1805-1881) with an index to 1935 -- directly covering John Dible's 1866 death and Jacob Dible's 1872 death, but the catalog page itself is a JavaScript shell that could not be rendered by automation this session (confirmed distinctly from the wiki pages, which return a hard Imperva bot-block).
  > N/A - catalog coverage description drawn from search-engine synthesis of the FamilySearch catalog entry; the live catalog page rendered as an empty JS shell to curl this session

## Search frames (15 unique from 15 raw)

### F1 (w1). Who was Zephaniah Dible's mother -- Catherine Heckman (per FamilySearch/WikiTree already on file), an unnamed 'Barbara' (per the Allshouse webGED), or is he simply missing from the Velma Parsons paper's 4-child list for John Dible + Catherine Heckman?

- Jurisdictions: Franklin Township (now Murrysville) and/or Bethel Township, Westmoreland County, PA (John Dible's stated birthplace/burial); Kiskiminetas Township, Armstrong County, PA (Zephaniah's own household by 1859-60); Pennsylvania has no statewide vital registration before 1852 (and inconsistent compliance until ~1906), so church and probate records carry the evidentiary weight
- Record sets:
  - Congruity Presbyterian Church, Salem Twp, Westmoreland Co PA (baptism/marriage/death index) -- https://www.familysearch.org/library/books/records/item/917629-congruity-presbyterian-church-salem-township-westmoreland-county-pennsylvania-1828-1909 (1828-1909)
  - Armstrong County PA Will Books & Index to Wills (FamilySearch catalog) -- https://www.familysearch.org/en/search/catalog/307875 (Will books 1805-1918; index to wills 1797-1961)
  - Armstrong County PA Index to Probate Records (FamilySearch catalog) -- https://www.familysearch.org/en/search/catalog/307893 (1805-1935)
  - Allshouse Family webGED (compiled, gives person-level source IDs for cross-checking) -- https://homepages.rootsweb.com/~allshous/Allshouse/wga16.html (compilation undated, covers 1780s-1900s)
  - Dible family paper, Families by Velma Parsons (compiled) -- https://www.familiesbyvelmaparsons.com/pdfs/DIBLE.pdf (compilation undated, covers 1732-1932)
- Next pulls:
  1. Pull the Westmoreland and/or Armstrong County probate/orphans-court file for John Dible (d.1866) to see if a will or estate distribution names Zephaniah among heirs -- would settle both the county-of-residence question and possibly the mother's identity
  1. Search the Congruity Presbyterian baptism index (1828-1909) for a Dible/Dibler baptism c.1834-1836 and for Catherine Heckman Dible's burial/death entry (d. 15 Jul 1846)
  1. Pull the 1850 US census household of John Dible (whichever township he was actually in) to see the wife's real name and full child list, directly testing the Heckman vs. 'Barbara' claims
  1. Search Westmoreland County marriage-return records (pre-1885 PA marriages were typically recorded as clergy return books, not licenses) for the 24 Mar 1859 Zephaniah Dible x Catherine Moore marriage to find the officiating clergy/denomination

### F2 (w1). When and where did Zephaniah Dible and Catherine Moore die and where are they buried -- does Catherine's death fall in 1864 (Ancestry) or c.1872 (WikiTree)?

- Jurisdictions: Kiskiminetas Township and/or Bethel Township, Armstrong County, PA; possibly Westmoreland County, PA
- Record sets:
  - Find a Grave cemetery browse, Armstrong County PA -- https://www.findagrave.com/cemetery-browse/USA/Pennsylvania/Armstrong-County?id=county_2243 (crowd-sourced, ongoing)
  - BillionGraves, Porter Cemetery, Ridge Rd, Vandergrift, Armstrong Co PA -- https://billiongraves.com/cemetery/Porter-Cemetery/85968 (0 headstones currently indexed)
  - Pennsylvania, Death Certificates (FamilySearch) -- https://www.familysearch.org/en/wiki/Pennsylvania,_Death_Certificates,_1906-1968_-_FamilySearch_Historical_Records (1906-1968 -- too late to cover either proposed death year, useful only as a negative check or for children)
  - 1870 US Federal Census, Kiskiminetas Township, Armstrong Co PA -- https://www.familysearch.org/search/collection/1438024 (1870)
- Next pulls:
  1. Browse Find a Grave and BillionGraves for 'Zephaniah Dible' and 'Catherine Moore Dible' via an actual browser session (curl was blocked by Cloudflare/AWS WAF on both sites in this pass)
  1. Pull the 1870 census for Zephaniah Dible's household in Kiskiminetas Twp: Catherine's presence or absence there directly tests the 1864-death claim
  1. Check the Armstrong County Index to Orphans' Court Dockets (1805-1931) for a guardianship filed for minor Dible children, which would pin down a mother's death year precisely

### F3 (w1). Can period land/tax records place the Dible household in Kiskiminetas Township relative to the Heckman and Moore families, and can they push Zephaniah's own tract (if any) into view?

- Jurisdictions: Kiskiminetas Township, Armstrong County, PA
- Record sets:
  - 1861 Pomeroy's Map of Armstrong County -- Kiskiminetas Township sheet (free reproduction) -- https://ancestortracks.com/Armstrong%20Co,%201861/KiskiminetasTp,ArmCo.jpg (1861)
  - Armstrong County, PA land ownership map 1861 (FamilySearch catalog copy) -- https://www.familysearch.org/en/search/catalog/1285138 (1861)
  - PA State Archives RG-17 Warrant Register Images, Armstrong County (free, browsable scans) -- https://www.phmc.state.pa.us/bah/dam/rg/di/r17-88warrantregisters/ArmstrongPages/r17-88ArmstrongPageInterface.htm (1733-1957 (register itself noted incomplete for this county))
  - PA State Archives RG-17 Warrant Register Images, Westmoreland County (free, browsable scans) -- https://www.phmc.state.pa.us/Bah/DAM/rg/di/r17-88WarrantRegisters/WestmorelandPages/r17-88WestmorelandPageInterface.htm (1733-1957)
- Next pulls:
  1. Finish scanning the rest of the same 1861 Kiskiminetas Twp map sheet (only a few grid sections were reviewed this pass) for a 'Z. Dible' or 'Moore' household label
  1. Search the Armstrong and Westmoreland warrant-register scans under surname 'D' for Dible/Dibler original tract acquisitions

### F4 (w1). Was this Dible family actually Lutheran/Reformed (as the research brief assumes) or Presbyterian (as every specific hit found so far shows)?

- Jurisdictions: Kiskiminetas Township, Armstrong County, PA; Salem Township, Westmoreland County, PA
- Record sets:
  - Apollo Presbyterian Church history, Kiskiminetas Twp (names John Dible as elder, 1830s) -- https://www.pa-roots.com/2025/08/13/apollo-presbyterian-church-kiskiminetas-township-armstrong-county-pennsylvania/ (congregation active from earlier 1800s; elder election in the 1830-1837 pastorate)
  - Congruity Presbyterian Church, Salem Twp, Westmoreland Co (baptism index) -- https://www.familysearch.org/library/books/records/item/917629-congruity-presbyterian-church-salem-township-westmoreland-county-pennsylvania-1828-1909 (1828-1909)
  - History of Armstrong County PA, Kiskiminetas Twp chapter -- names Boiling Spring Lutheran Church and Maysville Lutheran Church as active in-township congregations -- https://www.pa-roots.com/2025/08/13/chapter-10-kiskiminetas-history-of-armstrong-county-pennsylvania-part1/ (published county history, covers founding era through ~1914)
  - Armstrong County, Pennsylvania: her people past and present, vol. 2 (full text, free) -- https://archive.org/stream/armstrongcountyp02jhbe_0/armstrongcountyp02jhbe_0_djvu.txt (published 1914)
- Next pulls:
  1. Check Presbyterian Historical Society (Philadelphia, free finding aids) holdings for Apollo Presbyterian Church and Congruity Presbyterian Church session minutes/registers naming Dible, Heckman, or Moore
  1. Identify membership/baptism rolls of Boiling Spring Lutheran Church and Maysville Lutheran Church (both physically in Kiskiminetas Twp) and check for Dible or Heckman entries, since the family's Pennsylvania-German (Dreibelbis-derived Dible surname, Heckman, Allshouse) background makes an earlier Lutheran/Reformed baptism plausible even if the adult generation later joined Presbyterian congregations

### F5 (w2). Is Catherine Heckman or the unnamed 'Mrs. Barbara' (b. 1809, Armstrong Co) the true mother of Zephaniah Dible?

- Jurisdictions: Franklin/Salem Township & Murrysville, Westmoreland Co, PA (Dible birth-family home); Kiskiminetas Township, Armstrong Co, PA (Zephaniah's own household by 1860); no PA state-level vital registration exists this early (predates 1906)
- Record sets:
  - Pennsylvania, Probate Records, 1683-1994 (Armstrong Co Orphans' Court Dockets 1817-1868, index to 1931; Will Books 1805-1918, index to 1961) -- https://www.familysearch.org/en/search/catalog/1999196 (1805-1918)
  - The German church records of Westmoreland County (abstracted Lutheran/Reformed baptism registers) -- https://www.familysearch.org/en/search/catalog/62948 (unspecified, 19th c.)
  - Congruity Presbyterian Church & Apollo Presbyterian Church records (already flagged by wave 1, not yet pulled) --  (1840s-1860s)
  - Westmoreland County, Pennsylvania deeds -- https://www.familysearch.org/en/search/catalog/695617 (1773-1897)
- Next pulls:
  1. Pull Westmoreland Co Orphans' Court docket / guardianship filing for John Dible's estate (d.1866) -- a minor-children guardianship record would name the surviving/deceased mother directly
  1. Browse FamilySearch catalog 62948 (German church records of Westmoreland Co) for a Zephaniah baptism entry c.1835 naming his mother
  1. Get a human/logged-in browser to load wikitree.com/wiki/Dible-18 and /wiki/Dible-6 for their source citations -- both hard-blocked a Playwright headless session with a CAPTCHA wall this round

### F6 (w2). Where are John Dible (d.1866) and his wife/wives actually buried -- Porter Cemetery in Bethel Twp, Armstrong Co, or Murrysville Cemetery, Westmoreland Co (where his mother Susannah Allshouse Dible lies)?

- Jurisdictions: Bethel Township (est. 1878, formerly part of Allegheny Township), Armstrong Co, PA; Murrysville/Franklin Twp, Westmoreland Co, PA
- Record sets:
  - Porter Cemetery, Ridge Rd, Vandergrift -- https://billiongraves.com/cemetery/Porter-Cemetery/85968 (0 records indexed)
  - Murrysville Cemetery (has multiple confirmed Dible burials) -- https://www.findagrave.com/cemetery/204446/murrysville-cemetery (19th-20th c.)
  - Bethel Township, Armstrong Co local history/historical society (township formed 1878 from Allegheny Twp) -- https://www.betheltownshiparmstrong.com/ (n/a)
- Next pulls:
  1. Request an in-person Porter Cemetery (Ridge Rd, Vandergrift/Bethel Twp) survey via Armstrong County GenWeb or a local volunteer, since BillionGraves has zero photographed stones
  1. Pull the full Find A Grave burial list for Murrysville Cemetery to check for an unindexed John Dible or 'Mrs. Barbara Dible' stone alongside the confirmed Susanna Allshouse Dible, Clifford M Dible, Elizabeth Dible (1842-1904), and Helen M McClelland Dible entries

### F7 (w2). Who are Catherine Moore's parents, and did she die in 1864 (Ancestry) or c.1872 (WikiTree)?

- Jurisdictions: Franklin/Salem Township, Westmoreland Co, PA (Catherine's birth, 1839); Kiskiminetas Township, Armstrong Co, PA (married life/death)
- Record sets:
  - Allshouse family webGED Moore entries (confirmed to carry no parent data for Catherine or Hezekiah Moore) -- https://homepages.rootsweb.com/~allshous/Allshouse/wga31.html (n/a)
  - 1850 Westmoreland Co & 1860 Armstrong Co federal census (free at FamilySearch) -- https://www.familysearch.org/search/collection/1401638 (1850, 1860)
  - 'Cooker & Moore' fulling/woolen mill, near the head of the fourth western branch of Rattling Run, Kiskiminetas Twp -- a resident Moore family in the right decade and place, unconfirmed link --  (1820s-1830s per county history)
- Next pulls:
  1. Search 1850 Westmoreland Co census for a Moore household that could be both Catherine's and Hezekiah Moore's (Zephaniah's brother-in-law by his sister Mereyann's 1853 marriage) parent family, testing whether Catherine and Hezekiah are siblings
  1. Search 1860 Kiskiminetas Twp, Armstrong Co census directly for the Zephaniah Dible household to get Catherine's stated age/birthplace and any Moore relatives enumerated nearby
  1. Check Boiling Spring Presbyterian/Lutheran and Maysville Lutheran burial or membership registers for a Catherine Dible death entry

### F8 (w2). Which Lutheran or Reformed congregation, if any, actually served Zephaniah Dible's own household in Kiskiminetas Township (as opposed to the Presbyterian ties documented for his father's/aunt's generation in Westmoreland Co)?

- Jurisdictions: Kiskiminetas Township, Armstrong Co, PA
- Record sets:
  - Boiling Spring Presbyterian Church (organized 1840) / Boiling Spring Lutheran Church (General Synod, shared original building) --  (1840-present, no digitized register located yet)
  - Maysville Lutheran Church (General Synod) --  (no digitized register located yet)
  - FamilySearch Family History Library catalog, Armstrong Co church records (page returned only an Imperva bot-block to automated access this session) -- https://www.familysearch.org/en/wiki/Armstrong_County,_Pennsylvania_Genealogy (unknown)
- Next pulls:
  1. Manually (logged-in, non-automated) browse the FamilySearch Family History Library catalog for Kiskiminetas Twp / Boiling Spring / Maysville Lutheran or Presbyterian church record microfilm
  1. Contact the Bethel Twp/Kiskiminetas Twp historical society or Boiling Spring Presbyterian Church directly for surviving 1850s-60s session/baptism records

### F9 (w2). Which immigrant family does the Dible surname actually descend from -- the Dreibelbis line of Berks County, or the Divelbiss/Devilbiss line via Johan Jacob Diblebiss (1743 Frederick Co, MD - 1820 Harrison City, Westmoreland Co, PA)?

- Jurisdictions: Berks County, PA (Dreibelbis theory); Frederick County, MD and Harrison City/Murrysville, Westmoreland Co, PA (Divelbiss/Devilbiss theory)
- Record sets:
  - Dreibelbis Cousins of America family history (no Divelbiss/Dible connection appears in their own narrative -- weakens this lead) -- https://dreibelbiscousins.org/heritage-of-the-past-and-present/ (n/a)
  - Hans Michael Divelbiss (1748-1819) profile -- https://www.wikitree.com/wiki/Devilbiss-584 (n/a)
  - Hans Michael Divelbiss, FamilySearch -- https://ancestors.familysearch.org/en/LH8L-8X5/hans-michael-divelbiss-1748-1819 (n/a)
  - Westmoreland County, Pennsylvania land ownership map -- https://www.familysearch.org/en/search/catalog/1287088 (n/a)
- Next pulls:
  1. Re-attempt genealogy.com/ftm/p/r/e/Kim-M-Preston/GENE2-0006.html and the WorldConnect DB 554774 ID I23 page with an authenticated/human browser session -- both returned 403 or a JS shell to every automated method tried this session
  1. Pull Westmoreland County PA tax and deed records for the Harrison City vicinity, 1770s-1802, to look for the actual spelling transition Diblebiss/Divelbiss -> Dible in the county's own record, which would settle the immigrant question far better than any compiled tree

### F10 (w3). Who were Zephaniah Dible's actual parents -- John Albert Dibler/Dible + Catherine Heckman, John Dible + 'Mrs. Barbara,' or (per WikiTree's unlinked tree) parents still wholly unknown?

- Jurisdictions: Westmoreland County, PA (Zephaniah's 1836 birth and 1859 marriage) -> Kiskiminetas Township, Armstrong County, PA (household by 1860)
- Record sets:
  - WikiTree Zephaniah Dible profile (Dible-18) -- https://www.wikitree.com/wiki/Dible-18 (as edited through 2025)
  - WikiTree John Dible profile (Dible-6) -- https://www.wikitree.com/wiki/Dible-6 (as edited through 2016-2025)
  - Westmoreland County Register of Wills, Will Books 1773-1917 / Will Indexes 1773-1918 -- https://www.westmorelandcountypa.gov/333/Register-of-Wills (1773-1917)
  - Dible family paper, Families by Velma Parsons -- https://www.familiesbyvelmaparsons.com/pdfs/DIBLE.pdf (compiled)
  - Catherine Heckman, FamilySearch public tree index -- https://ancestors.familysearch.org/en/L6LS-FV3/catherine-heckman-1805-1846 (index)
- Next pulls:
  1. Pull the actual 24 Mar 1859 Westmoreland County marriage record for Zephaniah Dible x Catherine Moore (exact date now known) to see whether it names Zephaniah's father
  1. Search for Jacob Dible Sr.'s probated will (d. 9 Apr 1872, Westmoreland Co.) in the will-book index cited on his son John's WikiTree page, to see whether Zephaniah or John's children appear as heirs
  1. Resolve the WikiTree 'George F Dible' duplicate-profile confusion (1828-1904 Murrysville vs 1841-1916 Iowa) since it is corrupting automated sibling inference for Zephaniah's generation
  1. Attempt a logged-in human WikiTree session on Dible-18/Dible-6 to read the underlying source citations behind the infobox (still unreadable via automation)

### F11 (w3). Who were Catherine Moore's parents, and was she kin to Hezekiah Moore, who married Zephaniah's sister Mereyann Dible in 1853?

- Jurisdictions: Westmoreland County, PA
- Record sets:
  - Old Marriage Records, Westmoreland County PA (small collected sample, not exhaustive) -- https://www.pa-roots.com/westmoreland/data/oldmarriagerecords.html (1778-1863)
  - WikiTree Moore genealogy landing page -- https://www.wikitree.com/genealogy/MOORE (ongoing)
  - Westmoreland County Clerk of Courts / Orphans' Court marriage records -- https://www.westmorelandcountypa.gov/ (1852-1855+)
- Next pulls:
  1. Search Westmoreland County clerk's original marriage record for the exact 24 Mar 1859 Zephaniah Dible x Catherine Moore entry (not found in the small pa-roots sample index, which is not comprehensive)
  1. Identify Hezekiah Moore's own WikiTree/FamilySearch profile directly (not found via search this session) to check for shared parents or a documented sibling/cousin relationship to Catherine Moore
  1. Check Westmoreland County Orphans' Court guardianship records for any Moore minor children in the 1840s-1850s that would name a father

### F12 (w3). Which Lutheran/Reformed congregations in Armstrong County have primary registers naming Dible/Dibler, Heckman, or Kepple, and where are those registers archived today?

- Jurisdictions: Kiskiminetas Township / Apollo Borough, Parks Township, Bethel Township -- all Armstrong County, PA
- Record sets:
  - First Evangelical Lutheran Church of Apollo (org. 1859, in old Kiskiminetas Twp) -- https://apollopahistory.com/apollo-history/churches/lutheran-church/ (1859-present)
  - Bethel Evangelical Lutheran Church, Ford City (org. 1846, 2nd charter 1848) -- https://www.pa-roots.com/2025/08/12/beers-historical-record-chapter-24-bethel-township/ (1846-present)
  - Highfield / St. Paul Evangelical Lutheran Church Cemetery, Parks Twp -- https://www.findagrave.com/cemetery/2145715/highfield-lutheran-church-cemetery (burials indexed 19th-20th c.)
  - St. Michael's Lutheran Church Cemetery, Brick Church, Armstrong Co. -- https://www.findagrave.com/cemetery/163844/saint-michael (burials indexed 19th-20th c.)
  - Tri-Synod Lutheran Archives (western PA congregational records), Thiel College -- https://www.lutheranarchives.org/collections/lutheranism-in-america-1748-1988 (1748-1988 holdings)
- Next pulls:
  1. Contact/search Tri-Synod Archives at Thiel College, Greenville PA for original baptismal/communicant registers of Bethel Lutheran (Ford City) and First Ev. Lutheran of Apollo, looking for Dible/Dibler/Heckman entries
  1. Check whether First Lutheran Church of Apollo (modern successor, firstlutheranapollo.com) still holds pre-1900 registers locally
  1. Re-check the 1883 County History's Kiskiminetas chapter's Boiling Spring Presbyterian/Lutheran and Maysville Lutheran congregations against any surviving register (no Dible/Heckman/Moore names found in the narrative text itself, only in the Apollo and Bethel chapters)

### F13 (w3). Where exactly is the Dible family buried in Armstrong/Westmoreland County, and does Porter Cemetery hold more than the one indexed Dible headstone?

- Jurisdictions: Parks Township, Armstrong County, PA (Porter Cemetery, corrected from the prior wave's Bethel Twp guess); Spring Church, Armstrong Co. (Fairview Cemetery); Murrysville, Westmoreland Co.
- Record sets:
  - Porter Cemetery, Parks Township, Armstrong Co. -- https://www.findagrave.com/cemetery/45817/porter-cemetery (only 20 memorials indexed, 1 Dible)
  - Fairview Cemetery, Spring Church, Armstrong Co. -- https://www.findagrave.com/memorial/135345825/samuel-dible (19th-20th c.)
  - Murrysville Cemetery (Beulah Cemetery), Westmoreland Co. -- https://www.pa-roots.com/westmoreland/townships/franklin/beulahcemetery.html (19th-20th c.)
- Next pulls:
  1. Request or search BillionGraves/local historical-society transcriptions of Porter Cemetery for any unindexed John Dible, Jacob Dible Sr., or Zephaniah headstones beyond the one Catherine Dible (1775-1816) memorial found
  1. Check Beulah/Murrysville Cemetery, Westmoreland Co. directly for John Dible (1805-1866) and Catherine Heckman burials

### F14 (w3). How far back can the Allshouse (Zephaniah's grandmother's family) immigrant line be verified, and where do the German-origin claims lead?

- Jurisdictions: Easton, Northampton County, PA; Tinicum Township, Bucks County, PA; colonial Wuerttemberg/Bavaria and Saarland, Germany
- Record sets:
  - Ship Judith 1748 Philadelphia oath-of-allegiance list (Rupp 1876 compilation) -- http://www.searchforancestors.com/passengerlists/judith1748.html (1748)
  - Henry "Althaus" Allshouse FindAGrave (will text, Easton Cemetery) -- https://www.findagrave.com/memorial/137728961/henry-allshouse (1725-1803)
  - WikiTree John Dible ancestor chain (Allshouse/Truxell/Driessel/Trachsel) -- https://www.wikitree.com/wiki/Dible-6 (compiled, reaching 1680s Germany)
  - Northampton County, PA Register of Wills (Henry Allshouse Sr., d. 1803) -- https://www.norcopa.net/166/Register-of-Wills-Orphans-Court (1803 probate)
- Next pulls:
  1. Pull the original Northampton County probate file for Henry Allshouse Sr. (will dated 10 Mar 1803) to verify the will text quoted on FindAGrave
  1. Search First Reformed Church of Easton burial/baptismal registers (his original interment site before removal to Easton Cemetery)
  1. If pursued further, search parish records for Althausen (Bad Kissingen district, Bavaria) and Wolfersheim (Saarpfalz-Kreis, Saarland) for pre-emigration baptisms of Henry Allshouse and John Michael Troxell -- both compiled-tier claims only, unverified against any German archive this session

### F15 (w3). Which immigrant family does 'Dible/Dibler' actually descend from -- and can the Heckman immigrant claim (Albrecht Heckman, ship 'Beulah,' 1753) be verified at all?

- Jurisdictions: Lancaster County, PA (Philip Heckman's 1770 birthplace); Berks Co. PA (Dreibelbis); Westmoreland/Armstrong Co. PA and Frederick Co., MD (Divelbiss/Devilbiss)
- Record sets:
  - Palatine Ships Passenger Lists 1727-1808 (Strassburger/Hinke mirrors) -- https://www.olivetreegenealogy.com/ships/palship_list.shtml (1727-1808, no 'Beulah' found)
  - Johan Jacob Dreibelbis Family of America (Google Books) -- https://books.google.com/books/about/John_Jacob_Dreibelbis_Family_of_America.html?id=ODgZAQAAMAAJ (compiled)
  - Johan Jacob Devilbiss, Ancestry (JS-walled, unverified this session) -- https://www.ancestry.com/genealogy/records/johan-jacob-devilbiss-24-btj1x (paywalled/behind login, 1743-1820)
- Next pulls:
  1. Search Lancaster County PA German Lutheran/Reformed baptismal registers of the 1750s-1770s for an Albrecht/Heckman family, since Philip Heckman's own 1770 birth is documented there, before crediting any specific ship
  1. Obtain non-paywalled access (library-edition Ancestry, or a Devilbiss family association site) to verify Hans Michael Divelbiss's immigration record independent of the JS-shell page hit this session
  1. Re-run the Dreibelbis-vs-Divelbiss comparison against any Dible/Dibler Y-DNA or documentary link -- none found either direction yet

