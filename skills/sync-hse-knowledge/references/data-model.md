# HSE Data Model & Relational Schema Specification

## 1. Schema Domain Groups

The database schema is organized into 18 specialized entity groups:

1. **Source & Registry**: `source`, `source_endpoint`, `source_policy`, `entitlement`.
2. **Unattended Acquisition**: `access_contract`, `acquisition_route`, `attempt`, `retry_budget`, `circuit_breaker`, `challenge_event`.
3. **Operations & Audit**: `sync_run`, `checkpoint`, `coverage_report`, `quality_issue`, `audit_event`.
4. **Evidence & Raw Storage**: `raw_artifact`, `artifact_provenance`, `parsed_document`.
5. **Legal & Technical Documents**: `document`, `document_version`, `legal_provision`, `definition`, `sanction_link`.
6. **Obligations & Compliance**: `obligation`, `obligation_version`, `exception_rule`.
7. **Applicability Engine**: `applicability_rule`, `rule_version`, `rule_test`, `decision_trace`, `missing_fact`.
8. **Organization & Facility**: `organization`, `facility`, `location`, `facility_profile`, `commitment`.
9. **Operations & Work Context**: `activity`, `process`, `task`, `asset`, `equipment_class`, `worker_group`, `contractor_scope`.
10. **Chemical Master & Inventory**: `substance`, `substance_identifier`, `mixture`, `composition`, `chemical_product`, `inventory_item`.
11. **SDS & GHS**: `sds`, `sds_version`, `sds_section`, `ghs_profile`, `hazard_classification`, `label_element`.
12. **Exposure & Industrial Hygiene**: `exposure_agent`, `oel`, `sampling_method`, `seg`, `monitoring_requirement`, `monitoring_result_aggregate`.
13. **Hazard, Risk & Controls**: `hazard`, `scenario`, `cause`, `consequence`, `control`, `control_standard`, `bowtie_edge`, `risk_matrix`.
14. **Environmental Aspects & Limits**: `environmental_aspect`, `impact`, `receptor`, `emission_point`, `pollutant`, `limit`, `waste_stream`.
15. **Permits & Calendar**: `permit`, `permit_version`, `permit_condition`, `calendar_obligation`, `evidence_requirement`.
16. **Emergency & Fire Safety**: `emergency_scenario`, `emergency_requirement`, `fire_requirement`, `response_resource`, `drill_requirement`.
17. **Training & Competency**: `training_requirement`, `competency`, `role_requirement`, `inspection_requirement`.
18. **Retrieval, Graph & Webhooks**: `content_chunk`, `embedding`, `entity_edge`, `change_event`, `impact_case`, `webhook_subscription`, `webhook_delivery_log`.

---

## 2. Temporal Graph Principles

- **Transaction Time**: `recorded_at`, `recorded_until`.
- **Valid Time**: `valid_from`, `valid_to` (Real-world legal/technical validity).
- **Document Lifecycle**: `published_at`, `effective_at`, `repealed_at`.
- **Current Indicator**: `is_current` (Boolean flag indexing active latest version).
