from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_session
from app.models import Structure
from app.schemas.analytics import RiskTrendResponse, BudgetAnalyticsResponse, RiskForecastResponse, ForecastDataPoint, BridgeRiskSummary, RiskDistributionBucket, BridgeCostDetail, DistrictBudget

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/forecasts", response_model=RiskForecastResponse)
async def get_risk_forecasts(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Structure))
    structures = res.scalars().all()
    
    # Calculate Risk Table
    risk_table = []
    histo_counts = [0, 0, 0, 0, 0]
    
    for s in structures:
        risk = s.current_risk_score or 0.0
        status = s.current_status or "normal"
        
        # Calculate RUL
        rate = 2.5 if risk > 60 else 1.5
        rul = max(0.0, min(20.0, (100 - risk) / rate))
        failure_year = 2024 + int(rul)
        
        risk_table.append(BridgeRiskSummary(
            id=str(s.id),
            name=s.name,
            risk_score=risk,
            status=status,
            failure_year=failure_year,
            rul=round(rul, 1),
            confidence=85.0 + (100 - risk) * 0.1
        ))
        
        # Histogram buckets
        if risk < 20: histo_counts[0] += 1
        elif risk < 40: histo_counts[1] += 1
        elif risk < 60: histo_counts[2] += 1
        elif risk < 80: histo_counts[3] += 1
        else: histo_counts[4] += 1

    # Sort risk table
    risk_table.sort(key=lambda x: x.risk_score, reverse=True)
    top_5 = risk_table[:5]
    
    # Calculate Forecast
    forecast_data = []
    for i in range(11):
        year = 2024 + i
        scores = {}
        for b in top_5:
            rate = 2.5 if b.risk_score > 60 else 1.2
            scores[b.name] = min(100.0, round(b.risk_score + i * rate, 1))
        forecast_data.append(ForecastDataPoint(year=year, scores=scores))
        
    avg_rul = sum(b.rul for b in risk_table) / len(risk_table) if risk_table else 0.0
    
    return RiskForecastResponse(
        forecast_data=forecast_data,
        risk_table=risk_table,
        histogram=[
            RiskDistributionBucket(range="0-20%", count=histo_counts[0]),
            RiskDistributionBucket(range="20-40%", count=histo_counts[1]),
            RiskDistributionBucket(range="40-60%", count=histo_counts[2]),
            RiskDistributionBucket(range="60-80%", count=histo_counts[3]),
            RiskDistributionBucket(range="80-100%", count=histo_counts[4]),
        ],
        avg_rul=round(avg_rul, 1)
    )

@router.get("/budget", response_model=BudgetAnalyticsResponse)
async def get_budget_analytics(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Structure))
    structures = res.scalars().all()
    
    scatter_data = []
    district_map = {}
    total_portfolio = 0.0
    immediate_repairs = 0.0
    critical_count = 0
    
    for s in structures:
        risk = s.current_risk_score or 0.0
        status = s.current_status or "normal"
        length_m = s.metadata_.get("length_m", 50) if s.metadata_ else 50
        
        cost = float(length_m * risk * 1.8)
        total_portfolio += cost * 15  # Portfolio estimate factor
        
        district = (s.location_description or "Kigali").split("/")[0].strip()
        district_map[district] = district_map.get(district, 0.0) + cost
        
        detail = BridgeCostDetail(
            id=str(s.id),
            name=s.name,
            risk_score=risk,
            status=status,
            cost=cost
        )
        scatter_data.append(detail)
        
        if risk >= 60:
            immediate_repairs += cost
            critical_count += 1
            
    district_budget = [DistrictBudget(d=k, budget=v) for k, v in district_map.items()]
    district_budget.sort(key=lambda x: x.budget, reverse=True)
    
    return BudgetAnalyticsResponse(
        total_portfolio=total_portfolio,
        immediate_repairs=immediate_repairs,
        critical_count=critical_count,
        scatter_data=scatter_data,
        district_budget=district_budget,
        bridge_budgets=sorted(scatter_data, key=lambda x: x.risk_score, reverse=True)
    )
