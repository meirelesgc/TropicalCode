from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tropicalcode.models import Estacionamento, RegistroAtividade

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


async def build_graph(session):
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
        if c.direcao in ("IDA", "AMBOS"):
            graph[o].append(d)
        if c.direcao in ("VOLTA", "AMBOS"):
            graph[d].append(o)
    return graph


def dijkstra(graph, start, target):
    import heapq

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
    graph = await build_graph(session)
    origem = (ORIGEM_X, ORIGEM_Y)
    destino = (vaga.posicao_x, vaga.posicao_y)
    return dijkstra(graph, origem, destino)


async def calcular_distancia_trabalho(session, alvo, vaga):
    graph = await build_graph(session)
    origem = (alvo.posicao_x, alvo.posicao_y)
    destino = (vaga.posicao_x, vaga.posicao_y)
    return dijkstra(graph, origem, destino)


async def find_best_for_user(session, usuario, tipo_veiculo_selecionado: str):
    disponiveis = await get_available_estacionamentos(session)

    if not disponiveis:
        return None

    vagas_compativeis = [
        e for e in disponiveis if e.tipo_vaga == tipo_veiculo_selecionado
    ]

    if not vagas_compativeis:
        return None

    if usuario.local_trabalho:
        result = await session.execute(
            select(Estacionamento).where(
                Estacionamento.id == usuario.local_trabalho
            )
        )
        alvo = result.scalar_one_or_none()
        if alvo:
            menor = None
            menor_dist = float("inf")
            for v in vagas_compativeis:
                d = await calcular_distancia_trabalho(session, alvo, v)
                if d < menor_dist:
                    menor = v
                    menor_dist = d
            return menor

    menor = None
    menor_dist = float("inf")
    for v in vagas_compativeis:
        d = await calcular_distancia(session, v)
        if d < menor_dist:
            menor = v
            menor_dist = d
    return menor
