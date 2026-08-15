#!/usr/bin/env python3
"""Validate repository data, local documentation links, and CI safety boundaries."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", ".pytest_cache", "__pycache__"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
PINNED_ACTION = re.compile(
    r"^\s*(?:-\s+)?uses:\s*[^@\s]+@[0-9a-f]{40}(?:\s+#.*)?$",
    re.MULTILINE,
)
USES_LINE = re.compile(r"^\s*(?:-\s+)?uses:\s*\S+", re.MULTILINE)


class RepositoryYamlLoader(yaml.SafeLoader):
    """Safe loader that preserves vendor tags such as Docker Compose !override."""


def construct_tagged_value(
    loader: RepositoryYamlLoader,
    tag_suffix: str,
    node: yaml.Node,
) -> object:
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_scalar(node)


RepositoryYamlLoader.add_multi_constructor("!", construct_tagged_value)


@dataclass
class Counts:
    json_files: int = 0
    yaml_files: int = 0
    xml_files: int = 0
    markdown_files: int = 0
    requirement_files: int = 0
    workflow_files: int = 0


def repository_files(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    return sorted(
        path
        for pattern in patterns
        for path in root.rglob(pattern)
        if not any(part in EXCLUDED_PARTS for part in path.parts)
    )


def validate_data_files(root: Path, counts: Counts) -> list[str]:
    errors: list[str] = []
    for path in repository_files(root, ("*.json",)):
        counts.json_files += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(root)}: invalid JSON: {exc}")

    for path in repository_files(root, ("*.yml", "*.yaml")):
        counts.yaml_files += 1
        try:
            list(
                yaml.load_all(
                    path.read_text(encoding="utf-8"),
                    Loader=RepositoryYamlLoader,
                )
            )
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(root)}: invalid YAML: {exc}")

    wazuh_root = root / "detections" / "wazuh"
    xml_paths = sorted(wazuh_root.glob("*.xml"))
    xml_paths.extend(repository_files(root, ("*.svg",)))
    for path in xml_paths:
        counts.xml_files += 1
        try:
            ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            errors.append(f"{path.relative_to(root)}: invalid XML: {exc}")
    return errors


def validate_markdown_links(root: Path, counts: Counts) -> list[str]:
    errors: list[str] = []
    for path in repository_files(root, ("*.md",)):
        counts.markdown_files += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path.relative_to(root)}: unreadable Markdown: {exc}")
            continue
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_target = unquote(target.split("#", 1)[0])
            if not relative_target:
                continue
            resolved = (path.parent / relative_target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(
                    f"{path.relative_to(root)}: link escapes repository: {target}"
                )
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(root)}: broken link: {target}")
    return errors


def validate_requirement_pins(root: Path, counts: Counts) -> list[str]:
    errors: list[str] = []
    paths = [root / "requirements.txt", root / "requirements-dev.txt"]
    paths.extend(sorted(root.glob("*/requirements.txt")))
    for path in paths:
        if not path.is_file():
            continue
        counts.requirement_files += 1
        for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith(("#", "-r ")):
                continue
            if "==" not in line:
                errors.append(
                    f"{path.relative_to(root)}:{number}: dependency must use an exact pin"
                )
    return errors


def validate_workflows(root: Path, counts: Counts) -> list[str]:
    errors: list[str] = []
    workflow_root = root / ".github" / "workflows"
    for path in repository_files(workflow_root, ("*.yml", "*.yaml")):
        counts.workflow_files += 1
        text = path.read_text(encoding="utf-8")
        uses = USES_LINE.findall(text)
        pinned = PINNED_ACTION.findall(text)
        if len(uses) != len(pinned):
            errors.append(f"{path.relative_to(root)}: every action must use a full commit SHA")
        if not re.search(r"(?m)^permissions:\s*\n\s{2}contents:\s*read\s*$", text):
            errors.append(f"{path.relative_to(root)}: top-level contents: read is required")
        lower = text.lower()
        for forbidden in ("pull_request_target", "self-hosted", "secrets.", "environment:"):
            if forbidden in lower:
                errors.append(f"{path.relative_to(root)}: forbidden CI capability: {forbidden}")
        if "persist-credentials: false" not in text:
            errors.append(f"{path.relative_to(root)}: checkout credentials must not persist")
    return errors


def validate_repository(root: Path = ROOT) -> tuple[list[str], Counts]:
    counts = Counts()
    errors = [
        *validate_data_files(root, counts),
        *validate_markdown_links(root, counts),
        *validate_requirement_pins(root, counts),
        *validate_workflows(root, counts),
    ]
    return errors, counts


def main() -> int:
    errors, counts = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(
        "repository_validation=passed "
        f"json={counts.json_files} yaml={counts.yaml_files} xml={counts.xml_files} "
        f"markdown={counts.markdown_files} requirements={counts.requirement_files} "
        f"workflows={counts.workflow_files}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
