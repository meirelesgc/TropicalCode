from datetime import datetime

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()


@mapped_as_dataclass(table_registry)
class Usuario:
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    nome_usuario: Mapped[str] = mapped_column(unique=True)
    senha: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    local_trabalho: Mapped[int | None]
    criado_em: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )


@mapped_as_dataclass(table_registry)
class Estacionamento:
    __tablename__ = "estacionamentos"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    codigo_vaga: Mapped[str]
    tipo_vaga: Mapped[Enum] = mapped_column(
        Enum("MOTO", "CARRO", "PCD", "CARRO_ELETRICO", name="tipo_vaga")
    )
    posicao_geral: Mapped[int]
    posicao_x: Mapped[float]
    posicao_y: Mapped[float]


@mapped_as_dataclass(table_registry)
class Automovel:
    __tablename__ = "automoveis"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    placa: Mapped[str]
    tipo: Mapped[Enum] = mapped_column(
        Enum("MOTO", "CARRO", "PCD", "CARRO_ELETRICO", name="tipo_automovel")
    )


@mapped_as_dataclass(table_registry)
class RegistroAtividade:
    __tablename__ = "registro_atividade"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    estacionamento_id: Mapped[int] = mapped_column(
        ForeignKey("estacionamentos.id")
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    tipo: Mapped[Enum] = mapped_column(
        Enum("ENTRADA", "SAIDA", name="tipo_movimento")
    )
    horario: Mapped[datetime] = mapped_column(server_default=func.now())
    caminho: Mapped[str]


@mapped_as_dataclass(table_registry)
class Caminho:
    __tablename__ = "caminhos"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    origem_x: Mapped[int]
    origem_y: Mapped[int]
    destino_x: Mapped[int]
    destino_y: Mapped[int]
    direcao: Mapped[Enum] = mapped_column(
        Enum("IDA", "VOLTA", "AMBOS", name="direcao_caminho")
    )
