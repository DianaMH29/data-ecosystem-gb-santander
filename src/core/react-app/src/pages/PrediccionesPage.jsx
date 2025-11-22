import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { TimeSeriesChart, BarChartComponent } from "@/components/charts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";
import { prediccionesService, filtrosService } from "@/services/endpoints";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Brain,
} from "lucide-react";

function AlertCard({ alert }) {
  const getAlertColor = (nivel) => {
    switch (nivel) {
      case "CRÍTICO":
        return "destructive";
      case "ALTO":
        return "warning";
      default:
        return "secondary";
    }
  };

  return (
    <div className="flex items-center justify-between p-3 rounded-lg border bg-card">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{alert.municipio}</span>
          <Badge variant={getAlertColor(alert.nivel_alerta)} className="text-xs">
            {alert.nivel_alerta}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Predicción: {formatNumber(Math.round(alert.prediccion))} |
          Aumento: {alert.porcentaje_aumento?.toFixed(1)}%
        </p>
      </div>
      <AlertTriangle
        className={`h-5 w-5 ${
          alert.nivel_alerta === "CRÍTICO"
            ? "text-destructive"
            : "text-yellow-500"
        }`}
      />
    </div>
  );
}

function TrendIndicator({ tendencia, porcentaje }) {
  const Icon =
    tendencia === "AUMENTO"
      ? TrendingUp
      : tendencia === "DISMINUCIÓN"
      ? TrendingDown
      : Minus;
  const color =
    tendencia === "AUMENTO"
      ? "text-red-500"
      : tendencia === "DISMINUCIÓN"
      ? "text-green-500"
      : "text-muted-foreground";

  return (
    <div className={`flex items-center gap-1 ${color}`}>
      <Icon className="h-4 w-4" />
      <span className="text-sm font-medium">
        {porcentaje > 0 ? "+" : ""}
        {porcentaje?.toFixed(1)}%
      </span>
    </div>
  );
}

export default function PrediccionesPage() {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedMunicipio, setSelectedMunicipio] = useState("Bucaramanga");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [chartLoading, setChartLoading] = useState(false);

  const [serieData, setSerieData] = useState([]);
  const [comparativa, setComparativa] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [resumen, setResumen] = useState(null);

  // Load filters
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const res = await filtrosService.getResumen();
        setFilters(res);
      } catch (error) {
        console.error("Error loading filters:", error);
      } finally {
        setLoading(false);
      }
    };
    loadFilters();
  }, []);

  // Load predictions data
  useEffect(() => {
    const loadData = async () => {
      try {
        setChartLoading(true);
        const params = selectedCategory
          ? { categoria_delito: selectedCategory }
          : {};

        const [serie, comp, alerts, sum] = await Promise.all([
          prediccionesService.getMunicipio(selectedMunicipio, params),
          prediccionesService.getComparativa(selectedMunicipio),
          prediccionesService.getAlertas({ umbral_aumento: 10 }),
          prediccionesService.getResumen({ anio: 2025 }),
        ]);

        // Transform serie data for chart
        const chartData = (serie?.datos || []).map((item) => ({
          ...item,
          periodo: `${item.anio}-${String(item.mes).padStart(2, "0")}`,
        }));
        setSerieData(chartData);
        setComparativa(comp?.comparativa || []);
        setAlertas(alerts?.alertas || []);
        setResumen(sum);
      } catch (error) {
        console.error("Error loading predictions:", error);
      } finally {
        setChartLoading(false);
      }
    };

    loadData();
  }, [selectedMunicipio, selectedCategory]);

  if (loading) {
    return <LoadingOverlay message="Cargando..." />;
  }

  // Separate historical and predicted data for visualization
  const historicalData = serieData.filter((d) => !d.es_prediccion);
  const predictionData = serieData.filter((d) => d.es_prediccion);

  // Get top predictions
  const topPredictions = resumen?.predicciones?.slice(0, 10) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-8 w-8" />
            Predicciones ML
          </h1>
          <p className="text-muted-foreground">
            Predicciones de delitos basadas en Machine Learning
          </p>
        </div>
        <Badge variant="outline" className="self-start">
          Modelo: Series Temporales
        </Badge>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Selecciona un municipio para ver sus predicciones
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="w-[200px]">
              <label className="text-sm font-medium mb-2 block">Municipio</label>
              <Select
                value={selectedMunicipio}
                onValueChange={setSelectedMunicipio}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar municipio" />
                </SelectTrigger>
                <SelectContent>
                  {filters?.municipios?.filter(mun => mun && mun.trim() !== "").map((mun) => (
                    <SelectItem key={mun} value={mun}>
                      {mun}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-[200px]">
              <label className="text-sm font-medium mb-2 block">Categoría</label>
              <Select
                value={selectedCategory || "all"}
                onValueChange={(val) => setSelectedCategory(val === "all" ? "" : val)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todas las categorías" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {filters?.categorias_delito?.filter(cat => cat && cat.trim() !== "").map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Time Series */}
      <Card>
        <CardHeader>
          <CardTitle>Serie Temporal con Predicciones</CardTitle>
          <CardDescription>
            Datos históricos y predicciones para {selectedMunicipio}
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[400px]">
          <TimeSeriesChart
            data={serieData.slice(-60)}
            loading={chartLoading}
            xField="periodo"
            yField="total_delitos"
          />
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Comparativa */}
        <Card>
          <CardHeader>
            <CardTitle>Comparativa con Histórico</CardTitle>
            <CardDescription>
              Predicciones vs promedio histórico - {selectedMunicipio}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {comparativa && comparativa.length > 0 ? (
              <div className="space-y-4">
                {comparativa.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                  >
                    <div>
                      <p className="font-medium">
                        {item.anio}-{String(item.mes).padStart(2, "0")}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Predicción: {formatNumber(Math.round(item.prediccion))}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Histórico: {formatNumber(Math.round(item.promedio_historico_mes))}
                      </p>
                    </div>
                    <TrendIndicator
                      tendencia={item.tendencia}
                      porcentaje={item.porcentaje_cambio}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No hay datos de comparativa disponibles
              </p>
            )}
          </CardContent>
        </Card>

        {/* Alertas */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Alertas de Predicción
            </CardTitle>
            <CardDescription>
              Municipios con aumento significativo predicho
            </CardDescription>
          </CardHeader>
          <CardContent>
            {alertas.length > 0 ? (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {alertas.slice(0, 10).map((alert, i) => (
                  <AlertCard key={i} alert={alert} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No hay alertas activas
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Predictions */}
      <Card>
        <CardHeader>
          <CardTitle>Top Predicciones 2025</CardTitle>
          <CardDescription>
            Municipios con mayor cantidad de delitos predichos
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[350px]">
          <BarChartComponent
            data={topPredictions.map((p) => ({
              municipio: p.municipio,
              prediccion: Math.round(p.prediccion_delitos),
            }))}
            loading={chartLoading}
            xField="municipio"
            yField="prediccion"
            horizontal
          />
        </CardContent>
      </Card>
    </div>
  );
}
