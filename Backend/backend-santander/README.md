# Atlas al Crimen - Santander Backend

API Backend para el sistema de visualización de datos de seguridad del municipio de Santander.

## 🚀 Instalación

### 1. Crear y activar entorno virtual

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o en Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r backend-santander/requirements.txt
```

### 3. Configuración

Las credenciales de la base de datos se cargan automáticamente desde `confiig_santander.yml`.

## 🏃 Ejecutar el servidor

```bash
cd backend-santander
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentación

Una vez el servidor esté corriendo:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📌 Endpoints Disponibles

### Sección 1 — Geografía
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/geografia/delitos-por-municipio` | Mapa coroplético de delitos totales |
| `GET /api/v1/geografia/tasa-por-municipio` | Mapa coroplético de tasa por 100.000 hab |
| `GET /api/v1/geografia/municipios` | Lista de municipios |
| `GET /api/v1/geografia/categorias-delito` | Categorías de delitos disponibles |

### Sección 2 — Temporal
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/temporal/linea-mensual` | Serie temporal mensual |
| `GET /api/v1/temporal/linea-anual` | Serie temporal anual |
| `GET /api/v1/temporal/por-dia-semana` | Distribución por día de semana |
| `GET /api/v1/temporal/por-hora` | Distribución por hora del día |
| `GET /api/v1/temporal/heatmap-dia-hora` | Heatmap día vs hora |
| `GET /api/v1/temporal/anios-disponibles` | Años disponibles en los datos |

### Sección 3 — Víctimas
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/victimas/por-genero` | Distribución por género |
| `GET /api/v1/victimas/por-grupo-etario` | Distribución por grupo etario |
| `GET /api/v1/victimas/mapa-puntos` | GeoJSON de puntos de víctimas |
| `GET /api/v1/victimas/genero-por-delito` | Género por tipo de delito |
| `GET /api/v1/victimas/grupo-etario-por-delito` | Grupo etario por tipo de delito |

### Sección 4 — Clima
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/clima/scatter-lluvia-delitos` | Scatter plot lluvia vs delitos |
| `GET /api/v1/clima/barras-categorias-lluvia` | Delitos por categoría de lluvia |
| `GET /api/v1/clima/linea-tiempo-superpuesta` | Serie temporal lluvia + delitos |
| `GET /api/v1/clima/correlacion` | Estadísticas de correlación |
| `GET /api/v1/clima/resumen-precipitacion` | Resumen de precipitación |

## 🔧 Parámetros de Filtrado Comunes

La mayoría de endpoints aceptan estos parámetros:

- `anio`: Filtrar por año (ej: 2023)
- `categoria_delito`: Tipo de delito (ej: HURTO, HOMICIDIO)
- `codigo_dane`: Código DANE del municipio

## 📊 Estructura del Proyecto

```
Backend/
├── venv/                      # Entorno virtual
├── confiig_santander.yml      # Configuración de BD
└── backend-santander/
    ├── main.py                # Aplicación principal FastAPI
    ├── requirements.txt       # Dependencias
    └── app/
        ├── __init__.py
        ├── config.py          # Carga configuración desde YAML
        ├── database.py        # Conexión SQLAlchemy
        ├── models/            # Modelos SQLAlchemy
        │   ├── municipios.py
        │   ├── demografia.py
        │   ├── seguridad.py
        │   ├── clima.py
        │   └── ...
        └── routers/           # Endpoints por sección
            ├── geografia.py
            ├── temporal.py
            ├── victimas.py
            └── clima.py
```

## 🗃️ Base de Datos

El sistema espera una base de datos PostgreSQL con PostGIS habilitado, con las siguientes tablas:

- `master_municipios`: Geometría y datos de municipios
- `master_demografia`: Población por año
- `fact_seguridad`: Eventos delictivos
- `fact_clima`: Precipitación diaria

## 📝 Notas

- Los endpoints de geografía retornan GeoJSON listo para visualizar en mapas
- La tasa se calcula como: `(delitos / población) × 100,000`
- Los datos de víctimas dependen de las columnas `genero_victima` y `grupo_etario`
- La correlación lluvia-delitos usa el coeficiente de Pearson
