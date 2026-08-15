# Local threat-intelligence workflow

This directory contains the safe MISP fixtures and standard-library Python clients used in Phase 5.

## Files

- `fixtures/synthetic_indicators.json`: reserved and benign indicators with controlled reputation metadata.
- `scripts/misp_common.py`: API transport, input validation, response extraction, and normalization.
- `scripts/seed_misp.py`: idempotent MISP event/attribute creation.
- `scripts/enrich_ioc.py`: one-indicator lookup returning normalized JSON.
- `example-results/`: sanitized examples captured from live local validation.

## Seed

Run on `soc-mgr-01` after the MISP API is healthy:

```bash
python3 /opt/soc-lab/threat-intel/seed_misp.py \
  --fixture /opt/soc-lab/threat-intel/synthetic_indicators.json
```

The first run creates four attributes. A second run must report zero created and four existing.

## Enrich

```bash
python3 /opt/soc-lab/threat-intel/enrich_ioc.py suspicious-login.test \
  --type domain \
  --fixture /opt/soc-lab/threat-intel/synthetic_indicators.json
```

Supported logical types are `ip`, `domain`, `url`, and `hash`. The client reads the local API URL and key from `/opt/soc-lab/secrets/misp.env`. Do not copy that file into the repository.

The fixture metadata is used only after a matching attribute is returned by MISP. This prevents a local fixture from asserting reputation when the platform has no matching record.
