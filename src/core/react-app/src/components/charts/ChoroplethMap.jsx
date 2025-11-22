import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";

// Component to fit bounds when data changes
function FitBounds({ data }) {
  const map = useMap();

  useEffect(() => {
    if (data && data.features && data.features.length > 0) {
      const geoJsonLayer = L.geoJSON(data);
      const bounds = geoJsonLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20] });
      }
    }
  }, [data, map]);

  return null;
}

// Color scale function
function getColor(value, min, max) {
  if (value === null || value === undefined) return "#e0e0e0";
  const normalized = (value - min) / (max - min);
  const colors = [
    "#ffffcc",
    "#ffeda0",
    "#fed976",
    "#feb24c",
    "#fd8d3c",
    "#fc4e2a",
    "#e31a1c",
    "#bd0026",
    "#800026",
  ];
  const index = Math.min(Math.floor(normalized * colors.length), colors.length - 1);
  return colors[index];
}

export function ChoroplethMap({
  data,
  loading,
  valueField = "total_delitos",
  labelField = "nombre_municipio",
  title = "Mapa",
}) {
  const geoJsonRef = useRef();

  if (loading) {
    return <LoadingOverlay message="Cargando mapa..." />;
  }

  if (!data || !data.features || data.features.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px] text-muted-foreground">
        No hay datos disponibles para mostrar
      </div>
    );
  }

  // Calculate min and max values
  const values = data.features
    .map((f) => f.properties[valueField])
    .filter((v) => v !== null && v !== undefined);
  const min = Math.min(...values);
  const max = Math.max(...values);

  const style = (feature) => {
    const value = feature.properties[valueField];
    return {
      fillColor: getColor(value, min, max),
      weight: 1,
      opacity: 1,
      color: "#666",
      fillOpacity: 0.7,
    };
  };

  const onEachFeature = (feature, layer) => {
    const props = feature.properties;
    const value = props[valueField];
    const label = props[labelField];
    
    layer.bindTooltip(
      `<strong>${label}</strong><br/>
       ${title}: ${formatNumber(value)}`,
      { sticky: true }
    );

    layer.on({
      mouseover: (e) => {
        const layer = e.target;
        layer.setStyle({
          weight: 3,
          color: "#333",
          fillOpacity: 0.9,
        });
      },
      mouseout: (e) => {
        geoJsonRef.current?.resetStyle(e.target);
      },
    });
  };

  return (
    <div className="h-full min-h-[400px] rounded-lg overflow-hidden border">
      <MapContainer
        center={[7.1, -73.1]}
        zoom={8}
        className="h-full w-full"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON
          ref={geoJsonRef}
          data={data}
          style={style}
          onEachFeature={onEachFeature}
        />
        <FitBounds data={data} />
      </MapContainer>
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white/90 dark:bg-card/90 p-3 rounded-lg shadow-lg z-[1000]">
        <p className="text-xs font-medium mb-2">{title}</p>
        <div className="flex items-center gap-1">
          <span className="text-xs">{formatNumber(min)}</span>
          <div className="flex">
            {["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"].map((color, i) => (
              <div
                key={i}
                className="w-4 h-3"
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
          <span className="text-xs">{formatNumber(max)}</span>
        </div>
      </div>
    </div>
  );
}
