"""Tests for Applicability Rule DSL and Facility Profile Compiler."""

from service.rules.dsl_engine import ApplicabilityDSLEngine, RuleOutcome
from service.rules.facility_compiler import FacilityProfileCompiler, FacilityContext
from service.db.models import ApplicabilityRule


def test_applicability_dsl_positive(db_session):
    rule = ApplicabilityRule(
        code="RULE_BOILER_INSPECTION",
        jurisdiction="VN",
        expression={
            "when": {
                "all": [
                    {"fact": "asset.has_boiler", "op": "eq", "value": True}
                ]
            },
            "then": {
                "obligations": ["OBL_STRICT_EQUIPMENT_INSPECTION"]
            }
        },
        required_facts=["asset.has_boiler"]
    )
    db_session.add(rule)
    db_session.commit()

    ctx = FacilityContext(facility_id="FAC-001", province="Binh Duong", has_boiler=True)
    facts = FacilityProfileCompiler.compile_facts(ctx)

    trace = ApplicabilityDSLEngine.evaluate_rule(rule, facts)
    assert trace.outcome == RuleOutcome.APPLICABLE
    assert "OBL_STRICT_EQUIPMENT_INSPECTION" in trace.obligations


def test_applicability_dsl_negative(db_session):
    rule = ApplicabilityRule(
        code="RULE_BOILER_INSPECTION",
        jurisdiction="VN",
        expression={
            "when": {
                "all": [
                    {"fact": "asset.has_boiler", "op": "eq", "value": True}
                ]
            },
            "then": {
                "obligations": ["OBL_STRICT_EQUIPMENT_INSPECTION"]
            }
        },
        required_facts=["asset.has_boiler"]
    )
    db_session.add(rule)
    db_session.commit()

    ctx = FacilityContext(facility_id="FAC-002", province="Binh Duong", has_boiler=False)
    facts = FacilityProfileCompiler.compile_facts(ctx)

    trace = ApplicabilityDSLEngine.evaluate_rule(rule, facts)
    assert trace.outcome == RuleOutcome.NOT_APPLICABLE
