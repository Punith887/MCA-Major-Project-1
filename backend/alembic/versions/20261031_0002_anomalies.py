"""Add Prometheus resource mapping and anomaly records.

Revision ID: 20261031_0002
Revises: 20261030_0001
"""
from alembic import op
import sqlalchemy as sa

revision = "20261031_0002"
down_revision = "20261030_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "infrastructure_resources",
        sa.Column("prometheus_job", sa.String(length=120), nullable=True),
    )
    op.create_table(
        "anomalies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("incident_id", sa.Uuid(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("detected_features", sa.JSON(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["resource_id"],
            ["infrastructure_resources.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_id",
            "detected_at",
            name="uq_anomalies_resource_detected_at",
        ),
    )
    op.create_index(
        "ix_anomalies_resource_detected_at",
        "anomalies",
        ["resource_id", "detected_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_anomalies_resource_detected_at", table_name="anomalies")
    op.drop_table("anomalies")
    op.drop_column("infrastructure_resources", "prometheus_job")
