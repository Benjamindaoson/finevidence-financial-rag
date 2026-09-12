from finevidence.contracts.p0_h import LocalLLMConfig
from finevidence.evidence.llm_direct import parse_decomposition_json, run_direct_decomposition


def test_valid_llm_json_is_parsed_into_requirement_graph():
    raw = '{"question_type":"factual","requirements":[{"requirement_id":"R1","description":"revenue","fact_type":"RETRIEVED_FACT","role":"target_value","criticality":"CRITICAL"}]}'
    result = parse_decomposition_json(raw)
    assert result.status == "READY"
    assert result.graph.requirements[0].role == "target_value"


def test_malformed_json_returns_explicit_na_without_fake_requirements():
    result = parse_decomposition_json("not json")
    assert result.status == "N/A"
    assert result.reason == "MALFORMED_LLM_JSON"
    assert result.graph.requirements == []


def test_local_model_config_is_provenance_ready():
    config = LocalLLMConfig(model_id="local-test", revision="rev", prompt_version="p0-h-v1", temperature=0.0)
    assert config.temperature == 0.0

