import { useState } from "react";
import { Table2 } from "lucide-react";

interface ExcelSheetSelectorProps {
  sheetNames: string[];
  onSelect: (sheetName: string) => void;
  isLoading: boolean;
}

export function ExcelSheetSelector({ sheetNames, onSelect, isLoading }: ExcelSheetSelectorProps) {
  const [selected, setSelected] = useState<string>("");

  const handleSelect = (name: string) => {
    setSelected(name);
    onSelect(name);
  };

  return (
    <div className="rounded-lg border bg-card p-6 max-w-lg mx-auto">
      <div className="flex items-center gap-2 mb-4">
        <Table2 className="h-5 w-5 text-primary" aria-hidden="true" />
        <h2 className="font-semibold">Select a Worksheet</h2>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        This workbook has multiple worksheets. Select one to profile.
      </p>
      <div className="space-y-2" role="list" aria-label="Available worksheets">
        {sheetNames.map((name) => (
          <button
            key={name}
            role="listitem"
            onClick={() => handleSelect(name)}
            disabled={isLoading}
            aria-pressed={selected === name}
            className={`w-full text-left px-4 py-2.5 rounded-md text-sm border transition-colors
              ${
                selected === name
                  ? "border-primary bg-primary/10 font-medium"
                  : "border-border hover:border-primary/50 hover:bg-muted/30"
              }
              disabled:opacity-60 disabled:pointer-events-none`}
          >
            {name}
          </button>
        ))}
      </div>
    </div>
  );
}
