# Data Model Specification

## Temporal Modeling Rules
All legal and business tables implement effective-dating semantics:
- `recorded_at`: Timestamp when the record was ingested into the system.
- `valid_from`: Timestamp/date when the legal rule/tariff begins real-world legal validity.
- `valid_to`: Timestamp/date when the legal rule/tariff ceases validity (NULL if ongoing).
- `superseded_at`: Timestamp when a newer version replaces this record in our store.
- `is_current`: Convenience boolean flag (`valid_to IS NULL AND superseded_at IS NULL`).

## Core Tables Summary
1. `source`: Registry definition and authority level.
2. `source_endpoint`: URL patterns, strategies, and rate limits.
3. `source_policy`: Pre-fetch policy rules and robots caching.
4. `entitlement`: Time-bound usage rights for gated content.
5. `robots_snapshot`: Immutable snapshot of `robots.txt` per host.
6. `crawl_run`: Sync execution run tracking.
7. `crawl_checkpoint`: Checkpoint cursors for resumption.
8. `crawl_item`: Discovered candidate items and canonical URLs.
9. `fetch_attempt`: HTTP attempts, status codes, and timestamps.
10. `access_contract`: Approved machine-to-machine integration configuration.
11. `acquisition_route`: Configured route priorities per source.
12. `acquisition_attempt`: Acquisition attempts, response classes, and retry decisions.
13. `retry_budget`: Allocated attempts and cooldown windows per host.
14. `circuit_breaker`: Circuit breaker status (`CLOSED`, `OPEN`, `HALF_OPEN`).
15. `fallback_mapping`: Approved alternative mirror sources.
16. `challenge_event`: Redacted records of detected interactive challenges.
17. `browser_profile_ref`: Encrypted reference for authenticated browser runners.
18. `raw_artifact`: Content-addressed immutable blob manifest (SHA-256).
19. `artifact_provenance`: Source URL to artifact mapping.
20. `parsed_document`: Structured parser outputs and lineage.
21. `document`: Logical legal document identity.
22. `document_version`: Versioned document content, provisions, and relations.
23. `document_relation`: Document relationships (amends, replaces, repeals).
24. `legal_provision`: Granular structure (Section, Chapter, Article, Clause, Point).
25. `hs_edition`: HS/AHTN/Vietnam nomenclature editions.
26. `hs_node`: Hierarchy tree (Chapter 2, Heading 4, Subheading 6, National 8/10).
27. `hs_description`: Multilingual node descriptions (Vietnamese, English).
28. `hs_note`: Section/Chapter/Subheading legal notes and SEN.
29. `hs_correlation`: Trans-edition mapping (1:1, 1:n, n:1, n:n).
30. `tariff_schedule`: Tariff schedule metadata (MFN, FTA agreements).
31. `tariff_rate`: Specific tariff rates and conditions per line.
32. `trade_measure`: Non-tariff measures (licensing, inspection, quotas).
33. `measure_hs_scope`: Scope of HS codes mapped to trade measures.
34. `classification_ruling`: Public advance classification rulings and rulings.
35. `ruling_product_fact`: Commercial names, descriptions, and technical specifications.
36. `ruling_hs_result`: HS classification conclusion and legal reasoning.
