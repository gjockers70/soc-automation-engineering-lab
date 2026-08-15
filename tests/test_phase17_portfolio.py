'''Final portfolio-documentation consistency tests.'''

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_requested_top_level_documentation_exists() -> None:
    for name in (
        'README.md',
        'ARCHITECTURE.md',
        'SOC_OPERATIONS.md',
        'INCIDENT_RESPONSE_PLAN.md',
        'PLAYBOOKS.md',
        'DETECTION_ENGINEERING.md',
        'THREAT_INTELLIGENCE.md',
        'RUNBOOK.md',
        'TROUBLESHOOTING.md',
        'SECURITY.md',
    ):
        assert (ROOT / name).is_file()


def test_readme_is_portfolio_first_and_final_phase_is_complete() -> None:
    readme = read('README.md')
    for heading in (
        '## Problem and outcome',
        '## Current architecture',
        '## Implemented stack',
        '## Alert lifecycle',
        '## Portfolio evidence',
        '## Dashboard preview',
        '## Playbooks and detections',
        '## Security and operational controls',
        '## Commercial-platform transfer',
        '## Known limitations',
        '## Repository map',
    ):
        assert heading in readme
    assert '| 17 | Documentation and portfolio cleanup | Complete |' in readme


def test_commercial_mapping_is_explicit_and_non_equivalent() -> None:
    mapping = read('docs/COMMERCIAL_PLATFORM_MAPPING.md')
    for product in ('Tines', 'ThreatQ', 'Andesite'):
        assert product in mapping
    assert 'does not use or claim experience administering' in mapping
    assert 'not equivalence or feature-parity claims' in mapping


def test_job_mapping_contains_evidence_and_honest_gaps() -> None:
    mapping = read('docs/JOB_REQUIREMENTS_MAPPING.md')
    assert '## Demonstrated requirements' in mapping
    assert '## Remaining experience gaps' in mapping
    assert 'Direct Tines, ThreatQ, or Andesite administration' in mapping
    assert 'Synthetic events and attended operation only' in mapping


def test_dashboard_preview_matches_provisioned_panel_titles() -> None:
    dashboard = json.loads(
        read('observability/grafana/dashboards/soc-platform-overview.json')
    )
    titles = {panel['title'] for panel in dashboard['panels']}
    svg_path = ROOT / 'diagrams' / 'soc-platform-overview.svg'
    svg = svg_path.read_text(encoding='utf-8')
    ET.parse(svg_path)
    assert len(titles) == 11
    assert titles <= set(re.findall(r'>([^<>]+)</text>', svg))
