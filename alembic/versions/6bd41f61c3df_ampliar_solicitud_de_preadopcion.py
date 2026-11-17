"""ampliar solicitud de preadopcion

Revision ID: 6bd41f61c3df
Revises: 79286020c952
Create Date: 2026-11-16 18:54:12.034167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bd41f61c3df'
down_revision: Union[str, Sequence[str], None] = '79286020c952'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLA = "solicitudes_preadopcion"


def _agregar(nombre, tipo, valor_inicial):
    """Agrega una columna obligatoria usando un valor temporal por si hubiera filas."""
    op.add_column(
        TABLA, sa.Column(nombre, tipo, nullable=False, server_default=valor_inicial)
    )
    op.alter_column(TABLA, nombre, server_default=None)


def upgrade() -> None:
    # Renombres: conservan los datos existentes
    op.alter_column(TABLA, "telefono", new_column_name="telefono_movil")
    op.alter_column(TABLA, "domicilio", new_column_name="direccion_vivienda")

    # La experiencia previa pasa a ser opcional y "condiciones de cuidado" se elimina
    op.alter_column(TABLA, "experiencia_previa", existing_type=sa.Text(), nullable=True)
    op.drop_column(TABLA, "condiciones_cuidado")

    # Datos personales
    _agregar("nombres_completos", sa.String(120), "Sin dato")
    _agregar("cedula", sa.String(10), "0000000000")
    _agregar("fecha_nacimiento", sa.Date(), sa.text("'2000-01-01'"))
    op.add_column(TABLA, sa.Column("telefono_convencional", sa.String(20), nullable=True))
    _agregar("ocupacion", sa.String(100), "Sin dato")

    # Domicilio
    _agregar("tipo_vivienda", sa.String(20), "otro")
    _agregar("metros_vivienda", sa.Integer(), "0")
    _agregar("metros_area_verde", sa.Integer(), "0")
    op.add_column(TABLA, sa.Column("dimension_area_comunal", sa.String(100), nullable=True))
    _agregar("tenencia_vivienda", sa.String(20), "propia")

    # Motivos para adoptar
    _agregar("motivo_adopcion", sa.Text(), "Sin dato")
    _agregar("acepta_visitas", sa.Boolean(), sa.false())


def downgrade() -> None:
    for columna in (
        "acepta_visitas", "motivo_adopcion", "tenencia_vivienda", "dimension_area_comunal",
        "metros_area_verde", "metros_vivienda", "tipo_vivienda", "ocupacion",
        "telefono_convencional", "fecha_nacimiento", "cedula", "nombres_completos",
    ):
        op.drop_column(TABLA, columna)

    op.execute(f"UPDATE {TABLA} SET experiencia_previa = '' WHERE experiencia_previa IS NULL")
    op.alter_column(TABLA, "experiencia_previa", existing_type=sa.Text(), nullable=False)
    op.add_column(
        TABLA,
        sa.Column("condiciones_cuidado", sa.Text(), nullable=False, server_default=""),
    )
    op.alter_column(TABLA, "condiciones_cuidado", server_default=None)

    op.alter_column(TABLA, "direccion_vivienda", new_column_name="domicilio")
    op.alter_column(TABLA, "telefono_movil", new_column_name="telefono")