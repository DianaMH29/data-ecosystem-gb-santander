import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
} from "recharts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";

export function ScatterPlot({
  data,
  loading,
  xField = "x",
  yField = "y",
  xLabel = "",
  yLabel = "",
}) {
  if (loading) {
    return <LoadingOverlay message="Cargando gráfico..." />;
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[300px] text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      return (
        <div className="bg-popover border rounded-lg shadow-lg p-3">
          <p className="text-sm">
            {xLabel || xField}: {formatNumber(item[xField])}
          </p>
          <p className="text-sm">
            {yLabel || yField}: {formatNumber(item[yField])}
          </p>
          {item.fecha && (
            <p className="text-xs text-muted-foreground">{item.fecha}</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-full min-h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            type="number"
            dataKey={xField}
            name={xLabel || xField}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            label={xLabel ? { value: xLabel, position: "bottom", offset: 0 } : undefined}
          />
          <YAxis
            type="number"
            dataKey={yField}
            name={yLabel || yField}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatNumber(value)}
            label={yLabel ? { value: yLabel, angle: -90, position: "insideLeft" } : undefined}
          />
          <ZAxis range={[50, 50]} />
          <Tooltip content={<CustomTooltip />} />
          <Scatter
            data={data}
            fill="hsl(var(--chart-1))"
            fillOpacity={0.6}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
