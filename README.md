<h1 align="center">🐾 Refugios App</h1>

<p align="center">
  <img src="https://img.shields.io/badge/STATUS-EN%20DESARROLLO-yellow">
  <img src="https://img.shields.io/badge/Python-3.11+-blue">
  <img src="https://img.shields.io/badge/FastAPI-MVC-009688">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791">
  <img src="https://img.shields.io/badge/Deploy-Vercel%20%2B%20Neon-black">
</p>

<p align="center">
  Plataforma web que centraliza la información de animales rescatados y las solicitudes de preadopción de fundaciones y refugios de Ecuador.
</p>

<p align="center">
  🌐 <a href="https://refugios-app.vercel.app"><strong>Ver demo en línea</strong></a>
</p>

## Índice

* [Descripción del proyecto](#descripción-del-proyecto)
* [Estado del proyecto](#estado-del-proyecto)
* [Funcionalidades](#funcionalidades)
* [Roles y permisos](#roles-y-permisos)
* [Tecnologías utilizadas](#tecnologías-utilizadas)
* [Arquitectura MVC](#arquitectura-mvc)
* [Modelo de datos](#modelo-de-datos)
* [Instalación y ejecución](#instalación-y-ejecución)
* [Despliegue](#despliegue)
* [Flujo de trabajo en Git](#flujo-de-trabajo-en-git)
* [Autores](#autores)

## Descripción del proyecto

Muchas fundaciones y refugios de Ecuador gestionan sus registros y sus procesos de adopción de manera independiente. Refugios App reúne en un solo sitio a las fundaciones participantes y a los animales que tienen disponibles para adopción.

El **core** del proyecto es la gestión de animales y de solicitudes de preadopción: cualquier persona podrá consultar el catálogo público; los usuarios registrados podrán enviar una solicitud de preadopción; y el personal de cada fundación la revisará, la aprobará o la rechazará, con observaciones, historial de cambios y notificación por correo. Un módulo de administración permite gestionar fundaciones y usuarios, y consultar estadísticas básicas.

Proyecto semestral de Ingeniería Web (Universidad de las Américas), desarrollado con el patrón MVC.

## Estado del proyecto

**Proyecto en construcción** 

| Avance | Estado |
| --- | --- |
| Entregable 1: CRUD y Login con MVC | Completado |
| Entregable 2: Administración MVC (fundaciones, usuarios, estadísticas) y despliegue | Completado |
| Core: catálogo público, solicitudes de preadopción, correos y QR | En desarrollo |

## Funcionalidades

### Implementado

* **Registro, inicio y cierre de sesión:** sesión en cookie firmada y contraseñas protegidas con hash bcrypt.
* **Roles y permisos:** `admin`, `trabajador` y `adoptante`, con rutas y opciones diferenciadas por rol. El registro público siempre crea usuarios `adoptante`.
* **CRUD de animales** para trabajadores y administradores:
  * Datos: nombre, especie, raza, sexo, tamaño, edad aproximada en meses, estado de salud y descripción.
  * Cada trabajador gestiona **solo los animales de su fundación**.
  * El estado del animal (`disponible`, `en_proceso`, `adoptado`) no se edita a mano: cambiará únicamente con el flujo de solicitudes.
  * No se puede eliminar un animal que ya tiene solicitudes.
* **Panel de administración** (exclusivo del rol `admin`):
  * **Fundaciones:** registrar, editar, activar y desactivar. La ubicación se elige con desplegables dependientes **provincia → ciudad**.
  * **Usuarios:** asignar rol y fundación, y activar o desactivar cuentas.
  * **Estadísticas:** animales por estado, solicitudes por estado y actividad por fundación.
* **Validaciones en el servidor** antes de grabar en la base de datos:
  * Teléfono con formato ecuatoriano (celular o convencional).
  * Correo electrónico válido y nombre de fundación único.
  * La ciudad debe pertenecer a la provincia elegida.
  * Rol permitido, y un trabajador debe tener una fundación activa asignada.
  * Un administrador no puede quitarse su propio rol ni desactivar su propia cuenta.
* **Protección de URLs:** las rutas privadas redirigen a `/login` sin sesión, y muestran un aviso si el rol no tiene permiso.
* **Mensajes flash:** confirmaciones y errores visibles para el usuario.

### En desarrollo (core)

* **Catálogo público** con búsqueda y filtros por especie, tamaño, raza y edad, y ficha de cada animal.
* **Solicitudes de preadopción** con estados `pendiente`, `aprobada`, `rechazada`, `cancelada` y `finalizada`, e historial de cada cambio.
* **Reglas de negocio previstas:**
  * Solo se solicitan animales en estado `disponible`.
  * Un usuario no puede tener dos solicitudes pendientes para el mismo animal.
  * Al aprobar una solicitud, el animal pasa a `en_proceso` y las demás solicitudes pendientes se rechazan automáticamente.
  * Solo puede existir una solicitud aprobada activa por animal (garantizado también con un índice único en la base de datos).
  * Una solicitud aprobada puede cancelarse y el animal vuelve a `disponible`; la adopción definitiva se confirma sobre una solicitud aprobada.
* **Notificaciones por correo** al solicitante con el resultado de la revisión.
* **Código QR** por animal para acceder a su ficha.
* **Fotografías** e **información sanitaria** de cada animal.

### Fuera del alcance

Campañas de vacunación o esterilización, cálculo automático de compatibilidad entre solicitante y animal, evaluación automatizada de solicitantes, pagos, firmas electrónicas, historias clínicas completas e integración con sistemas externos.

## Roles y permisos

| Rol | Qué puede hacer |
| --- | --- |
| **Visitante** (sin cuenta) | Consultar el catálogo público (en desarrollo), registrarse e iniciar sesión |
| **Adoptante** | Todo lo del visitante y enviar y consultar sus solicitudes de preadopción (en desarrollo) |
| **Trabajador** | Gestionar los animales de su fundación y revisar sus solicitudes |
| **Admin** | Panel de administración: fundaciones, usuarios, roles y estadísticas, y gestión de animales de cualquier fundación |

## Tecnologías utilizadas

* **Python 3.11+** y **FastAPI**
* **SQLAlchemy 2.0** (ORM) y **Alembic** (migraciones)
* **PostgreSQL 16** (Docker Compose en local, Neon en producción)
* **Jinja2** para las vistas renderizadas en el servidor
* **bcrypt** para el hash de contraseñas
* **HTML, CSS y JavaScript** con nombres de clase en formato BEM
* **Vercel** para el despliegue de la aplicación

## Arquitectura MVC

```text
refugios-app/
├── app/
│   ├── main.py            # crea la app, middlewares y routers
│   ├── core/              # configuración, BD, seguridad, dependencias y constantes
│   ├── models/            # M: clases ORM
│   ├── services/          # lógica de negocio y validaciones
│   ├── controllers/       # C: routers (home, auth, animales, admin)
│   ├── views/             # V: plantillas Jinja2 (auth, animales, admin)
│   └── static/            # css y js
├── alembic/               # migraciones de la base de datos
├── docker-compose.yml     # PostgreSQL local
└── requirements.txt
```

| Capa | Responsabilidad |
| --- | --- |
| **Model** | Define las tablas y relaciones con SQLAlchemy |
| **View** | Plantillas HTML que se renderizan en el servidor |
| **Controller** | Recibe la petición, llama al servicio y devuelve la vista o una redirección |
| **Service** | Contiene las reglas de negocio y validaciones, para mantener delgados los controladores |

## Modelo de datos

| Tabla | Descripción |
| --- | --- |
| `users` | Usuarios con rol; los trabajadores se asocian a una fundación |
| `provincias` y `ciudades` | Catálogo de ubicaciones de Ecuador, cargado con la migración |
| `fundaciones` | Fundaciones y refugios participantes, con su ciudad |
| `animales` | Animales con estado, tamaño, edad aproximada y token para el QR |
| `fotos_animal` y `registros_sanitarios` | Fotografías e información sanitaria de cada animal |
| `solicitudes_preadopcion` e `historial_solicitud` | Solicitudes y el historial de cambios de estado |

Las tablas de fotos, información sanitaria y solicitudes ya existen en el esquema y se usarán en el desarrollo del core.

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

# 6. Crear las tablas (también carga provincias y ciudades de Ecuador)
alembic upgrade head

# 7. Iniciar el servidor
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000`.

### Crear el primer administrador

1. Regístrate desde `/registro`.
2. Asigna el rol de administrador a tu usuario:

```bash
docker exec -it refugios_db psql -U refugios_user -d refugios_db -c "UPDATE users SET rol = 'admin' WHERE username = 'TU_USUARIO';"
```

3. Cierra sesión y vuelve a entrar: te llevará al panel en `/admin`.
4. Crea una fundación desde **Fundaciones**, y asigna el rol `trabajador` y su fundación a otro usuario desde **Usuarios**.

### Variables de entorno

| Variable | Descripción |
| --- | --- |
| `DATABASE_URL` | Cadena de conexión a PostgreSQL |
| `SECRET_KEY` | Clave para firmar las cookies de sesión |

## Despliegue

La aplicación está desplegada en **Vercel** y la base de datos en **Neon** (PostgreSQL): 🌐 [https://refugios-app.vercel.app](https://refugios-app.vercel.app)

* Vercel despliega automáticamente cada cambio fusionado en `main`.
* En producción se usa la cadena de conexión **pooled** de Neon, y las variables `DATABASE_URL` y `SECRET_KEY` se configuran en el panel de Vercel.
* Las migraciones se aplican desde local con `alembic upgrade head`, apuntando a la cadena de conexión directa de Neon.
* La cookie de sesión se marca como solo HTTPS en producción.

## Flujo de trabajo en Git

* `main` recibe cambios mediante **Pull Requests** revisados por la otra persona.
* Cada funcionalidad se desarrolla en su propia rama, por ejemplo: `feature/auth-login`, `feature/crud-mascotas`, `feature/panel-admin`, `feature/deploy-vercel`.
* Los mensajes de commit siguen **Conventional Commits**: `feat`, `fix`, `docs`, `refactor`, `test` y `chore`.

Ejemplo:

```text
feat(admin): implementar panel de administración con control de acceso
```

## Autores

| [<img src="https://github.com/Mbot345.png" width=115><br><sub>Mateo Tipan</sub>](https://github.com/Mbot345) | [<img src="https://github.com/dav1d-lu1sVs.png" width=115><br><sub>Luis Vasquez</sub>](https://github.com/dav1d-lu1sVs) |
| :---: | :---: |