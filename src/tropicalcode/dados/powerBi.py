import asyncio
import os  # Importar 'os' para manipulação de caminhos

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.database import get_session
from tropicalcode.models import (
    Automovel,
    Estacionamento,
    RegistroAtividade,
    Usuario,
)

# Definir a pasta base para exportação
EXPORT_DIR = "src/tropicalcode/dados/arquivos"


async def export_usuarios_csv(session: AsyncSession, path: str):
    result = await session.execute(select(Usuario))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_csv(path, index=False)


async def export_usuarios_xlsx(session: AsyncSession, path: str):
    result = await session.execute(select(Usuario))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_excel(path, index=False)


async def export_estacionamentos_csv(session: AsyncSession, path: str):
    result = await session.execute(select(Estacionamento))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_csv(path, index=False)


async def export_estacionamentos_xlsx(session: AsyncSession, path: str):
    result = await session.execute(select(Estacionamento))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_excel(path, index=False)


async def export_automoveis_csv(session: AsyncSession, path: str):
    result = await session.execute(select(Automovel))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_csv(path, index=False)


async def export_automoveis_xlsx(session: AsyncSession, path: str):
    result = await session.execute(select(Automovel))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_excel(path, index=False)


async def export_registros_csv(session: AsyncSession, path: str):
    result = await session.execute(select(RegistroAtividade))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_csv(path, index=False)


async def export_registros_xlsx(session: AsyncSession, path: str):
    result = await session.execute(select(RegistroAtividade))
    rows = result.scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_excel(path, index=False)


async def export_dimensoes_xlsx(session: AsyncSession, path: str):
    usuarios = (await session.execute(select(Usuario))).scalars().all()
    estacionamentos = (
        (await session.execute(select(Estacionamento))).scalars().all()
    )
    automoveis = (await session.execute(select(Automovel))).scalars().all()
    df_usuarios = pd.DataFrame([r.__dict__ for r in usuarios])
    df_estacionamentos = pd.DataFrame([r.__dict__ for r in estacionamentos])
    df_automoveis = pd.DataFrame([r.__dict__ for r in automoveis])
    with pd.ExcelWriter(path) as writer:
        df_usuarios.to_excel(writer, sheet_name="dim_usuario", index=False)
        df_estacionamentos.to_excel(
            writer, sheet_name="dim_estacionamento", index=False
        )
        df_automoveis.to_excel(writer, sheet_name="dim_automovel", index=False)


async def export_fatos_xlsx(session: AsyncSession, path: str):
    registros = (
        (await session.execute(select(RegistroAtividade))).scalars().all()
    )
    df_registros = pd.DataFrame([r.__dict__ for r in registros])
    with pd.ExcelWriter(path) as writer:
        df_registros.to_excel(writer, sheet_name="fato_movimento", index=False)


async def export_estado_atual_estacionamentos_xlsx(
    session: AsyncSession, path: str
):
    sub = (
        select(
            RegistroAtividade.estacionamento_id,
            func.max(RegistroAtividade.horario).label("max_horario"),
        )
        .group_by(RegistroAtividade.estacionamento_id)
        .subquery()
    )
    query = select(RegistroAtividade).join(
        sub,
        (RegistroAtividade.estacionamento_id == sub.c.estacionamento_id)
        & (RegistroAtividade.horario == sub.c.max_horario),
    )
    rows = (await session.execute(query)).scalars().all()
    df = pd.DataFrame([r.__dict__ for r in rows])
    df.to_excel(path, index=False)


async def main():
    os.makedirs(EXPORT_DIR, exist_ok=True)

    async for session in get_session():
        await export_usuarios_csv(
            session, os.path.join(EXPORT_DIR, "usuarios.csv")
        )
        await export_usuarios_xlsx(
            session, os.path.join(EXPORT_DIR, "usuarios.xlsx")
        )
        await export_estacionamentos_csv(
            session, os.path.join(EXPORT_DIR, "estacionamentos.csv")
        )
        await export_estacionamentos_xlsx(
            session, os.path.join(EXPORT_DIR, "estacionamentos.xlsx")
        )
        await export_automoveis_csv(
            session, os.path.join(EXPORT_DIR, "automoveis.csv")
        )
        await export_automoveis_xlsx(
            session, os.path.join(EXPORT_DIR, "automoveis.xlsx")
        )
        await export_registros_csv(
            session, os.path.join(EXPORT_DIR, "registros.csv")
        )
        await export_registros_xlsx(
            session, os.path.join(EXPORT_DIR, "registros.xlsx")
        )
        await export_dimensoes_xlsx(
            session, os.path.join(EXPORT_DIR, "dimensoes.xlsx")
        )
        await export_fatos_xlsx(
            session, os.path.join(EXPORT_DIR, "fatos.xlsx")
        )
        await export_estado_atual_estacionamentos_xlsx(
            session, os.path.join(EXPORT_DIR, "estado_atual.xlsx")
        )
        break


if __name__ == "__main__":
    asyncio.run(main())
