# Basic Forensic Triage

Phase 11 uses Velociraptor 0.77.1 to collect a deliberately narrow snapshot from the owned Linux and Windows lab endpoints. The server runs on `soc-mgr-01`; both clients communicate only over `soc-telemetry`.

Raw collection archives remain on the private management VM under `/opt/soc-lab/velociraptor/collections`. They are not committed because even benign host inventories can expose user names, process arguments, paths, and network context. The repository contains the collection plan, artifact rationale, sanitized aggregate evidence, and investigation-note template.

See [collection-plan.md](collection-plan.md), [artifacts.md](artifacts.md), and [investigation-notes.md](investigation-notes.md).

## References

- [Velociraptor downloads and published hashes](https://docs.velociraptor.app/downloads/)
- [Client deployment guidance](https://docs.velociraptor.app/docs/deployment/clients/)
- [Artifact CLI reference](https://docs.velociraptor.app/docs/cli/commands/artifacts/)
