import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import { LoadingOverlay } from "@/components/ui/spinner";
import { formatNumber } from "@/lib/utils";

const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

export function BarChartComponent({
  data,
  loading,
  xField = "nombre",
  yField = "total",
  bars = null,
  horizontal = false,
  showColors = false,
  title = "",
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

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border rounded-lg shadow-lg p-3">
          <p className="font-medium text-sm">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatNumber(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const layout = horizontal ? "vertical" : "horizontal";

  return (
    <div className="h-full min-h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout={layout}
          margin={{ top: 10, right: 30, left: horizontal ? 100 : 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          {horizontal ? (
            <>
              <XAxis
                type="number"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => formatNumber(value)}
              />
              <YAxis
                type="category"
                dataKey={xField}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={90}
              />
            </>
          ) : (
            <>
              <XAxis
                dataKey={xField}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => formatNumber(value)}
              />
            </>
          )}
          <Tooltip content={<CustomTooltip />} />
          {bars ? (
            <>
              <Legend />
              {bars.map((bar, index) => (
                <Bar
                  key={bar.dataKey}
                  dataKey={bar.dataKey}
                  name={bar.name || bar.dataKey}
                  fill={COLORS[index % COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </>
          ) : (
            <Bar dataKey={yField} radius={[4, 4, 0, 0]}>
              {showColors
                ? data.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))
                : data.map((entry, index) => (
                    <Cell key={index} fill={COLORS[0]} />
                  ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
