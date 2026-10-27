"""Agregar catalogo geografico ecuatoriano y relacionarlo con fundaciones.

Revision ID: 3d6a9c2f1b70
Revises: 21f1e4f96aad
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "3d6a9c2f1b70"
down_revision: Union[str, Sequence[str], None] = "21f1e4f96aad"
branch_labels = None
depends_on = None

PROVINCIAS = {
    "Azuay": ["Cuenca", "Gualaceo", "Paute", "Sígsig"],
    "Bolívar": ["Guaranda"], "Cañar": ["Azogues"], "Carchi": ["Tulcán"],
    "Chimborazo": ["Riobamba"], "Cotopaxi": ["Latacunga", "Salcedo", "Pujilí"],
    "El Oro": ["Machala", "Pasaje", "Santa Rosa"], "Esmeraldas": ["Esmeraldas"],
    "Galápagos": ["Puerto Baquerizo Moreno"],
    "Guayas": ["Guayaquil", "Daule", "Durán", "Milagro", "Samborondón"],
    "Imbabura": ["Ibarra", "Otavalo", "Cotacachi", "Atuntaqui"],
    "Loja": ["Loja", "Catamayo", "Macará"], "Los Ríos": ["Babahoyo", "Quevedo", "Ventanas"],
    "Manabí": ["Portoviejo", "Manta", "Chone", "Jipijapa"], "Morona Santiago": ["Macas"],
    "Napo": ["Tena"], "Orellana": ["Francisco de Orellana"], "Pastaza": ["Puyo"],
    "Pichincha": ["Quito", "Cayambe", "Machachi", "Sangolquí", "Tabacundo"],
    "Santa Elena": ["Santa Elena"], "Santo Domingo de los Tsáchilas": ["Santo Domingo"],
    "Sucumbíos": ["Nueva Loja"], "Tungurahua": ["Ambato", "Baños", "Pelileo"],
    "Zamora Chinchipe": ["Zamora"],
}


def upgrade() -> None:
    provincias = op.create_table(
        "provincias", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(60), nullable=False, unique=True),
    )
    ciudades = op.create_table(
        "ciudades", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("provincia_id", sa.Integer(), sa.ForeignKey("provincias.id"), nullable=False),
        sa.UniqueConstraint("provincia_id", "nombre", name="uq_ciudad_provincia_nombre"),
    )
    op.bulk_insert(provincias, [{"nombre": n} for n in PROVINCIAS])
    ids = {
        fila["nombre"]: fila["id"]
        for fila in op.get_bind()
        .execute(sa.text("SELECT nombre, id FROM provincias"))
        .mappings()
    }
    op.bulk_insert(ciudades, [
        {"nombre": city, "provincia_id": ids[province]}
        for province, cities in PROVINCIAS.items() for city in cities
    ])
    op.add_column("fundaciones", sa.Column("ciudad_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_fundaciones_ciudad_id", "fundaciones", "ciudades", ["ciudad_id"], ["id"])
    op.execute("UPDATE fundaciones f SET ciudad_id = c.id FROM ciudades c WHERE lower(c.nombre) = lower(f.ciudad)")
    op.execute("UPDATE fundaciones SET ciudad_id = (SELECT id FROM ciudades WHERE nombre = 'Quito') WHERE ciudad_id IS NULL")
    op.alter_column("fundaciones", "ciudad_id", nullable=False)
    op.drop_column("fundaciones", "ciudad")


def downgrade() -> None:
    op.add_column("fundaciones", sa.Column("ciudad", sa.String(80), nullable=True))
    op.execute("UPDATE fundaciones f SET ciudad = c.nombre FROM ciudades c WHERE c.id = f.ciudad_id")
    op.alter_column("fundaciones", "ciudad", nullable=False)
    op.drop_constraint("fk_fundaciones_ciudad_id", "fundaciones", type_="foreignkey")
    op.drop_column("fundaciones", "ciudad_id")
    op.drop_table("ciudades")
    op.drop_table("provincias")
