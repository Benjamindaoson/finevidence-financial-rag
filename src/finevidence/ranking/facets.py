from __future__ import annotations

from dataclasses import dataclass
import re

from finevidence.contracts.evidence import Evidence


@dataclass(frozen=True)
class FinancialFacets:
    entity: str | None = None
    metric: str | None = None
    period: str | None = None
    basis: str | None = None
    segment: str | None = None
    geography: str | None = None
    currency: str | None = None
    period_type: str | None = None


_METRICS = (
    "CET1 ratio",
    "CET1 capital",
    "total capital ratio",
    "profit before tax",
    "cost of risk",
    "ECL charge",
    "average net loans",
    "revenue",
)
_ENTITIES = ("HSBC Group", "HSBC Bank plc", "HSBC Holdings")
_VOCAB = {
    "basis": ("reported", "adjusted"),
    "segment": ("CMB", "GBM", "WPB"),
    "geography": ("Hong Kong", "UK", "United Kingdom", "China"),
    "currency": ("USD", "HKD", "RMB", "GBP", "dollars", "dollar"),
}


def _find(text: str, values: tuple[str, ...]) -> str | None:
    lowered = text.lower()
    for value in values:
        if value.lower() in lowered:
            return value
    return None


def extract_facets(query: str) -> FinancialFacets:
    period_type = _find(
        query,
        (
            "full year",
            "FY",
            "first half",
            "H1",
            "second half",
            "H2",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
        ),
    )
    if period_type in {"full year", "FY"}:
        period_type = "FY"
    elif period_type in {"first half", "H1"}:
        period_type = "H1"
    elif period_type in {"second half", "H2"}:
        period_type = "H2"
    return FinancialFacets(
        entity=_find(query, _ENTITIES),
        metric=_find(query, _METRICS),
        period=next(iter(re.findall(r"\b20\d{2}\b", query)), None),
        basis=_find(query, _VOCAB["basis"]),
        segment=_find(query, _VOCAB["segment"]),
        geography=_find(query, _VOCAB["geography"]),
        currency=_find(query, _VOCAB["currency"]),
        period_type=period_type,
    )


def evidence_facets(evidence: Evidence) -> FinancialFacets:
    parsed = extract_facets(evidence.text)
    return FinancialFacets(
        entity=evidence.entity or parsed.entity,
        metric=evidence.metric or parsed.metric,
        period=evidence.period or parsed.period,
        basis=evidence.accounting_basis or parsed.basis,
        segment=evidence.segment or parsed.segment,
        geography=parsed.geography,
        currency=evidence.currency or parsed.currency,
        period_type=parsed.period_type,
    )


def facet_features(query: str, evidence: Evidence) -> tuple[float, ...]:
    query_facets = extract_facets(query)
    item_facets = evidence_facets(evidence)
    values = []
    for field in (
        "entity",
        "metric",
        "period",
        "basis",
        "segment",
        "geography",
        "currency",
        "period_type",
    ):
        expected = getattr(query_facets, field)
        actual = getattr(item_facets, field)
        values.append(
            1.0
            if expected and actual and expected.lower() == actual.lower()
            else 0.0
        )
    return tuple(values)
