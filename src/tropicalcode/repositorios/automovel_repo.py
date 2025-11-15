from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tropicalcode.models.automovel import Automovel


async def create_automovel(session: AsyncSession, data: dict):
    auto = Automovel(**data)
    session.add(auto)
    await session.commit()
    await session.refresh(auto)
    return auto


async def get_automovel(session: AsyncSession, automovel_id: int):
    result = await session.execute(
        select(Automovel).where(Automovel.id == automovel_id)
    )
    return result.scalar_one_or_none()


async def get_automoveis(session: AsyncSession):
    result = await session.execute(select(Automovel))
    return result.scalars().all()


async def update_automovel(
    session: AsyncSession, automovel_id: int, data: dict
):
    auto = await get_automovel(session, automovel_id)
    if not auto:
        return None
    for k, v in data.items():
        setattr(auto, k, v)
    await session.commit()
    await session.refresh(auto)
    return auto


async def delete_automovel(session: AsyncSession, automovel_id: int):
    auto = await get_automovel(session, automovel_id)
    if not auto:
        return False
    await session.delete(auto)
    await session.commit()
    return True
