# Plataforma de Gestión Académica

Sistema web para la gestión integral de una institución educativa: cursos, cohortes, docentes, estudiantes, inscripciones, pagos, asistencia, materiales, tareas y notificaciones.

Proyecto académico de **Ingeniería de Software II** — FPUNA.

---

## Stack tecnológico

- **Backend:** Python 3.14 · Django 6.0.4
- **Base de datos:** SQLite 3 (archivo local `gestion_academica.db`)
- **Frontend:** Bootstrap 5 · Bootstrap Icons · FullCalendar 6.1.11 (vía CDN)
- **Arquitectura:** MVC sobre Django con RBAC por roles (`@permiso_required`)
- **Plantillas:** Django Templates con context processors globales

---

## Requisitos previos

- Python **3.12+** (recomendado 3.14)
- `pip` y `venv` (incluidos con Python)
- Git
- (Opcional) Un editor con soporte Django: VS Code, PyCharm

---

## Instalación y arranque

### 1. Clonar el repositorio

```bash
git clone https://github.com/annamartinezPY/Gestion-Academica.git
cd "Gestion-Academica"
```

### 2. Crear y activar entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear la base de datos

La base de datos se construye con el script `database.py` ubicado en la raíz del proyecto:

```bash
python database.py
```

Esto genera el archivo `gestion_academica.db` con el esquema y datos iniciales (roles, permisos, usuario administrador).

### 5. Levantar el servidor Django

```bash
cd gestion_academica_web
python manage.py runserver
```

La aplicación queda disponible en: **http://localhost:8000/**

---

## Usuarios de prueba

Tras ejecutar `database.py`, quedan creados los siguientes usuarios (todos con contraseña `admin123` salvo indicación):

| Rol | Usuario | Acceso |
|---|---|---|
| **Administrador** | `admin` | Gestión total del sistema |
| **Tesorero** | `tesorero` | Validación de pagos, cola financiera |
| **Docente** | `docente1` | Sesiones, asistencia, materiales, tareas, salario |
| **Estudiante** | `estudiante1` | Mi portal, inscripciones, pagos, tareas |

> Para password reset: la app envía el link a la consola del servidor (configurado con `console.EmailBackend` en desarrollo).

---

## Estructura del proyecto

```
Gestion-Academica/
├── database.py                 # Script de creación del esquema SQLite
├── gestion_academica.db        # BD generada (excluida del repo)
├── requirements.txt            # Dependencias Python
├── .gitignore
│
└── gestion_academica_web/      # Proyecto Django principal
    ├── manage.py
    ├── academica/              # App de negocio
    │   ├── models.py           # ~30 modelos managed=False
    │   ├── views/              # Vistas por dominio
    │   │   ├── dashboard.py
    │   │   ├── asistencia.py
    │   │   ├── pagos.py
    │   │   ├── tareas.py
    │   │   ├── materiales.py
    │   │   ├── notificaciones.py
    │   │   └── ...
    │   ├── templates/          # Plantillas Bootstrap por dominio
    │   ├── templatetags/       # Filtros personalizados (formato guaraní, etc.)
    │   ├── context_processors.py
    │   ├── decorators.py       # @login_required, @permiso_required
    │   ├── forms.py
    │   ├── urls.py
    │   └── apps.py
    ├── gestion_academica_web/  # Configuración Django (settings, urls)
    ├── static/                 # CSS, JS, imágenes
    └── media/                  # Uploads de docentes (excluido del repo)
```

---

## Funcionalidades por rol

### Administrador
- ABM de cursos, cohortes, docentes, estudiantes e instituciones.
- Gestión de niveles educativos y tipos de contratación.
- Asignación de roles y permisos.
- Dashboard con KPIs globales.

### Tesorero
- Cola de validación financiera de pagos en revisión.
- Verificación / rechazo de pagos de estudiantes (con motivo).
- Gestión de pagos a docentes.
- KPIs: cobrado del mes, en revisión, vencidos, pagos docentes pendientes.

### Docente
- Calendario de sesiones (FullCalendar).
- Inicio / finalización de sesiones y marcado de asistencia.
- Carga de materiales por cohorte.
- Creación de tareas y revisión de entregas de estudiantes.
- Reporte "Mi Salario" con ledger por cohorte y horas verificadas.

### Estudiante
- Catálogo público de cursos e inscripción.
- Mi portal: próximas sesiones, tareas pendientes, materiales recientes.
- Mis pagos (alertas de vencidos y próximos).
- Entrega de tareas con archivo + comentario.
- Notificaciones in-app (campana en la barra superior).

---

## Comandos útiles

```bash
# Verificar configuración del proyecto
python manage.py check

# Levantar servidor en otro puerto
python manage.py runserver 8080

# Ingresar al shell de Django
python manage.py shell

# Recrear la BD desde cero (CUIDADO: borra todos los datos)
rm gestion_academica.db
python database.py
```

---

## Notas técnicas

- Los modelos usan `Meta: managed = False` → el esquema **no se gestiona** con `makemigrations`, sino con el script `database.py`.
- Las modificaciones al esquema entre sprints (`ALTER TABLE …`) se ejecutan manualmente; consultar el historial Git para detalle.
- La autenticación es **basada en sesión** (no usa `django.contrib.auth.User`): usa los modelos `Usuario`, `Rol`, `Permiso`.
- En desarrollo, los emails se imprimen en la consola (`console.EmailBackend`); para producción, descomentar el bloque SMTP en `settings.py`.
- La `SECRET_KEY` actual es de desarrollo. **Antes de desplegar a producción**, externalizarla a una variable de entorno.

---

## Equipo

| Integrante | Rol | Contacto |
|---|---|---|
| Ana Villalba | Desarrollo full-stack | annmartinez183@fpuna.edu.py |

---

## Estado del proyecto

- **Sprint actual:** Sprint 5
- **Última línea base:** commit `0745883` — *Sprint 5* — 2026-05-28
- **Repositorio:** https://github.com/annamartinezPY/Gestion-Academica

---

## Licencia

Proyecto académico — uso educativo (FPUNA, Ingeniería de Software II, 2026).
