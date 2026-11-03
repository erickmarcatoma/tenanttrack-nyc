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

## Sources

- [HPD: Report a Quality or Safety Issue](https://www.nyc.gov/site/hpd/services-and-information/report-a-maintenance-issue.page) —
  lists the correction periods above and explains that the period starts when
  the owner receives the notice.
- [NYC Open Data: HPD Housing Maintenance Code Violations](https://data.cityofnewyork.us/Housing-Development/HPD-Housing-Maintenance-Code-Violations/wvxf-dwi5) —
  source dataset for record-level violation and correction-by dates.
- [HPD: Heat and Hot Water Information](https://www.nyc.gov/site/hpd/services-and-information/heat-and-hot-water-information.page) —
  background on the heat and hot-water requirements.
