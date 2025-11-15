import asyncio

import streamlit as st
from sqlalchemy import select
from streamlit_cookies_manager import EncryptedCookieManager

from tropicalcode.database import get_session
from tropicalcode.models import RegistroAtividade
from tropicalcode.repositorios.registro_atividade_repo import (
    create_registro,
    usuario_tem_entrada_ativa,
)
from tropicalcode.repositorios.usuario_repo import get_usuario_por_nome

cookies = EncryptedCookieManager(prefix="app_", password="senha_muito_secreta")

if not cookies.ready():
    st.stop()

query = st.query_params
chave = query.get("chave", "")

if not chave.isdigit() or len(chave) != 4:
    st.error("Acesso negado. Parâmetro 'chave' inválido.")
    st.stop()

if "user" not in cookies or cookies.get("user") == "":
    st.error("Nenhum usuário logado")
    st.stop()

username = cookies.get("user")

st.title("Registrar Saída")


async def fluxo():
    async for session in get_session():
        usuario = await get_usuario_por_nome(session, username)
        if not usuario:
            return {"error": "Usuário não encontrado"}

        if not await usuario_tem_entrada_ativa(session, usuario.id):
            return {"error": "Você não possui saida ativa"}

        result = await session.execute(select(RegistroAtividade))
        registros = result.scalars().all()

        latest = None
        for r in registros:
            if r.usuario_id == usuario.id:
                if latest is None or r.horario > latest.horario:
                    latest = r

        if not latest:
            return {"error": "Nenhum registro de entrada encontrado"}

        registro = await create_registro(
            session,
            {
                "estacionamento_id": latest.estacionamento_id,
                "usuario_id": usuario.id,
                "tipo": "SAIDA",
                "caminho": f"/saida?chave={chave}",
            },
        )

        return {"registro": registro}


result = st.session_state.get("saida_result")

if result is None:
    result = asyncio.run(fluxo())
    st.session_state["saida_result"] = result

if "error" in result:
    st.error(result["error"])
    st.stop()

r = result["registro"]

st.success(f"Usuário logado: {username}")
st.info("Saída registrada com sucesso.")
st.write(f"Registro ID {r.id} às {r.horario}")
