from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.models import Usuario


async def create_usuario(session: AsyncSession, data: dict):
    usuario = Usuario(**data)
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario


async def get_usuario(session: AsyncSession, usuario_id: int):
    result = await session.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    return result.scalar_one_or_none()


async def get_usuarios(session: AsyncSession):
    result = await session.execute(select(Usuario))
    return result.scalars().all()


async def update_usuario(session: AsyncSession, usuario_id: int, data: dict):
    usuario = await get_usuario(session, usuario_id)
    if not usuario:
        return None
    for k, v in data.items():
        setattr(usuario, k, v)
    await session.commit()
    await session.refresh(usuario)
    return usuario


async def delete_usuario(session: AsyncSession, usuario_id: int):
    usuario = await get_usuario(session, usuario_id)
    if not usuario:
        return False
    await session.delete(usuario)
    await session.commit()
    return True
