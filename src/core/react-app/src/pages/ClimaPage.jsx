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
import { ScatterPlot, BarChartComponent, TimeSeriesChart } from "@/components/charts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";
import { climaService, filtrosService } from "@/services/endpoints";
import { CloudRain, TrendingDown, TrendingUp, Minus, BarChart3 } from "lucide-react";

function CorrelationCard({ correlation }) {
  if (!correlation) return null;

  const { correlacion_pearson, interpretacion, n_observaciones } = correlation;
  const value = correlacion_pearson?.toFixed(4) || 0;
  const isNegative = correlacion_pearson < 0;
  const absValue = Math.abs(correlacion_pearson || 0);

  let variant = "secondary";
  let Icon = Minus;
  if (absValue > 0.3) {
    variant = isNegative ? "success" : "destructive";
    Icon = isNegative ? TrendingDown : TrendingUp;
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Correlación de Pearson</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          <div className="text-3xl font-bold">{value}</div>
          <Badge variant={variant} className="flex items-center gap-1">
            <Icon className="h-3 w-3" />
            {interpretacion}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Basado en {formatNumber(n_observaciones)} observaciones
        </p>
      </CardContent>
    </Card>
  );
}

function PrecipitationSummary({ summary }) {
  if (!summary) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Resumen de Precipitación</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span className="text-sm text-muted-foreground">Días con registro</span>
          <span className="font-medium">{formatNumber(summary.dias_con_registro)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-muted-foreground">Días secos</span>
          <span className="font-medium">{formatNumber(summary.dias_secos)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-muted-foreground">Días con lluvia</span>
          <span className="font-medium">{formatNumber(summary.dias_con_lluvia)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-muted-foreground">Promedio (mm)</span>
          <span className="font-medium">{summary.precipitacion_promedio_mm?.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-muted-foreground">Máxima (mm)</span>
          <span className="font-medium">{summary.precipitacion_maxima_mm?.toFixed(1)}</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ClimaPage() {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedYear, setSelectedYear] = useState("2019");
  const [selectedCategory, setSelectedCategory] = useState("HURTO");
  const [chartLoading, setChartLoading] = useState(false);

  const [scatterData, setScatterData] = useState([]);
  const [barrasData, setBarrasData] = useState([]);
  const [lineaData, setLineaData] = useState([]);
  const [correlacion, setCorrelacion] = useState(null);
  const [resumenPrecip, setResumenPrecip] = useState(null);

  // Años con datos de clima (2005-2019)
  const climaYears = Array.from({ length: 15 }, (_, i) => 2005 + i);

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

  // Load chart data
  useEffect(() => {
    const loadData = async () => {
      try {
        setChartLoading(true);
        const params = {
          anio: parseInt(selectedYear),
          categoria_delito: selectedCategory,
        };

        const [scatter, barras, linea, corr, resumen] = await Promise.all([
          climaService.getScatterLluviaDelitos(params),
          climaService.getBarrasCategoriasLluvia(params),
          climaService.getLineaTiempoSuperpuesta({ ...params, agrupacion: "mensual" }),
          climaService.getCorrelacion(params),
          climaService.getResumenPrecipitacion({ anio: parseInt(selectedYear) }),
        ]);

        setScatterData(scatter || []);
        setBarrasData(barras || []);
        setLineaData(linea?.data || []);
        setCorrelacion(corr);
        setResumenPrecip(resumen);
      } catch (error) {
        console.error("Error loading data:", error);
      } finally {
        setChartLoading(false);
      }
    };

    loadData();
  }, [selectedYear, selectedCategory]);

  if (loading) {
    return <LoadingOverlay message="Cargando..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <CloudRain className="h-8 w-8" />
            Correlación Climática
          </h1>
          <p className="text-muted-foreground">
            Análisis de la relación entre precipitación y delitos
          </p>
        </div>
        <Badge variant="outline" className="self-start">
          Datos históricos: 2005 - 2019
        </Badge>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Los datos climáticos están disponibles para el período 2005-2019
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="w-[160px]">
              <label className="text-sm font-medium mb-2 block">Año</label>
              <Select value={selectedYear} onValueChange={setSelectedYear}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar año" />
                </SelectTrigger>
                <SelectContent>
                  {climaYears.map((year) => (
                    <SelectItem key={year} value={String(year)}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-[200px]">
              <label className="text-sm font-medium mb-2 block">Categoría</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar categoría" />
                </SelectTrigger>
                <SelectContent>
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

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <CorrelationCard correlation={correlacion} />
        <PrecipitationSummary summary={resumenPrecip} />
      </div>

      {/* Scatter Plot */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Scatter Plot: Precipitación vs Delitos
          </CardTitle>
          <CardDescription>
            Relación entre milímetros de lluvia y cantidad de delitos por día - {selectedYear}
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[400px]">
          <ScatterPlot
            data={scatterData}
            loading={chartLoading}
            xField="precipitacion_mm"
            yField="total_delitos"
            xLabel="Precipitación (mm)"
            yLabel="Total Delitos"
          />
        </CardContent>
      </Card>

      {/* Bar and Line Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Delitos por Categoría de Lluvia</CardTitle>
            <CardDescription>
              Promedio de delitos según intensidad de precipitación - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <BarChartComponent
              data={barrasData}
              loading={chartLoading}
              xField="categoria_lluvia"
              yField="promedio_delitos_dia"
              showColors
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Serie Temporal Superpuesta</CardTitle>
            <CardDescription>
              Evolución mensual de precipitación y delitos - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <TimeSeriesChart
              data={lineaData}
              loading={chartLoading}
              xField="periodo"
              lines={[
                { dataKey: "total_delitos", name: "Delitos" },
                { dataKey: "precipitacion_total", name: "Precipitación (mm)" },
              ]}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
