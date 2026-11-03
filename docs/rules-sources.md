# HPD correction-period sources

Research checked November 2, 2026. These are HPD correction periods, not legal
advice. The dates on an individual HPD notice or in the HPD dataset should take
precedence over a class-based estimate.

## Official correction periods

HPD says the owner must correct a violation within the period measured from
when the owner receives the Notice of Violation:

| HPD class or condition | Correction period |
| --- | --- |
| Class A (non-hazardous) | 90 days |
| Class B (hazardous) | 30 days |
| Class C lead-based paint | 21 days |
| Class C window guards, mold, mice/cockroaches, or rats | 21 days |
| Class C self-closing door | 14 days |
| Class C heat or hot water | Immediately |
| Class C, all other types | 24 hours |

HPD's page describes the periods as beginning when the owner receives the
notice. "Immediately" is HPD's stated period for Class C heat or hot water; it
should not be silently treated as a full 24-hour allowance.

## Application to TenantTrack

The HPD Housing Maintenance Code Violations dataset provides record-specific
correction-by dates (`newcorrectbydate` and `originalcorrectbydate`). The app
already prefers those dates when present. Keep that precedence: class-based
periods are only a fallback when a record has no correction-by date.

The current fallback of 90 days for A, 30 days for B, and one day for C does
not capture HPD's listed Class C exceptions. In particular, lead paint,
window guards, mold, pests, self-closing doors, and heat/hot-water conditions
need distinct treatment if no record-specific correction-by date is available.

The class-based fallback uses the violation's issue date as an estimate; HPD
measures the period from when the owner receives the notice, a date not
available to this calculation. The immediate heat/hot-water period is
represented by the issue date (zero additional days) when no dataset date is
available. Always prefer the record-specific correction-by date when present.

## Sources

- [HPD: Report a Quality or Safety Issue](https://www.nyc.gov/site/hpd/services-and-information/report-a-maintenance-issue.page) —
  lists the correction periods above and explains that the period starts when
  the owner receives the notice.
- [NYC Open Data: HPD Housing Maintenance Code Violations](https://data.cityofnewyork.us/Housing-Development/HPD-Housing-Maintenance-Code-Violations/wvxf-dwi5) —
  source dataset for record-level violation and correction-by dates.
- [HPD: Heat and Hot Water Information](https://www.nyc.gov/site/hpd/services-and-information/heat-and-hot-water-information.page) —
  background on the heat and hot-water requirements.

## Live data spot-check

Checked November 2, 2026 against the public HPD Housing Maintenance Code
Violations dataset. The three reports were loaded locally by BIN. For each
building, the five most recently issued open violations with an issue date
were selected. The app's `parse_violations` and `evaluate_violation` functions
were used; the expected deadline is the dataset's `newcorrectbydate`, falling
back to `originalcorrectbydate`, and status is evaluated as of November 2,
2026. All 15 app deadlines matched the dataset correction-by dates.

| Building | Violation ID | Class | Issued | HPD correct-by | App status | Match |
| --- | ---: | :---: | --- | --- | --- | :---: |
| 765 Lincoln Avenue, Brooklyn | 19305476 | C | 2026-10-19 | 2026-10-25 | Overdue | Yes |
| 765 Lincoln Avenue, Brooklyn | 19305477 | C | 2026-10-19 | 2026-10-25 | Overdue | Yes |
| 765 Lincoln Avenue, Brooklyn | 19305478 | C | 2026-10-19 | 2026-11-14 | On time | Yes |
| 765 Lincoln Avenue, Brooklyn | 19305479 | B | 2026-10-19 | 2026-11-23 | On time | Yes |
| 765 Lincoln Avenue, Brooklyn | 19305480 | B | 2026-10-19 | 2026-11-23 | On time | Yes |
| 1055 Bergen Street, Brooklyn | 19300156 | A | 2026-10-16 | 2027-01-19 | On time | Yes |
| 1055 Bergen Street, Brooklyn | 19300155 | A | 2026-10-16 | 2027-01-19 | On time | Yes |
| 1055 Bergen Street, Brooklyn | 19300154 | A | 2026-10-16 | 2027-01-19 | On time | Yes |
| 1055 Bergen Street, Brooklyn | 19300153 | B | 2026-10-16 | 2026-11-20 | On time | Yes |
| 1055 Bergen Street, Brooklyn | 19300157 | B | 2026-10-16 | 2026-11-20 | On time | Yes |
| 530 East 169 Street, Bronx | 19331362 | C | 2026-10-28 | 2026-11-11 | On time | Yes |
| 530 East 169 Street, Bronx | 19331363 | C | 2026-10-28 | 2026-11-03 | Due soon | Yes |
| 530 East 169 Street, Bronx | 19331361 | C | 2026-10-28 | 2026-11-03 | Due soon | Yes |
| 530 East 169 Street, Bronx | 19331360 | C | 2026-10-28 | 2026-10-28 | Overdue | Yes |
| 530 East 169 Street, Bronx | 19330320 | B | 2026-10-27 | 2026-12-01 | On time | Yes |

The local report pages returned HTTP 200 for all three BINs. The public dataset
request returned HTTP 200 with the configured NYC Open Data token. Address
lookups initially failed because the app used the retired
`/geo/geoclient/v2` endpoint; the supported endpoint is
`/geoclient/v2`. After correcting the default URL, Geoclient returned matches
for all three addresses. This spot-check verifies that the app honors HPD's
record-level dates and classifies status against them; it does not
independently validate HPD's underlying correction-period calculation.
