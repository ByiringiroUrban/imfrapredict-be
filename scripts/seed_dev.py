"""Seed development data matching the Kigali City case study context."""

import asyncio
import uuid
<<<<<<< HEAD
from datetime import datetime, timedelta, timezone, date

=======
import sys
import os
from datetime import datetime, timedelta, timezone, date

# Add parent directory to sys.path to resolve 'app' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

>>>>>>> 8b1ba381f6b43ed333b73d31dcfb8a40ce68933e
from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.core.enums import (
    SensorType,
    StructureType,
    UserRole,
    risk_status_from_score,
    MaintenancePriority,
    MaintenanceStatus
)
from app.models import Organization, RiskAssessment, Sensor, SensorReading, Structure, User, Inspection, MaintenancePlan, EnvironmentalReading
from app.core.security import hash_password

DEMO_ORG_ID = uuid.UUID("00000000-0000-4000-a000-000000000001")

STRUCTURES = [
    {
        "name": "Nyabugogo Bridge (Nyarugenge)",
        "structure_type": StructureType.REINFORCED_CONCRETE,
        "built_year": 1982,
        "risk_score": 74,
        "location_lat": -1.9382,
        "location_lng": 30.0436,
        "location_description": "Nyabugogo River Crossing, Nyarugenge District, Kigali",
        "factors": {
            "structural": {"score": 68, "status": "critical"},
            "corrosion": {"score": 75, "status": "critical"},
            "load": {"score": 80, "status": "critical"},
            "environmental": {"score": 73, "status": "critical"},
        },
        "metadata": {
            "district": "Nyarugenge",
            "traffic_load_label": "Heavy (25,000 vehicles/day)",
            "traffic_load_value": 25000,
            "annual_rainfall_mm": 1200,
            "slope_percent": 2.5,
            "landslide_history": False,
            "soil_type": "Silt Clay",
            "last_inspection_findings": "Heavy cracks on support piers and concrete spalling due to flooding."
        }
    },
    {
        "name": "Kicukiro Overpass Flyover (Kicukiro)",
        "structure_type": StructureType.STEEL_COMPOSITE,
        "built_year": 2022,
        "risk_score": 12,
        "location_lat": -1.9702,
        "location_lng": 30.1044,
        "location_description": "Kicukiro Centre Intersection, Kicukiro District, Kigali",
        "factors": {
            "structural": {"score": 10, "status": "normal"},
            "corrosion": {"score": 8, "status": "normal"},
            "load": {"score": 15, "status": "normal"},
            "environmental": {"score": 14, "status": "normal"},
        },
        "metadata": {
            "district": "Kicukiro",
            "traffic_load_label": "Very Heavy (40,000 vehicles/day)",
            "traffic_load_value": 40000,
            "annual_rainfall_mm": 1150,
            "slope_percent": 1.0,
            "landslide_history": False,
            "soil_type": "Sandy Loam",
            "last_inspection_findings": "Structure is in excellent condition. Elastomeric bearings stable."
        }
    },
    {
        "name": "Gatsata Mountain Slope Road (Gasabo)",
        "structure_type": StructureType.OTHER,
        "built_year": 2008,
        "risk_score": 58,
        "location_lat": -1.9167,
        "location_lng": 30.0632,
        "location_description": "Gatsata Road Slope Section, Gasabo District, Kigali",
        "factors": {
            "structural": {"score": 45, "status": "warning"},
            "corrosion": {"score": 12, "status": "normal"},
            "load": {"score": 55, "status": "warning"},
            "environmental": {"score": 68, "status": "critical"},
        },
        "metadata": {
            "district": "Gasabo",
            "traffic_load_label": "Medium (12,000 vehicles/day)",
            "traffic_load_value": 12000,
            "annual_rainfall_mm": 1300,
            "slope_percent": 15.0,
            "landslide_history": True,
            "soil_type": "Clay",
            "last_inspection_findings": "Soil erosion along embankment; potential risk of landslide during rainy season."
        }
    },
    {
        "name": "Nyabarongo River Bridge (Nyarugenge)",
        "structure_type": StructureType.STEEL_TRUSS,
        "built_year": 1975,
        "risk_score": 65,
        "location_lat": -1.9785,
        "location_lng": 29.9818,
        "location_description": "Nyabarongo Highway Crossing, Nyarugenge District, Kigali",
        "factors": {
            "structural": {"score": 62, "status": "warning"},
            "corrosion": {"score": 74, "status": "critical"},
            "load": {"score": 48, "status": "warning"},
            "environmental": {"score": 70, "status": "critical"},
        },
        "metadata": {
            "district": "Nyarugenge",
            "traffic_load_label": "Medium-Heavy (18,000 vehicles/day)",
            "traffic_load_value": 18000,
            "annual_rainfall_mm": 1250,
            "slope_percent": 3.0,
            "landslide_history": True,
            "soil_type": "Alluvial Silt",
            "last_inspection_findings": "Severe rust on main steel trusses. Truss joint corrosion needs containment."
        }
    },
    {
        "name": "Kanombe Airport Boulevard (Kicukiro)",
        "structure_type": StructureType.CONCRETE_BEAM,
        "built_year": 1999,
        "risk_score": 38,
        "location_lat": -1.9667,
        "location_lng": 30.1333,
        "location_description": "Kanombe Airport Highway, Kicukiro District, Kigali",
        "factors": {
            "structural": {"score": 35, "status": "warning"},
            "corrosion": {"score": 30, "status": "normal"},
            "load": {"score": 45, "status": "warning"},
            "environmental": {"score": 32, "status": "normal"},
        },
        "metadata": {
            "district": "Kicukiro",
            "traffic_load_label": "Heavy (30,000 vehicles/day)",
            "traffic_load_value": 30000,
            "annual_rainfall_mm": 1100,
            "slope_percent": 2.0,
            "landslide_history": False,
            "soil_type": "Loam",
            "last_inspection_findings": "Minor crack development in asphalt pavement. Asphalt wearing course thin."
        }
    },
    {
        "name": "Kimihurura Boulevard Overpass (Gasabo)",
        "structure_type": StructureType.CABLE_STAYED,
        "built_year": 2011,
        "risk_score": 22,
        "location_lat": -1.9548,
        "location_lng": 30.0827,
        "location_description": "Kimihurura Sector, Gasabo District, Kigali",
        "factors": {
            "structural": {"score": 18, "status": "normal"},
            "corrosion": {"score": 25, "status": "normal"},
            "load": {"score": 20, "status": "normal"},
            "environmental": {"score": 24, "status": "normal"},
        },
        "metadata": {
            "district": "Gasabo",
            "traffic_load_label": "Heavy (35,000 vehicles/day)",
            "traffic_load_value": 35000,
            "annual_rainfall_mm": 1150,
            "slope_percent": 1.5,
            "landslide_history": False,
            "soil_type": "Clay Loam",
            "last_inspection_findings": "Cables and anchorages inspected. Minor cosmetic concrete wear observed."
        }
    },
]


async def seed() -> None:
    async with async_session_factory() as session:
        # Check if organization exists, otherwise create it
        org = await session.get(Organization, DEMO_ORG_ID)
        if not org:
            org = Organization(id=DEMO_ORG_ID, name="Kigali City Infrastructure Board", slug="kigali-city")
            session.add(org)
            await session.flush()
        else:
            org.name = "Kigali City Infrastructure Board"
            org.slug = "kigali-city"

        # Check if admin user exists
<<<<<<< HEAD
        admin_email = "admin@infrapredict.ai"
=======
        admin_email = "admin@gmail.com"
>>>>>>> 8b1ba381f6b43ed333b73d31dcfb8a40ce68933e
        stmt = select(User).where(User.email == admin_email)
        admin_res = (await session.execute(stmt)).scalar_one_or_none()
        if not admin_res:
            admin = User(
                email=admin_email,
<<<<<<< HEAD
                password_hash=hash_password("password"),
=======
                password_hash=hash_password("12345678"),
>>>>>>> 8b1ba381f6b43ed333b73d31dcfb8a40ce68933e
                full_name="Alex Rivera",
                role=UserRole.ADMIN,
            )
            session.add(admin)
        else:
            admin = admin_res

<<<<<<< HEAD
=======
        # Seed Operator user
        operator_email = "operator@gmail.com"
        stmt = select(User).where(User.email == operator_email)
        if not (await session.execute(stmt)).scalar_one_or_none():
            session.add(User(
                email=operator_email,
                password_hash=hash_password("12345678"),
                full_name="Jordan Chen",
                role=UserRole.OPERATOR,
            ))
            print("  [OK] Operator user created")

        # Seed Viewer user
        viewer_email = "viewer@gmail.com"
        stmt = select(User).where(User.email == viewer_email)
        if not (await session.execute(stmt)).scalar_one_or_none():
            session.add(User(
                email=viewer_email,
                password_hash=hash_password("12345678"),
                full_name="Sam Patel",
                role=UserRole.VIEWER,
            ))
            print("  [OK] Viewer user created")

>>>>>>> 8b1ba381f6b43ed333b73d31dcfb8a40ce68933e
        # Clear existing structure-related data to allow clean re-seeding
        # Let's delete records tied to this organization's structures
        stmt_structs = select(Structure.id).where(Structure.organization_id == DEMO_ORG_ID)
        struct_ids = (await session.execute(stmt_structs)).scalars().all()
        
        if struct_ids:
            # Delete dependent tables first
            await session.execute(delete(SensorReading).where(SensorReading.sensor_id.in_(
                select(Sensor.id).where(Sensor.structure_id.in_(struct_ids))
            )))
            await session.execute(delete(Sensor).where(Sensor.structure_id.in_(struct_ids)))
<<<<<<< HEAD
            await session.execute(delete(RiskAssessment).where(RiskAssessment.structure_id.in_(struct_ids)))
            await session.execute(delete(Inspection).where(Inspection.structure_id.in_(struct_ids)))
            await session.execute(delete(MaintenancePlan).where(MaintenancePlan.structure_id.in_(struct_ids)))
=======
            await session.execute(delete(MaintenancePlan).where(MaintenancePlan.structure_id.in_(struct_ids)))
            await session.execute(delete(RiskAssessment).where(RiskAssessment.structure_id.in_(struct_ids)))
            await session.execute(delete(Inspection).where(Inspection.structure_id.in_(struct_ids)))
>>>>>>> 8b1ba381f6b43ed333b73d31dcfb8a40ce68933e
            await session.execute(delete(EnvironmentalReading).where(EnvironmentalReading.structure_id.in_(struct_ids)))
            await session.execute(delete(Structure).where(Structure.id.in_(struct_ids)))
            await session.flush()

        now = datetime.now(timezone.utc)
        total_readings = 0

        for item in STRUCTURES:
            status = risk_status_from_score(item["risk_score"])
            structure = Structure(
                organization_id=DEMO_ORG_ID,
                name=item["name"],
                structure_type=item["structure_type"],
                built_year=item["built_year"],
                current_risk_score=item["risk_score"],
                current_status=status,
                last_assessed_at=now,
                location_description=item["location_description"],
                location_lat=item["location_lat"],
                location_lng=item["location_lng"],
                metadata_=item["metadata"],
            )
            session.add(structure)
            await session.flush()

            # Seed Risk Assessment
            assessment = RiskAssessment(
                structure_id=structure.id,
                risk_score=item["risk_score"],
                status=status,
                confidence=0.947,
                factors=item["factors"],
                model_version="random-forest-v2.1.0",
                assessed_at=now,
            )
            session.add(assessment)

            # Seed Environmental Readings (Rainfall, Temperature, Humidity)
            env_rain = EnvironmentalReading(
                structure_id=structure.id,
                source="Meteo Rwanda",
                metric="rainfall",
                value=float(item["metadata"]["annual_rainfall_mm"] / 365.0), # daily average
                unit="mm",
                recorded_at=now,
            )
            env_temp = EnvironmentalReading(
                structure_id=structure.id,
                source="Meteo Rwanda",
                metric="temperature",
                value=24.5,
                unit="°C",
                recorded_at=now,
            )
            session.add(env_rain)
            session.add(env_temp)

            # Seed Inspection
            inspection = Inspection(
                structure_id=structure.id,
                inspector_name="Jean Damascene",
                inspection_date=date.today(),
                findings=item["metadata"]["last_inspection_findings"],
                severity=MaintenancePriority.HIGH if item["risk_score"] >= 60 else (MaintenancePriority.MEDIUM if item["risk_score"] >= 30 else MaintenancePriority.LOW)
            )
            session.add(inspection)

            # Seed Maintenance Plan if risk is elevated
            if item["risk_score"] >= 30:
                priority = MaintenancePriority.URGENT if item["risk_score"] >= 60 else MaintenancePriority.MEDIUM
                plan = MaintenancePlan(
                    structure_id=structure.id,
                    title="Structural Reinforcement and Concrete Repair",
                    description=f"Automated alert action: Repair crack defects and address {item['metadata']['last_inspection_findings']}",
                    priority=priority,
                    status=MaintenanceStatus.PLANNED,
                    estimated_cost=float(item["risk_score"] * 1500000), # in RWF
                    scheduled_date=date.today() + timedelta(days=15),
                )
                session.add(plan)

            # Seed Sensors and Readings
            sensors = [
                ("Strain Gauge", SensorType.STRAIN, "με"),
                ("Vibration Sensor", SensorType.VIBRATION, "mm/s"),
                ("Temperature Probe", SensorType.TEMPERATURE, "°C"),
            ]
            for sensor_name, sensor_type, unit in sensors:
                sensor = Sensor(
                    structure_id=structure.id,
                    name=f"{sensor_name} — {structure.name}",
                    sensor_type=sensor_type,
                    unit=unit,
                    installed_at=now - timedelta(days=365),
                )
                session.add(sensor)
                await session.flush()

                for hour in range(24):
                    reading = SensorReading(
                        sensor_id=sensor.id,
                        value=round(100 + item["risk_score"] + hour * 0.5, 2),
                        recorded_at=now - timedelta(hours=23 - hour),
                        idempotency_key=f"{sensor.id}-{hour}",
                    )
                    session.add(reading)
                    total_readings += 1

        await session.commit()
        print("Kigali data seed complete!")
        print(f"  Organization:    Kigali City Infrastructure Board")
        print(f"  Structures:      {len(STRUCTURES)}")
        print(f"  Sensor readings: {total_readings}")
<<<<<<< HEAD
        print(f"  Admin login:     admin@infrapredict.ai / password")
=======
        print(f"  Admin login:     admin@gmail.com / 12345678")
>>>>>>> 8b1ba381f6b43ed333b73d31dcfb8a40ce68933e


if __name__ == "__main__":
    asyncio.run(seed())
