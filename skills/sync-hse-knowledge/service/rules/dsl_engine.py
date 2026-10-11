"""Deterministic Applicability Rule DSL Evaluator (FR-042, FR-047, Section 15)."""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import ApplicabilityRule, DecisionTrace


class RuleOutcome(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class EvaluationTrace(BaseModel):
    rule_id: str
    rule_code: str
    outcome: RuleOutcome
    matched_conditions: List[str] = []
    unmatched_conditions: List[str] = []
    missing_facts: List[str] = []
    obligations: List[str] = []
    explanation: str


class ApplicabilityDSLEngine:
    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], facts: Dict[str, Any]) -> Tuple[Optional[bool], Optional[str]]:
        """Evaluates single condition against flat or nested facts."""
        fact_key = condition.get("fact")
        op = condition.get("op")
        expected = condition.get("value")

        if fact_key not in facts:
            return None, fact_key  # Missing fact

        actual = facts[fact_key]

        if op == "eq":
            return actual == expected, None
        elif op == "neq":
            return actual != expected, None
        elif op == "in":
            return actual in expected, None
        elif op == "not_in":
            return actual not in expected, None
        elif op == "contains":
            if isinstance(actual, (list, set, tuple)):
                return expected in actual, None
            return False, None
        elif op == "gt":
            return float(actual) > float(expected), None
        elif op == "gte":
            return float(actual) >= float(expected), None
        elif op == "lt":
            return float(actual) < float(expected), None
        elif op == "lte":
            return float(actual) <= float(expected), None
        elif op == "exists":
            return actual is not None, None

        return False, None

    @classmethod
    def evaluate_rule(cls, rule: ApplicabilityRule, facts: Dict[str, Any]) -> EvaluationTrace:
        expr = rule.expression
        when_clause = expr.get("when", {})
        then_clause = expr.get("then", {})

        matched = []
        unmatched = []
        missing = []

        if "all" in when_clause:
            for cond in when_clause["all"]:
                res, miss = cls.evaluate_condition(cond, facts)
                if miss:
                    missing.append(miss)
                elif res is True:
                    matched.append(f"{cond.get('fact')} {cond.get('op')} {cond.get('value')}")
                else:
                    unmatched.append(f"{cond.get('fact')} {cond.get('op')} {cond.get('value')}")

            if missing:
                outcome = RuleOutcome.UNKNOWN
                exp = f"Rule {rule.code} requires missing facts: {', '.join(missing)}"
            elif unmatched:
                outcome = RuleOutcome.NOT_APPLICABLE
                exp = f"Rule {rule.code} condition not met: {', '.join(unmatched)}"
            else:
                outcome = RuleOutcome.APPLICABLE
                exp = f"Rule {rule.code} conditions matched: {', '.join(matched)}"

        elif "any" in when_clause:
            any_matched = False
            for cond in when_clause["any"]:
                res, miss = cls.evaluate_condition(cond, facts)
                if miss:
                    missing.append(miss)
                elif res is True:
                    any_matched = True
                    matched.append(f"{cond.get('fact')} {cond.get('op')} {cond.get('value')}")
                else:
                    unmatched.append(f"{cond.get('fact')} {cond.get('op')} {cond.get('value')}")

            if any_matched:
                outcome = RuleOutcome.APPLICABLE
                exp = f"Rule {rule.code} at least one condition matched: {', '.join(matched)}"
            elif missing:
                outcome = RuleOutcome.UNKNOWN
                exp = f"Rule {rule.code} pending facts: {', '.join(missing)}"
            else:
                outcome = RuleOutcome.NOT_APPLICABLE
                exp = f"Rule {rule.code} no conditions matched"
        else:
            outcome = RuleOutcome.NOT_APPLICABLE
            exp = "Empty rule expression"

        obligations = then_clause.get("obligations", []) if outcome == RuleOutcome.APPLICABLE else []

        return EvaluationTrace(
            rule_id=rule.rule_id,
            rule_code=rule.code,
            outcome=outcome,
            matched_conditions=matched,
            unmatched_conditions=unmatched,
            missing_facts=missing,
            obligations=obligations,
            explanation=exp
        )
