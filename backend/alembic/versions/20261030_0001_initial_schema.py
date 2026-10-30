"""Create initial AIOps application schema.

Revision ID: 20261030_0001
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261030_0001"
down_revision = None
branch_labels = None
depends_on = None

user_role = sa.Enum("ADMIN", "DEVOPS_ENGINEER", "VIEWER", name="user_role")
resource_status = sa.Enum(
    "UNKNOWN", "HEALTHY", "WARNING", "CRITICAL", name="resource_status"
)
incident_severity = sa.Enum(
    "LOW", "MEDIUM", "HIGH", "CRITICAL", name="incident_severity"
)
incident_status = sa.Enum(
    "OPEN", "ACKNOWLEDGED", "RESOLVED", name="incident_status"
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_owner_id_created_at", "projects", ["owner_id", "created_at"])

    op.create_table(
        "infrastructure_resources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("resource_name", sa.String(length=160), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("status", resource_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resources_project_status", "infrastructure_resources", ["project_id", "status"]
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", incident_severity, nullable=False),
        sa.Column("status", incident_status, nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_status_detected_at", "incidents", ["status", "detected_at"])

    op.create_table(
        "deployments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("environment", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deployments_project_deployed_at", "deployments", ["project_id", "deployed_at"]
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column(
            "details",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_deployments_project_deployed_at", table_name="deployments")
    op.drop_table("deployments")
    op.drop_index("ix_incidents_status_detected_at", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("ix_resources_project_status", table_name="infrastructure_resources")
    op.drop_table("infrastructure_resources")
    op.drop_index("ix_projects_owner_id_created_at", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        incident_status.drop(bind, checkfirst=True)
        incident_severity.drop(bind, checkfirst=True)
        resource_status.drop(bind, checkfirst=True)
        user_role.drop(bind, checkfirst=True)
