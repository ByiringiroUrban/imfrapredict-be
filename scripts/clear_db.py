"""Clear development data, leaving a blank canvas for real data entry."""

import asyncio
from sqlalchemy import delete
from app.core.database import async_session_factory
from app.models import (
    RiskAssessment,
    Sensor,
    SensorReading,
    Structure,
    Inspection,
    MaintenancePlan,
    EnvironmentalReading,
)

async def clear_database() -> None:
    print("Connecting to PostgreSQL to wipe seed data...")
    async with async_session_factory() as session:
        # Delete dependent child tables first
        print("Clearing sensor readings...")
        await session.execute(delete(SensorReading))

        print("Clearing sensors...")
        await session.execute(delete(Sensor))

        print("Clearing maintenance plans...")
        await session.execute(delete(MaintenancePlan))

        print("Clearing risk assessments...")
        await session.execute(delete(RiskAssessment))

        print("Clearing inspections...")
        await session.execute(delete(Inspection))

        print("Clearing environmental readings...")
        await session.execute(delete(EnvironmentalReading))

        print("Clearing structures...")
        await session.execute(delete(Structure))

        # Commit transaction
        await session.commit()
        print("Database wiped successfully! Default users and organizations preserved.")

if __name__ == "__main__":
    asyncio.run(clear_database())
