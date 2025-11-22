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
import { DonutChart, BarChartComponent, HeatMap } from "@/components/charts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { victimasService, filtrosService } from "@/services/endpoints";
import { Users, UserCircle, MapPin, Shield, Flame } from "lucide-react";

export default function VictimasPage() {
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [selectedYear, setSelectedYear] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [chartLoading, setChartLoading] = useState(false);

  const [genderData, setGenderData] = useState([]);
  const [ageData, setAgeData] = useState([]);
  const [weaponData, setWeaponData] = useState([]);
  const [siteData, setSiteData] = useState([]);
  const [genderByDelito, setGenderByDelito] = useState([]);
  const [pointsData, setPointsData] = useState(null);
  const [pointsLoading, setPointsLoading] = useState(false);

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

        const [gender, age, weapon, site, genderDelito] = await Promise.all([
          victimasService.getPorGenero(params),
          victimasService.getPorGrupoEtario(params),
          victimasService.getPorArmaMedio(params),
          victimasService.getPorClaseSitio(params),
          victimasService.getGeneroPorDelito({ anio: parseInt(selectedYear) }),
        ]);

        setGenderData(gender || []);
        setAgeData(age || []);
        setWeaponData((weapon || []).slice(0, 10));
        setSiteData((site || []).slice(0, 10));
        setGenderByDelito(genderDelito || []);
      } catch (error) {
        console.error("Error loading data:", error);
      } finally {
        setChartLoading(false);
      }
    };

    loadData();
  }, [selectedYear, selectedCategory]);

  // Load points map data separately (can be heavy)
  useEffect(() => {
    const loadPoints = async () => {
      if (!selectedYear) return;

      try {
        setPointsLoading(true);
        const params = {
          anio: parseInt(selectedYear),
          limit: 2000, // Limit points for performance
        };
        if (selectedCategory) {
          params.categoria_delito = selectedCategory;
        }

        const points = await victimasService.getMapaPuntos(params);
        setPointsData(points);
      } catch (error) {
        console.error("Error loading points:", error);
        setPointsData(null);
      } finally {
        setPointsLoading(false);
      }
    };

    loadPoints();
  }, [selectedYear, selectedCategory]);

  if (loading) {
    return <LoadingOverlay message="Cargando..." />;
  }

  // Transform gender by delito for bar chart
  const genderDelitoForChart = genderByDelito.map((item) => ({
    categoria: item.categoria_delito,
    FEMENINO: item.generos?.FEMENINO || 0,
    MASCULINO: item.generos?.MASCULINO || 0,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-8 w-8" />
            Análisis de Víctimas
          </h1>
          <p className="text-muted-foreground">
            Perfil demográfico y características de los eventos
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

      {/* Main Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserCircle className="h-5 w-5" />
              Distribución por Género
            </CardTitle>
            <CardDescription>
              Víctimas según género - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <DonutChart
              data={genderData}
              loading={chartLoading}
              nameField="genero"
              valueField="total"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Distribución por Grupo Etario
            </CardTitle>
            <CardDescription>
              Víctimas según edad - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[350px]">
            <DonutChart
              data={ageData}
              loading={chartLoading}
              nameField="grupo_etario"
              valueField="total"
            />
          </CardContent>
        </Card>
      </div>

      {/* Weapon and Site */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Top 10 Armas/Medios
            </CardTitle>
            <CardDescription>
              Medios utilizados en los eventos - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[400px]">
            <BarChartComponent
              data={weaponData}
              loading={chartLoading}
              xField="arma_medio"
              yField="total"
              horizontal
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Top 10 Clases de Sitio
            </CardTitle>
            <CardDescription>
              Lugares donde ocurren los eventos - {selectedYear}
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[400px]">
            <BarChartComponent
              data={siteData}
              loading={chartLoading}
              xField="clase_sitio"
              yField="total"
              horizontal
            />
          </CardContent>
        </Card>
      </div>

      {/* Gender by Delito */}
      <Card>
        <CardHeader>
          <CardTitle>Género por Categoría de Delito</CardTitle>
          <CardDescription>
            Comparación de género en cada tipo de delito - {selectedYear}
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[400px]">
          <BarChartComponent
            data={genderDelitoForChart}
            loading={chartLoading}
            xField="categoria"
            bars={[
              { dataKey: "FEMENINO", name: "Femenino" },
              { dataKey: "MASCULINO", name: "Masculino" },
            ]}
          />
        </CardContent>
      </Card>

      {/* Heat Map */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5" />
            Mapa de Calor
          </CardTitle>
          <CardDescription>
            Concentración de eventos reportados - {selectedYear}
          </CardDescription>
        </CardHeader>
        <CardContent className="h-[500px]">
          <HeatMap
            data={pointsData}
            loading={pointsLoading}
          />
        </CardContent>
      </Card>
    </div>
  );
}
