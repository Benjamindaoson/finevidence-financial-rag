from __future__ import annotations

from finevidence.evidence.table_ir import parse_table, roundtrip_values, table_structure_invariants
from finevidence.retrieval.failure_router import oracle_failure_route, predict_failure_route


def test_table_ir_preserves_cell_identity_and_relations() -> None:
    source = {"uid": "tbl-1", "table": [["Metric", "2024", "2023"], ["Revenue", "12", "10"]]}
    table = parse_table(source, document_id="doc-1", source_record_id="record-1")
    assert table.table_id == "tbl-1"
    assert len({cell.cell_id for cell in table.cells}) == 6
    assert table.cells[-1].row_id.endswith(":r1")
    assert table.cells[-1].column_id.endswith(":c2")
    assert roundtrip_values(table) == source["table"]
    assert table_structure_invariants(table, source)["raw_value_roundtrip"] is True


def test_table_ir_keeps_header_path_for_multi_level_headers() -> None:
    source = {"uid": "tbl-2", "table": [["", "Assets", "Assets"], ["Metric", "2024", "2023"], ["Loans", "8", "7"]]}
    table = parse_table(source, document_id="doc-2")
    assert table.header_rows == (0, 1)
    assert table.cells[-1].header_path == ("Assets", "2023")


def test_oracle_routes_table_and_chart_failures_to_different_actions() -> None:
    assert oracle_failure_route("TABLE_ROW_MIXING").action == "STRUCTURED_TABLE_RETRIEVAL"
    assert oracle_failure_route("CHART_VALUE").action == "VISUAL_RETRIEVAL"
    assert oracle_failure_route("TEXT_RETRIEVAL_MISS").action == "TEXT_RETRY"


def test_predicted_router_does_not_use_gold_category() -> None:
    route = predict_failure_route("What is the revenue?", initial_coverage=0.0, parser_has_table_ir=False)
    assert route.oracle is False
    assert route.action == "TEXT_RETRY"


def test_predicted_router_uses_table_ir_only_when_available() -> None:
    without_ir = predict_failure_route("Compare the table row values", initial_coverage=0.0, parser_has_table_ir=False)
    with_ir = predict_failure_route("Compare the table row values", initial_coverage=0.0, parser_has_table_ir=True)
    assert without_ir.action == "TEXT_RETRY"
    assert with_ir.action == "STRUCTURED_TABLE_RETRIEVAL"
