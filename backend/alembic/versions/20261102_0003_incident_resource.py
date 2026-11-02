"""Add nullable resource association to incidents.

Revision ID: 20261102_0003
Revises: 20261031_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20261102_0003"
down_revision = "20261031_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("incidents") as batch_op:
        batch_op.add_column(sa.Column("resource_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_incidents_resource_id_infrastructure_resources",
            "infrastructure_resources",
            ["resource_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_incidents_resource_id_status",
        "incidents",
        ["resource_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_incidents_resource_id_status", table_name="incidents")
    with op.batch_alter_table("incidents") as batch_op:
        batch_op.drop_constraint(
            "fk_incidents_resource_id_infrastructure_resources",
            type_="foreignkey",
        )
        batch_op.drop_column("resource_id")
