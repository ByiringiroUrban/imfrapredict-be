from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    structures_monitored: int
    sensor_readings_today: int
    prediction_accuracy: float
    critical_count: int
    warning_count: int
    normal_count: int
