import ReactECharts from "echarts-for-react";
import type { ColumnProfile } from "@/types/dataset";

interface MissingValuesChartProps {
  columns: ColumnProfile[];
}

export function MissingValuesChart({ columns }: MissingValuesChartProps) {
  const withMissing = columns
    .filter((c) => c.missing_count > 0)
    .sort((a, b) => b.missing_percentage - a.missing_percentage)
    .slice(0, 15);

  if (withMissing.length === 0) {
    return (
      <section aria-label="Missing values analysis">
        <h3 className="text-sm font-semibold mb-3">Missing Values</h3>
        <p className="text-sm text-muted-foreground py-4 text-center">No missing values found.</p>
      </section>
    );
  }

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: { name: string; value: number }[]) => {
        const p = params[0];
        return `${p.name}: ${p.value}%`;
      },
    },
    grid: { left: "3%", right: "8%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "value",
      max: 100,
      axisLabel: { formatter: "{value}%" },
    },
    yAxis: {
      type: "category",
      data: withMissing.map((c) => c.name),
      axisLabel: {
        width: 120,
        overflow: "truncate" as const,
      },
    },
    series: [
      {
        type: "bar",
        data: withMissing.map((c) => ({
          value: c.missing_percentage,
          itemStyle: {
            color: c.missing_percentage >= 50 ? "#ef4444" : c.missing_percentage >= 20 ? "#f59e0b" : "#3b82f6",
          },
        })),
        label: {
          show: true,
          position: "right" as const,
          formatter: "{c}%",
          fontSize: 11,
        },
      },
    ],
  };

  return (
    <section aria-label="Missing values analysis">
      <h3 className="text-sm font-semibold mb-3">Missing Values</h3>
      <ReactECharts option={option} style={{ height: Math.max(180, withMissing.length * 28) }} notMerge />
    </section>
  );
}
