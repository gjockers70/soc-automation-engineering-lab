# Architecture Diagrams

These diagrams describe implemented data flow. Dashed paths are analyst-driven or monitoring paths rather than automatic response.

## Platform architecture

~~~mermaid
flowchart TB
    subgraph Endpoints
        Linux[ubuntu-web-01]
        Windows[win11-01]
    end
    subgraph Management[soc-mgr-01]
        Wazuh[Wazuh manager and indexer]
        Shuffle[Shuffle]
        Gateway[FastAPI gateway]
        MISP[MISP]
        Hive[TheHive]
        Velo[Velociraptor]
        Audit[SQLite and JSON audit]
        Prom[Prometheus]
        Grafana[Grafana]
    end
    Linux -->|auth audit process file| Wazuh
    Windows -->|Security PowerShell account process| Wazuh
    Wazuh --> Gateway
    Wazuh --> Shuffle
    Gateway --> MISP
    Gateway --> Hive
    Gateway --> Audit
    Gateway --> Prom
    Shuffle --> Gateway
    Prom --> Grafana
    Hive -. analyst task .-> Velo
    Velo -. bounded collection .-> Linux
    Velo -. bounded collection .-> Windows
~~~

## Alert and investigation sequence

~~~mermaid
sequenceDiagram
    participant E as Endpoint
    participant W as Wazuh
    participant G as Gateway
    participant M as MISP
    participant H as TheHive
    participant A as Analyst
    participant V as Velociraptor
    E->>W: Security event
    W->>G: Authenticated alert plus idempotency key
    G->>G: Validate and reserve delivery
    G->>M: Query normalized IOC
    M-->>G: Reputation, confidence, provenance
    G->>G: Score and build summary
    G->>H: Create or reuse case fingerprint
    H-->>A: Triage task and evidence
    A->>V: Optional bounded collection
    V-->>A: Sanitized findings
    A->>H: Recommendation and decision request
~~~

## Approval and response

~~~mermaid
flowchart LR
    Case[TheHive case] --> Proposal[Pending proposal]
    Proposal --> Decision{Independent decision}
    Decision -->|Reject| NoAction[Record no action]
    Decision -->|Escalate| Review[Return to investigation]
    Decision -->|Approve| Allow{Action and target allow list}
    Allow -->|Fail| Deny[Fail closed and audit]
    Allow -->|Pass| Execute[Change synthetic identity]
    Execute --> Validate[Validate result and audit]
~~~

No branch can block an IP, quarantine a host, delete a file, change an operating-system account, or alter Active Directory.

## Dashboard layout

The [sanitized SVG preview](soc-platform-overview.svg) is generated from the panel names and positions in the committed Grafana dashboard definition. It contains no runtime data.
