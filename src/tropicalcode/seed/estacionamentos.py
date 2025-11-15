import asyncio
import random
from datetime import datetime, timezone

from tropicalcode.database import get_session
from tropicalcode.repositorios.estacionamento_repo import (
    create_estacionamento,
    get_estacionamentos,
)
from tropicalcode.repositorios.registro_atividade_repo import create_registro
from tropicalcode.repositorios.usuario_repo import get_usuarios

tipos = ["MOTO", "CARRO", "PCD", "CARRO_ELETRICO"]


async def seed():
    async for session in get_session():
        ests = await get_estacionamentos(session)
        if not ests:
            for i in range(20):
                await create_estacionamento(
                    session,
                    {
                        "codigo_vaga": f"V{i + 1}",
                        "tipo_vaga": random.choice(tipos),
                        "posicao_geral": i + 1,
                        "posicao_x": random.uniform(0, 50),
                        "posicao_y": random.uniform(0, 50),
                    },
                )
            ests = await get_estacionamentos(session)

        usuarios = await get_usuarios(session)

        if usuarios and ests:
            for u in usuarios:
                e = random.choice(ests)
                await create_registro(
                    session,
                    {
                        "estacionamento_id": e.id,
                        "tipo": random.choice(["ENTRADA", "SAIDA"]),
                        "caminho": "seed",
                        "horario": datetime.now(timezone.utc),
                    },
                )


if __name__ == "__main__":
    asyncio.run(seed())
