from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "eaa88a1a9adc"
down_revision: Union[str, Sequence[str], None] = "26e476b49d36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("registro_atividade") as batch_op:
        batch_op.add_column(
            sa.Column("usuario_id", sa.Integer(), nullable=False)
        )
        batch_op.create_foreign_key(
            "fk_registro_atividade_usuario_id",
            "usuarios",
            ["usuario_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("registro_atividade") as batch_op:
        batch_op.drop_constraint(
            "fk_registro_atividade_usuario_id", type_="foreignkey"
        )
        batch_op.drop_column("usuario_id")
