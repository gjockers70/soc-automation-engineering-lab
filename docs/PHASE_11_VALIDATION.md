# Phase 11 Validation

Live validation confirmed:

- two endpoint clients enrolled over the isolated telemetry network;
- all 12 bounded collections completed and produced non-empty ZIP containers;
- every collection container passed archive-integrity testing;
- Linux and Windows installed binaries matched the official pinned SHA-256 values;
- the server, both clients, and the pre-existing SOC platform recovered after controlled reboots;
- frontend and GUI listeners were limited to `10.77.30.10`, with the API on `127.0.0.1`;
- server and endpoint default routes remained absent;
- raw process, identity, network, event, and filesystem results were not copied into Git.

The initial native service hardening denied access to the server datastore, and the initial Windows service definition treated the client as a console process. The final implementation corrected the directory ownership boundary and uses Velociraptor's supported Windows service installer. A mixed line-ending defect in the Linux writeback filename was also corrected and covered by post-reboot validation.

Sanitized evidence is in `forensics/example-results/phase11-summary.json`. The private collection run remains under `/opt/soc-lab/velociraptor/collections/phase11-20260814T002030Z` on `soc-mgr-01`.
