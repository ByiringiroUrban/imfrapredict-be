import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.security import hash_password, verify_password
from app.models import User, Organization, OrgMember
from app.schemas.user import UserRegister, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_ORG_ID = uuid.UUID("00000000-0000-4000-a000-000000000001")

@router.post("/register", response_model=UserResponse)
async def register(
    data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    # Check if user already exists
    stmt_user = select(User).where(User.email == data.email.lower())
    existing_user = (await session.execute(stmt_user)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Check/Create Organization
    org_name = data.organization_name.strip()
    is_demo_org = org_name.lower() in [
        "infrapredict global",
        "kigali city infrastructure board",
        "kigali city"
    ]
    
    if is_demo_org:
        stmt_org = select(Organization).where(Organization.id == DEMO_ORG_ID)
        org = (await session.execute(stmt_org)).scalar_one_or_none()
        if not org:
            org = Organization(
                id=DEMO_ORG_ID,
                name="Kigali City Infrastructure Board",
                slug="kigali-city"
            )
            session.add(org)
            await session.flush()
    else:
        stmt_org = select(Organization).where(Organization.name == org_name)
        org = (await session.execute(stmt_org)).scalar_one_or_none()
        if not org:
            org = Organization(
                name=org_name,
                slug=org_name.lower().replace(" ", "-")
            )
            session.add(org)
            await session.flush()

    # Create User
    new_user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    session.add(new_user)
    await session.flush()

    # Create OrgMember Link
    member = OrgMember(
        organization_id=org.id,
        user_id=new_user.id,
        role=data.role,
    )
    session.add(member)
    await session.commit()

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        fullName=new_user.full_name or "",
        role=new_user.role,
        organizationId=org.id,
        organizationName=org.name,
    )

@router.post("/login", response_model=UserResponse)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    stmt_user = select(User).where(User.email == data.email.lower())
    user = (await session.execute(stmt_user)).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Find organization membership
    stmt_member = select(OrgMember).where(OrgMember.user_id == user.id)
    member = (await session.execute(stmt_member)).scalars().first()
    
    if not member:
        # Link user to demo org if no membership exists
        org_id = DEMO_ORG_ID
        org_name = "Kigali City Infrastructure Board"
        
        stmt_org = select(Organization).where(Organization.id == DEMO_ORG_ID)
        org = (await session.execute(stmt_org)).scalar_one_or_none()
        if not org:
            org = Organization(
                id=DEMO_ORG_ID,
                name="Kigali City Infrastructure Board",
                slug="kigali-city"
            )
            session.add(org)
            await session.flush()
            
        member = OrgMember(
            organization_id=org.id,
            user_id=user.id,
            role=user.role,
        )
        session.add(member)
        await session.commit()
    else:
        stmt_org = select(Organization).where(Organization.id == member.organization_id)
        org = (await session.execute(stmt_org)).scalar_one()
        org_id = org.id
        org_name = org.name

    return UserResponse(
        id=user.id,
        email=user.email,
        fullName=user.full_name or "",
        role=user.role,
        organizationId=org_id,
        organizationName=org_name,
    )
