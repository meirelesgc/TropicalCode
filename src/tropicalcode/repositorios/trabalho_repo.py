from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.models import LocalTrabalho


async def create_local_trabalho(session: AsyncSession, data: dict):
    local = LocalTrabalho(**data)
    session.add(local)
    await session.commit()
    await session.refresh(local)
    return local


async def get_local_trabalho(session: AsyncSession, local_id: int):
    result = await session.execute(
        select(LocalTrabalho).where(LocalTrabalho.id == local_id)
    )
    return result.scalar_one_or_none()


async def get_locais_trabalho(session: AsyncSession):
    result = await session.execute(select(LocalTrabalho))
    return result.scalars().all()


async def update_local_trabalho(
    session: AsyncSession, local_id: int, data: dict
):
    local = await get_local_trabalho(session, local_id)
    if not local:
        return None
    for k, v in data.items():
        setattr(local, k, v)
    await session.commit()
    await session.refresh(local)
    return local


async def delete_local_trabalho(session: AsyncSession, local_id: int):
    local = await get_local_trabalho(session, local_id)
    if not local:
        return False
    await session.delete(local)
    await session.commit()
    return True
