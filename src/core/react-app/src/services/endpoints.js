import api from "./api";

export const geografiaService = {
  // Obtener delitos por municipio con geometría GeoJSON
  getDelitosPorMunicipio: (params = {}) => {
    return api.get("/geografia/delitos-por-municipio", { params });
  },

  // Obtener tasa de delitos por 100k habitantes
  getTasaPorMunicipio: (params = {}) => {
    return api.get("/geografia/tasa-por-municipio", { params });
  },

  // Lista de municipios (sin geometría)
  getMunicipios: () => {
    return api.get("/geografia/municipios");
  },

  // Categorías de delito disponibles
  getCategoriasDelito: () => {
    return api.get("/geografia/categorias-delito");
  },
};

export const temporalService = {
  // Serie temporal mensual
  getLineaMensual: (params = {}) => {
    return api.get("/temporal/linea-mensual", { params });
  },

  // Serie temporal anual
  getLineaAnual: (params = {}) => {
    return api.get("/temporal/linea-anual", { params });
  },

  // Distribución por día de la semana
  getPorDiaSemana: (params = {}) => {
    return api.get("/temporal/por-dia-semana", { params });
  },

  // Tendencia semanal
  getTendenciaSemanal: (params = {}) => {
    return api.get("/temporal/tendencia-semanal", { params });
  },

  // Comparativa anual
  getComparativaAnual: (params = {}) => {
    return api.get("/temporal/comparativa-anual", { params });
  },

  // Distribución por modalidad
  getPorModalidad: (params = {}) => {
    return api.get("/temporal/por-modalidad", { params });
  },

  // Distribución por zona
  getPorZona: (params = {}) => {
    return api.get("/temporal/por-zona", { params });
  },

  // Años disponibles
  getAniosDisponibles: () => {
    return api.get("/temporal/anios-disponibles");
  },
};

export const victimasService = {
  // Distribución por género
  getPorGenero: (params = {}) => {
    return api.get("/victimas/por-genero", { params });
  },

  // Distribución por grupo etario
  getPorGrupoEtario: (params = {}) => {
    return api.get("/victimas/por-grupo-etario", { params });
  },

  // Puntos georreferenciados
  getMapaPuntos: (params = {}) => {
    return api.get("/victimas/mapa-puntos", { params });
  },

  // Distribución por arma/medio
  getPorArmaMedio: (params = {}) => {
    return api.get("/victimas/por-arma-medio", { params });
  },

  // Distribución por clase de sitio
  getPorClaseSitio: (params = {}) => {
    return api.get("/victimas/por-clase-sitio", { params });
  },

  // Género por delito
  getGeneroPorDelito: (params = {}) => {
    return api.get("/victimas/genero-por-delito", { params });
  },

  // Grupo etario por delito
  getGrupoEtarioPorDelito: (params = {}) => {
    return api.get("/victimas/grupo-etario-por-delito", { params });
  },
};

export const climaService = {
  // Scatter plot lluvia vs delitos
  getScatterLluviaDelitos: (params = {}) => {
    return api.get("/clima/scatter-lluvia-delitos", { params });
  },

  // Barras por categorías de lluvia
  getBarrasCategoriasLluvia: (params = {}) => {
    return api.get("/clima/barras-categorias-lluvia", { params });
  },

  // Línea de tiempo superpuesta
  getLineaTiempoSuperpuesta: (params = {}) => {
    return api.get("/clima/linea-tiempo-superpuesta", { params });
  },

  // Correlación
  getCorrelacion: (params = {}) => {
    return api.get("/clima/correlacion", { params });
  },

  // Resumen precipitación
  getResumenPrecipitacion: (params = {}) => {
    return api.get("/clima/resumen-precipitacion", { params });
  },
};

export const filtrosService = {
  // Obtener todos los filtros en una sola llamada
  getResumen: () => {
    return api.get("/filtros/resumen");
  },

  getMunicipios: () => api.get("/filtros/municipios"),
  getCategoriasDelito: () => api.get("/filtros/categorias-delito"),
  getGeneros: () => api.get("/filtros/generos"),
  getGruposEtarios: () => api.get("/filtros/grupos-etarios"),
  getZonas: () => api.get("/filtros/zonas"),
  getArmasMedios: () => api.get("/filtros/armas-medios"),
  getModalidades: () => api.get("/filtros/modalidades"),
  getAnios: () => api.get("/filtros/anios"),
  getRangoFechas: () => api.get("/filtros/rango-fechas"),
};

export const chatbotService = {
  // Consulta en lenguaje natural
  consultar: (pregunta, contexto = "") => {
    return api.post("/chatbot/consultar", { pregunta, contexto });
  },

  // Sugerencias de preguntas
  getSugerencias: () => {
    return api.get("/chatbot/sugerencias");
  },

  // Capacidades del chatbot
  getCapacidades: () => {
    return api.get("/chatbot/capacidades");
  },

  // Estadísticas generales
  getEstadisticas: () => {
    return api.get("/chatbot/estadisticas");
  },
};

export const prediccionesService = {
  // Serie temporal de municipio con predicciones
  getMunicipio: (municipio, params = {}) => {
    return api.get(`/predicciones/municipio/${municipio}`, { params });
  },

  // Resumen de predicciones
  getResumen: (params = {}) => {
    return api.get("/predicciones/resumen", { params });
  },

  // Comparativa de predicciones
  getComparativa: (municipio) => {
    return api.get(`/predicciones/comparativa/${municipio}`);
  },

  // Alertas de predicciones
  getAlertas: (params = {}) => {
    return api.get("/predicciones/alertas", { params });
  },
};
