from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scriptweaver.ai.provider import (
    AIAnalysisProvider,
    AdaptationPlanProvider,
    ScreenplayProvider,
)
from scriptweaver.domain.analysis_validation import AnalysisValidationError
from scriptweaver.domain.models import (
    Chapter,
    UncertaintyResolution,
)
from scriptweaver.domain.plan_validation import PlanValidationError
from scriptweaver.domain.uncertainty_validation import (
    UncertaintyValidationError,
)
from scriptweaver.domain.workflow import WorkflowTransitionError
from scriptweaver.export.yaml_exporter import export_job_to_yaml
from scriptweaver.persistence.repository import (
    InMemoryJobRepository,
    JobRepository,
)
from scriptweaver.services.adaptation_service import (
    AdaptationService,
    AdaptationServiceError,
)
from scriptweaver.services.chapter_splitter import (
    ChapterSplitterError,
    split_chapters,
)


# ── Request models ───────────────────────────────────────────────


class CreateJobRequest(BaseModel):
    job_id: str


class ChapterInput(BaseModel):
    index: int
    title: str
    content: str


class AttachChaptersRequest(BaseModel):
    chapters: list[ChapterInput]


class UncertaintyAnswerRequest(BaseModel):
    uncertainty_id: str
    selected_option_id: str | None = None
    custom_answer: str | None = None


class ConfirmPlanRequest(BaseModel):
    target_format: str
    structure: str
    scenes: list[dict[str, Any]] = []
    review_questions: list[dict[str, Any]] = []

    def to_plan(self):
        from scriptweaver.domain.models import (
            AdaptationDecision,
            AdaptationPlan,
            PlanReviewQuestion,
            ScenePlan,
        )

        def _parse_decisions(
            raw_list: list[dict[str, Any]],
        ) -> list[AdaptationDecision]:
            return [
                AdaptationDecision(
                    id=d["id"],
                    description=d["description"],
                    reason=d["reason"],
                    source_event_ids=d.get("source_event_ids", []),
                )
                for d in raw_list
            ]

        try:
            return AdaptationPlan(
                target_format=self.target_format,
                structure=self.structure,
                scenes=[
                    ScenePlan(
                        id=s["id"],
                        scene_order=s["scene_order"],
                        title=s["title"],
                        dramatic_purpose=s["dramatic_purpose"],
                        character_ids=s.get("character_ids", []),
                        source_chapter_indexes=s.get(
                            "source_chapter_indexes", []
                        ),
                        retained_event_ids=s.get(
                            "retained_event_ids", []
                        ),
                        source_candidate_scene_ids=s.get(
                            "source_candidate_scene_ids", []
                        ),
                        compression_choices=_parse_decisions(
                            s.get("compression_choices", [])
                        ),
                        merge_choices=_parse_decisions(
                            s.get("merge_choices", [])
                        ),
                        rewrite_choices=_parse_decisions(
                            s.get("rewrite_choices", [])
                        ),
                        review_questions=[
                            PlanReviewQuestion(**rq)
                            for rq in s.get("review_questions", [])
                        ],
                    )
                    for s in self.scenes
                ],
                review_questions=[
                    PlanReviewQuestion(**rq)
                    for rq in self.review_questions
                ],
            )
        except (TypeError, KeyError) as error:
            raise ValueError(str(error)) from error


# ── App factory ──────────────────────────────────────────────────


def create_app(
    ai_provider: AIAnalysisProvider,
    plan_provider: AdaptationPlanProvider | None = None,
    screenplay_provider: ScreenplayProvider | None = None,
    repository: JobRepository | None = None,
    static_dir: str | None = None,
) -> FastAPI:
    app = FastAPI(
        title="ScriptWeaver API",
        description=(
            "Human-in-the-loop AI novel-to-screenplay adaptation "
            "backend."
        ),
        version="0.1.0",
    )

    service = AdaptationService(
        ai_provider,
        plan_provider=plan_provider,
        screenplay_provider=screenplay_provider,
    )
    repo = repository if repository is not None else InMemoryJobRepository()

    def _get_job(job_id: str):
        job = repo.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    def _save_job(job):
        repo.save(job)
        return job

    def _job_to_response(job):
        return job.to_dict()

    def _handle_error(status: int, detail: str):
        raise HTTPException(status_code=status, detail=detail)

    # ── Health ───────────────────────────────────────────────

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # ── Create job ───────────────────────────────────────────

    @app.post("/jobs", status_code=201)
    def create_job(req: CreateJobRequest):
        if repo.exists(req.job_id):
            raise HTTPException(
                status_code=409,
                detail="Job with this ID already exists",
            )
        job = service.create_job(req.job_id)
        _save_job(job)
        return _job_to_response(job)

    # ── Get job ──────────────────────────────────────────────

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str):
        return _job_to_response(_get_job(job_id))

    # ── Attach chapters ──────────────────────────────────────

    @app.post("/jobs/{job_id}/chapters")
    def attach_chapters(job_id: str, req: AttachChaptersRequest):
        job = _get_job(job_id)
        chapters = [
            Chapter(
                index=ch.index,
                title=ch.title,
                content=ch.content,
            )
            for ch in req.chapters
        ]
        try:
            job = service.attach_chapters(job, chapters)
        except AdaptationServiceError as error:
            _handle_error(400, str(error))
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Upload file ──────────────────────────────────────────

    @app.post("/jobs/{job_id}/upload")
    def upload_file(job_id: str, file: UploadFile = File(...)):
        job = _get_job(job_id)
        try:
            content = file.file.read().decode("utf-8")
        except UnicodeDecodeError:
            _handle_error(400, "File must be UTF-8 encoded text")
        try:
            chapters = split_chapters(content)
        except ChapterSplitterError as error:
            _handle_error(400, str(error))
        try:
            job = service.attach_chapters(job, list(chapters))
        except AdaptationServiceError as error:
            _handle_error(400, str(error))
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Generate analysis ────────────────────────────────────

    @app.post("/jobs/{job_id}/analyze")
    def analyze(job_id: str):
        job = _get_job(job_id)
        try:
            job = service.generate_analysis(job)
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        except (
            AdaptationServiceError,
            AnalysisValidationError,
            ValueError,
        ) as error:
            _handle_error(400, str(error))
        except RuntimeError as error:
            _handle_error(502, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Confirm analysis ────────────────────────────────────

    @app.post("/jobs/{job_id}/confirm-analysis")
    def confirm_analysis(job_id: str):
        job = _get_job(job_id)
        try:
            job = service.confirm_analysis(job)
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        except (AnalysisValidationError, ValueError) as error:
            _handle_error(400, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Next uncertainty ─────────────────────────────────────

    @app.get("/jobs/{job_id}/next-uncertainty")
    def next_uncertainty(job_id: str):
        job = _get_job(job_id)
        try:
            uncertainty = service.get_next_unanswered_uncertainty(job)
        except AdaptationServiceError as error:
            _handle_error(409, str(error))
        if uncertainty is None:
            return None
        return uncertainty.to_dict()

    # ── Uncertainty answer ───────────────────────────────────

    @app.post("/jobs/{job_id}/uncertainty-answer")
    def uncertainty_answer(
        job_id: str,
        req: UncertaintyAnswerRequest,
    ):
        job = _get_job(job_id)
        resolution = UncertaintyResolution(
            uncertainty_id=req.uncertainty_id,
            selected_option_id=req.selected_option_id,
            custom_answer=req.custom_answer,
        )
        try:
            job = service.submit_uncertainty_answer(job, resolution)
        except AdaptationServiceError as error:
            _handle_error(409, str(error))
        except UncertaintyValidationError as error:
            _handle_error(400, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Generate plan ────────────────────────────────────────

    @app.post("/jobs/{job_id}/generate-plan")
    def generate_plan(job_id: str):
        job = _get_job(job_id)
        try:
            job = service.generate_plan(job)
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        except AdaptationServiceError as error:
            _handle_error(400, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Confirm plan ─────────────────────────────────────────

    @app.post("/jobs/{job_id}/confirm-plan")
    def confirm_plan(job_id: str, req: ConfirmPlanRequest):
        job = _get_job(job_id)
        try:
            plan = req.to_plan()
            job = service.confirm_plan(job, plan)
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        except (PlanValidationError, ValueError) as error:
            _handle_error(400, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Generate screenplay ───────────────────────────────────

    @app.post("/jobs/{job_id}/generate-screenplay")
    def generate_screenplay(job_id: str):
        job = _get_job(job_id)
        try:
            job = service.generate_screenplay(job)
        except WorkflowTransitionError as error:
            _handle_error(409, str(error))
        except AdaptationServiceError as error:
            _handle_error(400, str(error))
        except RuntimeError as error:
            _handle_error(502, str(error))
        _save_job(job)
        return _job_to_response(job)

    # ── Export YAML ───────────────────────────────────────────

    @app.get("/jobs/{job_id}/export-yaml")
    def export_yaml(
        job_id: str,
        title: str = Query(default=""),
        author: str = Query(default=""),
        adapter: str = Query(default="ScriptWeaver AI"),
        target_format: str = Query(default="short_drama"),
        language: str = Query(default="zh-CN"),
    ):
        job = _get_job(job_id)
        metadata = {
            "title": title,
            "author": author,
            "adapter": adapter,
            "target_format": target_format,
            "language": language,
            "created_at": "",
        }
        yaml_str = export_job_to_yaml(job, metadata)
        return Response(
            content=yaml_str,
            media_type="application/x-yaml",
        )

    # ── Static files ──────────────────────────────────────────

    if static_dir is not None:
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


# ── Default application instance ──────────────────────────────────

from pathlib import Path as _Path  # noqa: E402

from scriptweaver.ai.mock_provider import (  # noqa: E402
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)

_web_dir = _Path(__file__).parent.parent / "web"
app = create_app(
    MockAIAnalysisProvider(),
    plan_provider=MockPlanProvider(),
    screenplay_provider=MockScreenplayProvider(),
    static_dir=str(_web_dir) if _web_dir.is_dir() else None,
)
