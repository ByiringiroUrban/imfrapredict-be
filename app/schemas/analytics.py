from pydantic import BaseModel
from typing import List

class RiskTrendResponse(BaseModel):
    month: str
    avg_risk_score: float
    critical_count: int

class ForecastDataPoint(BaseModel):
    year: int
    scores: dict[str, float]

class BridgeRiskSummary(BaseModel):
    id: str
    name: str
    risk_score: float
    status: str
    failure_year: int
    rul: float
    confidence: float

class RiskDistributionBucket(BaseModel):
    range: str
    count: int

class RiskForecastResponse(BaseModel):
    forecast_data: List[ForecastDataPoint]
    risk_table: List[BridgeRiskSummary]
    histogram: List[RiskDistributionBucket]
    avg_rul: float

class BridgeCostDetail(BaseModel):
    id: str
    name: str
    risk_score: float
    status: str
    cost: float

class DistrictBudget(BaseModel):
    d: str
    budget: float

class BudgetAnalyticsResponse(BaseModel):
    total_portfolio: float
    immediate_repairs: float
    critical_count: int
    scatter_data: List[BridgeCostDetail]
    district_budget: List[DistrictBudget]
    bridge_budgets: List[BridgeCostDetail]
