from finevidence.eval.final_rag import answerability_metrics, citation_metrics, table_semantic_metrics


def test_unverified_tracks_are_na_not_zero():
    assert citation_metrics([{"case_id": "c", "human_verified": False}], []) ["status"] == "BLOCKED"
    assert table_semantic_metrics([{"table_id": "t", "human_verified": False}])["cell_value_correct"] == "N/A"
    assert answerability_metrics([{"case_id": "c", "human_verified": False}])["answerability_accuracy"] == "N/A"


def test_verified_citation_metrics_and_location_accuracy():
    gold = [
        {
            "case_id": "c",
            "human_verified": True,
            "supporting_evidence_ids": ["e1"],
            "page": 3,
            "block_id": "b1",
            "cell_id": "c1",
        }
    ]
    predicted = [{"case_id": "c", "cited_evidence_ids": ["e1", "wrong"], "cited_pages": [3]}]
    result = citation_metrics(gold, predicted)
    assert result["citation_precision"] == 0.5
    assert result["citation_recall"] == 1.0
    assert result["citation_f1"] == 2 / 3
    assert result["unsupported_citation_rate"] == 0.5
    assert result["page_accuracy"] == 1.0
    assert result["block_accuracy"] == "N/A"
    assert result["cell_accuracy"] == "N/A"


def test_table_semantics_are_separate_from_structure():
    result = table_semantic_metrics(
        [
            {
                "human_verified": True,
                "structure_recoverable": True,
                "cell_value_correct": True,
                "row_mapping_correct": True,
                "column_mapping_correct": False,
                "header_path_correct": None,
            }
        ]
    )
    assert result["structure_recoverable_rate"] == 1.0
    assert result["cell_value_correct"] == 1.0
    assert result["column_mapping_correct"] == 0.0
    assert result["header_path_correct"] == "N/A"


def test_answerability_actions_are_scored_against_verified_labels():
    result = answerability_metrics(
        [
            {"human_verified": True, "answerability": "ANSWERABLE", "action": "ANSWER"},
            {"human_verified": True, "answerability": "PARTIAL_EVIDENCE", "action": "RETRIEVE_MORE"},
            {"human_verified": True, "answerability": "UNANSWERABLE", "action": "ABSTAIN"},
        ]
    )
    assert result["answerability_accuracy"] == 1.0
    assert result["abstention_precision"] == 1.0
    assert result["abstention_recall"] == 1.0
    assert result["partial_detection_rate"] == 1.0
    assert result["false_answer_rate"] == 0.0
