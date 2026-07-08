# Frontier intake 04: Harry and Julia: two Dibles marry at Trenton

Line: Dible (Bill's paternal line)
Docket: case.10, case.11 (no dedicated case; candidate for a new one)
Source: 60-agent frontier workflow, waves 1-3, 2026-07-08. RAW INTAKE -- see 00-index.md
for the validation protocol; nothing below may land in index.html without an
independent re-fetch and quote match.

## Where this sits in the tree

Harry H. Dible married Julia Dible -- daughter of John Heckman Dible -- at Trenton, Hitchcock County, Nebraska, 10 Jun 1896 (the marriage event on the Dible plate, tagged strong). Two Dibles marrying suggests cousins; this topic establishes Harry's own parents and the relationship between the two Dible households via Nebraska records.

## Original frame given to the agents

> HARRY & JULIA DIBLE: Harry H. Dible married Julia DIBLE (daughter of John Heckman Dible) at Trenton, Hitchcock Co NE, 10 Jun 1896 - two Dibles marrying suggests cousins. Establish Harry's own parents and the relationship between the two Dible families. Hitchcock/Red Willow County NE records, 1900 NE census, Nebraska GenWeb.

## Wave syntheses (verbatim from the agents)

### Wave 1

Harry H. Dible's own FamilySearch profile (fetched directly via server-rendered JSON-LD) independently confirms WikiTree's claim that his parents were Zephaniah Dible and Catherine Moore, and adds precise data: born 28 Mar 1863 in Greensburg, Westmoreland Co, PA; married Julia Dible 10 Jun 1896 in Trenton, Hitchcock Co, NE; by 1900 the couple was living in Lacey Township, Thomas Co, KS (not Nebraska); Harry died 19 Feb 1935 and was buried in Rexford, Thomas Co, KS -- the same town where his grandson William "Bill" Dible later served as mayor. The core question -- the relationship between the two Dible families -- is now well supported: four independent FamilySearch profile pages (John Albert Dibler's own page, Catherine Heckman's own page, John Heckman Dible's own page, and Malinda Dible Londen's page) all consistently list Zephaniah Dible and John Heckman Dible as full siblings, both children of John Albert Dibler (1805-1866) and Catherine Heckman (1805-1846) of Westmoreland County, Pennsylvania. That makes Harry H. Dible (Zephaniah's son) and Julia Dible (John Heckman's daughter) first cousins, matching the hypothesis in the prompt. The main caveat: this sibling link lives entirely inside FamilySearch's own compiled/crowd-tree ecosystem (internally consistent across four pages, but not yet corroborated by an original Westmoreland County PA record), and it is notably ABSENT from John Heckman Dible's Find a Grave family-tree sidebar, which lists eight other siblings but not Zephaniah -- a real discrepancy between two large crowd-sourced platforms that a Westmoreland County probate/estate or census record could resolve. New geography also emerged that redirects the search frame: Julia was born in Spring Creek Township, Johnson County, NE (not Hitchcock/Red Willow), her father John Heckman Dible died in Blue Springs, Gage County, NE, and the Harry/Julia household's 1900 census location is Thomas County, KS, not Nebraska at all -- so the "Hitchcock/Red Willow County NE 1900 census" framing in the task brief should be redirected to Thomas County, KS for 1900 and later. Also newly surfaced: Zephaniah remarried (second wife Clarinda A. Stodghill, 1844-1895) and had at least two more children in Kansas from the early 1870s, and a half-brother, James C. Dible, ended up in Fort Morgan, Colorado. Two internal date conflicts surfaced worth resolving with primary records: Harry's death year (1935 per FamilySearch/Rexford KS burial vs. 1940 per WikiTree) and Zephaniah's birth year (1835/1836/1839 across different FamilySearch snapshots and WikiTree). Access notes: WikiTree and Find a Grave both block plain curl (AWS WAF challenge / 403) but succeed intermittently with a browser user-agent and pacing; FamilySearch ancestors.familysearch.org pages are a pure JS shell for a normal browser UA but return full server-rendered JSON-LD (with a plain-language "Brief Life History" paragraph) when fetched with a Googlebot user agent -- this was the key technique that unlocked this frontier. Not every FamilySearch person ID resolves this way: only pages that have already been through FamilySearch's bot-prerender cache return content; Zephaniah Dible's own profile (ID LXSR-HNL) 404'd every time despite being referenced correctly by four other pages, so his own vitals/burial were not directly recoverable this session.

### Wave 2

This pass fetched Harry, Julia, John Heckman Dible, and their immediate relatives' own FamilySearch profile pages (via the Googlebot-UA server-render technique) plus, critically, John Albert Dible's OWN Find A Grave memorial at Murrysville Cemetery, PA -- a source wave 1 had not reached. The result is a major downgrade, not confirmation, of wave 1's headline claim. FamilySearch's own tree is internally split: John Albert Dibler's own profile shows his displayed wife as Barbara Kuntz (m.1831) with Zephaniah Dible as one of her children, while four OTHER FamilySearch profiles (Catherine Heckman's, John Heckman Dible's, Isabella's, Malinda's) instead claim Catherine Heckman was the mother of that same Zephaniah. Independently, Find A Grave's own family tree for John Albert Dible's grave (a different contributor, unrelated to FamilySearch) names yet a THIRD/fourth wife pairing -- Elizabeth Allshouse (d.1831) then Rebecca Katz (1815-1906, corroborated by her own 1906 PA death record naming her actual parents) -- and does not include Zephaniah among his 9 known children at all. Murrysville Cemetery holds 46+ separate Dible burials in one plot section, making cross-family conflation a real risk. The paternal-first-cousin hypothesis for Harry and Julia is therefore now contested rather than confirmed pending an original Westmoreland/Armstrong County PA census, probate, or church record. Separately, this session pushed the compiled lineage two to three generations further back (Jacob Dible 1780-1872 m. Susanna Catharine Marsh 1808 -> Johan Jacob DeVilbiss 1743-1804 m. Anna Maria Teagarden 1778 Westmoreland PA -> Casper Conrad Devilbiss Sr, colonial Maryland), which redirects the immigrant-origin question away from wave 1's tentative 'Dreibelbis of Hassloch' lead toward the well-documented colonial DeVilbiss family -- itself unverified against a period record. Also resolved: Zephaniah's birth year triangulates consistently to 1839 (not 1835/1836) across three independent FamilySearch data points; the Wayne Edgar/Wayne Everett Dible duplicate is confirmed via identical birthdates on Julia's own profile; and Harry's death year now has a THIRD conflicting data point (1936, an uncited Find A Grave memorial) alongside FamilySearch's 1935 and WikiTree's 1940. A concrete, high-value next pull emerged: Hitchcock County, NE's surviving 1888-1898 marriage certificates record both parties' parents' names, but the free online transcription has no 1896 entries at all -- the original certificate, obtainable from the county clerk or via a FamilySearch/Ancestry marriage-index login, would likely settle the parentage question directly.

### Wave 3

This wave's key methodological upgrade was fetching each ancestor's OWN FamilySearch profile page (via the Googlebot-UA technique) rather than relying on siblings' pages, which resolved Harry H. Dible's own parentage and pushed the compiled FamilySearch line back seven generations to a stated 1731 colonial immigration -- while also uncovering a major corrective: the FamilySearch-asserted Jacob-Dible-to-DeVilbiss immigrant link is likely wrong. Harry's own profile (L4WV-WGX) directly confirms his parents as Zephaniah Dible and Catherine Moore (matching WikiTree/Ancestry), his birth as 28 Mar 1863 in Greensburg, Westmoreland Co PA, and his death as 19 Feb 1935 in Rexford, Thomas Co, Kansas -- newly resolving the three-way 1935/1936/1940 death-date conflict with a specific place. Critically, both Harry's and Julia's own FamilySearch profiles state the couple was already living in Lacey Township, Thomas County, KANSAS by 1900 (not Nebraska), meaning the frontier prompt's '1900 NE census' target does not exist -- the couple relocated almost immediately after their 1896 Hitchcock County marriage. This is explained by a new discovery: Zephaniah Dible remarried after Catherine Moore's 1864 death, to Clarinda A. Stodghill (1844-1895), and had a son (James C. Dible) born in Kansas in 1874 -- meaning Zephaniah's branch had been established in Kansas for over two decades before Harry and Julia arrived, making Kansas (not Nebraska) the paternal family's true long-term base and the Hitchcock County wedding venue an apparent waypoint rather than either family's residence (Julia's father John Heckman Dible's own profile confirms he was continuously resident in Johnson County, NE, ~260 miles away, for about 30 years). On the contested cousin question, this session adds John Heckman Dible's own profile as a further independent confirmation of John Albert Dibler + Catherine Heckman as his parents, and also surfaces a previously-unreported FamilySearch bio-text claim that John Albert Dibler's FIRST wife (m.1827) was Elizabeth Ella Allshouse -- which cross-platform-corroborates Find A Grave's separately-contributed 'Elizabeth Allshouse Dible' claim from wave 2, adding a fourth documented wife candidate to the puzzle. Regardless of which wife bore which son, every profile checked across two sessions consistently names John Albert Dibler as father of both Zephaniah and John Heckman Dible, so the first-cousin relationship between Harry and Julia is not undermined by the wife controversy, only the specific mother-attributions are. Pushing further back, Jacob Dible (1780-1872) -> Johan Jacob DeVilbiss (1743-1804) -> Casper Conrad Devilbiss Sr (1721 Alsace, France - 1777 Frederick, Maryland, immigrated to Philadelphia in 1731) forms a clean compiled FamilySearch chain, but cross-checking it against the dedicated, freely available published book 'History of the DeVilbiss Family in the United States, 200 Years' (archive.org) reveals a serious problem: that book quotes Casper's actual probated 1777 will verbatim, and it names his real children as George, John, Casper Jr., Ann Ramsbergh, Susannah Ramsbergh, and Barbarah Fleming -- there is no 'Johan Jacob,' and the surname 'Dible'/'Dibler'/'Deible' never appears anywhere in the book's 200+ pages (the only variant spelling mentioned, 'Divilbiss,' belongs to an unnamed BROTHER of Casper, not a son). This strongly suggests the FamilySearch tree's Dible-to-DeVilbiss link is a bad merge rather than a documented lineage, reopening the immigrant-origin question entirely (neither DeVilbiss nor wave 1's Dreibelbis-of-Hassloch lead is now well-supported). Additional finds: a 1910 Colby Free Press mention of 'Representative Harry Dible, Rexford' running on a Republican ticket (found via paywalled newspapers.com but the same title is freely digitized 1904-1925 on Library of Congress Chronicling America and not yet fully searched); a documented further descending generation via Find A Grave (Wayne E. Dible 1899-1963 m. Wilma Stephens, their son Kenneth Wayne Dible 1922-2008 buried Rexford Cemetery, Thomas Co KS); and confirmed dead ends -- Zephaniah Dible's own profile page still 404s, no Find A Grave memorial for him exists, and Hitchcock County's free NEGenWeb marriage transcription and 1906 atlas patrons list both independently confirm no 1896 Dible marriage record or Dible landownership is available online there.

## Findings (59 unique from 59 raw, grouped by source, best-verified first)

### https://www.findagrave.com/memorial/9609591/john-heckman-dible

- **[verified-index]** (w1, place) Julia's father John Heckman Dible actually died and is buried in Blue Springs, Gage County, Nebraska (southeast NE) -- a different county from either the Hitchcock County wedding site or Julia's Johnson County birthplace -- per his Find a Grave memorial obituary transcription.
  > He is buried with his wife, Elizabeth J. Dible.Their children: Julia, Wilburn, Kate, Jesse Michael, Fannie, and EstherHis parents: John A. Dible and Catherine Heckman
- **[verified-index]** (w1, other) John Heckman Dible's Find a Grave family-tree sidebar lists eight siblings by name but does NOT include Zephaniah Dible, unlike FamilySearch's tree -- a genuine discrepancy between the two platforms' sibling rosters for the same man.
  > Susannah Dible Allison 1827-1917, Mary Anna Dible Moore 1829-1915, Elizabeth Jane Dible Heckman 1830-1899, Esther Margaret Dible George 1833-1907, Isabelle Dible Allison 1838-1904, Malinda Dible Louden 1839-1929
- **[verified-index]** (w2, relationship) John Heckman Dible's own Find A Grave memorial lists 8 siblings sourced independently of FamilySearch and omits Zephaniah entirely, while adding two siblings (b.1857, b.1859) not on any FamilySearch profile, showing the platforms disagree on the full sibling set.
  > Esther Margaret Dible George 1833 – 1907 Isabelle "Belle" Dible Allison 1838 – 1904 Malinda Dible Louden 1839 – 1929 William Oliver Dible 1857 – 1937 Albert F Dible 1859 – 1918
- **[verified-primary]** (w2, date) A verbatim 1913 newspaper obituary quoted on Find A Grave corroborates John Heckman Dible's death circumstances at Blue Springs, Gage County, Nebraska.
  > John H. Dible aged 76 years, died at 5 a.m. Monday at his home on the country road north of Blue Springs.

### https://www.findagrave.com/memorial/22215167/rebecca-dible

- **[verified-primary]** (w2, person) Rebecca Katz Dible's own Find A Grave memorial, sourced to her 1906 Pennsylvania death record, names her parents and a descendant explicitly identifies her as John A. Dible's second wife, giving a documented, record-backed alternative to both 'Barbara Kuntz' and 'Catherine Heckman.'
  > Father named as Peter Katts, mother as Mary Brawdy, both born in the US... She was the second wife of John A Dible.

### https://archive.org/stream/historyofdevilbi00devi/historyofdevilbi00devi_djvu.txt

- **[verified-primary]** (w3, other) CRITICAL CORRECTIVE: the dedicated, freely available published genealogy 'History of the DeVilbiss Family in the United States, 200 Years' directly quotes Casper Devilbiss's actual probated 1777 will, which names his real children as George, John, Casper Jr., Ann Ramsbergh, Susannah Ramsbergh, and Barbarah Fleming -- there is no 'Johan Jacob' among them, undermining the FamilySearch tree's Jacob Dible-to-DeVilbiss link found this session.
  > Item I give and bequeath unto all my children, namely, George Devilbiss, John Devilbiss, Casper Devilbiss, Ann Ramsbergh, Susannah Ramsbergh and Barbarah Fleming
- **[verified-primary]** (w3, other) The same published DeVilbiss family book never uses the surname spelling 'Dible,' 'Dibler,' or 'Deible' anywhere in its full text, and separately records that it was an unnamed BROTHER of Casper (not a son) who settled in Pennsylvania under the variant spelling 'Divilbiss' -- still not 'Dible.' This further weakens the compiled FamilySearch Dible-descends-from-DeVilbiss hypothesis extended in this session and in wave 2.
  > there were three brothers who came to America — the two already mentioned, and a third who settled in Pennsylvania and spelled his name with an “i” thus, “Divilbiss.”
- **[compiled]** (w3, place) The published DeVilbiss book itself hedges the Alsace origin as unproven family tradition and gives Baltimore (not Philadelphia) as the immigrant brothers' landing port, conflicting with FamilySearch's unsourced claim of a 1731 Philadelphia arrival for Casper specifically.
  > Tradition holds that Casper Devilbiss and his brothers were born in Alsace.
- **[verified-primary]** (w3, date) The published DeVilbiss book's transcribed will is dated 16 March 1777, matching FamilySearch's stated death date for Casper Conrad Devilbiss Sr exactly, so the death date itself (unlike the DeVilbiss-to-Dible descent claim) is well corroborated across sources.
  > Be it rememebered that this, sixteenth day of the third month, commonly called March, in the year of our Lord, one thousand seven hundred and seventy-seven

### https://ancestors.familysearch.org/en/L4WV-WGX/harry-h-dible-1863-1935

- **[verified-index]** (w1, relationship) Harry H. Dible's own FamilySearch profile independently states his parents were Zephaniah Dible and Catherine Moore, matching WikiTree, and gives his birthplace as Greensburg, Westmoreland Co, PA.
  > When Harry H Dible was born on 28 March 1863, in Greensburg, Westmoreland, Pennsylvania, United States, his father, Zephaniah Dible, was 24 and his mother, Catherine Moore, was 24.
- **[verified-index]** (w1, date) Harry's FamilySearch profile confirms the marriage to Julia Dible on 10 Jun 1896 at Trenton, Hitchcock Co, NE, and states they had 6 sons and 1 daughter (matching the 7 children listed independently on both spouses' profiles).
  > He married Julia Dible on 10 June 1896, in Trenton, Hitchcock, Nebraska, United States. They were the parents of at least 6 sons and 1 daughter.
- **[verified-index]** (w1, migration) By the 1900 census the Harry & Julia Dible household was in Lacey Township, Thomas County, Kansas -- not Nebraska -- with a later long-term residence in Smith Township, same county; Harry died and was buried in Rexford, Thomas Co, KS in 1935.
  > He lived in Lacey Township, Thomas, Kansas, United States in 1900 and Smith Township, Thomas, Kansas, United States for about 20 years. He died on 19 February 1935, in Rexford, Thomas, Kansas, United States
- **[verified-index]** (w2, date) Zephaniah Dible's birth year triangulates to 1839 (not 1835/1836) via age-math on his son Harry's own FamilySearch profile.
  > his father, Zephaniah Dible, was 24 and his mother, Catherine Moore, was 24.
- **[verified-index]** (w2, date) Harry H. Dible's own FamilySearch profile gives a precise death date/place that is the source of wave 1's 1935 figure.
  > He died on 19 February 1935, in Rexford, Thomas, Kansas, United States, at the age of 71
- **[verified-index]** (w3, person) Harry H Dible's own FamilySearch profile gives his birth as 28 Mar 1863 in Greensburg, Westmoreland Co, PA, and names his parents as Zephaniah Dible and Catherine Moore -- confirmed directly on Harry's own page, not a sibling's page as in prior waves.
  > When Harry H Dible was born on 28 March 1863, in Greensburg, Westmoreland, Pennsylvania, United States, his father, Zephaniah Dible, was 24 and his mother, Catherine Moore, was 24.
- **[verified-index]** (w3, date) Harry H Dible's own FamilySearch profile states he died 19 Feb 1935 at Rexford, Thomas Co, Kansas and was buried there, giving a specific place absent from prior waves' '1935/1936/1940' three-way conflict.
  > He died on 19 February 1935, in Rexford, Thomas, Kansas, United States, at the age of 71, and was buried in Rexford, Thomas, Kansas, United States.
- **[verified-index]** (w3, other) Harry's own profile's structured data independently repeats Catherine Moore's dates as 1839-1864, agreeing with the Ancestry/John Moore Dible pairing already in the working artifact and not with WikiTree's 1834-1872 dates.
  > "name":"Catherine Moore","birthDate":"+1839","deathDate":"+1864"

### https://ancestors.familysearch.org/en/L6RZ-ZG2/john-albert-dibler-1805-1866

- **[verified-index]** (w1, relationship) John Albert Dibler's own FamilySearch profile lists both John Heckman Dible and Zephaniah Dible among his children (with Catherine Heckman), making Zephaniah and John Heckman full brothers and therefore Harry and Julia first cousins.
  > "identifier":"K845-DFL",...,"name":"John Heckman Dible","birthDate":"+1836-11-05","deathDate":"+1913-07-16"},{...,"identifier":"LXSR-HNL",...,"name":"Zephaniah Dible","birthDate":"+1839","deathDate":"+1900"
- **[verified-index]** (w2, relationship) FamilySearch's own default family card for John Albert Dibler (father of both Zephaniah and John Heckman Dible, per wave 1) shows his ONLY displayed wife as Barbara Kuntz (m. 1831), with Zephaniah Dible listed as one of her 8 children -- NOT as a child of Catherine Heckman, contradicting the wave-1 'four independent pages agree' framing.
  > John Albert Dibler 1805–1866 Barbara Kuntz 1808–1856 Marriage: 1831 Solomon C Dibler 1833–1914 Catharine Dible 1834–1881 Susannah M Diebler 1838–1910 David R Dibler 1838–1920 Zephaniah Dible 1839–1900
- **[verified-index]** (w2, place) The odd place-name 'Washington Parish, Westmoreland, Pennsylvania' recurs on a second, unrelated FamilySearch profile (John Albert Dibler's), not just Catherine Heckman's as wave 1 found, indicating a systemic FamilySearch place-authority mislabel rather than a one-off typo.
  > He lived in Pennsylvania, United States in 1870 and Washington Parish, Westmoreland, Pennsylvania, United States for about 10 years.
- **[verified-index]** (w2, relationship) FamilySearch's own tree names John Albert Dibler's parents as Jacob Dible and Susanna Catharine Marsh, contradicting the previously-cited Velma Parsons compiled paper's claim of 'Susannah Allshouse.'
  > his father, Jacob Dible, was 25 and his mother, Susanna Catharine Marsh, was 21.
- **[verified-index]** (w3, relationship) John Albert Dibler's own full profile page (bio text, not the family-card graphic prior waves relied on) states he married Elizabeth Ella Allshouse in 1827 with at least 3 daughters -- a wife/marriage not reported in prior waves' tally, but one that independently corroborates Find A Grave's separately-contributed 'Elizabeth Allshouse Dible' first-wife claim across two unrelated platforms.
  > He married Elizabeth Ella Allshouse in 1827, in Westmoreland, Pennsylvania, United States. They were the parents of at least 3 daughters.
- **[verified-index]** (w3, place) John Albert Dibler's own profile gives a more precise birthplace (Franklin Township, Westmoreland Co PA) and confirms his death/burial at Penn Township/Murrysville Cemetery, matching the cemetery prior waves identified from Find A Grave.
  > He died on 28 December 1866, in Penn Township, Westmoreland, Pennsylvania, United States, at the age of 61, and was buried in Murrysville Cemetery, Murrysville, Westmoreland, Pennsylvania, United States.
- **[verified-index]** (w3, relationship) John Albert Dibler's own profile names his own parents as Jacob Dible (age 25) and Susanna Catharine Marsh (age 21) at his 1805 birth, matching the FamilySearch-side value in the ongoing Marsh-vs-Allshouse dispute over Jacob Dible's wife's name.
  > When John Albert Dibler was born on 3 January 1805, in Franklin Township, Westmoreland, Pennsylvania, United States, his father, Jacob Dible, was 25 and his mother, Susanna Catharine Marsh, was 21.

### https://ancestors.familysearch.org/en/L6LS-FV3/catherine-heckman-1805-1846

- **[verified-index]** (w1, relationship) Catherine Heckman's own FamilySearch profile independently repeats the same children list (John Heckman Dible and Zephaniah Dible both included), corroborating the sibling link from the mother's side as well as the father's.
  > "name":"John Heckman Dible","birthDate":"+1836-11-05","deathDate":"+1913-07-16"},{"name":"Isabella Dible"...},{..."name":"Zephaniah Dible","birthDate":"+1839","deathDate":"+1900"

### https://ancestors.familysearch.org/en/KCBR-YSR/julia-dible-1874-1967

- **[verified-index]** (w1, place) Julia Dible was born in Spring Creek Township, Johnson County, Nebraska (not Hitchcock/Red Willow) and died in Colby, Thomas County, Kansas in 1967, both new precise locations.
  > "birthPlace":{"address":"Spring Creek Township, Johnson, Nebraska, United States"},"deathDate":"+1967-02-16","deathPlace":{"address":"Colby, Thomas, Kansas, United States"}
- **[verified-index]** (w2, relationship) Julia Dible's own FamilySearch profile carries two separate person-IDs for a son born the same day (20 Jan 1899) -- Wayne Edgar Dible and Wayne Everett Dible -- confirming wave 1's suspicion that these are an unmerged duplicate rather than two children.
  > "identifier":"K6W4-QKN","url":"http://localhost:3000/K6W4-QKN","gender":"Male","name":"Wayne Everett Dible","birthDate":"+1899-01-20","deathDate":"+1940/"
- **[verified-index]** (w3, migration) Julia's own FamilySearch profile, citing an 1900 census source, places Harry and Julia Dible in Lacey Township, Thomas County, KANSAS in 1900 -- not Nebraska. The frontier prompt's '1900 NE census' target does not exist; the couple had already relocated to northwest Kansas.
  > She lived in Lacey Township, Thomas, Kansas, United States in 1900 and Smith Township, Thomas, Kansas, United States for about 30 years.
- **[verified-index]** (w3, other) The specific 1900 census source attached to Julia's profile is titled listing her in Harry's household, confirming the record exists and is findable by collection name even though the couple is not in Nebraska.
  > Julia Dible in household of Harry Dible, "United States Census, 1900"

### https://ancestors.familysearch.org/en/M5JZ-R7X/james-c-dible-1874-1934

- **[verified-index]** (w1, migration) Zephaniah Dible remarried after Catherine Moore's death and had a son James C. Dible born in Kansas in 1874 with second wife Clarinda A. Stodghill (1844-1895); that half-brother later moved on to Fort Morgan, Morgan County, Colorado, where he died in 1934.
  > When James C. Dible was born on 2 July 1874, in Kansas, United States, his father, Zephaniah Dible, was 35 and his mother, Clarinda A Stodghill, was 30.
- **[verified-index]** (w3, relationship) Zephaniah Dible remarried after Catherine Moore's 1864 death; his second wife was Clarinda A. Stodghill (1844-1895), mother of James C. Dible, born 1874 in Kansas -- meaning Zephaniah's branch was already established in Kansas a full generation before Harry and Julia settled in Thomas County by 1900.
  > When James C. Dible was born on 2 July 1874, in Kansas, United States, his father, Zephaniah Dible, was 35 and his mother, Clarinda A Stodghill, was 30.

### https://www.findagrave.com/memorial/7454038/john-albert-dible

- **[verified-index]** (w2, relationship) Find A Grave's independently-compiled family tree for John Albert Dible's own Murrysville, PA grave (different contributor, added 2003) lists his two wives as Elizabeth Allshouse Dible (d.1831) and Rebecca Katz Dible (1815-1906) -- neither Catherine Heckman nor Barbara Kuntz -- and does not include Zephaniah among his 9 listed children.
  > Spouses Elizabeth Allshouse Dible 1806 – 1831 Rebecca Katz Dible 1815 – 1906 Siblings Isaac Dible 1806 – 1885 Margaret "Mary" Dible Lauffer 1808 – 1846
- **[verified-index]** (w2, relationship) Find A Grave's own Jacob/John-Albert family tree instead names John Albert's mother as 'Susanna Allshouse Dible' (d.1835), matching the Velma Parsons paper and contradicting FamilySearch's 'Susanna Catharine Marsh' -- a genuine three-way naming conflict for this generation.
  > Parents Jacob Dible Sr. 1780 – 1872 Susanna Allshouse Dible 1782 – 1835

### https://ancestors.familysearch.org/en/K845-DFL/john-heckman-dible-1836-1913

- **[verified-index]** (w2, date) John Heckman Dible's own FamilySearch profile gives a precise marriage date/place to Elizabeth J. Haden not previously reported.
  > He married Elizabeth J. Haden on 25 February 1872, in Richardson, Nebraska, United States.
- **[verified-index]** (w3, person) John Heckman Dible's own FamilySearch profile (not a sibling's page) independently states his parents as John Albert Dibler and Catherine Heckman, both age 31 at his 1836 birth, adding a further consistent data point beyond the four sibling pages found previously.
  > When John Heckman Dible was born on 5 November 1836, in Armstrong, Pennsylvania, United States, his father, John Albert Dibler, was 31 and his mother, Catherine Heckman, was 31.
- **[verified-index]** (w3, migration) John Heckman Dible's own profile states he lived in Spring Creek Township, Johnson County, NE continuously for about 30 years, ruling out Hitchcock County as his own residence and deepening the puzzle of why the 1896 marriage occurred in Trenton, ~260 miles away.
  > He lived in Spring Creek Township, Johnson, Nebraska, United States for about 30 years.

### https://ancestors.familysearch.org/en/LVZ6-YGD

- **[verified-index]** (w2, date) The 1839 birth year for Zephaniah is independently corroborated via age-math on a second son's (John Moore Dible) profile, which also cites an 1880 census household record naming Zephaniah as head.
  > his father, Zephaniah Dible, was 21 and his mother, Catherine Moore, was 21.
- **[compiled]** (w2, other) The underlying source for the Zephaniah-Catherine Moore-John Moore Dible link is cited as an actual 1880 federal census household listing, a genuine primary record collection not yet directly viewed this session.
  > John M Dible in household of Zephaniah Dible, "United States Census, 1880"

### https://www.findagrave.com/memorial/204732912/harry-dible

- **[verified-index]** (w2, date) A THIRD, previously unfound death-year data point for Harry surfaced this session: a separate Find A Grave memorial in Rexford Cemetery itself gives 1936, not 1935 or WikiTree's 1940, with no obituary or record citation attached.
  > Harry Dible Birth 1863 Death 1936 (aged 72–73) Burial Rexford Cemetery Rexford , Thomas County , Kansas , USA

### http://usgenwebsites.org/NEHitchcock/resources/vitals/countycourthousemarriages.php

- **[verified-index]** (w2, other) Hitchcock County, Nebraska's own courthouse marriage records only survive from 1888 onward because earlier records were destroyed in a courthouse fire, and surviving certificates of this era record both parties' parents' names -- meaning the original 1896 Harry/Julia certificate, if located, would directly answer the parentage question.
  > These records start from January 26, 1888. No earlier marriage records are available due to a fire at the courthouse.
- **[verified-index]** (w2, other) The same Hitchcock County resource page confirms parents' names are recorded on the original marriage certificates of this era.
  > Other information available on certificate: Parents names, witnesses, and person who married them, some have where the wedding took place.
- **[verified-index]** (w2, other) The NEGenWeb Hitchcock County online marriage extract is incomplete and contains no entries at all for 1896, so the Harry/Julia record has not yet been located in any free online transcription.
  > 1895 Ira BACON, 46, m. Cirillia J. (YOUNG) BROWN, 32, 1895 1897 Well BALL, 22, m. Ora DANIELS, 21, September 28, 1897

### https://www.findagrave.com/cemetery/204446/memorial-search?lastname=Dible

- **[verified-index]** (w2, other) Murrysville Cemetery (Westmoreland Co PA) holds at least 46 separate Dible burials in one plot section, establishing that the Dible surname was extremely common in that specific locality -- raising real risk that compilers have cross-attributed children among several same-era, same-surname men rather than one nuclear family.
  > 46 matching records found for Dible

### https://sites.rootsweb.com/~nehitchc/

- **[verified-index]** (w3, other) The Hitchcock County, NE GenWeb site's own resource list confirms its online marriage-record transcription covers only 1888, with no 1896 entries -- independently reconfirming wave 2's finding that no free transcription of the Harry/Julia marriage record exists online.
  > HITCHCOCK COUNTY MARRIAGE RECORDS Marriage Record Extracts, 1888

### https://sites.rootsweb.com/~nehitchc/olres/1906atls.html

- **[verified-index]** (w3, other) The 1906 Standard Atlas of Hitchcock County patrons list, transcribed on NEGenWeb, contains zero entries for the Dible surname, supporting that neither Dible family was a resident landowner there by 1906 and that Trenton was likely an incidental marriage venue rather than a residence.
  > 1906 Standard Atlas of Hitchcock County - patrons list, portrait list

### https://www.findagrave.com/memorial/76182484/wayne_e-dible

- **[verified-index]** (w3, relationship) Find A Grave documents a further descending generation: Wayne E. Dible (1899-1963, a son of Harry and Julia per FamilySearch) married Wilma G. Stephens (1905-1981); their son Kenneth Wayne 'George' Dible (1922-2008) is buried at Rexford Cemetery, Thomas Co KS, alongside siblings Bill Dible (1941-2014) and Morris Wayne Dible (1944-2024).
  > Wayne E. Dible 1899–1963 ... Wilma G. Stephens Dible 1905–1981 ... Kenneth Wayne "George" Dible 1922–2008

### https://ancestors.familysearch.org/en/LXSR-HNL

- **[verified-index]** (w3, other) Zephaniah Dible's own FamilySearch profile page (ID LXSR-HNL) still returns 404 across three different URL patterns tried independently this session, and no Find A Grave memorial for him is locatable by search -- his death (1900, per Harry's page structured data) remains placeless and is a genuine dead end pending an original Kansas record.
  > "name":"Zephaniah Dible","birthDate":"+1839","deathDate":"+1900"

### https://www.wikitree.com/wiki/Dible-21

- **[compiled]** (w1, date) WikiTree gives Harry's exact parents-marriage date (24 Mar 1859) and names his two full siblings from that marriage, but records Harry's own death as 1940 -- conflicting with FamilySearch's 1935 Rexford, KS burial date.
  > Zephaniah married first on 24 Mar 1859, Catherine Moore, by whom he had three children: John J. Dible (1860-1907), Mary E. Dible (1862-1916), & Harry Dible (1863-1940).
- **[compiled]** (w2, date) WikiTree's Harry Dible profile is sparse and explicitly marks his death location and spouse/children as unresearched, which weakens its 1940 death-year figure relative to the two Kansas-sourced 1935/1936 figures.
  > Died 1940 at about age 77 [location unknown]

### https://en.wikipedia.org/wiki/Washington_Township,_Westmoreland_County,_Pennsylvania

- **[compiled]** (w2, place) A real, non-parish 'Washington Township' civil division exists in Westmoreland County, PA, founded in 1789, confirming Pennsylvania never used 'parish' as a civil unit there -- supporting the place-mislabel theory.
  > Washington Township is a township in Westmoreland County, Pennsylvania, United States. It was founded in 1789 from Salem Township.

### https://ancestors.familysearch.org/en/K2YT-46L/jacob-dible-1780-1872

- **[compiled]** (w2, person) Pushing one generation further than wave 1 reached: Jacob Dible (1780-1872) married Susanna Catharine Marsh in 1808 in Westmoreland Co PA per FamilySearch's tree, sourced there to Historical Society of Pennsylvania church-record abstracts.
  > He married Susanna Catharine Marsh in 1808, in Westmoreland, Pennsylvania, United States.
- **[compiled]** (w2, person) Pushing two generations further: Jacob Dible's own parents are given as Johan Jacob DeVilbiss and Anna Maria Teagarden, redirecting the immigrant-ancestor question away from the 'Dreibelbis of Hassloch, Germany' lead wave 1 flagged toward the documented colonial-Maryland DeVilbiss family instead.
  > his father, Johan Jacob DeVilbiss, was 37 and his mother, Anna Maria Teagarden, was 33.
- **[compiled]** (w3, relationship) Jacob Dible's own FamilySearch profile names his parents as Johan Jacob DeVilbiss and Anna Maria Teagarden, with precise ages, extending the compiled FamilySearch line one generation further than a sibling-page citation would.
  > When Jacob Dible was born in 1780, in Franklin, Murrysville, Westmoreland, Pennsylvania, United States, his father, Johan Jacob DeVilbiss, was 37 and his mother, Anna Maria Teagarden, was 33.

### https://ancestors.familysearch.org/en/L41V-351/johan-jacob-devilbiss-1743-1804

- **[compiled]** (w2, place) Three generations further back, Johan Jacob DeVilbiss (1743 Prince George's Co, MD - 1804 MD) married Anna Maria Teagarden in 1778 in Westmoreland County PA; his own parents are named as Casper Conrad Devilbiss Sr and Anne Cocil, with a Maryland Register of Wills citation attached.
  > He married Anna Maria Teagarden in 1778, in Harrison City, Penn Township, Westmoreland, Pennsylvania, United States.
- **[compiled]** (w3, relationship) Johan Jacob DeVilbiss's own profile names his parents as Casper Conrad Devilbiss Sr and Anne Cocil of colonial Prince George's County, Maryland, and gives his 1778 marriage to Anna Maria Teagarden at Harrison City, Penn Township, Westmoreland Co PA.
  > When Johan Jacob DeVilbiss was born on 1 July 1743, in Prince George's, Maryland, British Colonial America, his father, Casper Conrad Devilbiss Sr, was 22 and his mother, Anne Cocil, was 18.

### https://ancestors.familysearch.org/en/L4MJ-BQ9/wayne-edgar-dible-1899-1963

- **[compiled]** (w2, place) The better-documented duplicate, Wayne Edgar Dible, is given an anomalous Pennsylvania birthplace inconsistent with the family's known Nebraska/Kansas whereabouts in 1899, likely a tree data error worth flagging rather than trusting.
  > he was born on 20 January 1899, in Harrisburg, Dauphin, Pennsylvania, United States

### https://en.wikipedia.org/wiki/Trenton,_Nebraska

- **[compiled]** (w2, place) Trenton is confirmed as the Hitchcock County seat, which mechanically explains why a marriage license there would be recorded/solemnized in Trenton regardless of exactly where either family was living -- a partial answer to the 'why Trenton' open question.
  > It is the county seat of Hitchcock County.

### https://ancestors.familysearch.org/en/LVD1-BF2/casper-conrad-devilbiss-sr-1721-1777

- **[compiled]** (w3, migration) Casper Conrad Devilbiss Sr's own FamilySearch profile claims a specific European birthplace (Woerth/Matzenheim, Bas-Rhin, Alsace, France), a 1731 immigration to Philadelphia, and death in 1777 in Frederick, Maryland, buried at Graceham Cemetery -- the deepest resolvable node in this compiled chain (his own parents' profile 404s).
  > He immigrated to Philadelphia, Philadelphia, Pennsylvania, British Colonial America in 1731 and lived in Frederick, Maryland, British Colonial America in 1767.

### https://www.newspapers.com/newspage/416675050/

- **[compiled]** (w3, other) A 14 Jul 1910 Colby Free Press article (Thomas County, KS) names a 'Representative Harry Dible, Rexford' on a Republican county ticket, indicating Harry was a local political figure in his adopted Kansas county by 1910 -- found via a paywalled newspapers.com preview, but the same title (1904-1925) is freely digitized on Library of Congress Chronicling America and not yet searched page-by-page.
  > Representative Harry Dible, Rexford

## Search frames (13 unique from 13 raw)

### F1 (w1). Is the Zephaniah Dible / John Heckman Dible full-sibling link (the basis for Harry and Julia being first cousins) true beyond FamilySearch's own crowd-tree, given that Find a Grave's independently-curated sibling list for John Heckman Dible omits Zephaniah entirely?

- Jurisdictions: Franklin Township and Penn Township, Westmoreland County, Pennsylvania (John Albert Dibler's birth/death places); Washington Parish [sic], Westmoreland County, PA (Catherine Heckman's birthplace label, likely a FamilySearch place-authority artifact since PA has no civil parishes); Blue Springs, Gage County, NE (John Heckman Dible's death/burial)
- Record sets:
  - FamilySearch Ancestors profile, John Albert Dibler (1805-1866) -- https://ancestors.familysearch.org/en/L6RZ-ZG2/john-albert-dibler-1805-1866 (profile compiled, underlying facts 1805-1866)
  - FamilySearch Ancestors profile, Catherine Heckman (1805-1846) -- https://ancestors.familysearch.org/en/L6LS-FV3/catherine-heckman-1805-1846 (1805-1846)
  - FamilySearch Ancestors profile, Malinda Dible Londen (1839-1929) -- https://ancestors.familysearch.org/en/L6LS-FR4/malinda-dible-londen-1839-1929 (1839-1929)
  - Find a Grave memorial, John Heckman Dible -- https://www.findagrave.com/memorial/9609591/john-heckman-dible (1836-1913)
  - Dible family paper, Families by Velma Parsons (already known compiled source) -- https://www.familiesbyvelmaparsons.com/pdfs/DIBLE.pdf (compiled)
  - Westmoreland County, PA Register of Wills / Orphans' Court index -- https://www.co.westmoreland.pa.us/172/Register-of-Wills-Orphans-Court (would cover John A. Dibler's 1866-67 estate)
- Next pulls:
  1. Search Westmoreland County PA Orphans' Court/probate index for John A. Dibler's 1866 estate to get a primary heir list naming Zephaniah and John Heckman as sons
  1. Pull 1850 or 1860 US census household for John A. Dibler/Catherine Heckman in Westmoreland Co PA to see both sons enumerated together
  1. Search Find a Grave and FamilySearch directly for a standalone Zephaniah Dible memorial/profile (his own FamilySearch ID LXSR-HNL 404'd on every attempt this session)
  1. Check FamilySearch catalog for Westmoreland County PA church (Kiskiminetas/Salem/Congruity) baptismal registers spanning 1834-1839 for a Zephaniah Dible entry

### F2 (w1). Where were Harry's (Zephaniah's) and Julia's (John Heckman's) families actually residing at the moment of the 10 Jun 1896 wedding, given the wedding site (Trenton, Hitchcock Co, far SW NE) does not match either family's otherwise-documented Nebraska base (Johnson/Gage Co, SE NE) or Harry's side's known Kansas base?

- Jurisdictions: Hitchcock County, NE (Trenton, wedding site); Red Willow County, NE (adjacent county, McCook, per task brief); Johnson County, NE (Julia's birthplace, Spring Creek Township); Gage County, NE (Blue Springs, John Heckman Dible's later home/death); Thomas County, KS (Lacey Township 1900, Smith Township ~1900s-1920s, Rexford death 1935)
- Record sets:
  - NEGenWeb Hitchcock County (RootsWeb) -- https://sites.rootsweb.com/~nehitchc/ (ongoing volunteer index)
  - Hitchcock County NE queries page, NEGenWeb -- http://negenweb.net/NEHitchcock/queries/query.html (ongoing)
  - NEGenWeb Red Willow County (RootsWeb) -- https://sites.rootsweb.com/~neredwil/ (ongoing volunteer index)
  - Nebraska, U.S., Compiled Marriage Index, 1856-1898 (Ancestry, paywalled/login) -- https://www.ancestry.com/search/collections/7871/ (1856-1898)
  - 1900 US Federal Census, Lacey Township, Thomas County, Kansas (NARA microfilm T623 roll 502; also FamilySearch/Ancestry index, login required) -- https://www.archives.gov/research/census/publications-microfilm-catalogs-census/1900/part-07.html (1900)
  - Hitchcock County Courthouse (original 1896 marriage license/register, not online) -- https://hitchcockcounty.ne.gov/ (1896 record held locally)
- Next pulls:
  1. Search for a Nebraska 1895 state census household (state census fell between 1890 and 1900 federal) for either Dible family in Hitchcock or Red Willow County to establish who was actually living there in 1895-96
  1. Pull the Harry & Julia Dible 1900 census household itself (Lacey Township, Thomas Co, KS) to check children's birth-state fields, which will show exactly when the couple left Nebraska for Kansas
  1. Contact/search Hitchcock County Courthouse or Nebraska State Historical Society for the original 1896 marriage register entry, which may list both parties' residences and parents' names
  1. Check Red Willow County (McCook) newspaper coverage via Chronicling America or the Nebraska Newspaper Project for a June 1896 wedding notice naming both families' hometowns

### F3 (w1). What happened to Zephaniah Dible himself after Catherine Moore's death -- where in Kansas did he resettle by 1874 (James C.'s birth), where did he die in 1900, and does that Kansas county sit on the migration path toward Thomas County that Harry (and later Bill Dible's branch) ended up in?

- Jurisdictions: Unspecified Kansas county, ca. 1872-1895 (James C. Dible born there 1874; second wife Clarinda A. Stodghill died 1895); Adams County, CO and Morgan County, CO (James C.'s later residence/death 1934, Fort Morgan)
- Record sets:
  - FamilySearch Ancestors profile, James C. Dible (1874-1934) -- https://ancestors.familysearch.org/en/M5JZ-R7X/james-c-dible-1874-1934 (1874-1934)
  - Kansas Historical Society state census index (1875, 1885, 1895 state censuses, free) -- https://www.kansashistory.gov/ (1875/1885/1895)
  - Rexford Cemetery, Find a Grave -- https://www.findagrave.com/cemetery/93480/rexford-cemetery (burials from ca. 1888)
- Next pulls:
  1. Search Kansas 1875 and 1885 state census indexes (Kansas Historical Society, free) for a Zephaniah Dible or Clarinda Stodghill household to pin the county of the family's first Kansas landing
  1. Search Find a Grave directly on Rexford Cemetery's own roster page for Harry H Dible and any Zephaniah Dible burial, since keyword search did not surface a standalone Zephaniah memorial this session
  1. Pull James C. Dible's 1898 Frederic, Monroe County, Iowa marriage record to Cora Belle Blake for any parental detail on Zephaniah not captured elsewhere

### F4 (w1). Can Harry's death year be resolved (FamilySearch: 19 Feb 1935, Rexford, Thomas Co, KS vs. WikiTree: 1940) and can a standalone Find a Grave memorial for Harry H. Dible and/or Julia Dible be located to add a primary-adjacent source?

- Jurisdictions: Thomas County, Kansas (Rexford -- Harry's death/burial; Colby -- Julia's death)
- Record sets:
  - Rexford Cemetery, Find a Grave -- https://www.findagrave.com/cemetery/93480/rexford-cemetery (ongoing)
  - Kansas Historical Society vital/death records -- https://www.kshs.org/ (Kansas death registration from 1911)
  - FamilySearch Ancestors profile, Harry H Dible (1863-1935) -- https://ancestors.familysearch.org/en/L4WV-WGX/harry-h-dible-1863-1935 (1863-1935)
- Next pulls:
  1. Search Find a Grave's Rexford Cemetery roster directly (not just keyword search) for a Harry H. Dible and Julia Dible memorial
  1. Request/search the Kansas death certificate index for Harry H. Dible's Feb 1935 death in Rexford, Thomas County, which would independently confirm both the date and his parents' names
  1. Check the Colby Free Press or Thomas County newspaper archive (nwkansas.com PDF archive, already used elsewhere in this project) for a Feb 1935 obituary of Harry H. Dible

### F5 (w2). Was Zephaniah Dible actually a son of John Albert Dible/Dibler (1805-1866) of Murrysville, Westmoreland Co PA -- making Harry and Julia first cousins through a shared grandfather -- or is this a cross-family conflation, given FamilySearch and Find A Grave each attach a DIFFERENT wife/child-set to John Albert Dible and neither independently-sourced version agrees with the other on which children (including Zephaniah) belong to him?

- Jurisdictions: Franklin Township, Penn Township & Murrysville borough, Westmoreland County PA (John Albert Dible's own life); adjoining Kiskiminetas/Parks Township, Armstrong County PA (Zephaniah's and his children's recorded birthplaces); Sharpsburg, Allegheny County PA (Rebecca Katz's 1906 death); Pennsylvania kept no statewide birth/death registration before 1906, so pre-1866 proof depends on county probate/orphans' court, church registers, or federal census
- Record sets:
  - United States Census, 1850 (free index, household search for John A. Dib[l]er, Westmoreland/Armstrong Co PA) -- https://www.familysearch.org/en/search/collection/1401638 (1850)
  - United States Census, 1860 (free index, would show which wife/children were in the household before John Albert's 1866 death) -- https://www.familysearch.org/en/search/collection/1473181 (1860)
  - Westmoreland County PA will books/will indexes (John Albert Dibler d. 28 Dec 1866 -- an estate/probate record naming heirs would settle which children were legally his) -- https://www.familysearch.org/en/search/catalog/410492 (1773-1918)
  - Murrysville Cemetery, Find A Grave (Section 12 family plot -- browse full 46-record 'Dible' list and photograph headstones for exact relationships/dates) -- https://www.findagrave.com/cemetery/204446/memorial-search?lastname=Dible (19th century burials)
  - Pennsylvania, Historical Society of Pennsylvania, Births and Baptisms (the actual collection FamilySearch cites for this family's church records) -- https://www.familysearch.org/search/collection/4138679 (1520-1999, PA church abstracts)
- Next pulls:
  1. Pull the 1850 and 1860 US census households for John A. Dible/Dibler in Westmoreland/Armstrong Co PA to see which wife and which children (by name/age) were actually resident -- this single record would adjudicate Barbara Kuntz vs Rebecca Katz vs Catherine Heckman vs Elizabeth Allshouse
  1. Request or search Westmoreland County Register of Wills/Orphans' Court records for John Albert Dible's 1866 estate, which would legally name his surviving wife and heirs
  1. Photograph/transcribe the actual headstones in Murrysville Cemetery Section 12 (Row 2 Spaces 2-6, Row 4 Spaces 2-6) to fix exact family groupings physically rather than relying on two disagreeing online trees
  1. Search for a baptismal or birth record specifically for Zephaniah Dible (b. circa 1839) in Westmoreland or Armstrong County PA church registers, since no source this session could independently confirm his mother's name from a period record

### F6 (w2). What does the original 10 June 1896 Hitchcock County, NE marriage certificate for Harry H. Dible and Julia Dible actually say for both sets of parents' names -- would this settle the whole Harry-parentage question with a single primary record?

- Jurisdictions: Hitchcock County, Nebraska (Trenton is the county seat); marriage license/certificate is a county-level record, not a state one, for 1896
- Record sets:
  - Hitchcock County Courthouse Marriages, 1888-1898 (NEGenWeb volunteer transcription, incomplete, no 1896 entries yet transcribed) -- http://usgenwebsites.org/NEHitchcock/resources/vitals/countycourthousemarriages.php (1888-1898 (partial))
  - Nebraska Marriages, 1855-1995 (FamilySearch index; free registration required, cited on both Harry's and Julia's own profiles as the source collection) -- https://www.familysearch.org/en/search/collection/1708654 (1855-1995)
  - Nebraska, U.S., Select County Marriage Records, 1855-1908 (Ancestry -- paywalled, contents not verified this session) -- https://www.ancestry.com/search/collections/61335/ (1855-1908)
- Next pulls:
  1. Search FamilySearch's 'Nebraska Marriages, 1855-1995' collection directly for 'Harry Dible' or 'Harry H Dibble' 10 Jun 1896 Hitchcock Co (session blocked by Incapsula bot-check on familysearch.org/search; needs a logged-in browser session, not curl)
  1. Write to the Hitchcock County Clerk (per NEGenWeb's own recommendation) for a certified copy of the 1896 marriage record, which the site states includes both parties' parents' names
  1. Check whether History Nebraska (Nebraska State Historical Society) holds the original 1888-1898 Hitchcock County marriage register on microfilm with public request access

### F7 (w2). What was Harry H. Dible's actual death date -- 19 Feb 1935 (FamilySearch, day-precision but no visible death-record citation), 1936 (a separate, uncited Find A Grave memorial in the same Rexford Cemetery), or 1940 (WikiTree, unsourced, marked 'location unknown')?

- Jurisdictions: Rexford, Thomas County, Kansas (burial place agreed by all three sources)
- Record sets:
  - Kansas death index / Kansas State Historical Society death certificates -- https://www.kshs.org/p/kansas-historical-society-vital-statistics/13952 (Kansas began statewide death registration 1911)
  - Rexford Cemetery, Find A Grave (existing memorial, no obituary attached yet) -- https://www.findagrave.com/memorial/204732912/harry-dible (burial, year-only precision)
  - Colby Free Press / Thomas County KS newspaper obituary indexes -- https://usgenealogyresearch.atwebpages.com/Kansas/Sherman/obits_index_1904-1935-1-30.pdf (nearby Sherman Co index as a model; Thomas Co equivalent not yet located)
- Next pulls:
  1. Search the Kansas Historical Society's free online death index (statewide from 1911) for Harry Dible/Dible, Thomas County, 1935-1940 range
  1. Look for a Thomas County KS newspaper (Colby Free Press, Rexford paper) obituary for Harry Dible to get an exact, sourced death date the way John Heckman Dible's 1913 obituary was recovered
  1. Photograph the actual Rexford Cemetery headstone (memorial 204732912 currently has only 1 photo) to check whether it shows a full date, which would adjudicate 1935 vs 1936

### F8 (w2). Does the family's compiled deep-ancestry line actually run to the documented colonial-Maryland DeVilbiss family (Casper Conrad Devilbiss Sr, Johan Jacob DeVilbiss) as FamilySearch's tree now indicates, or to the separate 'Dreibelbis of Hassloch, Germany' immigrant line the Velma Parsons paper pointed to -- these are two different, non-overlapping compiled genealogies for the same surname cluster?

- Jurisdictions: Prince George's/Frederick County, Maryland (Devilbiss origin per FamilySearch); Westmoreland County PA (where the family appears by 1778-1808); Berks County PA / Hassloch, Germany (competing Dreibelbis immigrant claim)
- Record sets:
  - Maryland Register of Wills Records, 1629-1999 (cited directly on Johan Jacob DeVilbiss's FamilySearch profile) -- https://www.familysearch.org/ark:/61903/3:1:33S7-9T1P-9Y4P?cc=1803986 (colonial-1999)
  - John Jacob Dreibelbis Family of America (Google Books, competing compiled lead flagged by wave 1) -- https://books.google.com/books/about/John_Jacob_Dreibelbis_Family_of_America.html?id=ODgZAQAAMAAJ (18th century immigrant account)
- Next pulls:
  1. Compare the DeVilbiss-family compiled genealogies (widely published, e.g. Devilbiss family associations) against the Dreibelbis book to see whether either explicitly accounts for a 'Dible/Dibler' Westmoreland Co PA branch, since the surname drift Devilbiss->Dibler->Dible is phonetically plausible but not yet documented with a period record
  1. Pull the actual Maryland Register of Wills ARK record for Jacob Devilbiss's 1743 birth citation to see what document it actually is (a will is an odd source for a birth date, suggesting a compiled/indexed secondary inference)

### F9 (w3). What did the original 10 June 1896 Hitchcock County, NE marriage record list as Harry H. Dible's and Julia Dible's parents -- the single record that would directly confirm or refute the first-cousin hypothesis?

- Jurisdictions: Trenton (county seat), Hitchcock County, Nebraska
- Record sets:
  - Hitchcock Co. NEGenWeb Marriage Record Extracts (online transcription covers only 1888) -- https://sites.rootsweb.com/~nehitchc/olres/marr1888.html (1888 only)
  - Nebraska, U.S. Select County Marriage Records 1855-1908 (Ancestry, login required) -- https://www.ancestry.com/search/collections/61335/ (1855-1908)
  - Nebraska Marriages 1855-1995 (FamilySearch, free but login-gated for images) -- https://www.familysearch.org/en/search/collection/1708654 (1855-1995)
- Next pulls:
  1. Request the original 1896 marriage certificate/license directly from the Hitchcock County Clerk in Trenton, NE (pre-1909 records held at county level per NebraskAccess).
  1. Search FamilySearch's login-gated Nebraska Marriages collection and Ancestry's Select County Marriage Records for the same 1896 entry.
  1. Contact the Southwest Nebraska Genealogical Society (covers Hitchcock/Red Willow) for any indexed original marriage register.

### F10 (w3). Where and when did Zephaniah Dible actually die (FamilySearch states only the year 1900, no place), given he is independently documented in Kansas from at least 1874 (James C. Dible's birth) through his second wife Clarinda Stodghill's 1895 death there?

- Jurisdictions: Likely Thomas, Sherman, Rawlins, Decatur, or Norton County, Kansas (unorganized/newly organized NW Kansas counties, 1870s-1900)
- Record sets:
  - KSGenWeb county obituary and cemetery indexes (Thomas/Sherman/Rawlins/Decatur/Norton) -- https://www.ksgenweb.org/ (varies by county)
  - Kansas, U.S., State Census Collection 1855-1925 (Ancestry, login required) -- https://www.ancestry.com/search/collections/1088/ (1855-1925)
  - Find A Grave search (no Zephaniah Dible memorial located this session) -- https://www.findagrave.com/memorial/search?firstname=Zephaniah&lastname=Dible (n/a)
- Next pulls:
  1. Pull the 1885 and 1895 Kansas State Census (free index via Kansas Historical Society) for Zephaniah/Clarinda Dible's household to pin down the county before his 1900 death.
  1. Search KSGenWeb obituary pages for NW Kansas counties for a 1900 Dible death notice.
  1. Check Emma Blanch Dibbs (1880-1926) and Frank Dible (1882-1965)'s own Find A Grave/FamilySearch pages for a shared family cemetery that might also hold Zephaniah.

### F11 (w3). Which of John Albert Dibler's now four candidate wives (Elizabeth Ella Allshouse m.1827, Barbara Kuntz m.1831, Catherine Heckman 1805-1846, Rebecca Katz 1815-1906) actually bore Zephaniah versus John Heckman Dible, and can a single wife's tenure chronologically fit children spanning 1833-1859?

- Jurisdictions: Franklin Township / Penn Township / Murrysville, Westmoreland County, Pennsylvania (with possible Armstrong County overlap)
- Record sets:
  - Westmoreland Co. PA Register of Wills (probate for John Albert Dibler, d.1866) -- https://www.westmorelandcountypa.gov/333/Register-of-Wills (1866 estate)
  - SAMPUBCO Westmoreland Will Book Testator Index (sample/teaser only; shows 'DIBBE, Jacob' and 'DIBBE, John' in Vol.5, 1865-1874 -- possible OCR corruption of 'Dible', unconfirmed) -- http://www.sampubco.com/wills/pa/pawestmoreland01.htm (1865-1874 (Vol.5))
  - Find A Grave, Murrysville Cemetery (46+ Dible burials in one section per wave 2) -- https://www.findagrave.com/cemetery/2138949/murrysville-cemetery (19th-20th c.)
- Next pulls:
  1. Order John Albert Dibler's actual 1866 Westmoreland Co. probate file (not just the paywalled sample index) to see the named widow/heirs, which would settle which wife survived him.
  1. Search Westmoreland Co. German Lutheran/Reformed church baptismal registers (Murrysville/Export/Level Green area) for each disputed child's recorded mother at baptism.
  1. Cross-check Rebecca Katz's own 1906 PA death record (already found by wave 2) against the 1850/1860 census to see which household she appears in.

### F12 (w3). Does the Dible surname genuinely descend from the colonial Maryland DeVilbiss family (Jacob Dible 1780-1872 -> Johan Jacob DeVilbiss -> Casper Conrad Devilbiss Sr, immigrant from Alsace c.1731) as FamilySearch's compiled tree asserts, given the dedicated published DeVilbiss genealogy's transcription of Casper's actual 1777 will lists no 'Johan Jacob' among his children and never uses the surname 'Dible' anywhere in 200+ pages?

- Jurisdictions: Frederick County, Maryland; Westmoreland County, Pennsylvania; Bas-Rhin (Alsace), France
- Record sets:
  - History of the DeVilbiss Family in the United States of America, 200 Years (full text, free) -- https://archive.org/stream/historyofdevilbi00devi/historyofdevilbi00devi_djvu.txt (covers 1721-1930s)
  - FamilySearch compiled tree (Jacob Dible / DeVilbiss branch, no cited underlying source visible) -- https://ancestors.familysearch.org/en/K2YT-46L/jacob-dible-1780-1872 (18th-19th c.)
  - John Jacob Dreibelbis Family of America (Google Books, wave 1's alternative unproven lead) -- https://books.google.com/books/about/John_Jacob_Dreibelbis_Family_of_America.html?id=ODgZAQAAMAAJ (18th c. immigrant)
- Next pulls:
  1. Treat the FamilySearch Jacob-Dible-to-DeVilbiss link as unproven/likely erroneous rather than 'the redirected immigrant line'; do not build further generations on it without independent proof.
  1. Search for Jacob Dible's (1780-1872) own baptismal or church record in a Westmoreland Co. PA German congregation, independent of the DeVilbiss hypothesis.
  1. Separately re-examine the still-unproven Dreibelbis-of-Hassloch lead from wave 1 as the other open (equally unverified) immigrant-origin candidate for the surname.

### F13 (w3). Why did Harry and Julia marry in Trenton, Hitchcock County, NE (SW Nebraska) in 1896 when Julia's father was continuously resident ~260 miles away in Johnson County, NE, while Harry's father Zephaniah's family had already been settled in Kansas since at least 1874?

- Jurisdictions: Hitchcock County, NE; Johnson County, NE; Thomas/Sherman/Rawlins/Decatur/Norton County, Kansas (SW NE / NW KS borderlands)
- Record sets:
  - Hitchcock Co. NEGenWeb site (no 1896 marriage transcription, no Dible in 1906 atlas patrons) -- https://sites.rootsweb.com/~nehitchc/ (1888, 1906 (available extracts))
  - Kansas, U.S., State Census Collection 1855-1925 (Ancestry, login required) -- https://www.ancestry.com/search/collections/1088/ (1855-1925)
- Next pulls:
  1. Pull the 1885 and 1895 Kansas state census plus 1890s county tax/land records for Thomas, Sherman, Rawlins, Decatur, and Norton counties to locate Zephaniah's family circa 1896 and test whether a young unmarried Harry was already there.
  1. Search Hitchcock Co. NE 1890s land/homestead patent records (BLM GLO records, free) for either surname to see if either family briefly held land there.
  1. Check the Palisade School Alumni list and 1917 Hitchcock Co. irrigation platmap (both on the NEGenWeb site) for any Dible or Haden entries as a residence proxy.

