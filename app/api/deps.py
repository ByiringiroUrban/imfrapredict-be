from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

DbSession = AsyncGenerator[AsyncSession, None]


async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session
