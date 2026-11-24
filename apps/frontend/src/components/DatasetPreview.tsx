import type { PreviewResponse } from "@/types/dataset";

interface DatasetPreviewProps {
  preview: PreviewResponse;
}

function cellValue(val: unknown): string {
  if (val === null || val === undefined) return "";
  return String(val);
}

function isMissing(val: unknown): boolean {
  return val === null || val === undefined;
}

export function DatasetPreview({ preview }: DatasetPreviewProps) {
  if (preview.rows.length === 0) {
    return (
      <section aria-label="Dataset preview">
        <h3 className="text-sm font-semibold mb-3">
          Preview{" "}
          <span className="font-normal text-muted-foreground">
            (0 of {preview.total_rows.toLocaleString()} rows)
          </span>
        </h3>
        <p className="text-sm text-muted-foreground py-8 text-center">No rows to display.</p>
      </section>
    );
  }

  return (
    <section aria-label="Dataset preview">
      <h3 className="text-sm font-semibold mb-3">
        Preview{" "}
        <span className="font-normal text-muted-foreground">
          ({preview.preview_rows.toLocaleString()} of {preview.total_rows.toLocaleString()} rows)
        </span>
      </h3>
      <div className="overflow-x-auto rounded-lg border max-h-80 overflow-y-auto">
        <table className="w-full text-xs" aria-label="Dataset preview table">
          <thead className="sticky top-0 z-10 bg-muted/80 backdrop-blur-sm">
            <tr className="border-b">
              {preview.columns.map((col) => (
                <th
                  key={col}
                  className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap font-mono"
                  title={col}
                >
                  <span className="max-w-[120px] truncate block">{col}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/20 transition-colors">
                {preview.columns.map((col) => {
                  const val = row[col];
                  return (
                    <td
                      key={col}
                      className={`px-3 py-1.5 whitespace-nowrap max-w-[160px] truncate ${
                        isMissing(val) ? "text-muted-foreground/50 italic" : ""
                      }`}
                      title={isMissing(val) ? "null" : cellValue(val)}
                    >
                      {isMissing(val) ? "null" : cellValue(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
