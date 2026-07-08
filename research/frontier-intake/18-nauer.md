# Frontier intake 18: Nauer: Ontario to Kansas, Palatinate garble

Line: Zimmerman (Nauer side)
Docket: case.04
Source: 60-agent frontier workflow, waves 1-3, 2026-07-08. RAW INTAKE -- see 00-index.md
for the validation protocol; nothing below may land in index.html without an
independent re-fetch and quote match.

## Where this sits in the tree

Elizabeth Catherine Nauer (b. 1872, strong; the 1871-vs-1872 stone year is inside case.04) is Doyle's grandmother. Above her: Thomas A. Nauer (b. 27 Dec 1824, 'Munich, Spayer Province' per WikiTree -- garbled; Speyer is Palatinate, not Munich) and Johann Lorenz Nauer 1801-1870 + Mary Dorothea Wand/Meyer 1799-1878 (the Meyer-vs-Wand conflict is case.04; Wilmot Township then Carrick Township innkeeper, both residence events on the Zimmerman plate). Rhenish-Bavarian (Pfalz) emigration to Waterloo County frames.

## Original frame given to the agents

> NAUER ONTARIO-BAVARIA: Thomas A. Nauer (b. 27 Dec 1824, 'Munich, Spayer Province' per WikiTree - garbled; Speyer is PALATINATE not Munich - resolve). Parents Johann Lorenz Nauer 1801-1870 + Mary Dorothea Wand/Meyer 1799-1878 (Wilmot Twp then Carrick Twp, Bruce Co, innkeeper). Frame Rhenish-Bavarian (Pfalz) emigration to Waterloo County; St. Agatha/St. Clements registers; Bruce County records.

## Wave syntheses (verbatim from the agents)

### Wave 1

Ground-truth check confirms index.html/source-index.json already hold the solid Kansas-side chain (Elizabeth Catherine Nauer Zimmerman -> parents Thomas A. Nauer 1824-1884 and Catherina Marie Koeberger 1832-1906, both documented via FamilySearch/Find a Grave in Cawker City/Mitchell Co., Kansas) and the compiled Waterloo German Catholic Settlers PDF's hedge that Lorenz Nauer/Dorothea Meyer are only a *possible* parent pair for Thomas. This pass adds a major, previously-unused free source - the Waterloo Region Generations community database (generations.regionofwaterloo.ca), which independently indexes the actual 1851 Canadian census, an 1856 church-marriage card index, an 1856 Deutsche Canadier newspaper notice, and 1864/1871 Berliner Journal death notices for this Nauer/Wand cluster. Critically, these primary-adjacent sources say the family's origin was 'Prussia, Germany' (matching the compiled PDF's own 'of Prussia, Germany' language) and give Lorenz Nauer's death as 2 July 1864 in Carlsruhe, Carrick Township - both of which conflict with WikiTree's uncited 'Munich, Spayer Province, Germany' (implying Bavarian Palatinate) and uncited 1870 death year. The 'Munich, Spayer Province' phrase, though internally impossible (Munich is not in the Palatinate), traces on WikiTree to citations (census/passenger indexes/Ancestry Family Tree) that would not actually carry that level of European place detail, so it should be treated as an unverified compiled guess rather than settled fact pending direct inspection of the underlying census images or the Ancestry family tree it came from. Dorothea (Meyer) Wand-Nauer's 1878 death, by contrast, does trace to a real Archives of Ontario civil registration reel (MS935, Reel 18), giving more confidence in the Carrick Township/Bruce County end of the family's story than the German origin end.

### Wave 2

This pass mined the Waterloo Region Generations (WRG) community database person-by-person (not just as a name-check) and pulled the full 167-page 'German-French Catholic Settlers of Waterloo County' PDF text directly, rather than relying on the predecessor's characterization of it. Two things move the needle. First, WRG independently reconstructs the Lorenz Nauer/Dorothea Meyer household from the actual 1851 Census of Wilmot Township (Library and Archives Canada) with six named children (Lorenz b.1833, Maria b.1835, Carolina b.1837, Jacob b.1841, John b.1844, Maria b.1846, all 'Prussia, Germany'), and a Bruce County civil marriage register entry for son John Nauer (1866) names his parents as 'Lawrence' and 'Doroth Meyer' in a primary civil record -- the strongest documentary proof yet that this specific Lorenz+Dorothea family unit is real and reproduces itself consistently. Critically, Thomas Nauer's own WRG profile (I134297, matched beyond doubt to the Kansas Thomas via his 1856 Waterloo marriage to 'Katharina Christiane Coberger' and seven matching children's names) carries no Father/Mother field at all -- the same database that confidently links five other children to Lorenz+Dorothea does not link Thomas, despite having the data infrastructure to do so. Second, and new this wave: one of Lorenz's own census-documented sons (Lorenz Jr., b.1833) is recorded in WRG under the alternate name 'Lorenz Wand,' and the PDF independently states 'Another possible child was Lawrence Wand {about 1834}... a contractor of Bruce County' as a child of Adam Wand-Wandt-Wendt (died before 1852) and Dorothea Meyer, alongside a documented daughter Ann Wand who married Charles Gehl in 1853 at St. Agatha. This is two independent sources corroborating real Wand/Nauer surname fluidity in this specific family at exactly the transition generation (1833-34), which sharpens rather than resolves the Thomas question: Thomas (b.1823/24) is a full decade older than this entire sibling cohort (1833-1846), too old to be a late child of Lorenz+Dorothea's own marriage but plausibly an eldest child of Dorothea's first marriage to Adam Wand who, like his younger half-brother, could have carried the Nauer surname informally -- a new, testable hypothesis, not a proven fact. Separately, the '1864 Carlsruhe' death record the predecessor attributed to the patriarch is very likely a different, younger Lorenz Nauer: the Berliner Journal obituary gives his age as 53 at death (implying b.~1811), while both the WRG census reconstruction and the PDF independently and consistently give the patriarch's birth as 1802/1803 -- a 9-year mismatch that the WRG database itself does not attempt to bridge (it keeps these as two unconnected person records). Neither 1864 nor WikiTree's 1870 is actually proven for the patriarch. Also newly documented: Thomas Nauer's occupation was 'tanner' (1856) / 'White Tanner' (1871 census, Waterloo Twp, Roman Catholic), his 1856 marriage was performed 'by banns' in Berlin (Kitchener) with the officiant given as 'minister Feyfel, Petersburg,' and by 1873 the family's parish orbit had shifted to St. Boniface, Maryhill (founded 1834) based on son Moritz's birthplace there. WikiTree's Nauer-7 page remains inaccessible to automated tools this wave (AWS WAF JS challenge blocks curl, and WebFetch returns 403), so its citation list still cannot be directly inspected.

### Wave 3

This wave got past two prior blockers and found a load-bearing contradiction. First, WikiTree's Nauer-7 page (previously 403'd) finally loaded via retried curl: its 'Munich, Spayer Province, Germany' birthplace for Thomas has ZERO citation to any European record -- the birth line's seven footnotes resolve only to Canadian 1861/1871 census, an Ancestry immigration-list index, and two Find A Grave indexes. No document anywhere says 'Munich' or 'Speyer' for Thomas; this is very likely a compiled/free-text artifact, not a sourced fact. Second, and more consequential: the task's own framing of this line as 'Rhenish-Bavarian (Pfalz)' is not well supported by the actual evidence trail. Both WRG's 1851-census-based reconstruction of the Lorenz Nauer/Dorothea Meyer household and the compiled Waterloo PDF (quoted directly this wave: 'of Prussia, Germany') consistently and independently say PRUSSIA, not Bavaria -- and English Wikipedia (citing a 1956 CCHA report) states plainly that New Prussia was settled by immigrants from the Rhine Province of Prussia, the exact community Lorenz's family lived in. The same PDF elsewhere gives precise Palatinate villages for other Bavarian families (e.g., Birkenhördt), so its 'Prussia' label for the Nauers is a deliberate distinction, not filler. Rhenish Prussia (Rheinprovinz) and Rhenish Bavaria/the Pfalz (capital Speyer) are different 19th-century sovereign states with different dioceses and archives -- so this reframes which record sets to pull. Third, this wave found that WRG's Adam Wand/Dorothea-first-marriage narrative, which the predecessor treated as gaining independent corroboration, is NOT actually corroborated inside WRG at all: a direct WRG person search for 'Adam' 'Wand' returns zero results in a 360,805-person database, Dorothea Meyer's own WRG alternate-name list never includes 'Wand,' and WRG's Gehl-marriage entry for the Wand-surnamed daughter (Maria Josepha 'Mary' Wandt, d.1879) carries no Father/Mother field linking her to Adam Wand or Dorothea Meyer -- the entire first-marriage claim rests solely on the compiled PDF. A close read of the PDF's own text also surfaces a fresh, unresolved contradiction: it has Lawrence Wand's wife 'Josepha Fischer' dying in Bruce County in 1879 (matching WRG's Josepha Wandt/Gehl death year and place exactly) while separately having 'Ann Gehl nee Wand' -- widow of the same Charles Gehl -- remarry Henry Hahn in 1897, eighteen years after that 1879 death; Ann and Josepha cannot be the same woman on the dates given, which undercuts the predecessor's 'two sources corroborate' reading. Isolated confirmations: WRG's 1864 Carlsruhe Lorenz Nauer (I247851) is definitively a standalone, single-source record with no family links at all, distinct from the census-linked patriarch (I96264); Thomas's own WRG record gives his birthplace as bare 'Germany' with no state, sourced only to the 1871 census (not 'Prussia' -- that label attaches only to Lorenz's proven children); and WikiTree records Thomas's 1856 marriage as happening in 'Bridgeport, Ontario, Canada' (uncited) rather than Berlin/Kitchener (WRG's sourced location), which independently supports that 'Bridgeport' is a genuine Waterloo County place (used elsewhere in the same PDF for an unrelated family in 1857), strengthening the case that any 'Bridgeport, Oxford' attribution elsewhere is a county mistranscription. WikiTree's own family chart explicitly lists Thomas as having no known siblings under Johann Lorenz Nauer + Mary Dorothea Wand. WikiTree's Nauer-6 (father), Wand-109 (mother), and Nauer-5 (daughter Mary Magdalene Nauer Hahn) profiles remained blocked by the AWS WAF challenge all wave despite roughly 40 retry attempts; their footnoted sources for the parent-child link and for 'Munich, Spayer Province' specifically are still unseen by any research wave.

## Findings (42 unique from 42 raw, grouped by source, best-verified first)

### https://www.wikitree.com/wiki/Nauer-7

- **[compiled]** (w1, place) WikiTree gives Thomas A. Nauer's birthplace as the internally contradictory phrase 'Munich, Spayer Province, Germany' - Munich (city) is in Upper Bavaria, not in the Palatinate/Speyer administrative province at all, and none of the profile's own cited sources (1861/1871 Canadian census, 1880 US census, a passenger/immigration index, Find A Grave, Ancestry Family Trees) are documents that would carry this level of European place detail.
  > Born 27 Dec 1824 in Munich, Spayer Province, Germany
- **[verified-primary]** (w3, place) WikiTree's birth line for Thomas A. Nauer ('27 Dec 1824, Munich, Spayer Province, Germany') is footnoted to seven sources, all Canadian/US: 1861 and 1871 Canada census, an Ancestry immigration-list index, the 1880 US census, and two Find A Grave indexes -- no European record is cited.
  > Library and Archives Canada; Ottawa, Ontario, Canada; Census Returns For 1861; Roll: C-1083
- **[compiled]** (w3, date) WikiTree's family chart records Thomas's 1856 marriage to Catherina as taking place in Bridgeport, Ontario -- not Berlin (Kitchener), the location given by WRG's church-card-index and Deutsche Canadier newspaper-index sources -- and this location carries no footnote of its own.
  > married 1856 in Bridgeport, Ontario, Canada at age 31
- **[compiled]** (w3, relationship) WikiTree's own ancestor chart explicitly marks Thomas as having no known siblings under Johann Lorenz Nauer and Mary Dorothea Wand, meaning WikiTree's compiler never asserted a sibling set for him despite naming his parents -- a structural admission of the same weak link the predecessor identified via the missing Father/Mother field on Thomas's WRG profile.
  > Son of Johann Lorenz Nauer and Mary Dorothea Wand [sibling(s) unknown]

### https://www.findagrave.com/memorial/51169411/thomas-a-nauer

- **[verified-index]** (w1, place) Thomas A. Nauer's own Find A Grave memorial (a well-developed family-group memorial naming his wife and nine children) gives his birthplace simply as 'Germany' with no city or province - it does not corroborate 'Munich' or 'Speyer' at all.
  > Birth 27 Dec 1824 Germany
- **[verified-index]** (w2, person) A second, separate Find A Grave memorial exists for Thomas A. Nauer himself (distinct from son Moritz's memorial already in index.html), maintained independently, giving birth/death dates but no European place detail, and is not yet in source-index.json.
  > Birth 27 Dec 1824 Germany Death 24 Sep 1884 (aged 59) Cawker City, Mitchell County, Kansas, USA
- **[verified-primary]** (w3, person) Find A Grave's memorial for Thomas A. Nauer records his birthplace as plain 'Germany' with no state or city, and lists all eight surviving children (Bertha, Albert, Mary Magdalene, Emmelia, Augusta, Elizabeth, Moritz, Josephine) plus an infant, but records no parents for Thomas.
  > Birth 27 Dec 1824 Germany

### https://www.familysearch.org/en/search/collection/1927566

- **[verified-primary]** (w3, other) FamilySearch hosts a free (registration-required, non-paywalled) collection of Ontario Roman Catholic parish records spanning 1760-1923 across multiple parishes, which has not yet been searched for the Nauer/Meyer/Wand family's St. Agatha or St. Clements baptismal or marriage entries.
  > Baptisms, marriages, deaths and other records from several Roman Catholic parishes in the province of Ontario, Canada.

### https://www.wikitree.com/wiki/Wand-109

- **[compiled]** (w1, place) Mary Dorothea Wand's WikiTree profile repeats the same garbled birthplace and cites the 1871 Ontario census index as one of the sources for it, even though that index would not record a European place of birth this specific.
  > Born 1799 Munich, Spayer Province, Germany.
- **[verified-index]** (w1, date) Mary Dorothea Wand's death (2 Jan 1878, Carrick, Bruce County) is sourced on WikiTree to an actual Archives of Ontario civil death registration microfilm reel, not merely a family tree guess - this is a genuine, independently-checkable government record distinct from the unsourced Bavaria/Munich birthplace claim on the same profile.
  > Source: #S113 Archives of Ontario; Series: MS935; Reel: 18

### https://generations.regionofwaterloo.ca/getperson.php?personID=I96264&tree=generations

- **[verified-index]** (w1, place) The Waterloo Region Generations community database, citing the actual 1851 Census of Canada West (Wilmot Township, Division 4, Page 5), gives Lorenz Nauer's and his wife Dorothea Meyer's birthplace as Prussia, not Bavaria/Palatinate - directly contradicting WikiTree's Speyer/Munich framing for the same couple.
  > Born 1802 , Prussia, Germany [S134] Census - ON, Waterloo, Wilmot - 1851, Div 4 Pg 5
- **[verified-index]** (w1, relationship) The Waterloo Region Generations family-group record for Lorenz Nauer and Dorothea Meyer (sourced to the 1851 census) lists six children - Lorenz Jr., Maria, Carolina, Jacob, John, and a second Maria - and does NOT include Thomas among them, matching the compiled PDF's own hedge that Thomas is only a 'possible' (unproven) son.
  > Children 1. Lorenz Nauer , b. 1833, , Prussia, Germany ... 6. Maria Nauer , b. 1846, , Prussia, Germany

### https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=generations

- **[verified-index]** (w1, date) Waterloo Region Generations, citing the actual church-marriage-register card index at Kitchener Public Library, records Thomas Nauer's 1856 marriage with a witness list and the specific parish detail that the officiating priest was based at Petersburg (Wellesley Township) - richer and slightly different (Berlin, not 'Bridgeport') than what WikiTree states.
  > Thomas Nauer, tanner of Waterloo married 4 Mar 1856 in Berlin by banns to Catherine Christiane Coberger of Waterloo, wit: Benjamin Rudy of Waterloo & Diana Meyer of Woolwich
- **[verified-index]** (w1, relationship) A contemporary 1856 newspaper marriage notice in the Deutsche Canadier (Berlin, Canada West) independently corroborates the marriage date and names the officiating minister as 'Feyfel' of Petersburg - a concrete lead to the specific Catholic circuit/priest serving Thomas Nauer's family before any Waterloo-area parish is confirmed for baptisms.
  > COBERGER, Katharina Chris. married 4 Mar 1856 To Thomas NAUER. Both of W.T. minister Feyfel, Petersburg
- **[verified-index]** (w2, person) Thomas Nauer of Waterloo Township, a tanner, married Catherine Coberger on 4 Mar 1856 in Berlin (Kitchener), witnessed by Benjamin Rudy of Waterloo and Diana Meyer of Woolwich -- matching the Kansas Thomas A. Nauer/Catherina Marie Koeberger couple via near-identical names and seven shared children's names (Bertha, Albert, John, Mary, Amelia/Emmalia, Augusta, Theresa).
  > Thomas Nauer, tanner of Waterloo married 4 Mar 1856 in Berlin by banns to Catherine Christiane Coberger of Waterloo, wit: Benjamin Rudy of Waterloo & Diana Meyer of Woolwich
- **[verified-index]** (w2, place) The Deutsche Canadier newspaper's 1856 marriage notice for the same couple names the officiating minister and his base as Feyfel of Petersburg (a Wilmot Township Catholic mission village), giving a concrete parish-jurisdiction lead distinct from St. Agatha/St. Clements.
  > COBERGER, Katharina Chris. married 4 Mar 1856 To Thomas NAUER. Both of W.T. minister Feyfel, Petersburg
- **[verified-index]** (w2, other) Thomas Nauer's occupation in the 1871 Waterloo Township census was recorded as 'White Tanner' and his household was Roman Catholic -- a specific occupational detail not previously captured in the compiled record.
  > Occupation 1871 Waterloo Twp., Waterloo Region, Ontario, Canada White Tanner

### https://generations.regionofwaterloo.ca/getperson.php?personID=I247851&tree=generations

- **[verified-index]** (w1, date) A distinct Waterloo Region Generations person record for 'Lorenz Nauer', sourced to a contemporary Berliner Journal death notice, gives his death as 2 July 1864 in Carlsruhe, Carrick Township, Bruce County, at age 53 (implying b. c.1811) - this conflicts with WikiTree's uncited claim that Johann Lorenz Nauer died in 1870.
  > Lorenz Nauer died 2 Jul 1864 in Carlsruhe, Carrick Twp., 53 yrs.
- **[verified-index]** (w2, date) A Berliner Journal obituary indexed by WRG gives the Carlsruhe Lorenz Nauer's age at death (2 Jul 1864) as 53 years, implying a birth year of about 1811 -- nine years later than the 1802/1803 birth year given independently by both the WRG census reconstruction and the PDF for the patriarch, suggesting this may be a different Lorenz Nauer rather than resolving the 1864-vs-1870 death-date conflict.
  > Lorenz Nauer died 2 Jul 1864 in Carlsruhe, Carrick Twp., 53 yrs.

### https://generations.regionofwaterloo.ca/getperson.php?personID=I95231&tree=generations

- **[verified-index]** (w1, place) A different, distinct Nauer cluster in the same PDF - John Nauer (b. c.1808) and wife Agatha Ulmer - is independently documented via an actual 1861 Waterloo County marriage-register transcription giving a precise, different German origin (Rottenburg, Württemberg) for a daughter, underscoring that 'Bavaria' is not the only candidate origin circulating for this Nauer surname cluster.
  > Carolus Moser, 24 ... married 15 Oct 1861 Hedwig Nauer, 20, res. Mornington, b. Rottenberg, Wurtenburg, daughter of Johannes and Agatha (Ulmer)

### https://generations.regionofwaterloo.ca/getperson.php?personID=I96273&tree=generations

- **[verified-index]** (w2, relationship) A primary civil marriage register directly names Lorenz ('Lawrence') Nauer and Dorothea ('Doroth') Meyer as the parents of their son John Nauer, who married in Bruce County in 1866 -- the strongest documentary link yet for this specific parent-child pair (though it does not mention Thomas).
  > John Nauer Born: Germany Res: Carrick Township Age: 21 Born: abt 1845 Father: Lawrence Mother: Doroth Meyer Spouse: Paulina Bouder ... married 8 Feb 1866 county: Bruce

### https://generations.regionofwaterloo.ca/getperson.php?personID=I96277&tree=generations

- **[verified-index]** (w2, relationship) WRG's own 1851-census-based reconstruction of Lorenz Nauer's household independently records one of his documented sons (b.1833, Prussia) under the alternate surname 'Wand,' evidence of real Wand/Nauer surname fluidity within this specific family at the marriage-transition generation.
  > Name Lorenz Wand

### https://generations.regionofwaterloo.ca/showsource.php?sourceID=S134&tree=generations

- **[verified-index]** (w2, migration) The 1851 Census of Wilmot Township, the primary source underlying WRG's 'Prussia, Germany' origin claim for Lorenz Nauer and Dorothea Meyer, is identified as an actual Library and Archives Canada government record, not a secondary compilation.
  > Canada. Department of Agriculture, 1851 Census of Wilmot Township, Waterloo, Ontario (1851, Ottawa, Ontario, Canada: Library and Archives Canada, n.d.)

### https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=Generations

- **[verified-index]** (w3, place) WRG's own record for Thomas Nauer gives his birthplace as bare 'Germany' with no state, sourced only to the 1871 Waterloo Township census -- unlike Lorenz's proven children, none of Thomas's own primary-adjacent records anywhere say 'Prussia,' 'Bavaria,' 'Munich,' or 'Speyer.'
  > Thomas Nauer b. 1823 , Germany

### https://generations.regionofwaterloo.ca/search.php?myfirstname=Adam&mylastname=Wand&mybool=AND

- **[verified-index]** (w3, relationship) A direct WRG person-search for Adam Wand returns zero results in a database of 360,805 individuals -- the 'Dorothea Meyer, widow of Adam Wand' narrative has no independent WRG-linked record (marriage, death, or census) behind it anywhere; it rests solely on the compiled PDF.
  > No results found for Last Name contains Wand AND First Name contains Adam. Please try again.

### https://generations.regionofwaterloo.ca/search.php?myfirstname=Dorothea&mylastname=Meyer&mybool=AND

- **[verified-index]** (w3, relationship) WRG's own alternate-name list for Dorothea Meyer (Lorenz Nauer's wife) includes 'Dorothea Nauer,' 'Thorothea,' and 'Thorothea Meyer' but never 'Wand' -- WRG's data model has never linked her to any Wand identity despite otherwise tracking her closely (census, six children, residence).
  > Name Dorothea Nauer Name Thorothea Name Thorothea Meyer

### https://generations.regionofwaterloo.ca/getperson.php?personID=I59692&tree=Generations

- **[verified-index]** (w3, relationship) WRG's profile for Maria Josepha 'Mary' Wandt (who married Karl 'Charles' Gehl and died in Carrick Township in 1879) has no Father or Mother field at all -- her page jumps directly from death/Person-ID to spousal Family with no parent entry, unlike genuinely-linked children of Lorenz Nauer such as John or Lorenz Jr.
  > Died 2 Aug 1879 Carrick Twp., Bruce Co., Ontario, Canada Person ID I59692 Generations Last Modified 11 Jun 2026 Family Karl "Charles" Gehl

### https://generations.regionofwaterloo.ca/getperson.php?personID=I247851&tree=Generations

- **[verified-index]** (w3, person) WRG's 1864 Carlsruhe death record (I247851, age 53 implying b.~1811) is a fully standalone entry with exactly one source (a single newspaper obituary) and no Father, Mother, spouse, or children fields of any kind -- confirming it is entirely disconnected from the census-linked patriarch Lorenz Nauer (I96264, b.1802, six children, wife Dorothea Meyer) inside WRG's own data model.
  > Lorenz Nauer died 2 Jul 1864 in Carlsruhe, Carrick Twp., 53 yrs.

### https://www.wikitree.com/wiki/Nauer-6

- **[compiled]** (w1, place) The same 'Munich, Spayer Province, Germany' phrase is also attached to the proposed parents Johann Lorenz Nauer and Mary Dorothea Wand on their own WikiTree profiles, suggesting it was copied across profiles from a single unsourced tree rather than independently documented for each person.
  > Born 1801 Munich, Spayer Province, Germany.

### https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841

- **[compiled]** (w1, place) The compiled 'German Catholic Settlers of Waterloo County' PDF independently describes Lorenz Nauer and wife Dorothea Meyer, widow of Adam Wand-Wandt, as being 'of Prussia, Germany' - a second, independent compiled source agreeing with the census-sourced Prussia origin rather than Bavaria.
  > Lorenz Nauer and wife Dorothea Meyer, widow of Adam Wand-Wandt, of Prussia, Germany, resided in Wilmot Township by 1851/52
- **[compiled]** (w2, relationship) The compiled Waterloo settlers PDF independently corroborates that surname fluidity, naming a documented Wand daughter (Ann, who married Charles Gehl in 1853 at St. Agatha) and treating a 'Lawrence Wand' born about 1834 as a probable child of Adam Wand and Dorothea Meyer -- the same individual as WRG's 'Lorenz Wand.'
  > Adam Wand-Wandt-Wendt {died before 1852} and wife Dorothea Meyer-Meier {about 1802} had a daughter Ann who married Charles Gehl...in 1853 in St. Agatha...Another possible child was Lawrence Wand {about 1834}
- **[compiled]** (w2, date) The PDF explicitly frames Thomas as a weaker, appendix-level lead relative to Lorenz Nauer's other named children, using the heading 'Additional Notes' rather than listing him among the direct/likely children.
  > Additional Notes: Another possible son of Lorenz Nauer is Thomas Nauer {about 1824} and wife Catharine {about 1834} are residing in Waterloo County in 1871 and Cawker, Mitchell, Kansas by 1880.
- **[compiled]** (w2, place) The same PDF states Lorenz Nauer himself (not just a son) was recorded as an innkeeper in Carrick Township, Bruce County by the 1861 census, matching the frontier brief's 'innkeeper' detail to the patriarch rather than to a descendant.
  > By 1861 this family was residing in Carrick Township, Bruce County and Lorenz Nauer was an innkeeper.
- **[compiled]** (w2, person) The PDF identifies a previously untracked probable son, Peter Nauer (b. about 1838), also working as an innkeeper near the Andrew Zettler family in Bruce County by 1861 -- not present at all in WRG's census-based family reconstruction.
  > Note: Peter Nauer {about 1838}, an innkeeper residing with or near the Andrew Zettler family in 1861 is likely another son of Lorenz Nauer.
- **[compiled]** (w2, other) The compiled PDF's own statistics show Bavaria is a real, if minority, origin for this broader Waterloo County German-Catholic settler community (62 mentions vs. Alsace's 281), meaning a Bavarian origin claim is not implausible for the community in general even though no source ties the Nauer/Meyer family specifically to Bavaria.
  > Most of the individuals in this work are from Alsace, mentioned 281 times, Baden, 245, and Bavaria, 62 times.
- **[compiled]** (w3, place) The compiled Waterloo German-French Catholic Settlers PDF states explicitly, in its own entry for this family, that Lorenz Nauer and Dorothea Meyer (widow of Adam Wand) were 'of Prussia, Germany' -- not Bavaria -- when they settled in Wilmot Township.
  > Lorenz Nauer {about 1803} and wife Dorothea Meyer {about 1802-1878 in Carrick Township, Bruce County}, widow of Adam Wand-Wandt, of Prussia, Germany, resided in Wilmot Township by 1851/52.
- **[compiled]** (w3, other) The same PDF gives precise Palatinate/Bavaria villages for other families in the same document (e.g., a stonemason born in Birkenhördt, Pfalz, Bavaria), showing its 'Prussia' label for the Nauer/Meyer family is a deliberate jurisdictional distinction, not generic filler text.
  > George Jacob Aspenleiter {1812 in Birkenhoerdt, Pfalz, Bavaria}, stonemason-plasterer, son of John and
- **[compiled]** (w3, person) The compiled PDF itself contains an internal date conflict in the Adam Wand paragraph: it has 'Josepha' (Lawrence Wand's wife) dying in Bruce County in 1879, the same year/place as WRG's Wandt-Gehl death, while separately having 'Ann Gehl nee Wand' -- widow of the same Charles Gehl -- remarry Henry Hahn in 1897, which requires her to still be alive 18 years after that 1879 death.
  > Ann Gehl nee Wand married Henry Hahn in 1897 in Waterloo County... Another possible child was Lawrence Wand {about 1834} {Josepha Fischer}{about 1835-1879 in Bruce County} a contractor of Bruce County.
- **[compiled]** (w3, place) The same compiled PDF independently uses 'Bridgeport' as a real Waterloo County (not Oxford County) place name for an unrelated German Catholic family in the 1850s, supporting that any 'Bridgeport, Oxford, Canada West' attribution found for a Nauer family member elsewhere is a county-name transcription error rather than a real second Bridgeport.
  > NOTE: Charles Keller was the son of Joseph Keller and Josepha Beck of Bavaria Germany who were residing in Bridgeport, Canada West in 1857.

### https://www.wellesleyhistory.org/uploads/9/2/9/6/9296178/04_spetz_book_1_appendices_ocr.pdf

- **[compiled]** (w1, place) Rev. Theobald Spetz's 1916 Diamond Jubilee History of the Diocese of Hamilton (covering Waterloo County Catholic settlement) confirms Petersburg, Wellesley Township, had only a small Catholic colony attached to the wider St. Agatha mission network in the settlement era, useful context for locating which parish register would hold a 1856 Nauer-Coberger marriage entry.
  > the next village east, Petersburg, had a few

### https://www.stboniface-maryhill.ca/history.html

- **[compiled]** (w2, place) St. Boniface Catholic parish in Maryhill (Woolwich Township, adjoining Waterloo Township), founded in 1834, is a plausible home parish for the Thomas Nauer family by the 1870s given that son Moritz Thomas Nauer was born there in 1873, offering an alternative to St. Agatha/St. Clements for later parish-register searches.
  > The first settlers were Mathias Fehrenbach, Felix Scharbach and Christian Rich, with the first mass being said in the home of Christian Rich.

### https://en.wikipedia.org/wiki/New_Prussia,_Ontario

- **[compiled]** (w3, place) Wikipedia (citing a 1956 Canadian Catholic Historical Association report) states the Wilmot Township community where Lorenz Nauer's family lived was settled specifically by Rhenish PRUSSIAN Catholics, not Bavarians -- directly supporting 'Prussia' over 'Bavaria/Pfalz' as this family's likely origin state.
  > New Prussia was settled by Roman Catholic immigrants from the Rhine Province of Prussia.

## Search frames (13 unique from 13 raw)

### F1 (w1). What was Thomas A. Nauer's (and his presumed parents Johann Lorenz Nauer/Dorothea Meyer's) actual German origin: Rhenish-Bavarian Palatinate (Rheinkreis/Pfalz, capital Speyer) as WikiTree's garbled 'Munich, Spayer Province' implies, or Rhenish Prussia (Rheinprovinz) as the 1851 Canadian census and the compiled Waterloo PDF both independently state?

- Jurisdictions: Two competing hypotheses to test against each other: (A) Bavarian Rheinkreis/Pfalz (Palatinate), capital Speyer, Kingdom of Bavaria (renamed Pfalz in 1838) vs. (B) Prussian Rhine Province (Rheinprovinz), Kingdom of Prussia, likely Regierungsbezirk Koblenz/Trier/Aachen given the many other 'New Prussia' Waterloo County Catholic settlers from that district. Landing jurisdiction: Wilmot Township then Carrick Township, Bruce County, Canada West/Ontario.
- Record sets:
  - Library and Archives Canada free Census search/digitized images (1851 Wilmot, 1861/1871 Carrick) - view the actual enumerator handwriting for birthplace column -- https://recherche-collection-search.bac-lac.gc.ca/eng/Census/index (1851, 1861, 1871)
  - Waterloo Region Generations (free community DB), Lorenz Nauer/Dorothea Meyer family group, sourced to 1851 census Wilmot Div. 4 Pg 5 -- https://generations.regionofwaterloo.ca/getperson.php?personID=I96264&tree=generations (1851-1852)
  - German Genealogy Group Bavaria & Pfalz Emigration Database (149,500+ names from period emigration notices) - test for a Nauer/Wand/Meyer hit if truly Palatinate -- https://www.germangenealogygroup.com/records-search/german_emigrants.php (1840s emigration notices)
  - Ancestry.com U.S. and Canada, Passenger and Immigration Lists Index (paywalled) - underlying record behind WikiTree citations S22 (1847 'America' entry for Lorenz, page 260) and (1871 Ontario page 111 for Thomas) -- https://www.ancestry.com/search/collections/2185/ (1847, 1871 entries)
- Next pulls:
  1. View the LAC digitized 1851 Wilmot Township census image directly to read the literal birthplace word written for the Lorenz Nauer household (resolves Prussia vs Bavaria at the source rather than trusting any index).
  1. Identify and view the actual Ancestry 'Family Tree' (S8, tree ID 69509776) that WikiTree's Munich/Speyer claim traces back to, to see if it cites any document at all or is itself a guess.
  1. Search German Genealogy Group's free Pfalz emigration database and Speyer Landesarchiv Auswandererkartei-type finding aids for a Nauer emigrating circa 1846-1847 to test the Bavaria hypothesis directly.

### F2 (w1). Is Johann Lorenz Nauer (1801/1802-1870 per WikiTree, uncited) actually the same man as the Waterloo Region Generations 'Lorenz Nauer' who died 2 July 1864 in Carlsruhe, Carrick Township, age 53 (per a Berliner Journal obituary)? If so, WikiTree's death year is wrong and should be corrected to 1864.

- Jurisdictions: Carlsruhe hamlet, Carrick Township, Bruce County, Ontario (formerly Canada West), Canada. Catholic parish jurisdiction likely Immaculate Conception, Formosa (nearest RC parish/cemetery serving Carrick Township) or an earlier mission chapel predating the 1883 Formosa church building.
- Record sets:
  - Waterloo Region Generations - Lorenz Nauer death record, sourced to Berliner Journal obituary -- https://generations.regionofwaterloo.ca/getperson.php?personID=I247851&tree=generations (1864)
  - Immaculate Conception Roman Catholic Cemetery, Formosa, Bruce County - Find a Grave cemetery index (searched, zero Nauer hits as of this pull) -- https://www.findagrave.com/cemetery/2207777/immaculate-conception-roman-catholic-cemetery (burials from settlement era)
  - FamilySearch catalog: Canada, Ontario Roman Catholic Church Records (free browse with account) - check Formosa/Immaculate Conception and any earlier Carrick Township mission register for an 1864 Nauer burial -- https://www.familysearch.org/en/search/collection/1927566 (1760-1923)
  - Berliner Journal (Kitchener Public Library digitized German-Canadian newspaper, 1859-1917) full issue for 11 Aug 1864 - view the obituary in context -- https://www.regionofwaterloo.ca/en/exploring-the-outdoors/newspapers.aspx (1859-1917)
- Next pulls:
  1. Pull the actual Berliner Journal page for 11 Aug 1864 (Kitchener Public Library digitized newspaper collection) to confirm wording and any additional family detail beyond the WRG index snippet.
  1. Search Bruce County cemetery transcriptions (Bruce County Genealogical Society, brucecountygenealogicalsociety.ca) for an early/lost Carlsruhe-area Catholic burial ground that predates the 1883 Formosa church, since Find a Grave shows no Nauer burial there.
  1. Compare WikiTree Nauer-6's uncited 'Died 1870, Ontario, Canada' against its own citation list (S111/S22/S8, none of which mention a death) to confirm the 1870 figure is unsourced and should defer to the 1864 obituary.

### F3 (w1). Is the parent-child link between Thomas A. Nauer and Johann Lorenz Nauer + Dorothea Meyer/Wand real, or is it still just a same-surname/same-place coincidence? What was Dorothea's first husband Adam Wand's fate, and does the Wand family cluster at Carlsruhe (Lorenz Wand, Caroline Wand, John Wand) descend from him?

- Jurisdictions: Wilmot Township (to 1851/52) then Carrick Township/Carlsruhe, Bruce County, Ontario, Canada. Catholic registers: St. Agatha (Church of the Precious Blood) and St. Clements circuit for the Wilmot years; Formosa/Immaculate Conception or an earlier Carrick mission for the Bruce County years.
- Record sets:
  - Waterloo Region Generations - Wand surname index (9 entries, incl. Lorenz Wand of Carlsruhe b. c.1840, likely a second-marriage or first-marriage Wand child of Dorothea) -- https://generations.regionofwaterloo.ca/search.php?mylastname=Wand&lnqualify=equals&mybool=AND&nr=200&tree=-x--all--x- (1840s-1900s vital events)
  - The German Catholic Settlers of Waterloo County PDF - Wand/Nauer compiled narrative naming Adam Wand-Wandt (d. before 1852) and daughter Ann Wand Gehl -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (narrative covers 1840s-1880s)
  - 1851 Census of Canada West, Wilmot Township, Waterloo County (LAC roll C_11754, page 141, lines 47-48) - Lorenz Nauer and Mary Dorothea Wand appear on consecutive census lines; check whether any Wand or Nauer children in that same household entry include a 'Thomas' -- https://recherche-collection-search.bac-lac.gc.ca/eng/Census/index (1851)
- Next pulls:
  1. Pull the 1851 census image itself (LAC roll C_11754, p.141, lines 47-48) to see the full household listing - this is the one record that could either add or rule out a 'Thomas' in the Lorenz Nauer/Dorothea household directly.
  1. Search for St. Agatha or New Germany parish marriage record of Ann Wand to Charles Gehl (1853) and Ann Gehl's 1897 remarriage to Henry Hahn, both named in the compiled PDF, to anchor the Wand family with primary church records.
  1. Trace Lorenz Wand of Carlsruhe (b. c.1840, WRG I247858) forward/backward to see if he is documented as Dorothea's son by Adam Wand (would need a Bruce County-era baptismal or marriage record naming his mother).

### F4 (w1). Which specific Catholic parish register holds Thomas Nauer's 4 March 1856 marriage to Catherine Christiane Coberger, and can it be traced back further to establish where 'minister Feyfel of Petersburg' was actually stationed and whether it links to St. Agatha, St. Clements, or a separate Petersburg mission?

- Jurisdictions: Berlin (now Kitchener) and Petersburg, Wellesley Township, Waterloo County, Canada West. Diocese of Toronto pre-1856, then Diocese of Hamilton (erected 1856) thereafter.
- Record sets:
  - F. W. Bindeman card index of Waterloo-area church marriage records, Kitchener Public Library (source of the Waterloo Region Generations marriage citation) -- https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=generations (citation covers 1856)
  - Deutsche Canadier (1841-1865) births/deaths/marriages index, Waterloo Region Generations (Kitchener Public Library digitization project) -- https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=generations (13 Mar 1856 issue)
  - Rev. Theobald Spetz, Diamond Jubilee History of the Diocese of Hamilton (1916), free OCR PDF - Waterloo County Catholic settlement chapters describing Petersburg, St. Agatha, St. Clements -- https://www.wellesleyhistory.org/catholic-church-history-of-waterloo-county.html (narrative to 1916, covering 1830s-1850s founding)
  - FamilySearch catalog: Canada, Ontario Roman Catholic Church Records - browse for St. Agatha (Church of the Precious Blood) and St. Clements parish register films -- https://www.familysearch.org/en/search/collection/1927566 (1760-1923)
- Next pulls:
  1. Search the FamilySearch catalog specifically for 'St. Agatha' and 'St. Clements, Wellesley Township' Roman Catholic parish register films to find the actual 1856 marriage entry (would give Thomas's and Catherine's parents' names in Latin/German if a full sacramental entry survives).
  1. Identify the priest 'Feyfel' (surname possibly Anglicized/OCR-garbled from Feyerabend, Faller, or similar) via Diocese of Hamilton clergy lists in Spetz's history to confirm which mission register he kept.
  1. Cross-check the Bindeman card index citation directly at Kitchener Public Library (in person or via their local history staff) since it is the base source behind the Waterloo Region Generations entry.

### F5 (w2). Was Thomas A. Nauer a biological son of Johann Lorenz Nauer + Dorothea Meyer, an unrelated same-surname contemporary, or (new hypothesis) an elder son of Dorothea's first husband Adam Wand who adopted the Nauer surname as a stepson -- paralleling his likely half-brother Lorenz/Lawrence Wand-Nauer?

- Jurisdictions: Wilmot Twp. and Waterloo Twp. (Waterloo Co., Canada West/Ontario) 1851-1871; St. Agatha Catholic parish (marriage of presumed half-sister Ann Wand, 1853); Carrick Twp. (Bruce Co.) post-1861 for Lorenz's own line; Cawker City, Mitchell Co., Kansas post-1871/1880 for Thomas's line
- Name variants: Nauer / Wand / Wandt / Wendt; Meyer / Meier; Koeberger / Coberger / Koburger; Lorenz / Lawrence
- Record sets:
  - Waterloo Region Generations - Thomas Nauer (I134297) and family group F36788 -- https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=generations (1823-1871)
  - Waterloo Region Generations - Lorenz Nauer/Dorothea Meyer family group F24846 -- https://generations.regionofwaterloo.ca/familygroup.php?familyID=F24846&tree=generations (1851-1866)
  - 1851 Census of Wilmot Township (LAC, indexed by WRG) -- https://generations.regionofwaterloo.ca/showsource.php?sourceID=S134&tree=generations (1851)
  - Bindeman Card Index of Baptisms, Marriages, Deaths (Kitchener Public Library, indexed by WRG) -- https://generations.regionofwaterloo.ca/showsource.php?sourceID=S6&tree=generations (1850s-1860s)
  - German-French Catholic Settlers of Waterloo County PDF (Bowman/Wideen) -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled 1991-2018, covering 1824-1850s+)
  - Bruce County Marriage Register 1858-1869 (indexed by WRG) -- https://generations.regionofwaterloo.ca/showsource.php?sourceID=S69&tree=generations (1858-1869)
- Next pulls:
  1. Pull the actual 1851 Census of Canada West image for Wilmot Twp Div 4 pp.5-6 from Library and Archives Canada's free digitized census database to check for any Wand-surnamed entries in or near the Lorenz Nauer household, and to see if Thomas appears nearby as an independent adult
  1. Search Waterloo Township 1851/1861 census and any surviving Catholic parish register for a 'Thomas Wand' alias, to test whether Thomas was born to Adam Wand and only adopted 'Nauer' as an adult stepson, matching the documented Lorenz/Lawrence Wand-Nauer pattern
  1. Search St. Agatha parish marriage register (1853, Ann/Maria Josepha Wand x Charles Gehl) for Adam Wand's village of origin, which if found would anchor the whole Wand-Meyer-Nauer cluster to a specific European parish
  1. Request the Diocese of Hamilton Archives' holdings list for Petersburg/St. Agatha/St. Boniface Maryhill Catholic registers 1850s-1870s to identify which register book holds Thomas Nauer's 1856 marriage and his children's baptisms

### F6 (w2). What is the true German origin province for this family -- Rhenish Prussia (per the 1851 census and PDF) or Bavarian Rheinkreis/Pfalz (per WikiTree's uncorroborated 'Munich, Spayer Province')?

- Jurisdictions: Unidentified Prussian village (most likely Rhineland per regional emigration patterns) vs. an internally contradictory 'Munich, Spayer Province' claim; Wilmot Township, Waterloo Co., Ontario as the receiving jurisdiction
- Name variants: Nauer; Meyer/Meier; place-name only, no village yet identified
- Record sets:
  - 1851 Census of Wilmot Township (LAC, indexed by WRG) - gives 'Prussia, Germany' -- https://generations.regionofwaterloo.ca/showsource.php?sourceID=S134&tree=generations (1851)
  - German-French Catholic Settlers of Waterloo County PDF - community origin statistics and 'of Prussia, Germany' language -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled 1991-2018)
  - WikiTree Nauer-7 (uncited 'Munich, Spayer Province, Germany') -- https://www.wikitree.com/wiki/Nauer-7 (n/a - undated compiled profile)
- Next pulls:
  1. WikiTree's Nauer-7 profile is blocked to automated tools this wave by an AWS WAF JavaScript challenge (curl returns a 202 challenge page; WebFetch returns 403) -- a human or JS-capable browser session is needed to actually read the footnoted sources behind 'Munich, Spayer Province'
  1. Search Library and Archives Canada's free 1861 and 1871 census images directly (beyond the WRG index) for the literal 'country of birth' column entries for Lorenz Nauer's household to corroborate or refine 'Prussia'
  1. Check Grosse-Isle/New York passenger arrival indexes (e.g. immigrantships.net, Ancestry's free-to-browse indexes) for a Nauer family arriving before 1852, since ship manifests sometimes record last European residence at village level

### F7 (w2). Did Johann Lorenz Nauer (the Wilmot/Carrick patriarch, b. about 1802-1803) die in 1864 at Carlsruhe or in 1870 as WikiTree states, and is the 1864 Carlsruhe death record actually for him or for a different, younger Lorenz Nauer?

- Jurisdictions: Carlsruhe, Carrick Township, Bruce County, Ontario
- Name variants: Lorenz / Lawrence Nauer
- Record sets:
  - Berliner Journal obituary index, 'Lorenz Nauer' (WRG person I247851, b. CALC 1811, d. 2 Jul 1864, age 53) -- https://generations.regionofwaterloo.ca/getperson.php?personID=I247851&tree=generations (1864)
  - WRG census-based patriarch record (I96264, b.1802, 'Died: Yes, date unknown') -- https://generations.regionofwaterloo.ca/getperson.php?personID=I96264&tree=generations (1851-1852)
  - German-French Catholic Settlers of Waterloo County PDF (patriarch 'about 1803', no death year given) -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled 1991-2018)
- Next pulls:
  1. Search the Saint Francis Xavier Catholic Cemetery/parish burial register, Carlsruhe, for the 1864 burial to see whether the recorded age is 53 or closer to 62 (which would settle whether it is the patriarch)
  1. Search Bruce County land registry grantor/grantee indexes for 'Lorenz Nauer' in Carrick Township to see whether one or two distinct Lorenz Nauers held property there in the 1860s
  1. Search Archives of Ontario probate/estate files (RG 22) for a Lorenz Nauer estate opened in Bruce County circa 1864, which would typically state age and list heirs by name -- this could directly confirm or refute whether Thomas or John were named heirs

### F8 (w2). Who was Adam Wand (Dorothea Meyer's first husband), when did he die, and which of the 'Wand' individuals later found in Carrick Township/Carlsruhe are actually his children versus an unrelated same-surname family?

- Jurisdictions: Wilmot Township, Waterloo Co. (1820s-1852); St. Agatha Catholic parish; Carlsruhe, Carrick Twp., Bruce Co. (later generation, 1860s-1900s)
- Name variants: Wand / Wandt / Wendt; Meyer / Meier
- Record sets:
  - German-French Catholic Settlers of Waterloo County PDF - Adam Wand-Wandt-Wendt entry -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled, covering pre-1852 to 1897)
  - WRG - Maria Josepha 'Mary' Wandt (I59692), possible match to PDF's 'Ann' Wand, m. Charles Gehl, d.1879 Carrick Twp -- https://generations.regionofwaterloo.ca/getperson.php?personID=I59692&tree=generations (CA 1835-1879)
  - WRG - later, likely-unrelated Carlsruhe Wand cluster (Lorenz Wand b.abt 1840, Caroline Wand b.abt 1862, John Wand b.1863) -- https://generations.regionofwaterloo.ca/search.php?mylastname=Wand&tree=generations (1840s-1900s)
- Next pulls:
  1. Reconcile the first-name discrepancy between the PDF's 'Ann' Wand and WRG's 'Maria Josepha Mary' Wandt (both married a Charles/Karl Gehl) via the actual 1853 St. Agatha marriage register entry
  1. Determine whether the later Carlsruhe Wand family (Lorenz Wand b.~1840, children born 1862-1907) is genealogically connected to Adam Wand at all -- the birth years look too late to be Adam Wand's own children given he died before 1852, suggesting a separate, unrelated same-surname family that should not be folded into this line without direct proof
  1. Search Wilmot Township or Waterloo County burial/probate records 1830-1852 for an Adam Wand death record, none of which has yet been located in any source checked this wave

### F9 (w2). Which Catholic parish register holds the fuller sacramental record of Thomas Nauer's 1856 marriage (and any note of his parents), and which parish served his family afterward?

- Jurisdictions: Wilmot Township (Petersburg mission) 1856; Waterloo Township ('Berlin'/Kitchener) 1856-1871; Woolwich Township (Maryhill) by 1873
- Name variants: Nauer; Koeberger / Coberger / Koburger
- Record sets:
  - Deutsche Canadier newspaper index (WRG) - names officiant 'minister Feyfel, Petersburg' -- https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=generations (1856)
  - FamilySearch - Canada, Ontario Roman Catholic Church Records (login-walled, images only) -- https://www.familysearch.org/en/search/collection/1927566 (1760-1923)
  - St. Boniface Parish, Maryhill - founded 1834, plausible home parish by 1873 (son Moritz born there) -- https://www.stboniface-maryhill.ca/history.html (1834-present)
- Next pulls:
  1. Identify 'Fr./Rev. Feyfel' by cross-checking the PDF's priest-name index or Diocese of Hamilton Archives clergy lists, to determine which parish register (St. Agatha, St. Boniface, or a distinct Petersburg mission book) recorded the 1856 marriage
  1. FamilySearch's Ontario Roman Catholic Church Records collection is login-walled (a free account is required to view images) -- flag as a next pull for a researcher with a FamilySearch login rather than assuming its contents
  1. Search St. Boniface Maryhill's surviving baptismal registers 1857-1869 for Thomas Nauer's children, which sometimes carry marginal notes naming grandparents

### F10 (w3). Which German state -- Rhenish Prussia (Rheinprovinz) or Rhenish Bavaria/the Palatinate (Rheinkreis/Pfalz, capital Speyer) -- was the actual origin of Lorenz Nauer and Dorothea Meyer's family, and does that origin apply to Thomas at all?

- Jurisdictions: Village/parish unknown; Regierungsbezirk unknown; state = Kingdom of Prussia, Rhine Province (per WRG census + PDF + New Prussia settlement history) OR Kingdom of Bavaria, Rhine Circle/Palatinate (per WikiTree's uncited text only); German Confederation era (pre-1871); Wilmot Township, Waterloo County, Canada West as the receiving jurisdiction.
- Record sets:
  - WRG 1851 Census of Wilmot Township reconstruction (says 'Prussia, Germany' for all 6 documented children) -- https://generations.regionofwaterloo.ca/showsource.php?sourceID=S134&tree=Generations (1851-1852)
  - Library and Archives Canada, 1851/1852 Census of Canada West, Wilmot Twp, Waterloo Co. (original images; Cloudflare-protected, must browse manually, free) -- https://recherche-collection-search.bac-lac.gc.ca/eng/Census/index (1851-1852)
  - New Prussia, Ontario settlement history (Rhine Province of Prussia origin, sourced to 1956 CCHA report) -- https://en.wikipedia.org/wiki/New_Prussia,_Ontario (1830s-1900s)
  - German Catholic Settlers of Waterloo County PDF (states 'of Prussia, Germany' for this family; gives precise Palatinate villages for other families) -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled, covers 1830s-1900s)
  - Matricula Online (free digitized Catholic parish registers; Bistum Aachen substantially covered free, Bistum Trier/Bistum Speyer mostly on paywalled Archion instead -- check current coverage before relying on this) -- https://data.matricula-online.eu/de/deutschland/ (varies by diocese)
  - Deutsche Auswanderer-Datenbank (German Emigrants Database, Bremerhaven) -- free name search, ~28,000 pre-1865 records -- https://www.deutsche-auswanderer-datenbank.de/ (pre-1865)
- Next pulls:
  1. Pull the actual 1851/1852 LAC census image for Wilmot Twp, Division 4, pages 5-6 (not just WRG's transcription) to check whether the enumerator wrote anything more specific than 'Prussia' in the birthplace column.
  1. Search NY passenger arrival lists (free FamilySearch 'New York Passenger Arrival Lists (Castle Garden), 1820-1892' collection) for a Lorenz/Lawrence Nauer family group arriving 1847-1851 (the family's last Prussia-born child was born 1846 and they are first recorded in Ontario in 1851/52), which would fix a specific German port-of-departure town.
  1. Once a specific town or Kreis is identified, pick the matching diocese (Aachen = free on Matricula; Trier/Köln/Speyer = largely paywalled Archion or not yet public) before paying for any subscription access.

### F11 (w3). Did Dorothea Meyer really have a first husband named Adam Wand who died before 1852, and if so, where is the marriage or death record that proves it -- since neither exists inside WRG's own primary-linked database?

- Jurisdictions: Wilmot Township / St. Agatha Catholic mission, Waterloo County, Canada West (if the first marriage happened in Ontario) OR an unidentified European parish (if it happened before emigration); no civil registration existed in Canada West before 1869, so any Ontario-side proof would be a Catholic parish register entry.
- Record sets:
  - Canada, Ontario Roman Catholic Church Records (FamilySearch, free with registration, 126,534 images, multiple parishes) -- https://www.familysearch.org/en/search/collection/1927566 (1760-1923)
  - WRG person search interface (currently returns zero Adam Wand records) -- https://generations.regionofwaterloo.ca/search.php (n/a)
  - German Catholic Settlers of Waterloo County PDF, Wand entry (sole existing source for Adam Wand's existence) -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled)
- Next pulls:
  1. Search the FamilySearch Ontario RC church records collection directly for a Wilmot Twp/St. Agatha marriage entry 'Dorothea Meyer, widow Wand' x 'Lorenz Nauer,' which must predate 1833 (birth of their first census-documented child Lorenz Jr.).
  1. Contact the compiler/author of the Waterloo German Catholic Settlers PDF (a wsimg.com-hosted site, likely a named genealogist or society) to ask for the specific citation behind the 'Adam Wand-Wandt-Wendt {died before 1852}' entry, since it does not appear to derive from any record WRG has indexed.
  1. Check the Bruce County Genealogical Society's Carrick Township page for any independent transcription of Carlsruhe-area Catholic registers that might name Adam Wand directly.

### F12 (w3). Does Thomas Nauer (b.1823/24) actually belong to the Lorenz Nauer/Dorothea Meyer household at all, given that his own WRG and Find A Grave records give only 'Germany' (no state) for his birthplace and WikiTree lists him with no known siblings?

- Jurisdictions: Waterloo Township and Wilmot Township, Waterloo County, Canada West/Ontario (Thomas's documented residence); unknown European origin.
- Record sets:
  - WRG Thomas Nauer profile (I134297) -- no Father/Mother field -- https://generations.regionofwaterloo.ca/getperson.php?personID=I134297&tree=Generations (1856-1880)
  - WikiTree Nauer-7 (Thomas) -- parents named but siblings marked unknown, birthplace uncited -- https://www.wikitree.com/wiki/Nauer-7 (compiled)
  - Deutsche Auswanderer-Datenbank and NY/Quebec passenger lists 1846-1851 for the Lorenz Nauer household -- test whether an adult 'Thomas Nauer' (b.~1824) travels with them -- https://www.deutsche-auswanderer-datenbank.de/ (1846-1851)
- Next pulls:
  1. If a Lorenz Nauer household passenger manifest is found (see Frame 1), check specifically for an adult male traveler aged ~22-27 named Thomas alongside the six known children -- this is the single most decisive test available.
  1. Pull WikiTree Nauer-6 (Johann Lorenz Nauer) and Wand-109 (Mary Dorothea Wand) profile pages once the AWS WAF challenge clears, to see whether either lists Thomas among documented children or cites a source for the parent-child link that Thomas's own page lacks.
  1. Search for an original 1856 marriage register or banns record for Thomas Nauer x Catherina Coberger (Berlin/Petersburg, Waterloo Co.) beyond the newspaper-index abstract, since an original Catholic register entry sometimes names the groom's parents or origin parish.

### F13 (w3). Who exactly was the woman who married Charles Gehl -- 'Ann Wand' (per the PDF, later remarrying Henry Hahn in 1897) or 'Maria Josepha Mary Wandt' (per WRG, died 1879) -- and are these one person or two, given the PDF's own internal date conflict?

- Jurisdictions: St. Agatha Catholic parish and Carrick Township, Bruce County, Ontario (Charles Gehl's second known residence before his 1891 death in Thunder Bay District).
- Record sets:
  - WRG Maria Josepha 'Mary' Wandt / Karl Charles Gehl family record -- https://generations.regionofwaterloo.ca/getperson.php?personID=I59692&tree=Generations (1835-1891)
  - German Catholic Settlers of Waterloo County PDF, Wand/Gehl passage -- https://img1.wsimg.com/blobby/go/c0db0dfe-27d2-4632-889f-eeb26fbb14e1/downloads/f7bcaab9-38ae-4388-a9eb-f4fbecb15a21/Waterloo%20German%20Catholic%20Settlers.pdf?ver=1781326202841 (compiled)
  - Ontario civil marriage registrations (would include an 1897 Henry Hahn x Ann Gehl entry if it exists) -- https://www.familysearch.org/en/search/collection/1467268 (1869-1928)
- Next pulls:
  1. Search FamilySearch's free Ontario civil marriage registration collection (1869-1928) for a 1897 Waterloo County entry for Henry Hahn marrying a widowed 'Ann Gehl' -- her stated maiden name, age, and parents on that record would settle whether she is Wand-born or someone else entirely.
  1. Search the same collection or the 1853 St. Agatha parish register for the original marriage of Charles Gehl's first wife to see whether she is recorded as 'Ann' or 'Josepha' -- the PDF may have merged two different Gehl wives into one narrative.

