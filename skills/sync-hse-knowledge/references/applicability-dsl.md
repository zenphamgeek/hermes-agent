# HSE Applicability Rule DSL Specification

## 1. Syntax & Rule Structure

Applicability rules are deterministic expressions that match a facility profile to required obligations:

```yaml
rule_id: VN_CHEM_SPECIAL_CONTROL_STORAGE
version: 1
jurisdiction: VN
authority: A1_MANDATORY_LAW
source_clause: "69/2025/QH15#article-15"
when:
  all:
    - fact: activity.type
      op: in
      value: [use, store, trade]
    - fact: chemical.list_membership
      op: contains
      value: special_control
    - fact: chemical.storage_quantity_kg
      op: gte
      value: 1000.0
then:
  applicability: applicable
  obligations:
    - OBL_VN_CHEM_SPECIAL_CONTROL_REPORT
    - OBL_VN_CHEM_SECURITY_PLAN
missing_fact_behavior: ask
```

## 2. Supported Operators

- `eq`, `neq`: Exact equality / inequality.
- `in`, `not_in`: Set membership.
- `contains`, `not_contains`: Array / list element containment.
- `gt`, `gte`, `lt`, `lte`: Numeric / threshold comparison.
- `all`, `any`, `not`: Boolean logic combinators.
- `between`: Range comparison `[min, max]`.
- `exists`: Fact existence verification.

## 3. Evaluation Outcomes

- `applicable`: All conditions evaluated to True; obligations bind the facility.
- `not_applicable`: One or more conditions evaluated to False.
- `conditional`: Partial match; depends on missing fact.
- `unknown`: Missing essential fact required to evaluate rule.
- `superseded`: Rule has been repealed by a newer legal instrument.
