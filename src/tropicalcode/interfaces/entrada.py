import asyncio

import streamlit as st

from tropicalcode.database import get_session
from tropicalcode.repositorios.estacionamento_repo import get_estacionamentos
from tropicalcode.repositorios.registro_atividade_repo import create_registro

st.title("Entrada de Veículos")


async def obter_livre():
    async for session in get_session():
        ests = await get_estacionamentos(session)
    for e in ests:
        if e.tipo_vaga is not None:
            return e
    return None


async def registrar(e):
    async for session in get_session():
        await create_registro(
            session,
            {
                "estacionamento_id": e.id,
                "tipo": "ENTRADA",
                "caminho": "entrada",
            },
        )
    st.success(f"Entrada registrada para a vaga {e.codigo_vaga}")


async def main():
    vaga = await obter_livre()
    if not vaga:
        st.error("Nenhuma vaga disponível")
        return
    st.write(f"Vaga disponível: {vaga.codigo_vaga}")
    if st.button("Registrar Entrada"):
        await registrar(vaga)


asyncio.run(main())
