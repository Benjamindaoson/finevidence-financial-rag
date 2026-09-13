from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

TRACK_FILES = {"citation": "claim_citation_candidates.jsonl", "table": "table_semantic_candidates.jsonl"}


class ReviewSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annotator_id: str = Field(min_length=1, max_length=100)
    annotation_status: Literal["DRAFT", "NEEDS_REVIEW", "SKIPPED", "VERIFIED"]
    notes: str = Field(default="", max_length=4000)
    support_status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED"] | None = None
    gold_supporting_evidence_ids: list[str] = Field(default_factory=list)
    page: int | None = Field(default=None, ge=1)
    block_id: str | None = None
    table_id: str | None = None
    cell_id: str | None = None
    cell_labels: list[dict[str, Any]] = Field(default_factory=list)
    cell_value_correct: bool | None = None
    row_mapping_correct: bool | None = None
    column_mapping_correct: bool | None = None
    header_path_correct: bool | None = None
    unit_correct: bool | None = None
    period_correct: bool | None = None
    entity_correct: bool | None = None
    merged_semantics_correct: bool | None = None
    footnote_association_correct: bool | None = None
    answerability: Literal["ANSWERABLE", "PARTIAL_EVIDENCE", "UNANSWERABLE"] | None = None
    action: Literal["ANSWER", "RETRIEVE_MORE", "ABSTAIN"] | None = None
    reason: str = Field(default="", max_length=1000)


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class ReviewStore:
    """Append-only local review store; deliberately no database or product workflow."""

    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()
        self.candidate_root = self.root / "artifacts" / "final_rag_eval"
        self.annotation_root = self.candidate_root / "human_annotations"
        self._evidence: dict[str, dict[str, Any]] | None = None

    def _candidate_path(self, track: str) -> Path:
        if track == "citation":
            v1 = self.candidate_root / "claim_citation_candidates_v1.jsonl"
            if v1.exists():
                return v1
        if track == "answerability":
            v1 = self.candidate_root / "answerability_candidates_v1.jsonl"
            return v1 if v1.exists() else self.candidate_root / "candidates" / "answerability_candidates.jsonl"
        if track not in TRACK_FILES:
            raise KeyError(track)
        return self.candidate_root / "candidates" / TRACK_FILES[track]

    def _load_evidence(self) -> dict[str, dict[str, Any]]:
        if self._evidence is None:
            source = self.root / "benchmarks" / "real_finance_v1" / "evidence.jsonl"
            self._evidence = {row["evidence_id"]: row for row in _jsonl(source)}
        return self._evidence

    def _latest(self, track: str) -> dict[str, dict[str, Any]]:
        return {str(row["case_id"]): row for row in _jsonl(self.annotation_root / f"{track}.jsonl")}

    @staticmethod
    def _case_id(candidate: dict[str, Any]) -> str:
        return str(candidate.get("case_id") or candidate.get("table_id"))

    def queue(self, track: str) -> list[dict[str, Any]]:
        annotations = self._latest(track)
        evidence = self._load_evidence()
        result = []
        for candidate in _jsonl(self._candidate_path(track)):
            row = dict(candidate)
            row["case_id"] = self._case_id(candidate)
            row["annotation"] = annotations.get(row["case_id"])
            ids = candidate.get("evidence_candidate_ids", []) + candidate.get("supporting_evidence_ids", []) + candidate.get("available_evidence_ids", [])
            row["evidence"] = [
                {
                    "evidence_id": item,
                    "text": evidence.get(item, {}).get("text", "[source evidence not present in local IR]"),
                    "document_id": evidence.get(item, {}).get("document_id"),
                    "page": evidence.get(item, {}).get("page"),
                    "block_id": evidence.get(item, {}).get("block_id"),
                    "table_id": evidence.get(item, {}).get("table_id"),
                    "row_id": evidence.get(item, {}).get("row_id"),
                    "column_id": evidence.get(item, {}).get("column_id"),
                    "predicted": item in candidate.get("predicted_evidence_ids", []),
                    "proposed_supporting": item in candidate.get("proposed_supporting_evidence_ids", candidate.get("supporting_evidence_ids", [])),
                }
                for item in dict.fromkeys(ids)
            ]
            if track == "table":
                row["image_url"] = f"/api/v1/review/page-image?document_id={candidate.get('document_id', '')}&page={candidate.get('page', '')}"
            result.append(row)
        return result

    def save(self, track: str, case_id: str, submission: ReviewSubmission) -> dict[str, Any]:
        if track not in {"citation", "table", "answerability"}:
            raise KeyError(track)
        if not any(self._case_id(row) == case_id for row in _jsonl(self._candidate_path(track))):
            raise KeyError(case_id)
        if submission.annotation_status == "VERIFIED":
            valid = {
                "citation": submission.support_status is not None,
                "table": bool(submission.cell_labels) or bool(submission.notes.strip()),
                "answerability": submission.answerability is not None and submission.action is not None,
            }[track]
            if not valid:
                raise ValueError("VERIFIED_REQUIRES_TRACK_LABEL")
        row = submission.model_dump()
        row.update({
            "track": track,
            "case_id": case_id,
            "annotation_time": datetime.now(timezone.utc).isoformat(),
            "human_verified": submission.annotation_status == "VERIFIED",
            "protocol_version": "P0-J-human-review-v1",
        })
        self.annotation_root.mkdir(parents=True, exist_ok=True)
        with (self.annotation_root / f"{track}.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def page_image(self, document_id: str, page: int) -> Path:
        manifest = self.root / "artifacts" / "hsbc_page_images" / "page_render_manifest.json"
        for row in json.loads(manifest.read_text(encoding="utf-8")).get("pages", []):
            if row.get("document_id") == document_id and int(row.get("page", -1)) == page:
                path = Path(row["image_path"]).resolve()
                allowed = (self.root / "artifacts" / "hsbc_page_images").resolve()
                if allowed in path.parents and path.is_file():
                    return path
        raise FileNotFoundError((document_id, page))


REVIEW_HTML = r"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>FinEvidence 人工审核</title>
<style>body{font:14px system-ui;margin:0;background:#f4f6f8;color:#20242a}header{padding:14px 22px;background:#182333;color:white}main{max-width:1200px;margin:18px auto;padding:0 18px}.bar,.actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.card{background:white;border:1px solid #d8dde5;border-radius:8px;padding:14px;margin:12px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.evidence{border-left:4px solid #aab6c8;padding:8px;margin:8px 0;white-space:pre-wrap}.page{max-width:100%;max-height:650px;background:#222}.cells{max-height:380px;overflow:auto}.cell{display:grid;grid-template-columns:220px 1fr 150px;gap:8px;padding:5px;border-bottom:1px solid #eee}button,select,input,textarea{font:inherit;padding:7px;border:1px solid #aab4c2;border-radius:5px}button{cursor:pointer}.primary{background:#1769aa;color:white}.muted{color:#687385}</style>
<header><strong>FinEvidence 人工审核工作台</strong> <span class="muted">本地审核工具，不是生产前端</span></header><main>
<div class="bar"><label>Track <select id="track"><option value="citation">Citation</option><option value="table">Table Semantic</option><option value="answerability">Answerability</option></select></label><label>Annotator <input id="annotator" placeholder="你的标识"></label><span id="position"></span></div>
<div id="case" class="card">加载中...</div><div class="actions"><button onclick="move(-1)">Previous</button><button onclick="move(1)">Next</button><button onclick="save('SKIPPED')">Skip</button><button onclick="save('NEEDS_REVIEW')">Needs Review</button><button onclick="save('DRAFT')">Save</button><button class="primary" onclick="save('VERIFIED')">Confirm &amp; Save</button></div><p id="message"></p></main>
<script>
let queue=[],index=0;const track=document.getElementById('track'),annotator=document.getElementById('annotator');annotator.value=localStorage.getItem('finevidence-annotator')||'';annotator.onchange=()=>localStorage.setItem('finevidence-annotator',annotator.value);track.value=new URLSearchParams(location.search).get('track')||'citation';track.onchange=()=>{history.replaceState({},'',`/review?track=${track.value}`);load()};
function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function load(){let r=await fetch(`/api/v1/review/queue?track=${track.value}`);queue=await r.json();index=0;render()}
function render(){document.getElementById('position').textContent=queue.length?`${index+1}/${queue.length}`:'0/0';if(!queue.length){document.getElementById('case').innerHTML='没有候选记录';return}let x=queue[index],a=x.annotation||{};let h=`<h2>${esc(x.question||x.claim||x.case_id)}</h2><p class="muted">${esc(x.case_id)} · candidate=${esc(x.candidate_status||x.annotation_status)} · previous=${esc(a.annotation_status||'未审核')}</p>`;
if(track.value==='citation')h+=`<label>Claim status <select id="support"><option value="">请选择</option><option>SUPPORTED</option><option>PARTIALLY_SUPPORTED</option><option>UNSUPPORTED</option></select></label><div class="grid"><div><h3>Predicted / candidate evidence（可多选确认）</h3>${(x.evidence||[]).map(e=>`<div class="evidence"><label><input type="checkbox" class="support-id" value="${esc(e.evidence_id)}"> <strong>${esc(e.evidence_id)}</strong></label><span>predicted=${e.predicted?'YES':'NO'} · source-proposed=${e.proposed_supporting?'YES':'NO'} · ${esc(e.document_id)} page=${esc(e.page)} block=${esc(e.block_id)} table=${esc(e.table_id)} row=${esc(e.row_id)} col=${esc(e.column_id)}</span><br>${esc(e.text)}</div>`).join('')}</div><div><p>位置可确认时填写，否则留空。</p><input id="page" type="number" min="1" placeholder="page"><input id="block" placeholder="block_id"><input id="tableid" placeholder="table_id"><input id="cell" placeholder="cell_id"></div></div>`;
if(track.value==='table')h+=`<div class="grid"><div><h3>原始页面</h3><img class="page" src="${esc(x.image_url)}"></div><div><h3>TableIR cells</h3><div class="cells">${(x.cells||[]).map(c=>`<div class="cell"><span>${esc(c.cell_id)}</span><span>${esc(c.value)}<br><small>${esc((c.header_path||[]).join(' / '))} · bbox=${esc(c.bbox)}</small></span><select class="cell-label" data-cell="${esc(c.cell_id)}"><option value="">未判断</option><option>CORRECT</option><option>INCORRECT</option><option>NOT_APPLICABLE</option><option>UNCERTAIN</option></select></div>`).join('')}</div><h3>Region semantic checks</h3>${['cell_value_correct','row_mapping_correct','column_mapping_correct','header_path_correct','unit_correct','period_correct','entity_correct','merged_semantics_correct','footnote_association_correct'].map(k=>`<label>${k} <select id="${k}"><option value="">N/A</option><option value="true">CORRECT</option><option value="false">INCORRECT</option></select></label><br>`).join('')}</div></div>`;
if(track.value==='answerability')h+=`<p>Required facts: ${esc((x.required_facts||[]).map(f=>f.description||f).join(' | ')||'未提供')}<br>Available: ${esc((x.available_evidence_ids||[]).join(', ')||'无')}<br>Missing: ${esc((x.missing_evidence_ids||[]).join(', ')||'无')}</p>${(x.evidence||[]).map(e=>`<div class="evidence"><strong>${esc(e.evidence_id)}</strong> ${esc(e.document_id)} page=${esc(e.page)}<br>${esc(e.text)}</div>`).join('')}<label>Status <select id="answerability"><option value="">请选择</option><option>ANSWERABLE</option><option>PARTIAL_EVIDENCE</option><option>UNANSWERABLE</option></select></label> <label>Action <select id="action"><option value="">请选择</option><option>ANSWER</option><option>RETRIEVE_MORE</option><option>ABSTAIN</option></select></label><br><textarea id="reason" rows="2" placeholder="为什么？"></textarea>`;
h+=`<br><textarea id="notes" rows="3" placeholder="notes"></textarea>`;document.getElementById('case').innerHTML=h;if(a.support_status)document.getElementById('support').value=a.support_status;if(a.answerability)document.getElementById('answerability').value=a.answerability;if(a.action)document.getElementById('action').value=a.action;if(a.notes)document.getElementById('notes').value=a.notes;if(a.reason)document.getElementById('reason').value=a.reason;if(a.gold_supporting_evidence_ids)document.querySelectorAll('.support-id').forEach(e=>e.checked=a.gold_supporting_evidence_ids.includes(e.value))}
function payload(status){let p={annotator_id:annotator.value.trim(),annotation_status:status,notes:document.getElementById('notes')?.value||''};if(track.value==='citation'){p.support_status=document.getElementById('support')?.value||null;p.gold_supporting_evidence_ids=[...document.querySelectorAll('.support-id:checked')].map(e=>e.value);p.page=Number(document.getElementById('page')?.value)||null;p.block_id=document.getElementById('block')?.value||null;p.table_id=document.getElementById('tableid')?.value||null;p.cell_id=document.getElementById('cell')?.value||null}if(track.value==='table'){p.cell_labels=[...document.querySelectorAll('.cell-label')].filter(e=>e.value).map(e=>({cell_id:e.dataset.cell,label:e.value}));['cell_value_correct','row_mapping_correct','column_mapping_correct','header_path_correct','unit_correct','period_correct','entity_correct','merged_semantics_correct','footnote_association_correct'].forEach(k=>{let v=document.getElementById(k)?.value;p[k]=v===''?null:v==='true'})}if(track.value==='answerability'){p.answerability=document.getElementById('answerability')?.value||null;p.action=document.getElementById('action')?.value||null;p.reason=document.getElementById('reason')?.value||''}return p}
async function save(status){if(!annotator.value.trim()){alert('请先填写 annotator');return}let x=queue[index],r=await fetch(`/api/v1/review/${track.value}/${encodeURIComponent(x.case_id)}`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload(status))});let b=await r.json();document.getElementById('message').textContent=r.ok?`已保存：${status}（human_verified=${b.human_verified}）`:`保存失败：${b.detail||'unknown'}`;if(r.ok)queue[index].annotation=b}function move(d){if(queue.length){index=Math.max(0,Math.min(queue.length-1,index+d));render()}}load();
</script></html>"""


def create_review_router(store: ReviewStore) -> APIRouter:
    router = APIRouter()

    @router.get("/review", response_class=HTMLResponse)
    def review_page() -> str:
        return REVIEW_HTML

    @router.get("/api/v1/review/queue")
    def review_queue(track: str = Query(default="citation")) -> list[dict[str, Any]]:
        try:
            return store.queue(track)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail="unknown review track") from exc

    @router.post("/api/v1/review/{track}/{case_id}")
    def save_review(track: str, case_id: str, submission: ReviewSubmission) -> dict[str, Any]:
        try:
            return store.save(track, case_id, submission)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="review case not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @router.get("/api/v1/review/page-image")
    def page_image(document_id: str, page: int) -> FileResponse:
        try:
            return FileResponse(store.page_image(document_id, page))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="page image not found") from exc

    return router
