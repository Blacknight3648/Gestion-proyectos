# Sistema de Gestión de Proyectos & Control del Cambio (SGP)

Sistema integral de gestión de proyectos desarrollado en **Django** y **Python**, diseñado bajo los estándares de gestión de proyectos (EVM, PMBOK y Prosci). Incluye autenticación con control de acceso por roles (**Okta / Auth0 SSO** y modo local), estructura de desglose del trabajo (**EDT / WBS con Regla del 100%**), cálculo de precedencias dinámicas en **Carta Gantt**, gestión de recursos y costos con **detector automático de sobreasignaciones**, motor parametrizable de **20 KPIs** y un módulo formal de **Gestión del Cambio de 10 etapas con propagación automática**.

---

## ¿Para qué sirve este proyecto?

Este sistema centraliza el ciclo de vida completo de proyectos corporativos:
1. **Control de Acceso por Roles (RBAC)**: Distinción de privilegios entre *Director de Proyecto* (crear, editar, aprobar cambios y poblar datos) y *Miembro de Equipo / Cliente* (modo solo lectura).
2. **EDT / WBS Jerárquico**: Estructura de 3 niveles (*Etapas* `1.0`, *Actividades* `1.1` y *Subactividades* `1.1.1`) que valida matemáticamente la **Regla del 100%** para evitar duplicidad de costos y tiempos.
3. **Gestión de Recursos y Tarifas**: Control de tarifas horarias por tipo de recurso (Humanos, Materiales, Equipamiento, Licencias) y detección en tiempo real de sobreasignación de profesionales cuando superan su jornada diaria máxima (8 hrs/día).
4. **Carta Gantt Dinámica**: Soporte estricto para los 4 tipos de dependencias (`FS`, `SS`, `FF`, `SF`) y desfases (*lags* y *leads*), con prevención de dependencias circulares y recálculo automático en cascada de fechas planificadas vs. reales.
5. **Motor Configurable de KPIs**: 
   * **8 KPIs de Proyecto e Hitos**: SPI, CPI, Variación de Costo (CV), Variación de Plazo (SV), % Avance Ponderado, % Hitos Cumplidos, Tareas en Plazo y Desvío Presupuestario.
   * **12 KPIs de Gestión del Cambio**: Total Solicitudes, Tasa de Aprobación, Tasa de Rechazo, Tiempo de Ciclo, Impacto en Plazo, Impacto en Presupuesto, Prioridad Alta, Tasa de Propagación, Adopción Cultural, Satisfacción, Trazabilidad de 10 Etapas y Resistencia al Cambio.
6. **Módulo de Gestión del Cambio (RFC)**: Flujo formal de 10 etapas (desde Identificación hasta Adopción Cultural). Al aprobar un cambio, el sistema **propaga automáticamente** el impacto en días a la Carta Gantt y el impacto financiero al presupuesto del proyecto.
7. **Tableros de Comando Duales**:
   * **Tablero 1 (Operativo)**: Vista ejecutiva del proyecto, avance físico, EVM, hitos y alertas.
   * **Tablero 2 (Estratégico)**: Embudo de solicitudes del cambio, métricas de adopción y tiempos de ciclo CCB.

---

## Requisitos previos

Para ejecutar este proyecto en tu computadora necesitas:

* **Python 3.10 o superior** (compatible con Python 3.14).
* **Git** instalado.
* Conexión a internet (para descargar librerías y recursos visuales CDN).

---

## Guía de Instalación y Puesta en Marcha

Sigue estos comandos en tu terminal de PowerShell:

### 1. Clonar el repositorio y entrar a la carpeta
```powershell
git clone https://github.com/Blacknight3648/Gestion-proyectos.git
cd "Gestion-proyectos\webappexample"
```

### 2. Instalar dependencias
Instala los paquetes requeridos por el proyecto (`django`, `authlib`, `python-dotenv`, `requests`):
```powershell
py -m pip install -r requirements.txt
```

### 3. Configurar variables de entorno (`.env`) y aplicación en Okta / Auth0
El archivo `.env` se encuentra en la carpeta `webappexample/` y requiere las credenciales OIDC reales de tu tenant Okta / Auth0:
```env
AUTH0_CLIENT_ID=tu_client_id_aqui
AUTH0_CLIENT_SECRET=tu_client_secret_aqui
AUTH0_DOMAIN=tu_dominio.us.auth0.com
```

En el panel **Application Settings** de Okta / Auth0 configura las siguientes URIs autorizadas:
* **Allowed Callback URLs**: `http://localhost:3000/callback`
* **Allowed Logout URLs**: `http://localhost:3000, http://localhost:3000/login/`
* **Allowed Web Origins**: `http://localhost:3000`

Para inyectar los roles asignados en **User Management > Roles** (`Director` o `Miembro`) dentro del token JWT firmado, agrega un **Post-Login Action** en **Actions > Triggers > Post-Login**:
```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://sgp.proyectos/roles';
  if (event.authorization) {
    api.idToken.setCustomClaim(namespace, event.authorization.roles);
    api.accessToken.setCustomClaim(namespace, event.authorization.roles);
  }
};
```

### 4. Aplicar migraciones a la Base de Datos
Crea las tablas relacionales en la base de datos local SQLite:
```powershell
py manage.py migrate
```

### 5. Iniciar el servidor de desarrollo
Ejecuta el servidor en el puerto 3000:
```powershell
py manage.py runserver 3000
```

Abre tu navegador en:
👉 **`http://localhost:3000`**

---

## Cómo utilizar el sistema

### 1. Inicio de Sesión Obligatorio vía Okta SSO (`/login/`)
Al ingresar al sistema serás redirigido obligatoriamente a la pantalla de autenticación OIDC:
* Haz clic en **"Iniciar Sesión con Okta (SSO)"** para autenticarte con tu correo y contraseña en el portal seguro de Okta / Auth0.
* El rol se determina **exclusivamente desde el token firmado por Okta** (nunca seleccionable por el usuario):
  * **Director de Proyecto**: Permite crear proyectos, poblar el caso demo, modificar tareas, asignar recursos y aprobar/propagar cambios.
  * **Miembro de Equipo (Rol por defecto / Menor Privilegio)**: Permite consultar tableros, WBS, recursos y cronogramas en modo estricto de solo lectura.

### 2. Estado Inicial Limpio (Sin proyectos)
El sistema inicia intencionalmente con **0 proyectos registrados**:
* **Crear Proyecto**: Haz clic en el botón `+ Crear Proyecto` para iniciar un proyecto en blanco.
* **Cargar Caso de Prueba (Demo)**: Haz clic en el botón amarillo para poblar instantáneamente el escenario completo de evaluación:
  * 4 Etapas (25% c/u - Regla 100%)
  * 12 Actividades y 20 Subactividades
  * 4 Precedencias dinámicas (`FS`, `SS`, `FF`, `SF`)
  * 5 Profesionales con tarifas y caso de sobreasignación intencional
  * 6 Hitos y 20 KPIs calculados
  * 5 Solicitudes de cambio en distintas etapas

### 3. Navegación por las Pestañas Principales
* **EDT / WBS**: Explora la jerarquía del proyecto y comprueba los indicadores verdes de la Regla del 100%.
* **Recursos & Costos**: Visualiza las tarifas de los profesionales y las **alertas rojas de sobreasignación** que detallan qué profesional supera las 8 hrs diarias.
* **Carta Gantt**: Visualiza el cronograma interactivo. Puedes cambiar la duración de cualquier tarea para observar el **recálculo en cascada** en tiempo real.
* **Gestión del Cambio**: Registra solicitudes (RFC), avanza por las 10 etapas y presiona **⚡ Propagar** para ver cómo se añaden automáticamente los días al Gantt y el dinero al presupuesto.
* **Tableros 1 y 2**: Monitorea los semáforos (Verde/Amarillo/Rojo) de los KPIs de proyecto y de cambio.

### 4. Verificación de Roles (RBAC)
En la esquina superior derecha del Navbar se muestra permanentemente tu identidad autenticada en Okta junto con el badge inmutable de tu rol (`Rol: Director de Proyecto` o `Rol: Miembro de Equipo`). Para evaluar distintos privilegios, cierra sesión con el botón **Salir** e ingresa en Okta con una cuenta asignada al rol correspondiente.

---

## Estructura del Proyecto

```text
gestion de proyectos/
├── .gitignore                     # Exclusión de archivos sensibles (.env, SQLite, __pycache__)
├── README.md                      # Documentación del sistema
└── webappexample/                 # Proyecto Django principal
    ├── .env                       # Variables de configuración de autenticación
    ├── manage.py                  # CLI de gestión de Django
    ├── requirements.txt           # Dependencias Python
    ├── webappexample/             # Configuración central (settings, urls, views de autenticación)
    └── gestion/                   # Aplicación del núcleo del negocio
        ├── models.py              # Modelos relacionales (WBS, Recursos, Gantt, KPIs, Cambios)
        ├── views.py               # Controladores de vistas y tableros
        ├── urls.py                # Rutas del sistema
        ├── middleware.py          # Middleware de autenticación obligatoria
        ├── services/              # Motores en Python (WBS, Precedencias, Sobreasignación, KPIs, Propagación)
        └── management/commands/   # Comando de seeding de datos para demostración en vivo
```
