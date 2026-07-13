from datetime import datetime
from pydantic import BaseModel
from typing import List

class DatabaseStatsResponse(BaseModel):
    total_size_mb: float
    active_connections: int
    queries_per_minute: int
    cache_hit_ratio: float
    uptime_days: int

class SystemLogResponse(BaseModel):
    timestamp: datetime
    level: str
    source: str
    message: str

class ModelMetricResponse(BaseModel):
    model_name: str
    accuracy: float
    drift_score: float
    last_trained: datetime
    active_features: int
    status: str
