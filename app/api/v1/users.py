from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.deps import get_session
from app.models import User, OrgMember, Organization
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserResponse])
async def list_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User)
        .options(selectinload(User.memberships).selectinload(OrgMember.organization))
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    response = []
    for u in users:
        org_id = None
        org_name = ""
        if u.memberships:
            org = u.memberships[0].organization
            org_id = org.id
            org_name = org.name
            
        response.append(UserResponse(
            id=u.id,
            email=u.email,
            fullName=u.full_name or "Unknown",
            role=u.role,
            organizationId=org_id,
            organizationName=org_name
        ))
    return response


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> UserResponse:
    from fastapi import HTTPException
    result = await session.execute(
        select(User)
        .options(selectinload(User.memberships).selectinload(OrgMember.organization))
        .where(User.id == user_id)
    )
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
        
    org_id = None
    org_name = ""
    if u.memberships:
        org = u.memberships[0].organization
        org_id = org.id
        org_name = org.name
        
    return UserResponse(
        id=u.id,
        email=u.email,
        fullName=u.full_name or "Unknown",
        role=u.role,
        organizationId=org_id,
        organizationName=org_name
    )
