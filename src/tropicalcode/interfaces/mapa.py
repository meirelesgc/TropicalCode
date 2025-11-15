import asyncio

import streamlit as st
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.database import get_session
from tropicalcode.models import Caminho

MAP_SIZE = 10


def normalizar_caminho(p1, p2):
    if p1 == p2:
        return None, None, False
    origem_norm = min(p1, p2)
    destino_norm = max(p1, p2)
    foi_invertido = p1 != origem_norm
    return origem_norm, destino_norm, foi_invertido


async def salvar_caminho(session: AsyncSession, p1, p2, direcao):
    origem_norm, destino_norm, _ = normalizar_caminho(p1, p2)
    if origem_norm is None:
        st.toast("Seleção inválida.", icon="⚠️")
        return None

    q = await session.execute(
        select(Caminho).where(
            Caminho.origem_x == origem_norm[0],
            Caminho.origem_y == origem_norm[1],
            Caminho.destino_x == destino_norm[0],
            Caminho.destino_y == destino_norm[1],
        )
    )
    existente = q.scalar_one_or_none()

    if existente:
        existente.direcao = direcao
        await session.commit()
        await session.refresh(existente)
        st.toast(
            f"Caminho {origem_norm}↔{destino_norm} atualizado: {direcao}",
            icon="🔄",
        )
        return existente

    novo = Caminho(
        origem_x=origem_norm[0],
        origem_y=origem_norm[1],
        destino_x=destino_norm[0],
        destino_y=destino_norm[1],
        direcao=direcao,
    )
    session.add(novo)
    await session.commit()
    await session.refresh(novo)
    st.toast(
        f"Caminho {origem_norm}↔{destino_norm} criado: {direcao}", icon="✨"
    )
    return novo


async def deletar_caminho(session: AsyncSession, p1, p2):
    origem_norm, destino_norm, _ = normalizar_caminho(p1, p2)
    if origem_norm is None:
        return

    q = await session.execute(
        select(Caminho).where(
            Caminho.origem_x == origem_norm[0],
            Caminho.origem_y == origem_norm[1],
            Caminho.destino_x == destino_norm[0],
            Caminho.destino_y == destino_norm[1],
        )
    )
    existente = q.scalar_one_or_none()

    if existente:
        await session.delete(existente)
        await session.commit()
        st.toast(f"Caminho {origem_norm}↔{destino_norm} removido.", icon="🗑️")


async def carregar_caminhos(session: AsyncSession):
    r = await session.execute(select(Caminho))
    return r.scalars().all()


async def limpar_mapa_db(session: AsyncSession):
    await session.execute(delete(Caminho))
    await session.commit()


# --- INTERFACE STREAMLIT (Atualizada) ---


async def interface_mapa():
    st.title("Mapa de Caminhos")

    # Inicializa o session_state
    if "mapa" not in st.session_state:
        st.session_state.mapa = {}
    if "origem" not in st.session_state:
        st.session_state.origem = None
    if "modo_atual" not in st.session_state:
        st.session_state.modo_atual = "IDA"

    if st.button(
        "Limpar Mapa Completo", type="tertiary", use_container_width=True
    ):
        async for session in get_session():
            await limpar_mapa_db(session)
        st.session_state.mapa = {}
        st.session_state.origem = None
        st.session_state.modo_atual = "IDA"
        st.toast("Mapa limpo com sucesso!", icon="💥")
        st.rerun()

    # Seletor de Modo de Edição
    st.radio(
        "Modo de Edição",
        ["IDA", "VOLTA", "AMBOS", "EXCLUIR"],
        key="modo_atual",
        horizontal=True,
        label_visibility="collapsed",
    )

    st.divider()

    # Carregar o mapa do DB apenas uma vez
    if "mapa_carregado" not in st.session_state:
        st.toast("Carregando mapa do banco de dados...", icon="☁️")
        mapa_temp = {}
        async for session in get_session():
            caminhos = await carregar_caminhos(session)
            for c in caminhos:
                key = (c.origem_x, c.origem_y, c.destino_x, c.destino_y)
                mapa_temp[key] = c.direcao

        st.session_state.mapa = mapa_temp
        st.session_state.mapa_carregado = True
        st.rerun()

    # **MELHORIA 2: Calcular todos os pontos do caminho para colorir**
    pontos_ativos = set()
    for key, direcao in st.session_state.mapa.items():
        if direcao is not None:
            ox, oy, dx, dy = key

            if oy == dy:  # Linha Horizontal
                x_inicio = min(ox, dx)
                x_fim = max(ox, dx)
                for x in range(x_inicio, x_fim + 1):
                    pontos_ativos.add((x, oy))

            elif ox == dx:  # Linha Vertical
                y_inicio = min(oy, dy)
                y_fim = max(oy, dy)
                for y in range(y_inicio, y_fim + 1):
                    pontos_ativos.add((ox, y))

    # Desenha a grade de botões
    cols = st.columns(MAP_SIZE)
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            ponto = (x, y)
            label = f"{x},{y}"

            is_origem = st.session_state.origem == ponto
            # Verifica se o ponto faz parte de algum caminho ativo
            is_ativo = ponto in pontos_ativos

            btn_type = "secondary"
            if is_origem:
                btn_type = "primary"  # Origem selecionada (azul)
            elif is_ativo:
                btn_type = "primary"  # Ponto de caminho existente (azul)

            btn = cols[x].button(
                label, key=f"{x}-{y}", type=btn_type, use_container_width=True
            )

            if btn:
                if st.session_state.origem is None:
                    # Primeiro clique: define a origem
                    st.session_state.origem = ponto
                    st.rerun()

                else:
                    # Segundo clique: processa a ação
                    origem_clique = st.session_state.origem
                    destino_clique = ponto

                    # **MELHORIA 1: Validar se é uma reta (horizontal ou vertical)**
                    origem_x, origem_y = origem_clique
                    destino_x, destino_y = destino_clique

                    if origem_x != destino_x and origem_y != destino_y:
                        st.toast(
                            "Seleção inválida. Os caminhos devem ser retas.",
                            icon="🚫",
                        )
                        st.session_state.origem = None  # Reseta a seleção
                        st.rerun()
                        # Interrompe o processamento se for diagonal
                        continue

                    # Se a validação passar, continua o processo normal
                    modo_selecionado = st.session_state.modo_atual
                    origem_norm, destino_norm, _ = normalizar_caminho(
                        origem_clique, destino_clique
                    )

                    if origem_norm is None:  # Clicou no mesmo ponto
                        st.session_state.origem = None
                        st.toast("Seleção cancelada.", icon="🚫")
                        st.rerun()
                        continue

                    key_norm = (
                        origem_norm[0],
                        origem_norm[1],
                        destino_norm[0],
                        destino_norm[1],
                    )

                    # Processa a ação com base no modo selecionado
                    async for session in get_session():
                        if modo_selecionado == "EXCLUIR":
                            await deletar_caminho(
                                session, origem_clique, destino_clique
                            )
                            if key_norm in st.session_state.mapa:
                                del st.session_state.mapa[key_norm]
                        else:
                            await salvar_caminho(
                                session,
                                origem_clique,
                                destino_clique,
                                modo_selecionado,
                            )
                            st.session_state.mapa[key_norm] = modo_selecionado

                    st.session_state.origem = None
                    st.rerun()

    # Exibe os caminhos registrados
    st.divider()
    st.subheader("Caminhos Registrados")

    caminhos_ativos_map = {
        k: v for k, v in st.session_state.mapa.items() if v is not None
    }

    if not caminhos_ativos_map:
        st.caption("Nenhum caminho registrado.")

    for k, v in caminhos_ativos_map.items():
        o = (k[0], k[1])
        d = (k[2], k[3])

        if v == "IDA":
            arrow = f"{o} → {d}"
        elif v == "VOLTA":
            arrow = f"{o} ← {d}"
        else:  # AMBOS
            arrow = f"{o} ↔ {d}"

        st.write(f"Segmento: **{arrow}** | Permissão: **{v}**")


# --- Ponto de entrada ---
if __name__ == "__main__":
    asyncio.run(interface_mapa())
