"""ampliar roles

Revision ID: 79286020c952
Revises: 3d6a9c2f1b70
Create Date: 2026-11-16 11:36:11.709503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79286020c952'
down_revision: Union[str, Sequence[str], None] = '3d6a9c2f1b70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Un trabajador sin fundación no es un rol válido: pasa a adoptante
    op.execute(
        "UPDATE users SET rol = 'adoptante' WHERE rol = 'trabajador' AND fundacion_id IS NULL"
    )
    # Los trabajadores actuales pasan a administradores de su fundación
    op.execute("UPDATE users SET rol = 'admin_fundacion' WHERE rol = 'trabajador'")


def downgrade() -> None:
    op.execute(
        "UPDATE users SET rol = 'trabajador' WHERE rol IN "
        "('admin_fundacion', 'encargado_animales', 'encargado_adopciones', 'encargado_eventos')"
    )
    op.execute("UPDATE users SET rol = 'adoptante' WHERE rol = 'moderador'")