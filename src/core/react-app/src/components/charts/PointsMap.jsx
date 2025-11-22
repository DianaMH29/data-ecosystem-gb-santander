import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import { LoadingOverlay } from "@/components/ui/spinner";

// Component to render heatmap layer
function HeatmapLayer({ points, options = {} }) {
  const map = useMap();
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!points || points.length === 0) return;

    // Remove existing layer
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
    }

    // Create heatmap layer
    const heatLayer = L.heatLayer(points, {
      radius: 20,
      blur: 15,
      maxZoom: 12,
      max: 1.0,
      gradient: {
        0.0: '#3b82f6',
        0.25: '#22c55e', 
        0.5: '#eab308',
        0.75: '#f97316',
        1.0: '#ef4444'
      },
      ...options,
    });

    heatLayer.addTo(map);
    heatLayerRef.current = heatLayer;

    // Fit bounds to points
    if (points.length > 0) {
      const latLngs = points.map(p => [p[0], p[1]]);
      const bounds = L.latLngBounds(latLngs);
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [30, 30], maxZoom: 10 });
      }
    }

    return () => {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current);
      }
    };
  }, [map, points, options]);

  return null;
}

export function HeatMap({
  data,
  loading,
  title = "Mapa de Calor",
}) {
  if (loading) {
    return <LoadingOverlay message="Cargando mapa de calor..." />;
  }

  if (!data || !data.features || data.features.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px] text-muted-foreground">
        No hay datos disponibles para mostrar
      </div>
    );
  }

  // Convert GeoJSON to heatmap points [lat, lng, intensity]
  const heatPoints = data.features
    .filter(
      f => f.geometry && 
           f.geometry.coordinates && 
           f.geometry.coordinates[0] !== null && 
           f.geometry.coordinates[1] !== null
    )
    .map(f => [
      f.geometry.coordinates[1], // lat
      f.geometry.coordinates[0], // lng
      0.5 // intensity
    ]);

  return (
    <div className="h-full min-h-[400px] rounded-lg overflow-hidden border relative">
      <MapContainer
        center={[7.1, -73.1]}
        zoom={9}
        className="h-full w-full"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <HeatmapLayer points={heatPoints} />
      </MapContainer>
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white/90 dark:bg-card/90 p-3 rounded-lg shadow-lg z-[1000]">
        <p className="text-xs font-medium mb-2">Intensidad</p>
        <div className="flex items-center gap-1">
          <span className="text-xs">Baja</span>
          <div className="flex h-3 w-24 rounded overflow-hidden">
            <div className="flex-1" style={{ backgroundColor: '#3b82f6' }} />
            <div className="flex-1" style={{ backgroundColor: '#22c55e' }} />
            <div className="flex-1" style={{ backgroundColor: '#eab308' }} />
            <div className="flex-1" style={{ backgroundColor: '#f97316' }} />
            <div className="flex-1" style={{ backgroundColor: '#ef4444' }} />
          </div>
          <span className="text-xs">Alta</span>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {heatPoints.length.toLocaleString()} eventos
        </p>
      </div>
    </div>
  );
}

// Keep PointsMap for backwards compatibility but export HeatMap as main
export { HeatMap as PointsMap };
