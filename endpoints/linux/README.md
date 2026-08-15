# Linux endpoint

`ubuntu-web-01` retains its isolated workload address and adds `10.77.30.20/24` for SOC telemetry. The configuration enables `auditd`, focused identity and privilege watches, a safe file-validation location, and interactive-user process execution records.

The temporary provisioning scripts are used only while the libvirt provisioning interface is explicitly attached. They add and remove the short-lived address, route, and DNS state; they are not persistent boot configuration.

The Phase 3 Wazuh agent collects Linux Audit records and the standard authentication sources. Enrollment uses a temporarily transferred protected password file that is deleted after success, active response is disabled, and the supplied synthetic failed-login generator uses only TEST-NET address 198.51.100.23.

Phase 4 adds a safe generator for six synthetic invalid-user SSH messages from documentation-only address 198.51.100.44. It changes no authentication configuration and makes no network connection.
