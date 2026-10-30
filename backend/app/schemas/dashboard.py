from datetime import datetime

from pydantic import BaseModel


class ActivityItem(BaseModel):
    action: str
    resource_type: str
    created_at: datetime


class DashboardOverview(BaseModel):
    data_source: str = "database"
    monitoring_connected: bool = False
    total_monitored_resources: int
    healthy_resources: int
    warning_resources: int
    critical_resources: int
    open_incidents: int
    recent_deployments: int
    recent_activity: list[ActivityItem]
