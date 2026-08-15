from __future__ import annotations

from pathlib import Path

from tools.validate_repository import (
    Counts,
    validate_markdown_links,
    validate_repository,
    validate_workflows,
)

ROOT = Path(__file__).resolve().parents[1]


def test_current_repository_passes_asset_and_link_validation() -> None:
    errors, counts = validate_repository(ROOT)
    assert errors == []
    assert counts.json_files >= 20
    assert counts.yaml_files >= 10
    assert counts.markdown_files >= 50
    assert counts.workflow_files == 1


def test_broken_and_escaping_markdown_links_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "[missing](docs/missing.md)\n[escape](../outside.md)\n",
        encoding="utf-8",
    )
    errors = validate_markdown_links(tmp_path, Counts())
    assert any("broken link" in error for error in errors)
    assert any("escapes repository" in error for error in errors)


def test_workflow_rejects_mutable_actions_and_privileged_capabilities(
    tmp_path: Path,
) -> None:
    workflow_root = tmp_path / ".github" / "workflows"
    workflow_root.mkdir(parents=True)
    (workflow_root / "unsafe.yml").write_text(
        """
name: Unsafe
on: pull_request_target
permissions:
  contents: write
jobs:
  deploy:
    runs-on: self-hosted
    environment: production
    steps:
      - uses: actions/checkout@main
      - run: echo unsafe
        env:
          VALUE: secrets.TOKEN
""".lstrip(),
        encoding="utf-8",
    )
    errors = validate_workflows(tmp_path, Counts())
    assert any("full commit SHA" in error for error in errors)
    assert any("contents: read" in error for error in errors)
    assert any("self-hosted" in error for error in errors)
    assert any("environment:" in error for error in errors)
    assert any("secrets." in error for error in errors)
