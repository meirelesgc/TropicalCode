import asyncio

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from tropicalcode.database import get_session
from tropicalcode.repositorios.usuario_repo import create_usuario, get_usuarios

cookies = EncryptedCookieManager(prefix="app_", password="senha_muito_secreta")

if not cookies.ready():
    st.stop()

menu_options = ["Criar Conta", "Login", "Listar Usuários"]

params = st.query_params
menu_param = params.get("menu", ["Criar Conta"])[0]

if menu_param not in menu_options:
    menu_param = "Criar Conta"

menu = st.sidebar.selectbox(
    "Menu", menu_options, index=menu_options.index(menu_param)
)

st.query_params.menu = menu

st.title("Gerenciamento de Usuários")


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
    if "user" not in cookies or cookies.get("user") == "":
        st.error("Necessário login")
        return
    async for session in get_session():
        usuarios = await get_usuarios(session)
    for u in usuarios:
        st.write(
            f"ID: {u.id} | Usuário: {u.nome_usuario} | Email: {u.email} | Local: {u.local_trabalho}"
        )


def login():
    if "user" in cookies and cookies.get("user") != "":
        st.success(f"Logado como {cookies.get('user')}")
        if st.button("Sair"):
            cookies["user"] = ""
            cookies.save()
            st.rerun()
        return

    nome = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")

    async def validar():
        async for session in get_session():
            usuarios = await get_usuarios(session)
        for u in usuarios:
            if u.nome_usuario == nome and u.senha == senha:
                return u
        return None

    if st.button("Entrar"):
        user = asyncio.run(validar())
        if user:
            cookies["user"] = user.nome_usuario
            cookies.save()
            st.success("Login realizado")
            st.rerun()
        else:
            st.error("Credenciais inválidas")


if menu == "Criar Conta":
    asyncio.run(criar_conta())
elif menu == "Login":
    login()
elif menu == "Listar Usuários":
    asyncio.run(listar())
