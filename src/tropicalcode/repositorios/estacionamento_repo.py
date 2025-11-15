from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tropicalcode.models.estacionamento import Estacionamento


async def create_estacionamento(session: AsyncSession, data: dict):
    est = Estacionamento(**data)
    session.add(est)
    await session.commit()
    await session.refresh(est)
    return est


async def get_estacionamento(session: AsyncSession, estacionamento_id: int):
    result = await session.execute(
        select(Estacionamento).where(Estacionamento.id == estacionamento_id)
    )
    return result.scalar_one_or_none()


async def get_estacionamentos(session: AsyncSession):
    result = await session.execute(select(Estacionamento))
    return result.scalars().all()


async def update_estacionamento(
    session: AsyncSession, estacionamento_id: int, data: dict
):
    est = await get_estacionamento(session, estacionamento_id)
    if not est:
        return None
    for k, v in data.items():
        setattr(est, k, v)
    await session.commit()
    await session.refresh(est)
    return est


async def delete_estacionamento(session: AsyncSession, estacionamento_id: int):
    est = await get_estacionamento(session, estacionamento_id)
    if not est:
        return False
    await session.delete(est)
    await session.commit()
    return True
