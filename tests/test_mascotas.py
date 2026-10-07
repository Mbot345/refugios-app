import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Mascota, Refugio, User


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as db:
        db.add(Refugio(nombre="Huellas", direccion="Av. Central", ciudad="Quito"))
        db.add(
            User(
                username="demo",
                email="demo@example.com",
                password_hash=bcrypt.hashpw(b"clave-segura", bcrypt.gensalt()).decode(),
            )
        )
        db.commit()

    def override_get_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def autenticar(client: TestClient):
    client.cookies.set("session", "")
    client.post("/login", data={"username": "demo", "password": "clave-segura"})


def test_lista_sin_sesion_redirige_al_login(client: TestClient):
    response = client.get("/mascotas", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_usuario_autenticado_puede_ver_lista(client: TestClient):
    autenticar(client)
    response = client.get("/mascotas")
    assert response.status_code == 200
    assert "Mascotas" in response.text


def test_ciclo_crud_de_mascota(client: TestClient):
    autenticar(client)
    creada = client.post(
        "/mascotas/nueva",
        data={
            "nombre": "Luna", "especie": "Perro", "raza": "Mestiza", "sexo": "Hembra",
            "fecha_nacimiento": "2022-04-10", "descripcion": "Juguetona",
            "estado": "disponible", "refugio_id": "1",
        },
        follow_redirects=False,
    )
    assert creada.status_code == 303
    assert creada.headers["location"] == "/mascotas"

    with client as test_client:
        detalle = test_client.get("/mascotas/1")
        assert detalle.status_code == 200
        assert "Luna" in detalle.text

        editada = test_client.post(
            "/mascotas/1/editar",
            data={
                "nombre": "Luna Nueva", "especie": "Perro", "raza": "Mestiza", "sexo": "Hembra",
                "fecha_nacimiento": "2022-04-10", "descripcion": "Muy juguetona",
                "estado": "en_proceso", "refugio_id": "1",
            },
            follow_redirects=False,
        )
        assert editada.status_code == 303
        assert editada.headers["location"] == "/mascotas/1"
        assert "Luna Nueva" in test_client.get("/mascotas/1").text

        eliminada = test_client.post("/mascotas/1/eliminar", follow_redirects=False)
        assert eliminada.status_code == 303
        assert eliminada.headers["location"] == "/mascotas"
        assert "Aún no hay mascotas" in test_client.get("/mascotas").text


def test_mascota_inexistente_muestra_mensaje(client: TestClient):
    autenticar(client)
    response = client.get("/mascotas/999", follow_redirects=True)
    assert response.status_code == 200
    assert "Mascota no encontrada." in response.text
