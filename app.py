from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Optional


CATEGORY_WEIGHTS: dict[str, float] = {
    "Growth": 0.25,
    "Quality": 0.20,
    "Value": 0.15,
    "Momentum": 0.15,
    "Technical": 0.15,
    "Catalyst": 0.10,
}


@dataclass(frozen=True)
class MetricRule:
    name: str
    direction: str
    bad: float
    good: float
    weight: float = 1.0


@dataclass(frozen=True)
class CategoryResult:
    score: Optional[float]
    coverage: float
    used_metrics: int
    total_metrics: int
    details: dict[str, Optional[float]]


@dataclass(frozen=True)
class RatingResult:
    overall_score: Optional[float]
    rating: str
    confidence: str
    coverage: float
    categories: dict[str, CategoryResult]


def _valid(value: object) -> bool:
    try:
        return value is not None and isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _linear_score(value: float, rule: MetricRule) -> float:
    """Convert a raw metric into a bounded 0-100 score."""
    if rule.good == rule.bad:
        return 50.0

    if rule.direction == "higher":
        raw = (value - rule.bad) / (rule.good - rule.bad)
    elif rule.direction == "lower":
        raw = (rule.bad - value) / (rule.bad - rule.good)
    else:
        raise ValueError(f"Unsupported direction: {rule.direction}")

    return round(max(0.0, min(100.0, raw * 100.0)), 2)


def _score_category(
    values: Mapping[str, object],
    rules: tuple[MetricRule, ...],
) -> CategoryResult:
    details: dict[str, Optional[float]] = {}
    weighted_points = 0.0
    available_weight = 0.0
    total_weight = sum(rule.weight for rule in rules)
    used = 0

    for rule in rules:
        raw_value = values.get(rule.name)
        if not _valid(raw_value):
            details[rule.name] = None
            continue

        metric_score = _linear_score(float(raw_value), rule)
        details[rule.name] = metric_score
        weighted_points += metric_score * rule.weight
        available_weight += rule.weight
        used += 1

    score = None if available_weight == 0 else round(
        weighted_points / available_weight, 1
    )
    coverage = 0.0 if total_weight == 0 else round(
        available_weight / total_weight, 3
    )
    return CategoryResult(score, coverage, used, len(rules), details)


GROWTH_RULES = (
    MetricRule("revenue_growth_yoy", "higher", -0.10, 0.40, 1.5),
    MetricRule("revenue_growth_acceleration", "higher", -0.15, 0.15),
    MetricRule("eps_growth_yoy", "higher", -0.25, 0.50, 1.5),
    MetricRule("eps_growth_acceleration", "higher", -0.25, 0.25),
    MetricRule("free_cash_flow_growth_yoy", "higher", -0.30, 0.50),
    MetricRule("operating_income_growth_yoy", "higher", -0.20, 0.40),
    MetricRule("forward_revenue_growth", "higher", -0.05, 0.30),
    MetricRule("forward_eps_growth", "higher", -0.10, 0.35),
)

QUALITY_RULES = (
    MetricRule("roic", "higher", 0.00, 0.25, 1.5),
    MetricRule("roe", "higher", 0.00, 0.30),
    MetricRule("operating_margin", "higher", -0.05, 0.30),
    MetricRule("free_cash_flow_margin", "higher", -0.05, 0.25),
    MetricRule("gross_margin", "higher", 0.10, 0.70, 0.75),
    MetricRule("net_debt_to_ebitda", "lower", 5.0, 0.0, 1.25),
    MetricRule("interest_coverage", "higher", 0.0, 15.0),
    MetricRule("current_ratio", "higher", 0.75, 2.0, 0.75),
    MetricRule("share_dilution_yoy", "lower", 0.12, -0.03),
)

VALUE_RULES = (
    MetricRule("forward_pe", "lower", 45.0, 12.0),
    MetricRule("peg_ratio", "lower", 3.0, 0.8, 1.5),
    MetricRule("ev_to_ebitda", "lower", 30.0, 8.0),
    MetricRule("price_to_free_cash_flow", "lower", 50.0, 12.0, 1.25),
    MetricRule("earnings_yield", "higher", 0.00, 0.08),
    MetricRule("free_cash_flow_yield", "higher", 0.00, 0.08, 1.25),
)

MOMENTUM_RULES = (
    MetricRule("relative_strength_3m", "higher", -0.20, 0.25, 1.25),
    MetricRule("relative_strength_12m", "higher", -0.30, 0.50, 1.5),
    MetricRule("estimate_revision_90d", "higher", -0.15, 0.20, 1.25),
    MetricRule("earnings_surprise", "higher", -0.10, 0.20),
    MetricRule("cmf_20", "higher", -0.20, 0.25),
    MetricRule("obv_change_63d", "higher", -0.20, 0.35),
    MetricRule("up_down_volume_ratio", "higher", 0.70, 1.60),
)

TECHNICAL_RULES = (
    MetricRule("trend_alignment", "higher", 0.0, 1.0, 1.5),
    MetricRule("distance_from_52w_high", "lower", 0.40, 0.05),
    MetricRule("base_tightness", "lower", 0.35, 0.08, 1.25),
    MetricRule("atr_contraction", "higher", -0.20, 0.35),
    MetricRule("volume_dry_up", "higher", -0.20, 0.40),
    MetricRule("breakout_volume_ratio", "higher", 0.70, 2.00, 1.25),
    MetricRule("rsi_14_normalized", "higher", 0.20, 0.80, 0.75),
)

CATALYST_RULES = (
    MetricRule("backlog_growth_yoy", "higher", -0.10, 0.40, 1.25),
    MetricRule("capex_growth_yoy", "higher", -0.15, 0.35, 0.75),
    MetricRule("contract_growth_yoy", "higher", -0.10, 0.40),
    MetricRule("analyst_revision_breadth", "higher", -0.50, 0.75),
    MetricRule("next_earnings_proximity", "higher", 0.0, 1.0, 0.5),
    MetricRule("structural_tailwind_score", "higher", 0.0, 1.0),
)

RULES_BY_CATEGORY = {
    "Growth": GROWTH_RULES,
    "Quality": QUALITY_RULES,
    "Value": VALUE_RULES,
    "Momentum": MOMENTUM_RULES,
    "Technical": TECHNICAL_RULES,
    "Catalyst": CATALYST_RULES,
}


def rating_label(score: Optional[float]) -> str:
    if score is None:
        return "Insufficient Data"
    if score >= 95:
        return "Elite"
    if score >= 90:
        return "Exceptional"
    if score >= 80:
        return "Strong Buy Candidate"
    if score >= 70:
        return "Watch List"
    if score >= 60:
        return "Neutral"
    return "Avoid"


def confidence_label(coverage: float) -> str:
    if coverage >= 0.85:
        return "High"
    if coverage >= 0.65:
        return "Moderate"
    if coverage >= 0.45:
        return "Low"
    return "Insufficient"


def calculate_heartbeat_rating(
    values: Mapping[str, object],
) -> RatingResult:
    """Calculate the objective six-factor Heartbeat rating.

    Missing values receive neither points nor a neutral placeholder.
    Coverage is reported separately so sparse data cannot masquerade
    as a high-confidence rating.
    """
    categories = {
        name: _score_category(values, rules)
        for name, rules in RULES_BY_CATEGORY.items()
    }

    weighted_points = 0.0
    available_category_weight = 0.0
    total_coverage_weight = 0.0

    for name, result in categories.items():
        category_weight = CATEGORY_WEIGHTS[name]
        total_coverage_weight += category_weight * result.coverage
        if result.score is not None:
            weighted_points += result.score * category_weight
            available_category_weight += category_weight

    overall = None
    if available_category_weight > 0:
        overall = round(weighted_points / available_category_weight, 1)

    coverage = round(total_coverage_weight, 3)
    return RatingResult(
        overall_score=overall,
        rating=rating_label(overall),
        confidence=confidence_label(coverage),
        coverage=coverage,
        categories=categories,
    )


def explain_rating(result: RatingResult) -> list[str]:
    """Return factual explanation lines without making predictions."""
    available = [
        (name, category.score)
        for name, category in result.categories.items()
        if category.score is not None
    ]
    if not available:
        return ["Not enough verified data is available to calculate a rating."]

    ranked = sorted(available, key=lambda item: item[1], reverse=True)
    strongest = ", ".join(
        f"{name} ({score:.0f})" for name, score in ranked[:2]
    )
    weakest = ", ".join(
        f"{name} ({score:.0f})" for name, score in ranked[-2:]
    )
    return [
        f"Strongest measured categories: {strongest}.",
        f"Lowest measured categories: {weakest}.",
        (
            f"Data coverage is {result.coverage:.0%}, producing "
            f"{result.confidence.lower()} confidence."
        ),
        (
            "The rating summarizes reported fundamentals, market data, "
            "and explicitly coded catalysts; it is not a price forecast."
        ),
    ]
