import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_velociraptor_merge_is_isolated() -> None:
    config = json.loads((ROOT / "forensics/velociraptor/server-merge.json").read_text())
    assert config["Frontend"]["bind_address"] == "10.77.30.10"
    assert config["GUI"]["bind_address"] == "10.77.30.10"
    assert config["API"]["bind_address"] == "127.0.0.1"
    assert config["Client"]["server_urls"] == ["https://10.77.30.10:8000/"]


def test_collection_is_bounded_and_non_remediating() -> None:
    script = (ROOT / "forensics/velociraptor/collect_triage.sh").read_text()
    assert "--cpu_limit 20" in script
    assert "--timeout 300" in script
    assert script.count("Upload_File=N") == 2
    prohibited = ("rm -rf", "quarantine", "credential", "memory acquisition", "packet capture")
    assert all(term not in script.lower() for term in prohibited)


def test_release_hashes_are_pinned() -> None:
    linux = (ROOT / "forensics/velociraptor/prepare_server.sh").read_text()
    windows = (ROOT / "forensics/velociraptor/Install-WindowsClient.ps1").read_text()
    assert "6636020f3ce03ea4eff5d5b96d635c400e51d2636c823a8f0bd458ddc7c4d28a" in linux
    assert "c91cf8a32731c4c45c148393bc7d2af688c392194a9fffc4535e8b583260d55e" in windows
