import type { ColumnProfile } from "@/types/dataset";

const TYPE_BADGE: Record<string, string> = {
  numeric: "bg-blue-100 text-blue-800",
  categorical: "bg-purple-100 text-purple-800",
  text: "bg-gray-100 text-gray-800",
  boolean: "bg-amber-100 text-amber-800",
  datetime: "bg-emerald-100 text-emerald-800",
};

interface ColumnProfileTableProps {
  columns: ColumnProfile[];
}

export function ColumnProfileTable({ columns }: ColumnProfileTableProps) {
  return (
    <section aria-label="Column profiles">
      <h3 className="text-sm font-semibold mb-3">Column Profiles</h3>
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm" aria-label="Column statistics">
          <thead>
            <tr className="border-b bg-muted/40">
              <th className="text-left px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">Column</th>
              <th className="text-left px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">Type</th>
              <th className="text-right px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">Non-null</th>
              <th className="text-right px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">Missing</th>
              <th className="text-right px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">Missing %</th>
              <th className="text-right px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap">Unique</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((col) => (
              <tr key={col.name} className="border-b last:border-0 hover:bg-muted/20 transition-colors">
                <td className="px-4 py-2.5 font-mono text-xs max-w-[180px] truncate" title={col.name}>
                  {col.name}
                </td>
                <td className="px-4 py-2.5">
                  <span
                    className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${TYPE_BADGE[col.logical_type] ?? "bg-gray-100 text-gray-800"}`}
                  >
                    {col.logical_type}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums">{col.non_null_count.toLocaleString()}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">
                  {col.missing_count > 0 ? (
                    <span className="text-amber-600">{col.missing_count.toLocaleString()}</span>
                  ) : (
                    "0"
                  )}
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">
                  {col.missing_percentage.toFixed(1)}%
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">
                  {col.unique_count.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
