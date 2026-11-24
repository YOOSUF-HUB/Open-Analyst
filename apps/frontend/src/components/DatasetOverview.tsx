import type { DatasetMetrics } from "@/types/dataset";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
}

function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div className="rounded-lg border bg-card px-5 py-4">
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

function fmt(n: number): string {
  return n.toLocaleString();
}

interface DatasetOverviewProps {
  metrics: DatasetMetrics;
  filename: string;
}

export function DatasetOverview({ metrics, filename }: DatasetOverviewProps) {
  return (
    <section aria-label="Dataset overview">
      <div className="mb-3">
        <h2 className="text-lg font-semibold">{filename}</h2>
        <p className="text-sm text-muted-foreground capitalize">{metrics.file_type} file</p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Rows" value={fmt(metrics.row_count)} />
        <StatCard label="Columns" value={fmt(metrics.column_count)} />
        <StatCard
          label="Missing"
          value={`${metrics.missing_percentage}%`}
          sub={`${fmt(metrics.total_missing)} cells`}
        />
        <StatCard
          label="Duplicates"
          value={`${metrics.duplicate_percentage}%`}
          sub={`${fmt(metrics.duplicate_rows)} rows`}
        />
        <StatCard
          label="Quality"
          value={metrics.missing_percentage < 5 && metrics.duplicate_percentage < 1 ? "Good" : "Review"}
        />
      </div>
    </section>
  );
}
