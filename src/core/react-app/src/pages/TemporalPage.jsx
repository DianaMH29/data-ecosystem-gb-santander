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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TimeSeriesChart, BarChartComponent } from "@/components/charts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { temporalService, filtrosService } from "@/services/endpoints";
import { Clock, TrendingUp, Calendar } from "lucide-react";

export default function TemporalPage() {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedYear, setSelectedYear] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [activeTab, setActiveTab] = useState("mensual");

  const [monthlyData, setMonthlyData] = useState([]);
  const [yearlyData, setYearlyData] = useState([]);
  const [weekdayData, setWeekdayData] = useState([]);
  const [weeklyData, setWeeklyData] = useState([]);
  const [modalidadData, setModalidadData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);

  // Load filters
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const res = await filtrosService.getResumen();
        setFilters(res);
        if (res?.anios?.length > 0) {
          setSelectedYear(String(res.anios[0]));
        }
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
      if (!selectedYear) return;

      try {
        setChartLoading(true);
        const params = {
          anio: parseInt(selectedYear),
        };
        if (selectedCategory) {
          params.categoria_delito = selectedCategory;
        }

        const [monthly, yearly, weekday, weekly, modalidad] = await Promise.all([
          temporalService.getLineaMensual(params),
          temporalService.getLineaAnual(
            selectedCategory ? { categoria_delito: selectedCategory } : {}
          ),
          temporalService.getPorDiaSemana(params),
          temporalService.getTendenciaSemanal(params),
          temporalService.getPorModalidad(params),
        ]);

        setMonthlyData(monthly || []);
        setYearlyData(yearly || []);
        setWeekdayData(weekday || []);
        setWeeklyData(weekly || []);
        setModalidadData((modalidad || []).slice(0, 15));
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

  const MESES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
  ];

  const formattedMonthlyData = monthlyData.map((item) => ({
    ...item,
    mes_nombre: MESES[item.mes - 1] || item.mes,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Clock className="h-8 w-8" />
            Análisis Temporal
          </h1>
          <p className="text-muted-foreground">
            Series de tiempo y distribuciones temporales
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
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
                  {filters?.anios?.map((year) => (
                    <SelectItem key={year} value={String(year)}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-[200px]">
              <label className="text-sm font-medium mb-2 block">Categoría</label>
              <Select value={selectedCategory || "all"} onValueChange={(val) => setSelectedCategory(val === "all" ? "" : val)}>
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

      {/* Charts */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
          <TabsTrigger value="mensual">Mensual</TabsTrigger>
          <TabsTrigger value="anual">Anual</TabsTrigger>
          <TabsTrigger value="semanal">Día Semana</TabsTrigger>
          <TabsTrigger value="modalidad">Modalidad</TabsTrigger>
        </TabsList>

        <TabsContent value="mensual" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Evolución Mensual
              </CardTitle>
              <CardDescription>
                Delitos por mes - {selectedYear}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[450px]">
              <TimeSeriesChart
                data={formattedMonthlyData}
                loading={chartLoading}
                xField="mes_nombre"
                yField="total"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="anual" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Tendencia Histórica
              </CardTitle>
              <CardDescription>
                Total de delitos por año
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[450px]">
              <TimeSeriesChart
                data={yearlyData}
                loading={chartLoading}
                xField="anio"
                yField="total"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="semanal" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Distribución por Día de Semana</CardTitle>
              <CardDescription>
                Comparación de delitos por día - {selectedYear}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[450px]">
              <BarChartComponent
                data={weekdayData}
                loading={chartLoading}
                xField="dia"
                yField="total"
                showColors
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="modalidad" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Distribución por Modalidad</CardTitle>
              <CardDescription>
                Top 15 modalidades de delito - {selectedYear}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[500px]">
              <BarChartComponent
                data={modalidadData}
                loading={chartLoading}
                xField="modalidad"
                yField="total"
                horizontal
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Additional charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Tendencia Semanal</CardTitle>
            <CardDescription>
              Delitos por semana del año - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <TimeSeriesChart
              data={weeklyData}
              loading={chartLoading}
              xField="semana"
              yField="total"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Comparación Día de Semana</CardTitle>
            <CardDescription>
              Vista alternativa - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <BarChartComponent
              data={weekdayData}
              loading={chartLoading}
              xField="dia"
              yField="total"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
