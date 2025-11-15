import asyncio

import streamlit as st
from sqlalchemy import select
from streamlit_cookies_manager import EncryptedCookieManager

from tropicalcode.database import get_session
from tropicalcode.models import Automovel
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

st.title("Área Restrita - Registrar Entrada")
st.success(f"Usuário logado: {username}")


async def registrar_entrada(usuario, automovel_selecionado):

    async for session in get_session():
        if await usuario_tem_entrada_ativa(session, usuario.id):
            return {"error": "Você já possui uma entrada ativa."}

        estacionamento = await find_best_for_user(
            session, usuario, automovel_selecionado.tipo
        )

        if not estacionamento:
            return {
                "error": f"Nenhuma vaga do tipo '{automovel_selecionado.tipo}' está disponível no momento."
            }

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


async def setup_ui_selecao():

    async for session in get_session():
        usuario = await get_usuario_por_nome(session, username)
        if not usuario:
            st.error("Usuário não encontrado")
            st.stop()

        if await usuario_tem_entrada_ativa(session, usuario.id):
            st.warning(
                "Você já possui uma entrada ativa e só pode usar uma vaga por vez."
            )
            st.stop()

        automoveis_result = await session.execute(
            select(Automovel).where(Automovel.usuario_id == usuario.id)
        )
        automoveis_usuario = automoveis_result.scalars().all()

        if not automoveis_usuario:
            st.error(
                "Você não possui veículos cadastrados. "
                "Por favor, cadastre um veículo antes de registrar uma entrada."
            )
            st.stop()

        opcoes_carros = {
            f"{auto.placa} ({auto.tipo})": auto for auto in automoveis_usuario
        }

        st.markdown("---")
        st.subheader("Selecione seu veículo")

        selecao_formatada = st.selectbox(
            "Qual veículo você está usando hoje?", options=opcoes_carros.keys()
        )

        if not selecao_formatada:
            st.stop()

        automovel_escolhido = opcoes_carros[selecao_formatada]

        st.markdown("---")

        if st.button("Confirmar Entrada e Receber Vaga"):
            if "entrada_result" in st.session_state:
                del st.session_state["entrada_result"]

            result = await registrar_entrada(usuario, automovel_escolhido)
            st.session_state["entrada_result"] = result
            st.rerun()


if "entrada_result" in st.session_state:
    result = st.session_state["entrada_result"]

    if "error" in result:
        st.error(result["error"])
    else:
        e = result["estacionamento"]
        r = result["registro"]

        st.balloons()
        st.success(f"Entrada registrada com sucesso! (ID {r.id})")
        st.info(f"Vaga recomendada: {e.codigo_vaga} (ID {e.id})")
        st.write(f"Tipo da Vaga: {e.tipo_vaga}")
        st.write(f"Posição geral: {e.posicao_geral}")
        st.write(f"Horário: {r.horario.strftime('%d/%m/%Y às %H:%M:%S')}")

    if st.button("Voltar"):
        del st.session_state["entrada_result"]
        st.rerun()

else:
    asyncio.run(setup_ui_selecao())
