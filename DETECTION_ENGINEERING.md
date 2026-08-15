# Detection engineering

## Security concept

A detection converts a security hypothesis into testable logic over a defined event source. Good detection engineering records what must be logged, why the behavior matters, how severity was chosen, expected false positives, how the rule was tested, and how it will be tuned or retired.

Phase 4 implements three behavioral hypotheses:

| ID | Hypothesis | Wazuh rule | Sigma |
|---|---|---:|---|
| `SOC1001` | Repeated invalid SSH usernames from one source may represent credential guessing. | 100100 | Portable base-event rule |
| `SOC1002` | Encoded PowerShell reduces command visibility and warrants investigation. | 100101 | Process-creation rule |
| `SOC1003` | Unplanned user creation can provide unauthorized access or persistence. | 100102 | Security-event rule |

## Rule lifecycle

```text
Hypothesis
  -> source and field verification
  -> rule implementation
  -> structural validation
  -> safe positive test
  -> negative and false-positive review
  -> test deployment
  -> monitoring and tuning
  -> promotion, revision, or retirement
```

These rules remain in test status. A live positive match proves that the event pipeline and matching logic work; it does not prove acceptable false-positive rates in a production environment.

## Severity

Wazuh levels reflect operational attention rather than certainty. Rule 100102 uses level 9 for a security-relevant identity event. Rules 100100 and 100101 use level 10 because temporal correlation or command obfuscation raises triage priority. No rule triggers an automatic response.

## Wazuh and Sigma relationship

Wazuh XML is platform-specific executable logic that can inherit decoded fields and correlate prior Wazuh rule matches. Sigma is a vendor-neutral expression of detection intent that must be mapped through an appropriate backend and field pipeline before use in a target SIEM. The two implementations are comparable but not identical.

See the individual records under `detections/documentation/` for purpose, source, logic, false positives, validation, tuning, and response guidance.
