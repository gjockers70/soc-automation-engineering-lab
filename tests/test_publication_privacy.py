from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".json", ".md", ".ps1", ".py", ".sh", ".toml", ".yaml", ".yml"}
PROHIBITED_SUFFIXES = {
    ".har",
    ".img",
    ".iso",
    ".key",
    ".pcap",
    ".pcapng",
    ".pem",
    ".pfx",
    ".p12",
    ".qcow2",
}
PERSONAL_PATH = re.compile(r"(?i)[a-z]:\\users\\[^\\\s]+")
EMAIL = re.compile(r"(?i)\b[a-z0-9._%+-]+@([a-z0-9.-]+\.[a-z]{2,})\b")
ALLOWED_EMAIL_SUFFIXES = (".test", ".local", "users.noreply.github.com")


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def test_tracked_files_exclude_sensitive_artifact_types() -> None:
    matches = [
        path.relative_to(ROOT).as_posix()
        for path in tracked_files()
        if path.suffix.lower() in PROHIBITED_SUFFIXES
    ]
    assert matches == []


def test_tracked_text_excludes_personal_paths_and_non_lab_email() -> None:
    matches: list[str] = []
    for path in tracked_files():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        domains = (match.group(1).lower() for match in EMAIL.finditer(text))
        if PERSONAL_PATH.search(text) or any(
            not domain.endswith(ALLOWED_EMAIL_SUFFIXES) for domain in domains
        ):
            matches.append(path.relative_to(ROOT).as_posix())
    assert matches == []


def test_local_private_markers_are_absent_when_configured() -> None:
    marker_file = ROOT / ".publication-private-markers"
    if not marker_file.exists():
        return
    markers = [
        line.strip().lower()
        for line in marker_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    matches: list[str] = []
    for path in tracked_files():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8").lower()
        if any(marker in content for marker in markers):
            matches.append(path.relative_to(ROOT).as_posix())
    assert matches == []
