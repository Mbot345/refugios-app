"""adaptar modelo al documento de analisis

Revision ID: 21f1e4f96aad
Revises: 717907ed0a2b
Create Date: 2026-10-25 15:08:56.684167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21f1e4f96aad'
down_revision: Union[str, Sequence[str], None] = '717907ed0a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- Fundaciones (antes refugios) ----------
    op.rename_table("refugios", "fundaciones")
    op.add_column("fundaciones", sa.Column("descripcion", sa.Text(), nullable=True))
    op.add_column(
        "fundaciones",
        sa.Column("email_contacto", sa.String(120), nullable=False,
                  server_default="sin-correo@example.com"),
    )
    op.add_column(
        "fundaciones",
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("fundaciones", "email_contacto", server_default=None)

    # ---------- Usuarios: trabajador pertenece a una fundación ----------
    op.add_column("users", sa.Column("fundacion_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_fundacion_id", "users", "fundaciones", ["fundacion_id"], ["id"]
    )
    op.execute("UPDATE users SET rol = 'trabajador' WHERE rol = 'gestor'")

    # ---------- Animales (antes mascotas) ----------
    op.rename_table("mascotas", "animales")
    op.alter_column("animales", "refugio_id", new_column_name="fundacion_id")

    op.add_column(
        "animales",
        sa.Column("tamano", sa.String(20), nullable=False, server_default="mediano"),
    )
    op.add_column("animales", sa.Column("edad_meses", sa.Integer(), nullable=True))
    op.add_column(
        "animales",
        sa.Column("estado_salud", sa.String(100), nullable=False,
                  server_default="Sin evaluar"),
    )
    op.add_column("animales", sa.Column("qr_token", sa.String(36), nullable=True))
    op.add_column(
        "animales",
        sa.Column("creado_en", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # Datos existentes: token único, edad en meses y estado en masculino
    op.execute("UPDATE animales SET qr_token = gen_random_uuid()::text")
    op.alter_column("animales", "qr_token", nullable=False)
    op.create_index("ix_animales_qr_token", "animales", ["qr_token"], unique=True)
    op.execute(
        """
        UPDATE animales
        SET edad_meses = (
            DATE_PART('year', AGE(CURRENT_DATE, fecha_nacimiento)) * 12
            + DATE_PART('month', AGE(CURRENT_DATE, fecha_nacimiento))
        )::int
        WHERE fecha_nacimiento IS NOT NULL
        """
    )
    op.drop_column("animales", "fecha_nacimiento")
    op.execute("UPDATE animales SET estado = 'adoptado' WHERE estado = 'adoptada'")
    op.alter_column("animales", "tamano", server_default=None)
    op.alter_column("animales", "estado_salud", server_default=None)

    # ---------- Fotos e información sanitaria ----------
    op.create_table(
        "fotos_animal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ruta", sa.String(255), nullable=False),
        sa.Column("es_principal", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("animal_id", sa.Integer(),
                  sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_table(
        "registros_sanitarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("animal_id", sa.Integer(),
                  sa.ForeignKey("animales.id", ondelete="CASCADE"), nullable=False),
    )

    # ---------- Solicitudes e historial ----------
    op.create_table(
        "solicitudes_preadopcion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("telefono", sa.String(20), nullable=False),
        sa.Column("domicilio", sa.String(200), nullable=False),
        sa.Column("experiencia_previa", sa.Text(), nullable=False),
        sa.Column("condiciones_cuidado", sa.Text(), nullable=False),
        sa.Column("observacion_revision", sa.Text(), nullable=True),
        sa.Column("fecha_solicitud", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("fecha_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("animal_id", sa.Integer(), sa.ForeignKey("animales.id"),
                  nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("users.id"),
                  nullable=False),
        sa.Column("revisada_por", sa.Integer(), sa.ForeignKey("users.id"),
                  nullable=True),
    )
    op.create_index(
        "uq_solicitud_pendiente_usuario_animal",
        "solicitudes_preadopcion",
        ["animal_id", "usuario_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'pendiente'"),
    )
    op.create_index(
        "uq_solicitud_activa_por_animal",
        "solicitudes_preadopcion",
        ["animal_id"],
        unique=True,
        postgresql_where=sa.text("estado IN ('aprobada', 'finalizada')"),
    )

    op.create_table(
        "historial_solicitud",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estado_anterior", sa.String(20), nullable=True),
        sa.Column("estado_nuevo", sa.String(20), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("solicitud_id", sa.Integer(),
                  sa.ForeignKey("solicitudes_preadopcion.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("users.id"),
                  nullable=False),
    )


def downgrade() -> None:
    op.drop_table("historial_solicitud")
    op.drop_table("solicitudes_preadopcion")
    op.drop_table("registros_sanitarios")
    op.drop_table("fotos_animal")

    op.execute("UPDATE animales SET estado = 'adoptada' WHERE estado = 'adoptado'")
    op.add_column("animales", sa.Column("fecha_nacimiento", sa.Date(), nullable=True))
    op.drop_index("ix_animales_qr_token", table_name="animales")
    for columna in ("creado_en", "qr_token", "estado_salud", "edad_meses", "tamano"):
        op.drop_column("animales", columna)
    op.alter_column("animales", "fundacion_id", new_column_name="refugio_id")
    op.rename_table("animales", "mascotas")

    op.drop_constraint("fk_users_fundacion_id", "users", type_="foreignkey")
    op.drop_column("users", "fundacion_id")
    op.execute("UPDATE users SET rol = 'gestor' WHERE rol = 'trabajador'")

    for columna in ("activa", "email_contacto", "descripcion"):
        op.drop_column("fundaciones", columna)
    op.rename_table("fundaciones", "refugios")