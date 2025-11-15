import asyncio

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from tropicalcode.database import get_session
from tropicalcode.repositorios.estacionamento_repo import find_best_for_user
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

st.title("Área Restrita")


async def fluxo():
    async for session in get_session():
        usuario = await get_usuario_por_nome(session, username)
        if not usuario:
            return {"error": "Usuário não encontrado"}

        if await usuario_tem_entrada_ativa(session, usuario.id):
            return {
                "error": "Você já possui uma entrada ativa e só pode usar uma vaga por vez."
            }

        estacionamento = await find_best_for_user(session, usuario)
        if not estacionamento:
            return {"error": "Nenhum estacionamento disponível"}

        registro = await create_registro(
            session,
            {
                "estacionamento_id": estacionamento.id,
                "usuario_id": usuario.id,
                "tipo": "ENTRADA",
                "caminho": f"/entrada?chave={chave}",
            },
        )

        return {
            "estacionamento": estacionamento,
            "registro": registro,
        }


result = st.session_state.get("entrada_result")

if result is None:
    result = asyncio.run(fluxo())
    st.session_state["entrada_result"] = result

if "error" in result:
    st.error(result["error"])
    st.stop()

e = result["estacionamento"]
r = result["registro"]

st.success(f"Usuário logado: {username}")
st.info(f"Vaga recomendada: {e.codigo_vaga} (ID {e.id})")
st.write(f"Tipo: {e.tipo_vaga}")
st.write(f"Posição geral: {e.posicao_geral}")
st.write(f"Registro criado (ID {r.id}) às {r.horario}")
