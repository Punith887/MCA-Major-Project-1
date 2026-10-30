from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_owner_id_created_at", "owner_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    environment: Mapped[str] = mapped_column(String(40), default="demo", nullable=False)
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    resources: Mapped[list["InfrastructureResource"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
