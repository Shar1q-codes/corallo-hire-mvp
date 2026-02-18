from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact
from app.models.hitl import DecisionChainEvent, HumanAcknowledgement


class HITLRepository:
    @staticmethod
    async def insert_acknowledgement(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        evaluation_id: UUID,
        acknowledgement_type: str,
        subject_ref_type: str,
        subject_ref_id: str | None,
        content_text: str,
        decision_mode: str,
        created_by: UUID,
    ) -> HumanAcknowledgement:
        row = HumanAcknowledgement(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            job_id=job_id,
            resume_id=resume_id,
            evaluation_id=evaluation_id,
            acknowledgement_type=acknowledgement_type,
            subject_ref_type=subject_ref_type,
            subject_ref_id=subject_ref_id,
            content_text=content_text,
            decision_mode=decision_mode,
            created_by=created_by,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def insert_chain_event(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
        actor_user_id: UUID,
        event_type: str,
        detail_json: dict,
    ) -> DecisionChainEvent:
        row = DecisionChainEvent(
            tenant_id=tenant_id,
            evaluation_id=evaluation_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            detail_json=detail_json,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def list_acknowledgements_for_evaluation(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
    ) -> list[HumanAcknowledgement]:
        result = await session.execute(
            select(HumanAcknowledgement)
            .where(
                HumanAcknowledgement.tenant_id == tenant_id,
                HumanAcknowledgement.evaluation_id == evaluation_id,
            )
            .order_by(HumanAcknowledgement.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_chain_events_for_evaluation(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
    ) -> list[DecisionChainEvent]:
        result = await session.execute(
            select(DecisionChainEvent)
            .where(
                DecisionChainEvent.tenant_id == tenant_id,
                DecisionChainEvent.evaluation_id == evaluation_id,
            )
            .order_by(DecisionChainEvent.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def has_risk_signals_artifact(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
    ) -> bool:
        result = await session.execute(
            select(Artifact.id).where(
                Artifact.tenant_id == tenant_id,
                Artifact.evaluation_id == evaluation_id,
                Artifact.artifact_type == "risk_signals",
            )
        )
        return result.scalar_one_or_none() is not None

