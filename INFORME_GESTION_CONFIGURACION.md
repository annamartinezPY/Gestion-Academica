# Informe de Gestión de la Configuración
## Actividad #05 — Ingeniería de Software II

---

## 1. Datos generales del proyecto

| Campo | Valor |
|---|---|
| **Nombre del proyecto** | Plataforma de Gestión Académica |
| **Integrantes del equipo** | Ana Villalba (annmartinez183@fpuna.edu.py) |
| **Sprint actual** | Sprint 5 |
| **Fecha del informe** | 2026-05-28 |
| **Link del repositorio** | https://github.com/annamartinezPY/Gestion-Academica.git |
| **Link al tablero Jira / gestor de tareas** | *(a completar por el equipo)* |
| **Stack tecnológico** | Python 3.14 · Django 6.0.4 · SQLite · Bootstrap 5 · FullCalendar 6.1.11 |
| **Arquitectura** | MVC sobre Django (capa `views/`, `models.py`, `templates/`) con RBAC por roles |

---

## 2. Identificación de elementos de configuración

| # | Elemento de configuración | Ubicación / Identificador | Responsable | Versionado en Git |
|---|---|---|---|---|
| 1 | **Código fuente Django (app principal)** | `gestion_academica_web/academica/` (views, models, forms, decorators, templates) | Ana Villalba | Sí |
| 2 | **Modelo de datos (ORM)** | `gestion_academica_web/academica/models.py` (~30 modelos `managed=False`) | Ana Villalba | Sí |
| 3 | **Capa de presentación (templates)** | `gestion_academica_web/academica/templates/` (≈ 25 carpetas / >60 plantillas Bootstrap) | Ana Villalba | Sí |
| 4 | **Configuración del proyecto Django** | `gestion_academica_web/gestion_academica_web/settings.py`, `urls.py`, `wsgi.py`, `asgi.py` | Ana Villalba | Sí |
| 5 | **Esquema de base de datos / scripts** | `database.py` (raíz del repo, scripts de creación e inserción) + migraciones inline `ALTER TABLE` ejecutadas vía shell | Ana Villalba | Parcial (`database.py` sí; scripts ALTER inline NO) |
| 6 | **Archivos estáticos y media** | `gestion_academica_web/static/`, `gestion_academica_web/media/` | Ana Villalba | Estáticos sí; media excluida vía `.gitignore` |
| 7 | **Documentación de control de versiones** | `.gitignore` | Ana Villalba | Sí |
| 8 | **Evidencias de sprint (capturas, informes)** | *(no presentes en el repo — externos)* | Equipo | No |
| 9 | **Repositorio / herramienta de versionado** | GitHub — `annamartinezPY/Gestion-Academica` | Ana Villalba (owner) | — |
| 10 | **Base de datos SQLite local** | `gestion_academica.db`, `db.sqlite3` | Cada desarrollador en su entorno | No (excluidas vía `.gitignore`, correcto) |

---

## 3. Revisión del repositorio Git

**Link al repositorio:** https://github.com/annamartinezPY/Gestion-Academica.git
**Plataforma:** GitHub
**Visibilidad:** *(verificar — público / privado)*

### 3.1 Estructura de carpetas (resumen del repo)

```
Proyecto Tema 1/
├── .gitignore                  ✔ Versionado y bien configurado
├── manage.py                   ✔ (versión legacy raíz — proyecto Django previo)
├── database.py                 ✔ Script de creación de esquema SQLite
├── main.py                     ✔ Entrypoint legacy (consola)
├── controllers/                ✔ Controladores MVC (versión legacy consola)
├── models/                     ✔ Modelos MVC legacy
├── views/                      ✔ Vistas MVC legacy
├── menus/                      ✔ Menús consola
├── portales/                   ✔ Portales por rol (legacy)
├── ui/                         ✔ Helpers de UI consola
├── static/, templates/, core/  ✔ Restos de proyecto Django previo
└── gestion_academica_web/      ✔ Proyecto Django actual (PRINCIPAL)
    ├── manage.py
    ├── academica/              ← App Django de negocio
    │   ├── views/              (24 módulos: dashboard, pagos, asistencia, …)
    │   ├── templates/          (>25 carpetas con plantillas Bootstrap)
    │   ├── templatetags/       (filtros guarani, etc.)
    │   ├── models.py           (~30 modelos managed=False)
    │   ├── forms.py
    │   ├── urls.py
    │   ├── decorators.py       (RBAC: @permiso_required)
    │   ├── context_processors.py (notificaciones globales)
    │   └── apps.py
    ├── gestion_academica_web/  ← settings.py, urls.py raíz
    ├── static/                 (CSS, JS, imágenes)
    └── media/                  (uploads — excluido del repo)
```

### 3.2 Archivos clave detectados

| Archivo | Estado | Observación |
|---|---|---|
| `README.md` | ❌ **No existe** | Falta documentación de instalación y arranque |
| `.gitignore` | ✔ Existe | Excluye `__pycache__`, `*.sqlite3`, `*.db`, `.venv`, `.vscode`, `.idea`, `media/` |
| `requirements.txt` | ❌ **No existe** | Falta archivo de dependencias para reproducir el entorno |
| `.env.example` | ❌ **No existe** | No hay plantilla de variables de entorno |
| `database.py` | ✔ Existe en raíz | Script de creación de esquema + inserciones |
| Scripts SQL (`*.sql`) | ❌ **No existen** | Migraciones se ejecutan inline (no quedan archivadas) |
| Carpeta `migrations/` Django | ❌ **No existe** | Modelos `managed=False`; no se usa el sistema de migraciones de Django |
| Tags / releases | ❌ **Ninguno** | No hay versionado semántico de baselines |

### 3.3 Hallazgos

- ✅ La estructura del proyecto Django (`gestion_academica_web/academica/`) está bien modularizada: vistas separadas por dominio (asistencia, pagos, tareas, etc.).
- ✅ El `.gitignore` está correctamente configurado: las bases de datos locales y los archivos generados (`__pycache__`, `.venv`) no entran al repo (commit `c59a2f4` realizó esa limpieza).
- ⚠️ Conviven la **versión legacy** (consola, carpetas `controllers/`, `models/`, `views/`, `menus/` en la raíz) y la **versión Django web** (`gestion_academica_web/`). Esto puede confundir a un nuevo integrante.
- ⚠️ No hay `README.md` ni `requirements.txt` → no es trivial levantar el proyecto sin instrucciones verbales.

---

## 4. Control de versiones y estrategia de ramas

### 4.1 Datos del repositorio

| Campo | Valor |
|---|---|
| Sistema de control de versiones | Git |
| Plataforma de hospedaje | GitHub |
| URL remota (`origin`) | https://github.com/annamartinezPY/Gestion-Academica.git |
| Rama principal | `main` |
| Total de ramas activas | **1** (sólo `main`) |
| Total de commits (rama `main`) | **10** |
| Último commit | `0745883` — *"Sprint 5"* — Ana Villalba — 2026-05-28 |
| Commits firmados (GPG) | No |
| Pull Requests cerrados | 1 (PR #1 `python-to-django-frontend` → `main`, abril 2026) |
| Tags / releases | **0** |
| Frecuencia de commits | Por hito de sprint (≈ 1 commit grande por sprint) |

#### 4.1.1 Commits relevantes

| Commit | Fecha | Autor | Mensaje | Hito |
|---|---|---|---|---|
| `0745883` | 2026-05-28 | Ana Villalba | Sprint 5 | Sprint 5 (asistencia + materiales + tareas + tesorero + notificaciones) |
| `c59a2f4` | 2026-05-24 | Ana Villalba | Limpieza: remover archivos generados y bases de datos | Higiene del repo |
| `696e670` | 2026-05-24 | Ana Villalba | Sprint 4: gestión de instituciones, perfil docente, niveles educativos, password reset | Sprint 4 |
| `9f874b6` | 2026-04-08 | Ana Villalba | Se agregan templates html | Sprint 3 |
| `f947dc1` | 2026-04-07 | Ana Villalba | Desarrollo Front + templates | Sprint 3 |
| `5b292af` | 2026-04-07 | Ana Villalba | Se agrega front con Django | Migración consola → web |
| `6b29057` | 2026-04-07 | annamartinezPY | Merge pull request #1 from `python-to-django-frontend` | Merge frontend |
| `d8921ec` | 2026-04-07 | Ana Villalba | Segundo Avance: gestión de pagos e inscripciones | Sprint 2 |

#### 4.1.2 Commits por integrante

| Autor | Commits | Observación |
|---|---|---|
| Ana Villalba | 7 | Desarrolladora principal |
| v0 | 2 | Generación inicial de andamiaje Django (herramienta externa) |
| annamartinezPY | 1 | Cuenta de la propietaria del repositorio en GitHub (merge del PR #1) |

### 4.2 Estrategia de ramas

**Estrategia actual:** *trunk-based simplificada* — todo el desarrollo se commitea directamente sobre `main`. Históricamente existió una rama temporal `python-to-django-frontend` (mergeada vía PR #1 y eliminada).

| Rama | Propósito | Estado actual |
|---|---|---|
| `main` | Rama principal de integración y entrega | Activa (única rama) |
| `python-to-django-frontend` | Migración de versión consola a Django (histórica) | Eliminada tras merge (PR #1) |

**Convenciones de nombrado de ramas:** no documentadas (sólo se observa una rama histórica `python-to-django-frontend`).

> **Mejora propuesta (Sección 6):** adoptar una estrategia tipo *GitHub Flow* o *GitFlow* ligero —`feature/<nombre-corto>`, `fix/<nombre>`, mergeo por PR con revisión— para aislar el trabajo de cada historia de usuario y permitir trabajar en paralelo.

---

## 5. Definición de la línea base (versión estable)

Una **línea base** es un snapshot del producto en un momento dado, sobre el cual se acuerda no hacer modificaciones directas sin pasar por control de cambios. En este proyecto, se define la siguiente línea base como **versión estable de cierre de Sprint 5**:

| Campo | Valor |
|---|---|
| **Nombre de la línea base** | `v0.5-sprint5` *(propuesta — pendiente de crear tag en GitHub)* |
| **Fecha de la línea base** | 2026-05-28 |
| **Sprint correspondiente** | Sprint 5 |
| **Rama / Tag / Commit** | Rama `main` · Commit `0745883f4402805e0081cac6df390678b8d25d9c` |
| **Responsable** | Ana Villalba |
| **Funcionalidades incluidas** | RBAC + login y reseteo de contraseña · ABM cursos, cohortes, docentes, estudiantes · Inscripciones · Pagos de estudiantes (con flujo `pendiente → en_revision → aprobado/rechazado`) · Pagos de docentes y reporte "Mi Salario" con ledger · Asistencia (sesiones planificada/en_curso/finalizada) · Materiales · Tareas con entregas de estudiantes · Calendario FullCalendar por cohorte · Dashboards diferenciados por rol (admin/docente/estudiante/tesorero) · Sistema de notificaciones in-app · Catálogo público de cursos |
| **Funcionalidades fuera de alcance** | Reportes BI avanzados · Notificaciones por email · API REST pública · Tests automatizados |
| **Comando para reproducirla** | `git checkout 0745883` (o `git checkout tags/v0.5-sprint5` una vez creado el tag) |
| **Estado** | ✅ Aprobada como línea base de Sprint 5 |

**Acción inmediata recomendada:** crear el tag de manera explícita:

```bash
git tag -a v0.5-sprint5 0745883 -m "Línea base Sprint 5: tesorero, notificaciones, asistencia, materiales, tareas"
git push origin v0.5-sprint5
```

---

## 6. Auditoría rápida de configuración

Evaluación de 12 criterios de gestión de la configuración. Para cada uno: ✅ Sí (cumple), 🟡 Parcial (cumple parcialmente), ❌ No (no cumple).

| # | Criterio | Cumple | Evidencia / Observación |
|---|---|:-:|---|
| 1 | El proyecto está versionado en un sistema de control de versiones | ✅ | Repositorio Git público en GitHub |
| 2 | Todos los integrantes del equipo realizan commits | 🟡 | Sólo Ana Villalba commitea código real. `v0` es una herramienta externa y `annamartinezPY` es la cuenta GitHub de la owner (mismo equipo) |
| 3 | Existe una rama principal estable (`main`) | ✅ | `main` es la única rama activa, siempre desplegable |
| 4 | Existe estrategia de ramas para nuevas funcionalidades | ❌ | No se usan ramas `feature/*`. Todo va directo a `main` |
| 5 | Los mensajes de commit son descriptivos y consistentes | 🟡 | Los recientes describen el sprint ("Sprint 4", "Sprint 5") pero faltan referencias a HU o ticket Jira |
| 6 | Existen tags / releases para marcar versiones estables | ❌ | `git tag` retorna vacío. Ninguna línea base está congelada formalmente |
| 7 | El repositorio incluye `README.md` con instrucciones de instalación | ❌ | No existe `README.md` en la raíz |
| 8 | Existe un archivo de dependencias reproducible (`requirements.txt`, `pyproject.toml`) | ❌ | No se incluye lista de dependencias. Recrear el entorno requiere conocimiento previo |
| 9 | `.gitignore` está configurado y excluye archivos generados | ✅ | Excluye `__pycache__/`, `*.pyc`, `*.sqlite3`, `*.db`, entornos virtuales, `media/`, IDE |
| 10 | No se commitean credenciales ni archivos sensibles | ✅ | `settings.py` contiene `SECRET_KEY` de desarrollo, pero **debería externalizarse en producción** vía variables de entorno |
| 11 | Los cambios al esquema de BD están versionados | 🟡 | `database.py` (creación inicial) está versionado, pero los `ALTER TABLE` aplicados en sprints posteriores se ejecutaron inline y **no quedaron archivados como scripts** |
| 12 | Existen evidencias de revisión por pares (Pull Requests con review) | 🟡 | Se observa 1 PR histórico (`#1` mergeado en abril), pero no es práctica habitual |

**Resumen cuantitativo:**

| Resultado | Cantidad | Porcentaje |
|---|:-:|:-:|
| ✅ Cumple | 4 | 33 % |
| 🟡 Parcial | 4 | 33 % |
| ❌ No cumple | 4 | 33 % |

### 6.1 Conclusión

#### Fortalezas

- 🟢 **Repositorio limpio y disciplinado:** el `.gitignore` está bien diseñado y un commit explícito (`c59a2f4`) reforzó la higiene al remover `__pycache__/` y bases de datos locales.
- 🟢 **Estructura modular del proyecto Django:** la app `academica/` separa vistas por dominio (asistencia, pagos, tareas, materiales, notificaciones…), facilitando la mantenibilidad y el trabajo en paralelo a futuro.
- 🟢 **Trazabilidad por sprint:** los commits están etiquetados con el sprint correspondiente, lo que permite mapear cada hito del cronograma con un punto concreto del historial.
- 🟢 **No hay credenciales productivas comprometidas:** ningún `.env` ni base de datos de producción fue commiteada.

#### Aspectos a mejorar

- 🟠 **Falta de `README.md` y `requirements.txt`:** un nuevo integrante no puede levantar el proyecto sin instrucciones verbales del equipo.
- 🟠 **Estrategia de ramas inexistente:** todo el trabajo se concentra en `main`. No permite trabajar en paralelo ni hacer code review antes del merge.
- 🟠 **Líneas base no congeladas con tags:** aunque se identifican commits que cierran cada sprint, no existen `tags` ni *releases* que congelen formalmente esas versiones para auditoría o rollback.
- 🟠 **Migraciones de BD inline no documentadas:** los `ALTER TABLE` aplicados en Sprint 3, 4 y 5 (por ejemplo, columnas nuevas en `notificaciones`) se ejecutaron en consola y **no quedaron archivados** como scripts versionados. Reproducir la BD desde cero requiere reconstruir manualmente esos cambios.
- 🟠 **Coexistencia legacy + Django web:** la raíz del repo aún contiene la versión consola anterior (`controllers/`, `menus/`, `portales/`, `main.py`). Conviene archivarla en una rama `archive/legacy-cli` y dejar `main` sólo con el proyecto Django actual.

#### Acciones concretas (próximos 7 días)

1. **Crear `README.md`** con: descripción, requisitos, comandos de arranque (`pip install -r requirements.txt`, `python manage.py runserver`), credenciales de usuarios de prueba y matriz de roles.
2. **Generar `requirements.txt`** ejecutando `pip freeze > requirements.txt` desde el entorno virtual y commitearlo.
3. **Crear tag de línea base** `v0.5-sprint5` apuntando al commit `0745883` y publicarlo como Release en GitHub.
4. **Adoptar GitHub Flow:** a partir del Sprint 6, abrir ramas `feature/<historia>` y mergear vía Pull Request (aunque el equipo sea reducido, sirve como evidencia de control).
5. **Archivar las migraciones de BD pendientes** como un script `migrations/sprint5_alters.sql` versionado, de modo que reconstruir la BD desde `database.py` + los scripts incrementales sea reproducible.
6. **Mover `SECRET_KEY` y `DEBUG`** a un archivo `.env` (excluido por `.gitignore`) y agregar `.env.example` con valores ficticios.
7. **Archivar el código legacy** moviéndolo a una rama `archive/cli-version` y removiéndolo de `main` para que la raíz refleje únicamente el proyecto Django vigente.

---

*Informe generado el 2026-05-28 con base en el estado del repositorio en el commit `0745883` (HEAD de `main`).*
