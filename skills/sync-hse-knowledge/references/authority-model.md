# HSE Authority Model & Hierarchy Specification

## 1. Authority Hierarchy

The HSE Knowledge Platform enforces strict hierarchy of authority when evaluating compliance and answering queries:

| Authority Level | Source Classification | Binding Status & Usage |
| :--- | :--- | :--- |
| **`A1_MANDATORY_LAW`** | National Laws, Government Decrees, Prime Minister Decisions, Ministerial Circulars, Site Permits. | **Legally Mandatory** if facility applicability facts evaluate to True. |
| **`A2_MANDATORY_TECH_REG`** | National Technical Regulations (QCVN), mandatory technical codes. | **Legally Mandatory** threshold/control within jurisdiction. |
| **`A3_BINDING_COMMITMENT`** | Specific Environmental Permits, EIA commitments, Loan covenants (e.g. IFC Performance Standards). | **Binding** on the specific facility or signatory organization. |
| **`B1_VOLUNTARY_STANDARD`** | TCVN (Voluntary), ISO 14001, ISO 45001, NFPA, IEC, ASTM, API. | **Commitment-gated** (Mandatory only if organization has pledged certification or customer contract). |
| **`B2_GIIP_GUIDANCE`** | IFC EHS Guidelines, ILO Encyclopaedia, WHO, CDC/NIOSH Pocket Guide, OSHA guidance. | **Good International Industry Practice (GIIP)**; benchmark and control library. |
| **`C1_INTERNAL_CONTROL`** | Corporate EHS Policies, Site SOPs, Work Instructions, JSA templates, Internal limits. | **Internal Binding** approved by site leadership. |
| **`D1_SECONDARY`** | Trade articles, blog posts, consulting summaries, vendor notes. | **Discovery only**; never used as single compliance basis. |

---

## 2. Conflict Resolution Rules

1. **Permit Over QCVN**: If a facility's specific Environmental Permit sets a stricter concentration limit (e.g. COD ≤ 30 mg/L) than the national QCVN (e.g. COD ≤ 50 mg/L), the **stricter permit condition takes precedence** for that specific facility.
2. **Effective Dates & Transition**: An amended legal document only supersedes specific articles from its `effective_date`. Prior dates queryable via `as_of` return the historical version.
3. **Multi-Jurisdiction OELs**: When reporting Occupational Exposure Limits across Vietnam, ACGIH, and NIOSH, the system retains separate authority entries and does not arbitrarily merge or pick the lowest value without explicit user policy context.
4. **Guidance Separation**: International guidance (e.g. IFC EHS or NIOSH REL) is never labeled as mandatory Vietnamese law.
