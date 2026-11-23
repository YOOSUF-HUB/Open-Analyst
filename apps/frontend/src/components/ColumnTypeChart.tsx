import ReactECharts from "echarts-for-react";
import type { DatasetMetrics } from "@/types/dataset";

interface ColumnTypeChartProps {
  metrics: DatasetMetrics;
}

const TYPE_COLORS: Record<string, string> = {
  Numeric: "#3b82f6",
  Categorical: "#8b5cf6",
  Text: "#6b7280",
  Boolean: "#f59e0b",
  Datetime: "#10b981",
};

export function ColumnTypeChart({ metrics }: ColumnTypeChartProps) {
  const data = [
    { name: "Numeric", value: metrics.numeric_columns },
    { name: "Categorical", value: metrics.categorical_columns },
    { name: "Text", value: metrics.text_columns },
    { name: "Boolean", value: metrics.boolean_columns },
    { name: "Datetime", value: metrics.datetime_columns },
  ].filter((d) => d.value > 0);

  const option = {
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c} column{c > 1 ? 's' : ''}",
    },
    legend: {
      orient: "vertical",
      right: 0,
      top: "center",
      textStyle: { fontSize: 12 },
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        center: ["40%", "50%"],
        avoidLabelOverlap: false,
        label: { show: false },
        emphasis: { label: { show: false } },
        data: data.map((d) => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: TYPE_COLORS[d.name] },
        })),
      },
    ],
  };

  return (
    <section aria-label="Column type distribution">
      <h3 className="text-sm font-semibold mb-3">Column Types</h3>
      <ReactECharts option={option} style={{ height: 220 }} notMerge />
    </section>
  );
}
