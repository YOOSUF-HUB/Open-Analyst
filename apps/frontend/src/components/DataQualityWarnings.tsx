import { AlertCircle, AlertTriangle, Info } from "lucide-react";
import type { QualityWarning } from "@/types/dataset";

const ICONS = {
  error: <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" aria-hidden="true" />,
  warning: <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />,
  info: <Info className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" aria-hidden="true" />,
};

const BG = {
  error: "bg-destructive/10 border-destructive/20",
  warning: "bg-amber-50 border-amber-200",
  info: "bg-blue-50 border-blue-200",
};

interface DataQualityWarningsProps {
  warnings: QualityWarning[];
}

export function DataQualityWarnings({ warnings }: DataQualityWarningsProps) {
  if (warnings.length === 0) {
    return (
      <section aria-label="Data quality warnings">
        <h3 className="text-sm font-semibold mb-3">Data Quality</h3>
        <p className="text-sm text-muted-foreground py-2">No quality issues detected.</p>
      </section>
    );
  }

  const errors = warnings.filter((w) => w.severity === "error");
  const warnItems = warnings.filter((w) => w.severity === "warning");
  const infos = warnings.filter((w) => w.severity === "info");
  const ordered = [...errors, ...warnItems, ...infos];

  return (
    <section aria-label="Data quality warnings">
      <h3 className="text-sm font-semibold mb-3">
        Data Quality{" "}
        <span className="font-normal text-muted-foreground">({warnings.length} notice{warnings.length !== 1 ? "s" : ""})</span>
      </h3>
      <ul className="space-y-2" role="list">
        {ordered.map((w, i) => (
          <li
            key={i}
            className={`flex items-start gap-2 rounded-md border px-3 py-2 text-sm ${BG[w.severity]}`}
          >
            {ICONS[w.severity]}
            <span>{w.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
