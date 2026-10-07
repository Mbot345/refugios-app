<h1 align="center">🐾 Refugios App</h1>

<p align="center">
  <img src="https://img.shields.io/badge/STATUS-EN%20DESARROLLO-yellow">
  <img src="https://img.shields.io/badge/Python-3.11+-blue">
  <img src="https://img.shields.io/badge/FastAPI-MVC-009688">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791">
</p>

<p align="center">
  Plataforma web que conecta refugios, adoptantes y campañas de salud animal.
</p>

## Índice

* [Descripción del proyecto](#descripción-del-proyecto)
* [Estado del proyecto](#estado-del-proyecto)
* [Funcionalidades](#funcionalidades)
* [Tecnologías utilizadas](#tecnologías-utilizadas)
* [Arquitectura MVC](#arquitectura-mvc)
* [Instalación y ejecución](#instalación-y-ejecución)
* [Flujo de trabajo en Git](#flujo-de-trabajo-en-git)
* [Autores](#autores)

## Descripción del proyecto

Refugios App busca centralizar el proceso de adopción de mascotas: cada refugio administra sus animales, los adoptantes solicitan adopciones y, más adelante, el sistema integrará centros de vacunación y campañas de esterilización con cupos y lista de espera.

Proyecto semestral de Ingeniería Web, desarrollado con el patrón MVC.

## Estado del proyecto

🚧 **Proyecto en construcción** 🚧

**Entregable 1 (CRUD y Login con MVC): completado.**

## Funcionalidades

### Entregable 1

* **Registro de usuarios:** validación de usuario, correo y contraseña.
* **Login y logout:** manejo de sesión mediante cookie firmada y contraseñas protegidas con hash bcrypt.
* **Protección de rutas:** las URLs de `/mascotas` requieren una sesión iniciada.
* **CRUD de mascotas:** crear, listar, editar y eliminar mascotas, con validaciones.
* **Roles:** el sistema contempla los roles `admin`, `gestor` y `adoptante`.
* **Mensajes flash:** confirmaciones y errores visibles para el usuario.

### Planeado

* Solicitudes de adopción con estados, cuestionario y puntaje de compatibilidad.
* Vacunación con esquemas por especie y edad.
* Campañas de esterilización con cupos y lista de espera.
* Panel de administración y reportes.
* Vistas diferenciadas por rol.

## Tecnologías utilizadas

* **Python 3.11+** y **FastAPI**
* **SQLAlchemy 2.0** (ORM) y **Alembic** (migraciones)
* **PostgreSQL 16** con **Docker Compose**
* **Jinja2** para las vistas
* **bcrypt** para el hash de contraseñas
* **HTML y CSS** con nombres de clase en formato BEM

## Arquitectura MVC

```text
refugios-app/
├── app/
│   ├── main.py            # crea la app, middlewares y routers
│   ├── core/              # configuración, BD, seguridad, dependencias
│   ├── models/            # M: clases ORM (User, Refugio, Mascota)
│   ├── services/          # lógica de negocio y validaciones
│   ├── controllers/       # C: routers (auth, home, mascotas)
│   ├── views/             # V: plantillas Jinja2
│   └── static/css/        # estilos
├── alembic/               # migraciones de la base de datos
├── docker-compose.yml     # PostgreSQL local
└── requirements.txt
```

| Capa           | Responsabilidad                                                             |
| -------------- | --------------------------------------------------------------------------- |
| **Model**      | Define las tablas y relaciones con SQLAlchemy                               |
| **View**       | Plantillas HTML que se renderizan en el servidor                            |
| **Controller** | Recibe la petición, llama al servicio y devuelve la vista o una redirección |
| **Service**    | Contiene las reglas de negocio para mantener delgados los controladores     |

## Instalación y ejecución

**Requisitos:** Python 3.11+, Git y Docker Desktop.

```bash
# 1. Clonar el repositorio
git clone https://github.com/Mbot345/refugios-app.git
cd refugios-app

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1
# source .venv/bin/activate       # Mac/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear el archivo .env a partir de la plantilla
copy .env.example .env
# Mac/Linux: cp .env.example .env

# Generar una clave y pegarla en SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 5. Levantar PostgreSQL
docker compose up -d

# 6. Crear las tablas
alembic upgrade head

# 7. Crear un refugio de prueba
docker exec -it refugios_db psql -U refugios_user -d refugios_db -c "INSERT INTO refugios (nombre, direccion, ciudad, telefono) VALUES ('Refugio Huellitas', 'Av. Principal 123', 'Quito', '0999999999');"

# 8. Iniciar el servidor
uvicorn app.main:app --reload
```

## Flujo de trabajo en Git

* `main` recibe cambios mediante **Pull Requests** revisados por la otra persona.
* Cada funcionalidad se desarrolla en su propia rama, por ejemplo: `feature/auth-login`, `feature/crud-mascotas`.
* Los mensajes de commit siguen **Conventional Commits**: `feat`, `fix`, `docs`, `refactor` y `chore`.

Ejemplo:

```text
feat(auth): implementar registro, login y logout
```

## Autores

| [<img src="https://github.com/Mbot345.png" width=115><br><sub>Mateo Tipan</sub>](https://github.com/Mbot345) | [<img src="https://github.com/dav1d-lu1sVs.png" width=115><br><sub>Luis Vasquez</sub>](https://github.com/dav1d-lu1sVs) | 
| :----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------------------------: |
