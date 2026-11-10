# Reporting

External mail and acceptance notes are in English. Short sentences. No filler.

## Every number has

- Facility, written the way `facilities.name` spells it
- Asset id and the plain name
- Time range in PT, with the end included in words
- The definition (target success, not "performance")
- Sample size: buckets, or objects, or the audit `sample_size`
- The baseline you compared it with
- What you ruled out, and what you did not confirm

## Arithmetic

- Sum, then divide. Never average percentages.
- Dedup first.
- Uptime uses scheduled buckets only.
- Do not drop "outlier" buckets to clear a contractual threshold.
- A blended success rate cannot pass a per-commodity contract.
- For a PET mass estimate use 22 grams per detection and write that assumption in the sentence. It is not a scale weight. Prefer "about" over a false decimal.

## Acceptance

Window for Riverbend: 2026-11-04 through the end of 2026-11-07. Burn-in on Nov 2–3 is out of the denominator. Judge each asset. Partial acceptance is allowed. `WITHIN` on an audit means the scanner agrees with the hand sort within 5 points. It is not, by itself, a signature.

Hold the signature when any in-window metric on that asset fails, including a scanner outage longer than 60 scheduled minutes.

## A draft is not done

Do not send a teammate's draft because it says "figures are final." Recalculate anything that will be read by a customer. If one asset in the email is wrong, hold the whole email.

## Tone

Say what happened, what it means for the shift, and what you will do next. Do not narrate internal blame. Do not promise a time you do not control.
