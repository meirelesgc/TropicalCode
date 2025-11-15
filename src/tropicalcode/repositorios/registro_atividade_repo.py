from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.models import RegistroAtividade


async def create_registro(session: AsyncSession, data: dict):
    registro = RegistroAtividade(
        **data,
        horario=datetime.now(timezone.utc),
    )
    session.add(registro)
    await session.commit()
    await session.refresh(registro)
    return registro


async def get_registro(session: AsyncSession, registro_id: int):
    result = await session.execute(
        select(RegistroAtividade).where(RegistroAtividade.id == registro_id)
    )
    return result.scalar_one_or_none()


async def get_registros(session: AsyncSession):
    result = await session.execute(select(RegistroAtividade))
    return result.scalars().all()


async def update_registro(session: AsyncSession, registro_id: int, data: dict):
    registro = await get_registro(session, registro_id)
    if not registro:
        return None
    for k, v in data.items():
        setattr(registro, k, v)
    await session.commit()
    await session.refresh(registro)
    return registro


async def delete_registro(session: AsyncSession, registro_id: int):
    registro = await get_registro(session, registro_id)
    if not registro:
        return False
    await session.delete(registro)
    await session.commit()
    return True
