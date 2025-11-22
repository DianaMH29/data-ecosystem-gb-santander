import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TimeSeriesChart, BarChartComponent, DonutChart } from "@/components/charts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";
import {
  filtrosService,
  temporalService,
  victimasService,
  chatbotService,
} from "@/services/endpoints";
import {
  TrendingUp,
  TrendingDown,
  MapPin,
  Users,
  AlertTriangle,
  Calendar,
} from "lucide-react";

function StatCard({ title, value, description, icon: Icon, trend }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
            {trend === "up" && <TrendingUp className="h-3 w-3 text-red-500" />}
            {trend === "down" && <TrendingDown className="h-3 w-3 text-green-500" />}
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedYear, setSelectedYear] = useState("");
  const [stats, setStats] = useState(null);
  const [yearlyData, setYearlyData] = useState([]);
  const [weekdayData, setWeekdayData] = useState([]);
  const [genderData, setGenderData] = useState([]);
  const [zoneData, setZoneData] = useState([]);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        const [filtersRes, statsRes] = await Promise.all([
          filtrosService.getResumen(),
          chatbotService.getEstadisticas(),
        ]);
        setFilters(filtersRes);
        setStats(statsRes);
        
        // Set default year to most recent
        if (filtersRes?.anios?.length > 0) {
          setSelectedYear(String(filtersRes.anios[0]));
        }
      } catch (error) {
        console.error("Error loading initial data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  useEffect(() => {
    const loadChartData = async () => {
      if (!selectedYear) return;

      try {
        const year = parseInt(selectedYear);
        const [yearlyRes, weekdayRes, genderRes, zoneRes] = await Promise.all([
          temporalService.getLineaAnual(),
          temporalService.getPorDiaSemana({ anio: year }),
          victimasService.getPorGenero({ anio: year }),
          temporalService.getPorZona({ anio: year }),
        ]);
        
        setYearlyData(yearlyRes || []);
        setWeekdayData(weekdayRes || []);
        setGenderData(genderRes || []);
        setZoneData(zoneRes || []);
      } catch (error) {
        console.error("Error loading chart data:", error);
      }
    };

    loadChartData();
  }, [selectedYear]);

  if (loading) {
    return <LoadingOverlay message="Cargando dashboard..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Resumen general de datos de seguridad en Santander
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Año" />
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
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total de Eventos"
          value={formatNumber(stats?.total_eventos)}
          description="Registros históricos"
          icon={AlertTriangle}
        />
        <StatCard
          title="Municipios"
          value={formatNumber(stats?.municipios_cubiertos || 87)}
          description="Departamento de Santander"
          icon={MapPin}
        />
        <StatCard
          title="Categorías"
          value={stats?.categorias_disponibles?.length || 5}
          description="Tipos de delito"
          icon={Users}
        />
        <StatCard
          title="Período"
          value={`${stats?.fecha_inicio?.split("-")[0] || "2003"} - ${
            stats?.fecha_fin?.split("-")[0] || "2025"
          }`}
          description="Rango de datos"
          icon={Calendar}
        />
      </div>

      {/* Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Categorías de Delito</CardTitle>
          <CardDescription>Tipos de delitos registrados en el sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {stats?.categorias_disponibles?.map((cat) => (
              <Badge key={cat} variant="secondary" className="text-sm">
                {cat}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Charts Row 1 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Evolución Anual</CardTitle>
            <CardDescription>Total de delitos por año</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <TimeSeriesChart
              data={yearlyData}
              xField="anio"
              yField="total"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Delitos por Día de Semana</CardTitle>
            <CardDescription>Distribución semanal - {selectedYear}</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <BarChartComponent
              data={weekdayData}
              xField="dia"
              yField="total"
              showColors
            />
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Género</CardTitle>
            <CardDescription>Víctimas por género - {selectedYear}</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <DonutChart
              data={genderData}
              nameField="genero"
              valueField="total"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Zona Urbana vs Rural</CardTitle>
            <CardDescription>Distribución geográfica - {selectedYear}</CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <DonutChart
              data={zoneData}
              nameField="zona"
              valueField="total"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
