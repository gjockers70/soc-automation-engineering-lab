# Phase 14 validation

Validation is complete when:

- the full suite passes under strict pytest configuration;
- webhook parsing and authentication paths are covered;
- IP, domain, URL, and hash extraction and normalization are covered;
- scoring boundary behavior is deterministic;
- delivery and incident duplicate controls are covered;
- Wazuh, Shuffle, MISP, and TheHive clients use mocked responses;
- rate limit, timeout, unavailable, authentication, and HTTP failures are covered;
- failed incident handoff and dependency recovery release incomplete state;
- approval enforcement fails closed;
- configuration loading and secret redaction are covered;
- tests require no live service or network access;
- JSON assets parse and Python sources compile.

## Result

All 83 tests passed on August 14, 2026 (America/Chicago) in under one second of pytest execution. The suite used the pinned project environment and no live API.

The expanded tests identified one defensive normalization edge case: untrusted local MISP metadata could exceed the confidence model bound or provide tags with the wrong type. The implementation now clamps confidence to 0-100 and accepts metadata tags only when represented as a list of strings. The complete suite passed after the correction.

Sanitized evidence is stored in evidence/phase14-test-validation.json.
