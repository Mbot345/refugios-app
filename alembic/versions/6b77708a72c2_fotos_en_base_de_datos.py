"""fotos en base de datos

Revision ID: 6b77708a72c2
Revises: 6bd41f61c3df
Create Date: 2026-11-18 00:22:14.844058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b77708a72c2'
down_revision: Union[str, Sequence[str], None] = '6bd41f61c3df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hasta ahora no existía forma de subir fotos, así que no hay datos que conservar
    op.execute("DELETE FROM fotos_animal")
    op.drop_column("fotos_animal", "ruta")
    op.add_column("fotos_animal", sa.Column("datos", sa.LargeBinary(), nullable=False))


def downgrade() -> None:
    op.execute("DELETE FROM fotos_animal")
    op.drop_column("fotos_animal", "datos")
    op.add_column("fotos_animal", sa.Column("ruta", sa.String(length=255), nullable=False))