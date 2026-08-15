# Detection-as-code repository

Phase 4 stores portable Sigma rules, deployed Wazuh rules, safe test events, and a detection record for every implemented behavior.

```text
detections/
├── sigma/
├── wazuh/
├── test-events/
└── documentation/
```

The Wazuh rules are the executable lab implementation. Sigma captures transferable detection intent and field expectations; it is not described as automatically native to Wazuh. Rule status remains `test` until sufficient representative benign and suspicious telemetry supports promotion.

Install `detections/requirements.txt`, then run `python3 detections/validate.py` for repository relationships and `python3 detections/validate_with_pysigma.py` for official pySigma parsing.
