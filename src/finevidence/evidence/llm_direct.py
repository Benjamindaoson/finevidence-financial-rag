from __future__ import annotations

import json
import os
from pathlib import Path

from finevidence.contracts.p0_h import LLMDecompositionResult, LocalLLMConfig
from finevidence.contracts.requirements import Requirement, RequirementGraph


_QUESTION_TYPES = {"factual", "comparison", "numerical", "trend", "explanation", "multi-document synthesis"}
_REQUIREMENT_FIELDS = {"requirement_id", "description", "fact_type", "role", "entity", "metric", "period", "segment", "basis", "geography", "currency", "unit", "operation", "criticality", "depends_on", "acceptable_evidence_ids", "evidence_role"}


def parse_decomposition_json(raw: str) -> LLMDecompositionResult:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return LLMDecompositionResult(status="N/A", raw_output=raw, reason="MALFORMED_LLM_JSON")
    try:
        payload = json.loads(raw[start : end + 1])
        question_type = str(payload["question_type"]).lower()
        if question_type not in _QUESTION_TYPES or not isinstance(payload.get("requirements"), list):
            raise ValueError("invalid question_type or requirements")
        requirements = []
        for index, item in enumerate(payload["requirements"], start=1):
            if not isinstance(item, dict):
                raise ValueError("requirement must be an object")
            value = {key: item[key] for key in _REQUIREMENT_FIELDS if key in item}
            value.setdefault("requirement_id", f"R{index}")
            value.setdefault("description", value["role"] if "role" in value else f"requirement {index}")
            value.setdefault("fact_type", "RETRIEVED_FACT")
            value.setdefault("role", "predicted_fact")
            requirements.append(Requirement(**value))
        return LLMDecompositionResult(status="READY", question_type=question_type, graph=RequirementGraph(requirements=requirements), raw_output=raw)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return LLMDecompositionResult(status="N/A", raw_output=raw, reason=f"MALFORMED_LLM_JSON: {exc}")


class LocalLLMRunner:
    def __init__(self, config: LocalLLMConfig) -> None:
        self.config = config
        self._tokenizer = None
        self._model = None
        self.resolved_model_path: str | None = config.model_path

    def _load(self) -> None:
        if self._model is not None:
            return
        from huggingface_hub import snapshot_download
        from transformers import AutoModelForCausalLM, AutoTokenizer

        revision = "main" if self.config.revision == "local-cache" else self.config.revision
        path = self.config.model_path or _cached_snapshot(self.config.model_id)
        if path is None:
            path = snapshot_download(self.config.model_id, revision=revision, local_files_only=self.config.local_files_only)
        self.resolved_model_path = str(path)
        self._tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=self.config.local_files_only)
        self._model = AutoModelForCausalLM.from_pretrained(path, local_files_only=self.config.local_files_only)
        self._model.to(self.config.device)
        self._model.eval()

    def generate(self, question: str, strict: bool = False) -> str:
        self._load()
        messages = [{"role": "user", "content": _prompt(question, strict)}]
        if hasattr(self._tokenizer, "apply_chat_template"):
            prompt = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            prompt = messages[0]["content"]
        encoded = self._tokenizer(prompt, return_tensors="pt")
        encoded = {key: value.to(self.config.device) for key, value in encoded.items()}
        import torch

        with torch.inference_mode():
            output = self._model.generate(**encoded, max_new_tokens=self.config.max_new_tokens, do_sample=False)
        return self._tokenizer.decode(output[0][encoded["input_ids"].shape[1] :], skip_special_tokens=True)


def _cached_snapshot(model_id: str) -> str | None:
    """Use a complete local snapshot when hub cache metadata cannot resolve offline."""
    roots = [Path(os.environ["HF_HOME"])] if os.environ.get("HF_HOME") else []
    roots.extend(user / ".cache" / "huggingface" for user in Path("C:/Users").glob("*"))
    roots.append(Path.home() / ".cache" / "huggingface")
    for root in roots:
        snapshot_root = root / "hub" / f"models--{model_id.replace('/', '--')}" / "snapshots"
        snapshots = sorted(item for item in snapshot_root.glob("*") if item.is_dir())
        if snapshots:
            return str(snapshots[-1])
    return None

def _prompt(question: str, strict: bool) -> str:
    suffix = " Return ONLY one valid JSON object; no prose, no markdown." if strict else " Return one JSON object and no explanatory prose."
    return (
        "Decompose this financial question into the minimum evidence requirements. "
        "Use question_type from factual, comparison, numerical, trend, explanation, multi-document synthesis. "
        "Each requirement must have requirement_id, description, fact_type, role, criticality; "
        "fact_type is RETRIEVED_FACT, DERIVED_FACT, EXPLANATORY_FACT, or CONTEXT_FACT. "
        f"Question: {question}.{suffix}"
    )


def run_direct_decomposition(question: str, config: LocalLLMConfig, runner: LocalLLMRunner | None = None) -> LLMDecompositionResult:
    active = runner or LocalLLMRunner(config)
    try:
        raw = active.generate(question)
        result = parse_decomposition_json(raw)
        if result.status == "READY":
            return result
        retry_raw = active.generate(question, strict=True)
        retry = parse_decomposition_json(retry_raw)
        retry.retry_count = 1
        retry.raw_output = json.dumps({"first": raw, "retry": retry_raw}, ensure_ascii=False)
        return retry
    except Exception as exc:
        return LLMDecompositionResult(status="N/A", reason=f"LOCAL_LLM_RUNTIME_ERROR: {type(exc).__name__}: {exc}")
