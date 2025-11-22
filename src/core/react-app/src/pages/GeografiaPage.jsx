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
import { ChoroplethMap } from "@/components/charts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";
import { geografiaService, filtrosService } from "@/services/endpoints";
import { Map, BarChart3 } from "lucide-react";

export default function GeografiaPage() {
  const [loading, setLoading] = useState(true);
  const [mapLoading, setMapLoading] = useState(false);
  const [filters, setFilters] = useState(null);
  const [selectedYear, setSelectedYear] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [mapType, setMapType] = useState("total");
  const [geoData, setGeoData] = useState(null);

  // Load filters on mount
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

  // Load map data when filters change
  useEffect(() => {
    const loadMapData = async () => {
      if (!selectedYear) return;

      try {
        setMapLoading(true);
        const params = {
          anio: parseInt(selectedYear),
        };
        if (selectedCategory) {
          params.categoria_delito = selectedCategory;
        }

        let data;
        if (mapType === "total") {
          data = await geografiaService.getDelitosPorMunicipio(params);
        } else {
          data = await geografiaService.getTasaPorMunicipio(params);
        }
        setGeoData(data);
      } catch (error) {
        console.error("Error loading map data:", error);
      } finally {
        setMapLoading(false);
      }
    };

    loadMapData();
  }, [selectedYear, selectedCategory, mapType]);

  if (loading) {
    return <LoadingOverlay message="Cargando filtros..." />;
  }

  // Calculate top municipalities
  const topMunicipios = geoData?.features
    ?.map((f) => ({
      nombre: f.properties.nombre_municipio,
      valor: mapType === "total" 
        ? f.properties.total_delitos 
        : f.properties.tasa_por_100k,
    }))
    .sort((a, b) => (b.valor || 0) - (a.valor || 0))
    .slice(0, 10) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Map className="h-8 w-8" />
            Geografía
          </h1>
          <p className="text-muted-foreground">
            Mapas coropléticos de delitos por municipio
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

      {/* Map Tabs */}
      <Tabs value={mapType} onValueChange={setMapType} className="space-y-4">
        <TabsList>
          <TabsTrigger value="total">Total de Delitos</TabsTrigger>
          <TabsTrigger value="tasa">Tasa por 100k habitantes</TabsTrigger>
        </TabsList>

        <div className="grid gap-4 lg:grid-cols-3">
          {/* Map */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>
                {mapType === "total" ? "Delitos por Municipio" : "Tasa por 100,000 Habitantes"}
              </CardTitle>
              <CardDescription>
                {selectedCategory || "Todos los delitos"} - {selectedYear}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[500px] relative">
              <ChoroplethMap
                data={geoData}
                loading={mapLoading}
                valueField={mapType === "total" ? "total_delitos" : "tasa_por_100k"}
                labelField="nombre_municipio"
                title={mapType === "total" ? "Delitos" : "Tasa"}
              />
            </CardContent>
          </Card>

          {/* Ranking */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Top 10 Municipios
              </CardTitle>
              <CardDescription>
                {mapType === "total" ? "Mayor cantidad de delitos" : "Mayor tasa por habitante"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topMunicipios.map((mun, index) => (
                  <div
                    key={mun.nombre}
                    className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-muted-foreground w-6">
                        {index + 1}
                      </span>
                      <span className="text-sm font-medium truncate max-w-[120px]">
                        {mun.nombre}
                      </span>
                    </div>
                    <span className="text-sm font-semibold">
                      {mapType === "total"
                        ? formatNumber(mun.valor)
                        : mun.valor?.toFixed(1)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </Tabs>
    </div>
  );
}
