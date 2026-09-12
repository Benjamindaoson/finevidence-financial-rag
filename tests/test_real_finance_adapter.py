from finevidence.benchmarks.real_finance import project_finqa_record, project_tatqa_record


def test_tatqa_table_text_projection_preserves_both_modalities_and_provenance():
    record = {
        "table": {"uid": "table-1", "table": [["Metric", "2024"], ["Revenue", "100"]]},
        "paragraphs": [{"uid": "p-1", "order": 1, "text": "Management explained the revenue movement."}],
        "questions": [],
    }
    question = {
        "uid": "q-1",
        "question": "What was revenue and why did it move?",
        "answer": ["100"],
        "answer_from": "table-text",
        "rel_paragraphs": ["1"],
        "derivation": "",
        "answer_type": "span",
        "scale": "",
    }

    evidence, case = project_tatqa_record(record, question, report_id="report-1", split="dev")

    assert {item.modality for item in evidence} == {"table", "text"}
    assert {ref.evidence_id for ref in case.required_evidence} == {"tatqa:report-1:table", "tatqa:report-1:paragraph:1"}
    assert case.source_dataset == "TAT-QA"
    assert case.source_question_id == "q-1"
    assert case.gold_supporting_facts["answer_from"] == "table-text"


def test_finqa_projection_preserves_gold_inds_program_and_execution_answer():
    record = {
        "id": "report/page-1-1",
        "pre_text": ["The report defines revenue."],
        "post_text": [],
        "table": [["Metric", "2024"], ["Revenue", "100"]],
        "qa": {
            "question": "What was revenue?",
            "gold_inds": {
                "table_1": "revenue in 2024 is 100 ;",
                "text_0": "the report defines revenue .",
            },
            "program": "divide(100, const_1)",
            "exe_ans": 100.0,
            "answer": "100",
        },
    }

    evidence, case = project_finqa_record(record, split="dev")

    assert {item.modality for item in evidence} == {"table", "text"}
    assert {ref.evidence_id for ref in case.required_evidence} == {
        "finqa:report/page-1-1:table:1",
        "finqa:report/page-1-1:text:pre:0",
    }
    assert case.gold_supporting_facts["table_1"] == "revenue in 2024 is 100 ;"
    assert case.reasoning_program == "divide(100, const_1)"
    assert case.gold_execution_answer == 100.0
