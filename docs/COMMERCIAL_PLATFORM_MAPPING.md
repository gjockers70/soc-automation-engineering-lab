# Commercial Platform Mapping

## Scope

This project does not use or claim experience administering Tines, ThreatQ, or Andesite. It demonstrates technical and operational concepts that transfer to those platforms. Product terminology, licensing, data models, deployment architecture, and enterprise support differ.

## Shuffle and FastAPI to Tines

[Tines](https://www.tines.com/) describes a vendor-agnostic workflow platform that connects tools and data through workflows, APIs, webhooks, governance, and human-driven cases. This lab maps the following concepts:

| Lab implementation | Transferable Tines concept | Important difference |
|---|---|---|
| Authenticated Shuffle webhook | Event-driven workflow trigger | Tines uses its own action and Story model |
| JSON extraction and normalization | Event transformation | Field syntax and runtime behavior differ |
| Python API clients | HTTP/API integration | Tines can express many connections directly in workflow actions |
| Bounded retry and error classes | Failure paths and workflow reliability | Native retry/monitoring features are product-specific |
| TheHive case plus analyst handoff | Collaborative case workflow | Tines Cases has its own records, views, and permissions |
| Separate approval decision | Human-in-the-loop branch | UI, identity, and policy controls differ |
| Prometheus workflow metrics | Automation performance measurement | Tines reporting and telemetry are not reproduced |

The relevant skill is designing observable, idempotent, governed workflows across unreliable APIs—not claiming that a Shuffle export can be imported into Tines.

## MISP to ThreatQ

[ThreatQ](https://helpcenter.threatq.com/ThreatQ_Platform/ThreatQ_Platform.htm) describes collection, normalization, correlation, enrichment, scoring, prioritization, analyst work, and distribution of intelligence across integrated tools. This lab maps:

| Lab implementation | Transferable ThreatQ concept | Important difference |
|---|---|---|
| MISP attributes and events | Central intelligence repository | ThreatQ has a distinct object and relationship model |
| IOC validation and normalization | Intake quality and deconfliction | Enterprise ingestion covers more formats and sources |
| Tags, confidence, reputation, provenance | Context and prioritization | ThreatQ scoring/configuration is product-specific |
| Local REST client | Open API integration | Authentication, endpoints, SDKs, and rate limits differ |
| MISP-to-alert enrichment | Operationalizing intelligence | The lab has one synthetic source and no feed governance |
| Unknown result handling | Intelligence reliability discipline | ThreatQ can aggregate and correlate many sources |

The project demonstrates why intelligence must retain source, confidence, age, and uncertainty. It does not reproduce ThreatQ's Threat Library, Adaptive Workbench, marketplace, or TDR Orchestrator.

## Integrated lab to Andesite

[Andesite](https://andesite.ai/product/) describes a human-AI SOC workspace that connects existing data sources, prioritizes alerts, supports investigation and enrichment, keeps humans in control, and retains evidence trails. This lab has no AI investigation engine. It maps only selected underlying operating patterns:

| Lab implementation | Related Andesite operating concept | Important difference |
|---|---|---|
| Wazuh, MISP, TheHive, and Velociraptor integration | Working across existing SOC data/tool silos | The lab uses explicit point integrations, not a decision fabric |
| Deterministic scoring and summaries | Prioritized, contextual analyst handoff | No machine reasoning, agents, natural-language investigation, or persistent AI memory |
| Approval-gated response | Humans retain consequential decisions | The lab action is a single harmless allow-listed state change |
| Structured audit events and evidence | Traceable investigation and action history | No Evidentiary AI or AI evaluation framework is implemented |
| Playbooks and bounded triage | Repeatable investigation workflow | No configurable AI agents or enterprise connector library |
| Isolated self-hosting | Controlled data boundary | It is a small lab, not an enterprise self-managed deployment |

The transferable lesson is that automation or AI should operate through scoped connectors, explicit evidence, observable assumptions, approval boundaries, and auditable outcomes. Experience with this lab is not product experience with Andesite.

## Other platform relationships

| Lab tool | General commercial category |
|---|---|
| Wazuh | SIEM/XDR-style collection, detection, search, and agent operations |
| TheHive | Security incident/case management and analyst collaboration |
| Velociraptor | Endpoint live response, hunt, and forensic triage |
| Prometheus/Grafana | Platform observability, reliability metrics, and dashboards |

These are category mappings, not equivalence or feature-parity claims.
