<h1 align="center">Refugios App</h1>

<p align="center">
  <img src="https://img.shields.io/badge/STATUS-FINALIZADO-brightgreen">
  <img src="https://img.shields.io/badge/Python-3.11+-blue">
  <img src="https://img.shields.io/badge/FastAPI-MVC-009688">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791">
  <img src="https://img.shields.io/badge/Deploy-Vercel%20%2B%20Neon-black">
</p>

<p align="center">
  Plataforma web que centraliza la información de animales rescatados y el proceso de preadopción de fundaciones y refugios de Ecuador.
</p>

<p align="center">
  <a href="https://refugios-app.vercel.app"><strong>Ver demo en línea</strong></a>
</p>

## Índice

* [Descripción del proyecto](#descripción-del-proyecto)
* [Funcionalidades](#funcionalidades)
* [Reglas de negocio](#reglas-de-negocio)
* [Roles y permisos](#roles-y-permisos)
* [Estructura de URLs](#estructura-de-urls)
* [Tecnologías utilizadas](#tecnologías-utilizadas)
* [Arquitectura MVC](#arquitectura-mvc)
* [Modelo de datos](#modelo-de-datos)
* [Instalación y ejecución](#instalación-y-ejecución)
* [Despliegue](#despliegue)
* [Flujo de trabajo en Git](#flujo-de-trabajo-en-git)
* [Autores](#autores)

## Descripción del proyecto

Muchas fundaciones y refugios de Ecuador gestionan sus registros y sus procesos de adopción de manera independiente. Refugios App reúne en un solo sitio a las fundaciones participantes, los animales que tienen disponibles para adopción y sus campañas.

El **core** del proyecto es la gestión de animales y de solicitudes de preadopción:

1. Cualquier persona consulta el catálogo público y la ficha de cada animal.
2. Un usuario registrado envía una solicitud de preadopción con sus datos personales y de vivienda.
3. El personal de la fundación revisa la solicitud y la aprueba o rechaza con observaciones.
4. El solicitante sigue el estado en una línea de tiempo, recibe cada respuesta por correo y, si es aprobada, descarga su hoja de aprobación en PDF.
5. La fundación confirma la adopción cuando se completan los trámites.

Un módulo de administración permite gestionar fundaciones y usuarios, supervisar el contenido y consultar estadísticas.

Proyecto semestral de Ingeniería Web (Universidad de las Américas), desarrollado con el patrón MVC.

## Funcionalidades

### Sitio público

* **Portada** con los animales recién llegados, accesos por especie, cómo funciona la adopción y las próximas campañas.
* **Catálogo de animales** con filtros por raza, especie, tamaño, sexo y rango de edad (cachorro, joven, adulto, senior).
* **Ficha del animal** con galería de fotos, datos, información sanitaria, ficha técnica en PDF y código QR.
* **Fundaciones** con su ubicación, contacto y número de animales disponibles.
* **Campañas y eventos** próximos y pasados, con su detalle.
* **Quiénes somos** con la misión y la visión del proyecto.

### Adoptante

* **Registro, inicio y cierre de sesión:** sesión en cookie firmada y contraseñas protegidas con hash bcrypt. El registro público siempre crea usuarios con rol adoptante.
* **Solicitud de preadopción** en tres bloques: datos personales, domicilio y motivos. La cédula se valida con el algoritmo oficial y el solicitante debe ser mayor de edad.
* **Mis solicitudes:** las solicitudes en curso muestran una línea de tiempo con cada etapa; las anteriores quedan en una lista plegable.
* **Cancelar** una solicitud pendiente o aprobada.
* **Hoja de aprobación en PDF** con los datos del animal, de la fundación y del solicitante.

### Personal de fundación

* **Panel de la fundación** con accesos según el rol y estadísticas propias.
* **Animales:** registrar, editar y eliminar, con hasta 4 fotos (una principal), información sanitaria (vacunas, desparasitaciones, esterilización y otros) y código QR descargable.
* **Revisión de solicitudes:** filtrar por estado, ver los datos del solicitante, aprobar, rechazar, revocar una aprobación y confirmar la adopción, con historial detallado de cada cambio.
* **Eventos:** crear, editar y cancelar con motivo.
* **Equipo:** agregar a usuarios registrados, cambiar su rol o quitarlos de la fundación.
* **Perfil:** descripción, dirección y datos de contacto de la fundación.

### Administración

* **Panel general** con usuarios, fundaciones, animales y solicitudes por estado, y actividad por fundación.
* **Fundaciones:** registrar, editar, suspender y reactivar. La ubicación se elige con desplegables dependientes **provincia → ciudad**.
* **Usuarios:** asignar rol y fundación, y activar o desactivar cuentas.
* **Supervisión** de los animales y eventos de todas las fundaciones (solo lectura).
* **Estadísticas por fundación.**

### Funciones transversales

* **Correos** al solicitante cuando su solicitud se recibe, se aprueba (con la hoja de aprobación en PDF adjunta), se rechaza, se revoca o se finaliza. Si no hay un servidor SMTP configurado, los correos se muestran en la consola.
* **Código QR** por animal: al escanearlo abre su ficha técnica en PDF.
* **Fotos guardadas en la base de datos:** se corrige la orientación, se reducen a 1000 px y se comprimen en JPEG, porque Vercel no tiene disco permanente.
* **Fechas en hora de Ecuador** (UTC-5) en la línea de tiempo, los PDF y los eventos.
* **Diseño responsive** para móvil, tablet y escritorio, con iconos SVG de [Lucide](https://lucide.dev).

## Reglas de negocio

**Estados de una solicitud**

| Desde | Hacia | Quién lo hace |
| --- | --- | --- |
| `pendiente` | `aprobada` o `rechazada` | La fundación |
| `pendiente` | `cancelada` | El adoptante |
| `aprobada` | `finalizada` | La fundación, al confirmar la adopción |
| `aprobada` | `cancelada` | El adoptante (cancela) o la fundación (revoca la aprobación) |

**Estados de un animal:** `disponible` → `en_proceso` → `adoptado`. El estado nunca se edita a mano: cambia solo con el flujo de solicitudes.

* Solo se pueden solicitar animales `disponibles`, y un usuario no puede tener dos solicitudes pendientes para el mismo animal.
* Al **aprobar** una solicitud, el animal pasa a `en_proceso` y las demás solicitudes pendientes de ese animal se rechazan automáticamente con el motivo «Se aprobó otra solicitud para este animal».
* Al **cancelar o revocar** una solicitud aprobada, el animal vuelve a `disponible`.
* Al **confirmar la adopción**, la solicitud queda `finalizada` y el animal `adoptado`.
* Rechazar, revocar y cancelar un evento exigen un motivo.
* Un animal tiene una sola solicitud aprobada activa. Se garantiza en tres niveles: bloqueo de la fila al aprobar (`SELECT ... FOR UPDATE`), validación en el servicio e índices únicos parciales en la base de datos.
* Una **fundación suspendida** desaparece del sitio público y su personal solo puede consultar.
* Un administrador no puede quitarse su propio rol ni desactivar su propia cuenta.

## Roles y permisos

| Rol | Qué puede hacer |
| --- | --- |
| **Visitante** (sin cuenta) | Ver el sitio público, registrarse e iniciar sesión |
| **Adoptante** | Todo lo del visitante, enviar solicitudes de preadopción y seguir su estado |
| **Encargado de animales** | Gestionar los animales de su fundación, sus fotos e información sanitaria |
| **Encargado de adopciones** | Revisar las solicitudes de su fundación |
| **Encargado de eventos** | Gestionar los eventos de su fundación |
| **Administrador de fundación** | Todo lo anterior dentro de su fundación, además del equipo y el perfil |
| **Moderador** | Supervisar fundaciones, animales y eventos, ver estadísticas y suspender fundaciones |
| **Administrador general** | Todo lo del moderador, además de gestionar usuarios, crear y editar fundaciones y reactivarlas |

Los datos personales de los solicitantes solo los ve el personal de la fundación que revisa la solicitud. El administrador y el moderador ven únicamente totales.

## Estructura de URLs

| Ruta | Quién | Contenido |
| --- | --- | --- |
| `/`, `/animales`, `/animales/{id}` | Todos | Portada, catálogo y ficha |
| `/fundaciones`, `/eventos`, `/quienes-somos` | Todos | Páginas informativas |
| `/animales/{id}/ficha.pdf`, `/qr/{token}` | Todos | Ficha técnica y enlace del QR |
| `/login`, `/registro`, `/logout` | Todos | Acceso |
| `/animales/{id}/solicitar`, `/mis-solicitudes` | Adoptante | Solicitudes de preadopción |
| `/fundacion` | Personal de fundación | Panel de la fundación |
| `/fundacion/animales` | Admin. de fundación, encargado de animales | Animales |
| `/fundacion/solicitudes` | Admin. de fundación, encargado de adopciones | Revisión de solicitudes |
| `/fundacion/eventos` | Admin. de fundación, encargado de eventos | Eventos |
| `/fundacion/equipo`, `/fundacion/perfil` | Admin. de fundación | Equipo y perfil |
| `/admin` | Administrador general y moderador | Panel, fundaciones, animales, eventos y estadísticas |
| `/admin/usuarios` | Administrador general | Usuarios |

Las rutas privadas redirigen a `/login` si no hay sesión y muestran un aviso si el rol no tiene permiso.

## Tecnologías utilizadas

* **Python 3.11+** y **FastAPI**
* **SQLAlchemy 2.0** (ORM) y **Alembic** (migraciones)
* **PostgreSQL 16** (Docker Compose en local, Neon en producción)
* **Jinja2** para las vistas renderizadas en el servidor
* **Pico CSS** como base de estilos, con hoja propia y clases en formato BEM
* **bcrypt** para el hash de contraseñas
* **Pillow** para procesar las fotos, **segno** para los códigos QR y **reportlab** para los PDF
* **smtplib** para el envío de correos
* **Vercel** para el despliegue de la aplicación

## Arquitectura MVC

```text
refugios-app/
├── app/
│   ├── main.py            # crea la app, middlewares, manejo de errores y routers
│   ├── core/              # configuración, BD, seguridad, dependencias por rol,
│   │                      # constantes, validadores, fechas, iconos y mensajes flash
│   ├── models/            # M: clases ORM (usuarios, fundaciones, ubicación,
│   │                      #    animales, solicitudes y eventos)
│   ├── services/          # reglas de negocio, validaciones, PDF, QR, fotos y correos
│   ├── controllers/       # C: routers por módulo (público, auth, solicitudes,
│   │                      #    revisión, animales, eventos, fundación, admin, estadísticas)
│   ├── views/             # V: plantillas Jinja2 por módulo, componentes y correos
│   └── static/            # css/styles.css y js (galería, ciudades y usuarios)
├── alembic/               # migraciones de la base de datos
├── docker-compose.yml     # PostgreSQL local
└── requirements.txt
```

| Capa | Responsabilidad |
| --- | --- |
| **Model** | Define las tablas y relaciones con SQLAlchemy |
| **View** | Plantillas HTML renderizadas en el servidor; los componentes (tarjetas, línea de tiempo, estadísticas) se reutilizan con macros |
| **Controller** | Recibe la petición, comprueba el rol con una dependencia, llama al servicio y devuelve la vista o una redirección |
| **Service** | Contiene las reglas de negocio y validaciones, para mantener delgados los controladores |

**Flujo de una petición:** ruta del controlador → dependencia de rol (`core/deps.py`) → servicio → modelo y base de datos → plantilla Jinja2 o redirección con mensaje flash.

## Modelo de datos

| Tabla | Descripción |
| --- | --- |
| `users` | Usuarios con rol; el personal de fundación se asocia a una fundación |
| `provincias` y `ciudades` | Catálogo de ubicaciones de Ecuador, cargado con una migración |
| `fundaciones` | Fundaciones y refugios participantes, con su ciudad y estado activa o suspendida |
| `animales` | Animales con estado, tamaño, edad aproximada y token para el QR |
| `fotos_animal` | Fotografías guardadas en la base de datos, con la foto principal marcada |
| `registros_sanitarios` | Vacunas, desparasitaciones y otros registros de cada animal |
| `solicitudes_preadopcion` | Datos del solicitante y de su vivienda, estado y revisión |
| `historial_solicitud` | Cada cambio de estado con fecha, usuario y observación |
| `eventos` | Campañas y eventos de cada fundación, con motivo si se cancelan |

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
2. Asigna el rol de administrador general a tu usuario:

```bash
docker exec -it refugios_db psql -U refugios_user -d refugios_db -c "UPDATE users SET rol = 'admin' WHERE username = 'TU_USUARIO';"
```

3. Cierra sesión y vuelve a entrar: te llevará al panel en `/admin`.
4. Crea una fundación desde **Fundaciones**.
5. Desde **Usuarios**, asigna a otro usuario el rol **Administrador de fundación** y su fundación. Esa persona podrá agregar a su equipo desde `/fundacion/equipo`.

### Variables de entorno

| Variable | Obligatoria | Descripción |
| --- | --- | --- |
| `DATABASE_URL` | Sí | Cadena de conexión a PostgreSQL |
| `SECRET_KEY` | Sí | Clave para firmar las cookies de sesión |
| `APP_URL` | No | Dirección pública de la app, usada en los QR y en los enlaces de los correos (por defecto `http://localhost:8000`) |
| `SMTP_HOST`, `SMTP_PORT` | No | Servidor de correo (por defecto `smtp.gmail.com` y `587`) |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | No | Cuenta que envía los correos. Si `SMTP_USER` está vacío, los correos se muestran en la consola |

## Despliegue

La aplicación está desplegada en **Vercel** y la base de datos en **Neon** (PostgreSQL): [https://refugios-app.vercel.app](https://refugios-app.vercel.app)

* Vercel despliega automáticamente cada cambio fusionado en `main`.
* En producción se usa la cadena de conexión **pooled** de Neon, y las variables de entorno se configuran en el panel de Vercel.
* Las migraciones se aplican desde local con `alembic upgrade head`, apuntando a la cadena de conexión **directa** de Neon.
* La cookie de sesión se marca como solo HTTPS en producción.
* Como Vercel no tiene disco permanente, las fotos se guardan en la base de datos y se sube una foto por petición, para respetar el límite de 4.5 MB de Vercel.

## Flujo de trabajo en Git

* `main` recibe cambios mediante **Pull Requests** revisados por la otra persona.
* Cada funcionalidad se desarrolla en su propia rama, por ejemplo: `feature/auth-login`, `feature/panel-admin`, `feature/revision-solicitudes`, `feature/fotos-animales`, `feature/rediseno-publico`.
* Los mensajes de commit siguen **Conventional Commits**: `feat`, `fix`, `docs`, `style`, `refactor`, `test` y `chore`.

Ejemplo:

```text
feat(revision): aprobar y rechazar solicitudes con rechazo automático de las demás
```

## Autores

| [<img src="https://github.com/Mbot345.png" width=115><br><sub>Mateo Tipán</sub>](https://github.com/Mbot345) | [<img src="https://github.com/dav1d-lu1sVs.png" width=115><br><sub>Luis Vásquez</sub>](https://github.com/dav1d-lu1sVs) |
| :---: | :---: |