# Automated enrichment and scoring

Phase 9 connects authenticated alert intake to local MISP enrichment, deterministic triage scoring, analyst summaries, and TheHive case creation. All data is synthetic and no response action is available in this phase.

## Processing flow

1. Validate the Wazuh-style webhook and its delivery idempotency key.
2. Recursively extract valid IP, domain, URL, and MD5/SHA-1/SHA-256 indicators.
3. Query local MISP and normalize each result into a stable JSON model.
4. Calculate an explainable score from Wazuh rule level, maximum local-intelligence confidence, and validated indicator count.
5. Generate an analyst-facing summary that states no response occurred.
6. Fingerprint the one-hour UTC correlation bucket, rule ID, endpoint ID, and sorted normalized indicators.
7. Create one TheHive case or reuse the case already associated with that fingerprint.
8. Record the outcome in the append-only audit log.

## Normalized enrichment

Each result contains `indicator`, `type`, `sources`, `reputation`, `confidence`, `tags`, and a UTC `timestamp`. A MISP miss remains `unknown` with confidence `0`; the pipeline does not convert absence of intelligence into a benign verdict.

The lab fixtures use locally authored metadata. Confidence expresses how strongly that source supports its assessment, not the probability that an alert is malicious. Reputation and confidence are inputs to analyst triage, not substitutes for investigation.

## Scoring model

The score is capped at 100:

- Wazuh rule level: `min(level × 4, 60)`
- maximum confidence among matched local-MISP results: `round-half-up(confidence × 0.3)`
- validated indicator count: `min(count × 2, 10)`

Severity thresholds are low `0–29`, medium `30–59`, high `60–79`, and critical `80–100`. Every API response and case description includes the factors. This model is deliberately simple and deterministic so an analyst can challenge or tune it; it is not a claim of production detection accuracy.

## Duplicate boundaries

Delivery idempotency and incident deduplication solve different problems:

- Reusing an `Idempotency-Key` with the same payload suppresses a transport replay. Reusing it with different content returns HTTP 409.
- Separate alert deliveries in the same one-hour UTC bucket with the same rule ID, endpoint ID, and normalized indicators reuse one incident. A later bucket can create a new investigation.

The incident fingerprint is stored in SQLite and in a TheHive case tag. The local store prevents concurrent duplicate creation; the case tag supports recovery if local state must be reconstructed.

## Failure behavior

If enrichment or incident creation fails, the incident reservation is released while the durable delivery enters bounded retry state. The intake API has already acknowledged only after persistence, so recovery does not depend on the producer resending it. Terminal failures remain visible for explicit analyst replay. Consequential response remains outside this pipeline and requires the separately authenticated approval workflow.
