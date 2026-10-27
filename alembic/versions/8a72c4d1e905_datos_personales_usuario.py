"""Añade datos personales y ubicación a usuarios.

Revision ID: 8a72c4d1e905
Revises: 3d6a9c2f1b70
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8a72c4d1e905"
down_revision: Union[str, Sequence[str], None] = "3d6a9c2f1b70"
branch_labels = None
depends_on = None


def _duplicados_por_valor(columna: str):
    return op.get_bind().execute(sa.text(
        f"SELECT lower({columna}) AS valor, array_agg(id ORDER BY id) AS ids "
        f"FROM users GROUP BY lower({columna}) HAVING count(*) > 1"
    )).mappings().all()


def upgrade() -> None:
    # No se normaliza ni elimina información existente. En caso de conflictos
    # de mayúsculas/minúsculas se detiene la migración e informa qué filas revisar.
    conflictos = []
    for columna in ("username", "email"):
        filas = _duplicados_por_valor(columna)
        if filas:
            conflictos.append(
                f"{columna}: " + ", ".join(f"{fila['valor']} (users.id {fila['ids']})" for fila in filas)
            )
    if conflictos:
        raise RuntimeError(
            "No se puede crear la unicidad sin distinguir mayúsculas/minúsculas. "
            "Revisa manualmente estos usuarios, sin borrar datos automáticamente: "
            + "; ".join(conflictos)
        )

    op.add_column("users", sa.Column("nombres_completos", sa.String(150), nullable=True))
    op.add_column("users", sa.Column("cedula", sa.String(10), nullable=True))
    op.add_column("users", sa.Column("telefono", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("provincia_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("ciudad_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("direccion", sa.Text(), nullable=True))
    op.create_foreign_key("fk_users_provincia_id", "users", "provincias", ["provincia_id"], ["id"])
    op.create_foreign_key("fk_users_ciudad_id", "users", "ciudades", ["ciudad_id"], ["id"])
    op.create_index("uq_users_username_lower", "users", [sa.text("lower(username)")], unique=True)
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
    op.create_index("uq_users_cedula", "users", ["cedula"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_cedula", table_name="users")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_index("uq_users_username_lower", table_name="users")
    op.drop_constraint("fk_users_ciudad_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_provincia_id", "users", type_="foreignkey")
    for columna in ("direccion", "ciudad_id", "provincia_id", "telefono", "cedula", "nombres_completos"):
        op.drop_column("users", columna)
