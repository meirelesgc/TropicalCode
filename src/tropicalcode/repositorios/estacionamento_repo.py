from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.models import Estacionamento, RegistroAtividade


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


async def get_available_estacionamentos(session):
    result = await session.execute(select(Estacionamento))
    estacionamentos = result.scalars().all()

    result2 = await session.execute(select(RegistroAtividade))
    registros = result2.scalars().all()

    latest = {}
    for r in registros:
        e = r.estacionamento_id
        if e not in latest or r.horario > latest[e].horario:
            latest[e] = r

    ocupados = {k for k, v in latest.items() if v.tipo == "ENTRADA"}

    return [e for e in estacionamentos if e.id not in ocupados]


async def find_best_for_user(session, usuario):
    disponiveis = await get_available_estacionamentos(session)

    if not disponiveis:
        return None

    if usuario.local_trabalho:
        for e in disponiveis:
            if e.id == usuario.local_trabalho:
                return e

        result = await session.execute(
            select(Estacionamento).where(
                Estacionamento.id == usuario.local_trabalho
            )
        )
        alvo = result.scalar_one_or_none()

        if alvo:
            return min(
                disponiveis,
                key=lambda x: abs(x.posicao_geral - alvo.posicao_geral),
            )

    return min(disponiveis, key=lambda x: x.posicao_geral)
