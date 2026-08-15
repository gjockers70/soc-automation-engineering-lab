# Failure scenario register

| ID | Scenario | Injection method | Expected signal | Safe recovery |
|---|---|---|---|---|
| P12-F01 | MISP unavailable | Local connection-refusal substitute | misp:unavailable, 3 attempts | Retry after health recovers |
| P12-F02 | Malformed webhook | Real gateway, incomplete synthetic body | HTTP 422 | Correct schema and resend |
| P12-F03 | API timeout | Local timeout substitute | misp:timeout, 3 attempts | Remove latency cause and retry |
| P12-F04 | Duplicate delivery | Real gateway, repeated exact key and body | HTTP 202 duplicate | No repair; retain original receipt |
| P12-F05 | TheHive unavailable | Local connection-refusal substitute | thehive:unavailable, 3 attempts | Restore readiness and replay |
| P12-F06 | Endpoint disconnected | Ten-minute-old synthetic heartbeat | disconnected | Restore telemetry/collector if approved |
| P12-F07 | Malformed IOC | Three invalid synthetic candidates | 3 rejected, 0 enriched | Correct mapping or discard IOC |
| P12-F08 | Service authentication failure | Local HTTP 401 substitute | authentication, 1 attempt | Restore protected credential |

Each scenario ends with response_action_executed=false. The harness never disables accounts, blocks addresses, quarantines endpoints, stops services, or changes endpoint state.
