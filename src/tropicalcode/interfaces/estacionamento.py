import asyncio
import random
import string

import streamlit as st
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.database import get_session
from tropicalcode.models import Caminho, Estacionamento

MAP_SIZE = 10


def normalizar_caminho(p1, p2):
    if p1 == p2:
        return None, None, False
    origem_norm = min(p1, p2)
    destino_norm = max(p1, p2)
    foi_invertido = p1 != origem_norm
    return origem_norm, destino_norm, foi_invertido


def gerar_codigo_vaga():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


async def salvar_estacionamento(
    session: AsyncSession,
    codigo_vaga,
    tipo_vaga,
    posicao_geral,
    posicao_x,
    posicao_y,
):
    novo_estacionamento = Estacionamento(
        codigo_vaga=codigo_vaga,
        tipo_vaga=tipo_vaga,
        posicao_geral=posicao_geral,
        posicao_x=posicao_x,
        posicao_y=posicao_y,
    )
    session.add(novo_estacionamento)
    await session.commit()
    await session.refresh(novo_estacionamento)
    st.toast(f"Estacionamento {codigo_vaga} criado!", icon="🅿️")
    return novo_estacionamento


async def deletar_estacionamento(session: AsyncSession, estacionamento_id):
    q = await session.execute(
        select(Estacionamento).where(Estacionamento.id == estacionamento_id)
    )
    existente = q.scalar_one_or_none()

    if existente:
        await session.delete(existente)
        await session.commit()
        st.toast(f"Estacionamento {existente.codigo_vaga} removido.", icon="🗑️")


async def carregar_estacionamentos(session: AsyncSession):
    r = await session.execute(select(Estacionamento))
    return r.scalars().all()


async def carregar_caminhos(session: AsyncSession):
    r = await session.execute(select(Caminho))
    return r.scalars().all()


async def interface_estacionamento_caminhos():
    st.title("Gerenciar Estacionamentos e Caminhos")

    if "caminhos_carregados" not in st.session_state:
        st.session_state.caminhos_carregados = False
    if "estacionamentos_carregados" not in st.session_state:
        st.session_state.estacionamentos_carregados = False
    if "caminhos_map" not in st.session_state:
        st.session_state.caminhos_map = {}
    if "estacionamentos_map" not in st.session_state:
        st.session_state.estacionamentos_map = {}
    if "pontos_caminho" not in st.session_state:
        st.session_state.pontos_caminho = set()
    if "ponto_selecionado_estacionamento" not in st.session_state:
        st.session_state.ponto_selecionado_estacionamento = None
    if "id_max_estacionamento" not in st.session_state:
        st.session_state.id_max_estacionamento = 0

    # Carregar caminhos
    if not st.session_state.caminhos_carregados:
        st.toast("Carregando caminhos do banco de dados...", icon="🗺️")
        async for session in get_session():
            caminhos = await carregar_caminhos(session)
            temp_caminhos_map = {}
            temp_pontos_caminho = set()
            for c in caminhos:
                key = (c.origem_x, c.origem_y, c.destino_x, c.destino_y)
                temp_caminhos_map[key] = c.direcao

                # Adicionar todos os pontos do caminho ao set
                ox, oy, dx, dy = key
                if oy == dy:  # Linha Horizontal
                    x_inicio = min(ox, dx)
                    x_fim = max(ox, dx)
                    for x in range(x_inicio, x_fim + 1):
                        temp_pontos_caminho.add((x, oy))
                elif ox == dx:  # Linha Vertical
                    y_inicio = min(oy, dy)
                    y_fim = max(oy, dy)
                    for y in range(y_inicio, y_fim + 1):
                        temp_pontos_caminho.add((ox, y))

            st.session_state.caminhos_map = temp_caminhos_map
            st.session_state.pontos_caminho = temp_pontos_caminho
            st.session_state.caminhos_carregados = True
        st.rerun()

    # Carregar estacionamentos
    if not st.session_state.estacionamentos_carregados:
        st.toast("Carregando estacionamentos do banco de dados...", icon="🅿️")
        async for session in get_session():
            estacionamentos = await carregar_estacionamentos(session)
            temp_estacionamentos_map = {}
            max_id = 0
            for e in estacionamentos:
                temp_estacionamentos_map[
                    (int(e.posicao_x), int(e.posicao_y))
                ] = e
                if e.id > max_id:
                    max_id = e.id
            st.session_state.estacionamentos_map = temp_estacionamentos_map
            st.session_state.id_max_estacionamento = max_id
            st.session_state.estacionamentos_carregados = True
        st.rerun()

    st.subheader("Visualização do Mapa")
    st.markdown(
        """
    - **Azul (Cheio):** Caminho ou Estacionamento existente.
    - **Contorno (Vazio):** Local disponível para criar estacionamento.
    - **Cinza (Padrão):** Ponto vazio.
    
    Clique em um ponto com **Contorno** para cadastrar.
    """
    )

    # Desenha a grade de botões
    cols = st.columns(MAP_SIZE)
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            ponto_atual = (x, y)
            label = f"{x},{y}"

            is_caminho = ponto_atual in st.session_state.pontos_caminho
            has_estacionamento = (
                ponto_atual in st.session_state.estacionamentos_map
            )
            is_adjacente_a_caminho = False

            # Verifica se o ponto é adjacente a um caminho
            if not is_caminho and not has_estacionamento:
                for dx, dy in [
                    (0, 1),
                    (0, -1),
                    (1, 0),
                    (-1, 0),
                ]:  # Vizinhos diretos
                    vizinho = (x + dx, y + dy)
                    if vizinho in st.session_state.pontos_caminho:
                        is_adjacente_a_caminho = True
                        break

            # --- CORREÇÃO APLICADA AQUI ---
            # Define o tipo do botão baseado nas regras e tipos válidos
            btn_type = "secondary"  # Padrão: Ponto vazio normal
            if is_caminho:
                btn_type = "primary"  # Caminho existente (azul)
            elif has_estacionamento:
                btn_type = "primary"  # Estacionamento existente (também azul)
                label += f" (🅿️ {st.session_state.estacionamentos_map[ponto_atual].codigo_vaga})"
            elif is_adjacente_a_caminho:
                btn_type = "tertiary"  # Ponto adjacente, clicável (contorno)
            # --- FIM DA CORREÇÃO ---

            btn = cols[x].button(
                label,
                key=f"map-{x}-{y}",
                type=btn_type,
                use_container_width=True,
            )

            if btn:
                # Se for um caminho, não faz nada para estacionamento
                if is_caminho:
                    st.toast(
                        "Não é possível cadastrar estacionamento em um caminho.",
                        icon="🚫",
                    )
                    st.session_state.ponto_selecionado_estacionamento = None
                # Se for adjacente (clicável) ou já tiver estacionamento (clicável)
                elif is_adjacente_a_caminho or has_estacionamento:
                    st.session_state.ponto_selecionado_estacionamento = (
                        ponto_atual
                    )
                else:
                    st.toast(
                        "Selecione um ponto adjacente a um caminho (com contorno) ou um estacionamento existente.",
                        icon="⚠️",
                    )
                    st.session_state.ponto_selecionado_estacionamento = None
                st.rerun()

    st.divider()

    if st.session_state.ponto_selecionado_estacionamento:
        ponto = st.session_state.ponto_selecionado_estacionamento
        estacionamento_existente = st.session_state.estacionamentos_map.get(
            ponto
        )

        st.subheader(f"Gerenciar Estacionamento em {ponto}")

        with st.form(f"form_estacionamento_{ponto}"):
            if estacionamento_existente:
                st.write(
                    f"**Estacionamento existente:** {estacionamento_existente.codigo_vaga}"
                )
                tipo_vaga_default_index = [
                    "MOTO",
                    "CARRO",
                    "PCD",
                    "CARRO_ELETRICO",
                ].index(estacionamento_existente.tipo_vaga)
                tipo_vaga_selecionado = st.selectbox(
                    "Tipo da Vaga:",
                    ["MOTO", "CARRO", "PCD", "CARRO_ELETRICO"],
                    index=tipo_vaga_default_index,
                    key="tipo_vaga_update",
                )

                # Botões de ação no form
                col_up, col_del = st.columns(2)
                if col_up.form_submit_button(
                    "Atualizar Tipo", use_container_width=True, type="primary"
                ):
                    # Lógica de atualização aqui
                    # (Exemplo: atualizar o tipo no banco de dados e no session_state)
                    async for session in get_session():
                        estacionamento_existente.tipo_vaga = (
                            tipo_vaga_selecionado
                        )
                        session.add(
                            estacionamento_existente
                        )  # Adiciona para "merge"
                        await session.commit()
                        await session.refresh(estacionamento_existente)
                    st.session_state.estacionamentos_map[ponto] = (
                        estacionamento_existente
                    )
                    st.toast(
                        f"Vaga {estacionamento_existente.codigo_vaga} atualizada!",
                        icon="🔄",
                    )
                    st.rerun()

                if col_del.form_submit_button(
                    "Remover Estacionamento",
                    use_container_width=True,
                    type="secondary",
                ):
                    async for session in get_session():
                        await deletar_estacionamento(
                            session, estacionamento_existente.id
                        )
                    del st.session_state.estacionamentos_map[ponto]
                    st.session_state.ponto_selecionado_estacionamento = None
                    st.toast("Vaga removida.", icon="🗑️")
                    st.rerun()

            else:
                st.write("Cadastrar novo estacionamento:")
                tipo_vaga = st.selectbox(
                    "Tipo da Vaga:",
                    ["MOTO", "CARRO", "PCD", "CARRO_ELETRICO"],
                    key="tipo_vaga_new",
                )
                submitted = st.form_submit_button(
                    "Cadastrar Estacionamento", type="primary"
                )

                if submitted:
                    async for session in get_session():
                        novo_codigo_vaga = gerar_codigo_vaga()
                        novo_est = await salvar_estacionamento(
                            session,
                            novo_codigo_vaga,
                            tipo_vaga,
                            st.session_state.id_max_estacionamento
                            + 1,  # Posição geral simples
                            float(ponto[0]),
                            float(ponto[1]),
                        )
                    st.session_state.estacionamentos_map[ponto] = novo_est
                    st.session_state.id_max_estacionamento += 1
                    st.session_state.ponto_selecionado_estacionamento = None
                    st.rerun()

            if st.form_submit_button("Cancelar", type="secondary"):
                st.session_state.ponto_selecionado_estacionamento = None
                st.rerun()

    st.divider()
    st.subheader("Caminhos Registrados")

    if not st.session_state.caminhos_map:
        st.caption("Nenhum caminho registrado.")

    for k, v in st.session_state.caminhos_map.items():
        o = (k[0], k[1])
        d = (k[2], k[3])

        if v == "IDA":
            arrow = f"{o} → {d}"
        elif v == "VOLTA":
            arrow = f"{o} ← {d}"
        else:  # AMBOS
            arrow = f"{o} ↔ {d}"

        st.write(f"Segmento: **{arrow}** | Permissão: **{v}**")

    st.divider()
    st.subheader("Estacionamentos Registrados")
    if not st.session_state.estacionamentos_map:
        st.caption("Nenhum estacionamento registrado.")
    else:
        for ponto, est in st.session_state.estacionamentos_map.items():
            st.write(
                f"**Código:** {est.codigo_vaga} | **Tipo:** {est.tipo_vaga} | **Posição:** ({int(est.posicao_x)}, {int(est.posicao_y)})"
            )


if __name__ == "__main__":
    asyncio.run(interface_estacionamento_caminhos())
