from finevidence.evidence.fact_understanding import (
    classify_question,
    decompose_required_facts_by_variant,
)


def test_schema_decomposition_emits_financial_slots_for_comparison():
    result = decompose_required_facts_by_variant(
        "Compare revenue in 2024 with revenue in 2023.", "D2"
    )

    assert result.status == "READY"
    assert result.question_type == "comparison"
    assert result.facts[0].slots.fact_type == "financial_metric"
    assert result.facts[0].slots.role == "comparison_value_a"
    assert result.facts[0].slots.critical is True


def test_llm_direct_is_explicitly_unavailable_without_provider():
    result = decompose_required_facts_by_variant("What was revenue in 2024?", "D1")

    assert result.status == "N/A"
    assert result.facts == []
    assert result.reason == "LLM_PROVIDER_NOT_CONFIGURED"


def test_evidence_aware_decomposition_keeps_only_candidate_evidence():
    result = decompose_required_facts_by_variant(
        "What was revenue in 2024?",
        "D3",
        [("e-1", "Revenue in 2024 was 100 million.")],
    )

    assert result.facts[0].acceptable_evidence_ids == ["e-1"]
    assert classify_question("Why did cost of risk increase?") == "explanation"
