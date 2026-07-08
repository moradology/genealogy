Source intake file: research/frontier-intake/19-connelly-durham-ford-staples.md
Graduated: 2026-07-08; Case: case.15

### F2 (w1). What North Carolina county did David Monroe Durham's family come from, and who were his parents? (WKU's own 1981-1983 newsletter queries from two different named researchers went unanswered in the volumes checked.)

- Jurisdictions: Unidentified North Carolina county of origin (Caswell County is an unproven hypothesis based on the Ford migration pattern, not yet confirmed for the Durhams specifically); Muhlenberg/Hopkins County KY (Nebo, death 1897); Menard County, Illinois (marriage 1857)
- Record sets:
  - Muhlenberg County Heritage Vol. 5 No. 1 (1983) -- family Bible record, full sibling list -- https://web.archive.org/web/20231219224240/https://digitalcommons.wku.edu/cgi/viewcontent.cgi?article=1021&context=muhlenberg_cty_heritage (1832-1931)
  - Muhlenberg County Heritage Vol. 3 No. 4 (1981) -- Mrs. Virginia E. Tice query, unanswered -- https://web.archive.org/web/20240730124324/https://digitalcommons.wku.edu/cgi/viewcontent.cgi?article=1014&context=muhlenberg_cty_heritage (1981)
  - Muhlenberg County Heritage Vol. 6 No. 1 (1983) -- Mrs. Pat Brock query, unanswered -- https://web.archive.org/web/20240804143903/https://digitalcommons.wku.edu/cgi/viewcontent.cgi?article=1026&context=muhlenberg_cty_heritage (1983)
  - Illinois Statewide Marriage Index, 1763-1900 (free, but bot-blocked to automated fetch -- must be searched manually in a browser) -- https://apps.ilsos.gov/isavital/marriagesrch.jsp (1763-1900)
  - 1850 North Carolina census (Caswell and adjoining counties) -- free FamilySearch index -- https://www.familysearch.org/en/search/collection/1401638 (1850)
- Next pulls:
  1. Manually query the Illinois Statewide Marriage Index for groom 'Durham' x bride 'Ford', Menard County, 1857, to obtain the volume/page citation for the original marriage record (the automated fetch was blocked by the state's bot-detection WAF, not by absence of data).
  1. Locate David Monroe Durham's own cemetery/Find A Grave record (not yet found in this pass) to check for a stated birthplace or family plot at Nebo.
  1. Search the free FamilySearch 1850 census index for Durham households in Caswell County and adjoining North Carolina counties (Person, Rockingham, Orange) for a male aged ~18 matching an 1832 birth, to test the Caswell-origin hypothesis before ruling out other counties.
  1. Check the Hopkins County KY probate/estate index for 1897-1900 for a David Monroe Durham estate file, which may name heirs and could indirectly confirm family details even if it does not name his own parents.
  1. Check later, unpulled volumes of Muhlenberg County Heritage (the full run spans 1978-2001 on digitalcommons.wku.edu) for a reader reply to the Tice or Brock queries -- none appeared answered in the four issues pulled here.

### F7 (w2). What North Carolina county did David Monroe Durham (b. 28 Dec 1832 - d. 24 Aug 1897, Nebo, Hopkins Co. KY) and his own parents come from?

- Jurisdictions: Unknown North Carolina county -> Menard/Sangamon County, Illinois (transit, married there 1857) -> Muhlenberg/Hopkins Co., Kentucky (final settlement)
- Record sets:
  - Muhlenberg County Heritage newsletter (WKU Digital Commons) -- full run 1978-2001, ~90 issues; only 4 reviewed to date across two research passes, direct WKU fetch returns empty HTTP 202, most issues not yet mirrored on Wayback Machine -- https://digitalcommons.wku.edu/muhlenberg_cty_heritage/ (1978-2001)
  - Otto Rothert, 'A History of Muhlenberg County' (1913) -- checked this pass, contains zero independent Durham-family content beyond the one Ford-footnote mention -- https://archive.org/details/historyofmuhlenb00roth (1913)
  - Illinois Statewide Marriage Index, 1763-1900 (official IL State Archives database) -- returned HTTP 403 to automated fetch this pass, needs manual browser search -- https://apps.ilsos.gov/isavital/marriagesrch.jsp (1763-1900)
  - 1850 US Census, Menard Co., IL (FamilySearch) -- JS shell blocked automated access -- https://www.familysearch.org/en/search/collection/1401638 (1850)
- Next pulls:
  1. Manually search the Illinois Statewide Marriage Index for the Durham x Ford, Menard County, 1857 record to get the license/return citation and any parent or witness names on the original document.
  1. Manually pull the 1850 census for Menard Co., IL to find David M. Durham (would be ~17-18, likely still in a parental household) and read his father's and mother's names/ages/birthplaces directly.
  1. Systematically work through the ~85 unreviewed Muhlenberg County Heritage issues via Wayback Machine as more get archived, focusing on any 'answers to queries' sections following the 1981 (Tice) and 1983 (Brock) unanswered queries about David Monroe Durham's NC origin.
  1. Check Menard/Sangamon County, IL local/county history books (often free on Internet Archive) for a Durham family biographical sketch.

### F9 (w3). Which David Monroe Durham identity is correct -- the fully cross-linked Find A Grave cluster (1829-1887, born Virginia, buried Durham Cemetery, Madisonville) or WKU's compiled record (28 Dec 1832-24 Aug 1897, born North Carolina, died Nebo) -- and does either rest on an actual headstone?

- Jurisdictions: Hopkins County, Kentucky (Nebo and Madisonville, ~10 miles apart, same county); Menard County, Illinois (1857 marriage); North Carolina vs. Virginia birth disputed
- Record sets:
  - Muhlenberg County Heritage, Vol. 5 No. 1 (WKU digitalcommons) -- https://digitalcommons.wku.edu/cgi/viewcontent.cgi?article=1021&context=muhlenberg_cty_heritage
  - Find A Grave: David Monroe Durham (1829-1887) -- https://www.findagrave.com/memorial/208617503/david_monroe-durham
  - Find A Grave: Virginia Ann Ford Durham (1842-1931) -- https://www.findagrave.com/memorial/171887228/virginia_ann-durham
  - Find A Grave: Durham Cemetery, Madisonville, Hopkins Co. KY -- https://www.findagrave.com/cemetery/2626305/durham-cemetery
  - Find A Grave: America Ellen Durham Connelly -- https://www.findagrave.com/memorial/203439026/america_ellen-connelly
  - Illinois Statewide Marriage Index, 1763-1900 (blocked, HTTP 403/000 on every fetch attempt) -- https://apps.ilsos.gov/isavital/marriagesrch.jsp
- Next pulls:
  1. Request the Durham Cemetery, Madisonville full memorial list via a logged-in Find A Grave session (this pass's server-side scrape returned no listing, likely JS-rendered) to see if a second Durham grave or a death-year-correcting note exists
  1. Pull the original Menard County, IL 19 Aug 1857 marriage license/return for David M. Durham x Virginia A. Ford in person or via the Menard County Clerk -- would typically state groom's age/residence and sometimes nativity
  1. Search Hopkins County, KY probate/estate/deed indexes for a David M. Durham estate filing in either 1887 or 1897 -- the filing date would independently settle the death-year conflict
  1. Retry the Illinois Statewide Marriage Index with a logged-in browser session rather than curl/WebFetch, since it returns 403/connection-refused to both on every path tried this pass
