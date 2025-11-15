import asyncio

import streamlit as st

from tropicalcode.database import get_session
from tropicalcode.repositorios.usuario_repo import create_usuario, get_usuarios

st.title("Gerenciamento de Usuários")

menu = st.sidebar.selectbox(
    "Menu", ["Criar Conta", "Login", "Listar Usuários"]
)


async def criar_conta():
    nome = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")
    email = st.text_input("Email")
    local = st.text_input("Local de trabalho")
    if st.button("Criar"):
        async for session in get_session():
            await create_usuario(
                session,
                {
                    "nome_usuario": nome,
                    "senha": senha,
                    "email": email,
                    "local_trabalho": local,
                },
            )
        st.success("Usuário criado")


async def listar():
    async for session in get_session():
        usuarios = await get_usuarios(session)
    for u in usuarios:
        st.write(
            f"ID: {u.id} | Usuário: {u.nome_usuario} | Email: {u.email} | Local: {u.local_trabalho}"
        )


def login():
    nome = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):

        async def validar():
            async for session in get_session():
                usuarios = await get_usuarios(session)
            for u in usuarios:
                if u.nome_usuario == nome and u.senha == senha:
                    return u
            return None

        user = asyncio.run(validar())
        if user:
            st.success("Login realizado")
        else:
            st.error("Credenciais inválidas")


if menu == "Criar Conta":
    asyncio.run(criar_conta())
elif menu == "Login":
    login()
elif menu == "Listar Usuários":
    asyncio.run(listar())
