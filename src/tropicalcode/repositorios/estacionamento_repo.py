import heapq

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.models import (
    Caminho,
    Estacionamento,
    RegistroAtividade,
    Usuario,
)
from tropicalcode.repositorios.trabalho_repo import get_local_trabalho

ORIGEM_X = 0
ORIGEM_Y = 0


async def create_estacionamento(session: AsyncSession, data: dict):
    est = Estacionamento(**data)
    session.add(est)
    await session.commit()
    await session.refresh(est)
    return est


async def get_estacionamento(session: AsyncSession, estacionamento_id: int):
    result = await session.execute(
        select(Estacionamento).where(Estacionamento.id == estacionamento_id)
    )
    return result.scalar_one_or_none()


async def get_estacionamentos(session: AsyncSession):
    result = await session.execute(select(Estacionamento))
    return result.scalars().all()


async def update_estacionamento(
    session: AsyncSession, estacionamento_id: int, data: dict
):
    est = await get_estacionamento(session, estacionamento_id)
    if not est:
        return None
    for k, v in data.items():
        setattr(est, k, v)
    await session.commit()
    await session.refresh(est)
    return est


async def delete_estacionamento(session: AsyncSession, estacionamento_id: int):
    est = await get_estacionamento(session, estacionamento_id)
    if not est:
        return False
    await session.delete(est)
    await session.commit()
    return True


async def get_available_estacionamentos(session):
    result = await session.execute(select(Estacionamento))
    estacionamentos = result.scalars().all()

    result2 = await session.execute(select(RegistroAtividade))
    registros = result2.scalars().all()

    latest = {}
    for r in registros:
        e = r.estacionamento_id
        if e not in latest or r.horario > latest[e].horario:
            latest[e] = r

    ocupados = {k for k, v in latest.items() if v.tipo == "ENTRADA"}

    return [e for e in estacionamentos if e.id not in ocupados]


async def build_graph(session, vagas=[], local_trabalho=None):
    result = await session.execute(select(Caminho))
    caminhos = result.scalars().all()
    graph = {}

    for c in caminhos:
        o = (c.origem_x, c.origem_y)
        d = (c.destino_x, c.destino_y)

        if o not in graph:
            graph[o] = []
        if d not in graph:
            graph[d] = []

        current = o
        while current != d:
            if current not in graph:
                graph[current] = []

            next_node = None
            if current[0] < d[0]:
                next_node = (current[0] + 1, current[1])
            elif current[0] > d[0]:
                next_node = (current[0] - 1, current[1])
            elif current[1] < d[1]:
                next_node = (current[0], current[1] + 1)
            elif current[1] > d[1]:
                next_node = (current[0], current[1] - 1)
            else:
                break

            if next_node not in graph:
                graph[next_node] = []

            if c.direcao in ("IDA", "AMBOS"):
                if next_node not in graph[current]:
                    graph[current].append(next_node)
            if c.direcao in ("VOLTA", "AMBOS"):
                if current not in graph[next_node]:
                    graph[next_node].append(current)

            current = next_node

    # 2. Cria uma lista de "nós especiais" (vagas + local de trabalho)
    nodes_to_connect = []
    for v in vagas:
        nodes_to_connect.append((v.posicao_x, v.posicao_y))

    if local_trabalho:
        nodes_to_connect.append((
            local_trabalho.posicao_x,
            local_trabalho.posicao_y,
        ))

    # 3. Conecta os "nós especiais" ao grafo principal
    for pos in nodes_to_connect:
        if pos not in graph:
            graph[pos] = []

        for node in graph:
            if node != pos:
                # Sua lógica original de conexão
                if node[0] == pos[0] or node[1] == pos[1]:
                    if abs(node[0] - pos[0]) + abs(node[1] - pos[1]) <= 1.5:
                        if pos not in graph[node]:
                            graph[node].append(pos)
                        if node not in graph[pos]:
                            graph[pos].append(node)

    return graph


def dijkstra(graph, start, target):
    queue = [(0, start)]
    visited = set()
    while queue:
        dist, node = heapq.heappop(queue)
        if node == target:
            return dist
        if node in visited:
            continue
        visited.add(node)
        for neigh in graph.get(node, []):
            heapq.heappush(queue, (dist + 1, neigh))
    return float("inf")


async def calcular_distancia(session, vaga):
    graph = await build_graph(session, vagas=[vaga])
    origem = (ORIGEM_X, ORIGEM_Y)
    destino = (vaga.posicao_x, vaga.posicao_y)

    if origem not in graph or destino not in graph:
        return float("inf")
    print("ENTREI AQUi")
    return dijkstra(graph, origem, destino)


async def find_best_for_user(
    session, usuario: Usuario, tipo_veiculo_selecionado: str
):
    disponiveis = await get_available_estacionamentos(session)

    if not disponiveis:
        return None

    vagas_compativeis = [
        e for e in disponiveis if e.tipo_vaga == tipo_veiculo_selecionado
    ]

    if not vagas_compativeis:
        return None
    local_trabalho = await get_local_trabalho(session, usuario.local_trabalho)
    graph = await build_graph(
        session, vagas=vagas_compativeis, local_trabalho=local_trabalho
    )
    origem = (ORIGEM_X, ORIGEM_Y)

    if origem not in graph:
        return None

    menor = None
    menor_dist = float("inf")

    for v in vagas_compativeis:
        destino = (v.posicao_x, v.posicao_y)

        if destino not in graph:
            continue

        d = dijkstra(graph, origem, destino)

        if d < menor_dist:
            menor = v
            menor_dist = d

    return menor
