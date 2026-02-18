import json
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.orchestrator.run import run_evaluation  # noqa: E402
from app.validators.types import ArtifactType, FailureCode, RoleType  # noqa: E402


FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "validators" / "fixtures"


def _fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _context():
    tenant_id = uuid4()
    evaluation = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        workspace_id=uuid4(),
        job_id=uuid4(),
        resume_id=uuid4(),
        status="created",
        failure_reason_code=None,
    )
    job = SimpleNamespace(description="d" * 400, recruiter_notes="notes")
    resume = SimpleNamespace(extracted_text="resume text")
    return SimpleNamespace(evaluation=evaluation, job=job, resume=resume), tenant_id


class FakeLLM:
    def __init__(self, role_outputs: dict[RoleType, list[str]]) -> None:
        self.role_outputs = role_outputs
        self.calls: list[tuple[RoleType, list[dict[str, str]]]] = []
        self._idx: dict[RoleType, int] = {}

    def generate(self, role, messages, **_kwargs):
        self.calls.append((role, messages))
        idx = self._idx.get(role, 0)
        self._idx[role] = idx + 1
        return self.role_outputs[role][idx]


@pytest.mark.asyncio
async def test_orchestrator_success_path_persists_three_artifacts_and_internal_assumption(monkeypatch):
    context, tenant_id = _context()
    user_id = uuid4()
    session = object()
    artifact_types: list[str] = []
    assumptions_written: list[dict] = []
    completed_called = {"value": False}

    llm = FakeLLM(
        {
            RoleType.INTENT: [_fixture_text("valid_intent.json")],
            RoleType.RISK: [_fixture_text("valid_risks.json")],
            RoleType.ASSUMPTION: [_fixture_text("valid_assumptions.json")],
            RoleType.INTERVIEW: [_fixture_text("valid_interview_guidance.json")],
        }
    )

    async def _get_context(*_args, **_kwargs):
        return context

    async def _create_artifact(*_args, **kwargs):
        artifact_types.append(kwargs["artifact_type"].value)
        return SimpleNamespace(id=uuid4())

    async def _create_assumption(*_args, **kwargs):
        assumptions_written.append(kwargs["content_json"])
        return SimpleNamespace(id=uuid4())

    async def _log_stage(*_args, **_kwargs):
        return None

    async def _mark_completed(*_args, **_kwargs):
        completed_called["value"] = True
        context.evaluation.status = "completed"
        return context.evaluation

    async def _mark_failed(*_args, **_kwargs):
        raise AssertionError("mark_failed should not be called in success path")

    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.get_context", _get_context)
    monkeypatch.setattr("app.orchestrator.run.ArtifactRepository.create", _create_artifact)
    monkeypatch.setattr("app.orchestrator.run.InternalAssumptionRepository.create", _create_assumption)
    monkeypatch.setattr("app.orchestrator.run.AuditRepository.log_stage", _log_stage)
    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.mark_completed", _mark_completed)
    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.mark_failed", _mark_failed)

    result = await run_evaluation(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        evaluation_id=context.evaluation.id,
        llm_client=llm,
    )

    assert result["status"] == "completed"
    assert completed_called["value"] is True
    assert artifact_types == [
        ArtifactType.INTENT_HYPOTHESES.value,
        ArtifactType.RISK_SIGNALS.value,
        ArtifactType.INTERVIEW_GUIDANCE.value,
    ]
    assert len(assumptions_written) == 1


@pytest.mark.asyncio
async def test_orchestrator_fails_role1_schema_invalid_twice(monkeypatch):
    context, tenant_id = _context()
    user_id = uuid4()
    session = object()
    artifact_calls: list[dict] = []
    failed_code = {"value": None}

    llm = FakeLLM(
        {
            RoleType.INTENT: ['{"not_hypotheses": []}', '{"still_wrong": true}'],
            RoleType.RISK: [_fixture_text("valid_risks.json")],
            RoleType.ASSUMPTION: [_fixture_text("valid_assumptions.json")],
            RoleType.INTERVIEW: [_fixture_text("valid_interview_guidance.json")],
        }
    )

    async def _get_context(*_args, **_kwargs):
        return context

    async def _create_artifact(*_args, **kwargs):
        artifact_calls.append(kwargs)
        return None

    async def _create_assumption(*_args, **_kwargs):
        raise AssertionError("assumption should not be inserted")

    async def _log_stage(*_args, **_kwargs):
        return None

    async def _mark_failed(*_args, **kwargs):
        failed_code["value"] = kwargs["failure_reason_code"]
        context.evaluation.status = "failed"
        context.evaluation.failure_reason_code = kwargs["failure_reason_code"]
        return context.evaluation

    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.get_context", _get_context)
    monkeypatch.setattr("app.orchestrator.run.ArtifactRepository.create", _create_artifact)
    monkeypatch.setattr("app.orchestrator.run.InternalAssumptionRepository.create", _create_assumption)
    monkeypatch.setattr("app.orchestrator.run.AuditRepository.log_stage", _log_stage)
    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.mark_failed", _mark_failed)

    result = await run_evaluation(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        evaluation_id=context.evaluation.id,
        llm_client=llm,
    )

    assert result["status"] == "failed"
    assert failed_code["value"] == FailureCode.SCHEMA_INVALID.value
    assert artifact_calls == []


@pytest.mark.asyncio
async def test_orchestrator_fails_role2_forbidden_language_and_keeps_intent_only(monkeypatch):
    context, tenant_id = _context()
    user_id = uuid4()
    session = object()
    artifact_types: list[str] = []
    assumptions_written: list[dict] = []
    failed_code = {"value": None}

    invalid_risk = {
        "risks": [
            {
                "risk_statement": "Escalation delay -> prolonged outage impact.",
                "mechanism": "The best action is immediate escalation because this is clearly severe.",
                "evidence": ["Operational handoff ambiguity occurred in prior incidents."],
                "counter_signals": ["Recent runbooks improved ownership handoff clarity."],
                "validation_suggestion": "Ask for incident timeline and ownership transitions in detail.",
                "confidence": "Medium",
                "confidence_rationale": "Signal appears plausible but requires direct verification."
            },
            {
                "risk_statement": "Dependency drift -> rollout delays under integration pressure.",
                "mechanism": "Changes across teams can block integration readiness and extend release windows.",
                "evidence": ["Cross-team work frequently required additional coordination cycles."],
                "counter_signals": ["The team has introduced dependency tracking rituals recently."],
                "validation_suggestion": "Probe for an example coordinating dependencies under changing deadlines.",
                "confidence": "Low",
                "confidence_rationale": "Available examples are limited and not uniformly current."
            }
        ]
    }

    llm = FakeLLM(
        {
            RoleType.INTENT: [_fixture_text("valid_intent.json")],
            RoleType.RISK: [json.dumps(invalid_risk), json.dumps(invalid_risk)],
            RoleType.ASSUMPTION: [_fixture_text("valid_assumptions.json")],
            RoleType.INTERVIEW: [_fixture_text("valid_interview_guidance.json")],
        }
    )

    async def _get_context(*_args, **_kwargs):
        return context

    async def _create_artifact(*_args, **kwargs):
        artifact_types.append(kwargs["artifact_type"].value)
        return None

    async def _create_assumption(*_args, **kwargs):
        assumptions_written.append(kwargs)
        return None

    async def _log_stage(*_args, **_kwargs):
        return None

    async def _mark_failed(*_args, **kwargs):
        failed_code["value"] = kwargs["failure_reason_code"]
        return context.evaluation

    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.get_context", _get_context)
    monkeypatch.setattr("app.orchestrator.run.ArtifactRepository.create", _create_artifact)
    monkeypatch.setattr("app.orchestrator.run.InternalAssumptionRepository.create", _create_assumption)
    monkeypatch.setattr("app.orchestrator.run.AuditRepository.log_stage", _log_stage)
    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.mark_failed", _mark_failed)

    result = await run_evaluation(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        evaluation_id=context.evaluation.id,
        llm_client=llm,
    )

    assert result["status"] == "failed"
    assert failed_code["value"] == FailureCode.FORBIDDEN_LANGUAGE.value
    assert artifact_types == [ArtifactType.INTENT_HYPOTHESES.value]
    assert assumptions_written == []


@pytest.mark.asyncio
async def test_repair_instruction_is_passed_to_attempt_two(monkeypatch):
    context, tenant_id = _context()
    user_id = uuid4()
    session = object()

    bad_intent = json.loads(_fixture_text("valid_intent.json"))
    bad_intent["hypotheses"][0]["hypothesis_statement"] = (
        "The best answer appears obvious and should trigger a direct selection decision."
    )

    llm = FakeLLM(
        {
            RoleType.INTENT: [json.dumps(bad_intent), _fixture_text("valid_intent.json")],
            RoleType.RISK: [_fixture_text("valid_risks.json")],
            RoleType.ASSUMPTION: [_fixture_text("valid_assumptions.json")],
            RoleType.INTERVIEW: [_fixture_text("valid_interview_guidance.json")],
        }
    )

    async def _get_context(*_args, **_kwargs):
        return context

    async def _create_artifact(*_args, **_kwargs):
        return None

    async def _create_assumption(*_args, **_kwargs):
        return None

    async def _log_stage(*_args, **_kwargs):
        return None

    async def _mark_completed(*_args, **_kwargs):
        return context.evaluation

    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.get_context", _get_context)
    monkeypatch.setattr("app.orchestrator.run.ArtifactRepository.create", _create_artifact)
    monkeypatch.setattr("app.orchestrator.run.InternalAssumptionRepository.create", _create_assumption)
    monkeypatch.setattr("app.orchestrator.run.AuditRepository.log_stage", _log_stage)
    monkeypatch.setattr("app.orchestrator.run.EvaluationRepository.mark_completed", _mark_completed)

    await run_evaluation(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        evaluation_id=context.evaluation.id,
        llm_client=llm,
    )

    intent_calls = [entry for entry in llm.calls if entry[0] == RoleType.INTENT]
    assert len(intent_calls) == 2
    attempt2_user_text = intent_calls[1][1][1]["content"]
    assert "Repair instruction" in attempt2_user_text
    assert "Remove forbidden words" in attempt2_user_text

