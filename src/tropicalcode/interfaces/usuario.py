import asyncio

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from tropicalcode.database import get_session
from tropicalcode.repositorios.automovel_repo import (
    create_automovel,
    get_automoveis,
)
from tropicalcode.repositorios.trabalho_repo import (
    create_local_trabalho,
    get_locais_trabalho,
)
from tropicalcode.repositorios.usuario_repo import create_usuario, get_usuarios

cookies = EncryptedCookieManager(prefix="app_", password="senha_muito_secreta")

if not cookies.ready():
    st.stop()

MAP_SIZE = 10

menu_options = [
    "Criar Conta",
    "Login",
    "Listar Usuários",
    "Registrar Automóvel",
    "Criar Local de Trabalho",
]

params = st.query_params
menu_param = params.get("menu", ["Criar Conta"])[0]

if menu_param not in menu_options:
    menu_param = "Criar Conta"

menu = st.sidebar.selectbox(
    "Menu", menu_options, index=menu_options.index(menu_param)
)

st.query_params.menu = menu

st.title("Gerenciamento de Usuários e Automóveis")


async def criar_conta():
    nome = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")
    email = st.text_input("Email")

    async for session in get_session():
        locais = await get_locais_trabalho(session)
    local_map = {l.nome: l.id for l in locais}
    local_nome = st.selectbox(
        "Local de trabalho", ["Selecione"] + list(local_map.keys())
    )

    if st.button("Criar"):
        if local_nome == "Selecione":
            st.error("Selecione um local de trabalho válido")
            return

        local_id = local_map[local_nome]

        async for session in get_session():
            await create_usuario(
                session,
                {
                    "nome_usuario": nome,
                    "senha": senha,
                    "email": email,
                    "local_trabalho": local_id,
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


async def registrar_automovel():
    if "user" not in cookies or cookies.get("user") == "":
        st.error("Necessário login")
        return

    async for session in get_session():
        usuarios = await get_usuarios(session)
    usuario = next(
        (u for u in usuarios if u.nome_usuario == cookies.get("user")), None
    )
    if not usuario:
        st.error("Usuário não encontrado")
        return

    placa = st.text_input("Placa do veículo")
    tipo = st.selectbox("Tipo", ["MOTO", "CARRO", "PCD", "CARRO_ELETRICO"])

    if st.button("Registrar Automóvel"):
        async for session in get_session():
            await create_automovel(
                session,
                {
                    "usuario_id": usuario.id,
                    "placa": placa,
                    "tipo": tipo,
                },
            )
        st.success("Automóvel registrado")

    st.subheader("Meus Automóveis")
    async for session in get_session():
        autos = await get_automoveis(session)
    autos_user = [a for a in autos if a.usuario_id == usuario.id]
    for a in autos_user:
        st.write(f"ID: {a.id} | Placa: {a.placa} | Tipo: {a.tipo}")


async def criar_local():
    st.title("Criar Local de Trabalho no Mapa")

    if "local_nome" not in st.session_state:
        st.session_state.local_nome = ""
    if "local_pos" not in st.session_state:
        st.session_state.local_pos = None

    # --- INÍCIO DA MUDANÇA ---

    # 1. Use `value` para ler o estado e remova `key`.
    # 2. Salve o retorno do widget de volta no estado.
    nome_input = st.text_input(
        "Nome do Local de Trabalho",
        value=st.session_state.local_nome,  # Use `value`
        placeholder="Digite o nome do local",
    )
    st.session_state.local_nome = nome_input  # Atualize o estado manualmente

    # --- FIM DA MUDANÇA ---

    st.subheader("Selecione a posição no mapa")
    cols = st.columns(MAP_SIZE)
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            label = f"{x},{y}"
            is_selected = st.session_state.local_pos == (x, y)
            btn_type = "primary" if is_selected else "secondary"
            btn = cols[x].button(label, key=f"local-{x}-{y}", type=btn_type)
            if btn:
                st.session_state.local_pos = (x, y)
                st.rerun()

    if st.button("Criar Local"):
        if not st.session_state.local_nome:
            st.error("Informe o nome do local")
            return
        if st.session_state.local_pos is None:
            st.error("Selecione uma posição no mapa")
            return

        x, y = st.session_state.local_pos
        async for session in get_session():
            await create_local_trabalho(
                session,
                {
                    "nome": st.session_state.local_nome,
                    "posicao_x": x,
                    "posicao_y": y,
                },
            )
        st.success(
            f"Local '{st.session_state.local_nome}' criado em ({x},{y})"
        )

        st.session_state.local_nome = ""
        st.session_state.local_pos = None
        st.rerun()


if menu == "Criar Conta":
    asyncio.run(criar_conta())
elif menu == "Login":
    login()
elif menu == "Listar Usuários":
    asyncio.run(listar())
elif menu == "Registrar Automóvel":
    asyncio.run(registrar_automovel())
elif menu == "Criar Local de Trabalho":
    asyncio.run(criar_local())
