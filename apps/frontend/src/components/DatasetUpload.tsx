import { useCallback, useRef, useState } from "react";
import { Upload, FileText, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DatasetUploadProps {
  onUploadStart: () => void;
  onUploadSuccess: (file: File) => void;
  onUploadError: (message: string) => void;
  isUploading: boolean;
  uploadProgress?: number;
}

const ACCEPTED_EXTENSIONS = [".csv", ".xlsx"];
const MAX_SIZE_MB = 25;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

function validateFile(file: File): string | null {
  const name = file.name.toLowerCase();
  const hasValidExt = ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
  if (!hasValidExt) {
    return `Unsupported file type. Please upload a CSV or XLSX file.`;
  }
  if (file.size === 0) {
    return "File is empty.";
  }
  if (file.size > MAX_SIZE_BYTES) {
    return `File is too large. Maximum size is ${MAX_SIZE_MB} MB.`;
  }
  return null;
}

export function DatasetUpload({
  onUploadStart,
  onUploadSuccess,
  onUploadError,
  isUploading,
}: DatasetUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setValidationError(null);
      const error = validateFile(file);
      if (error) {
        setValidationError(error);
        onUploadError(error);
        return;
      }
      onUploadStart();
      onUploadSuccess(file);
    },
    [onUploadStart, onUploadSuccess, onUploadError],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    // Reset so the same file can be re-selected
    e.target.value = "";
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload dataset — drag and drop or click to select a file"
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && !isUploading && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          "relative flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-12 text-center transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50 hover:bg-muted/30",
          isUploading && "pointer-events-none opacity-60",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          className="sr-only"
          onChange={handleInputChange}
          disabled={isUploading}
          aria-hidden="true"
        />

        {isUploading ? (
          <Loader2 className="h-10 w-10 animate-spin text-primary" aria-hidden="true" />
        ) : (
          <Upload className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
        )}

        <div>
          <p className="font-medium text-sm">
            {isUploading ? "Uploading and profiling…" : "Drag & drop your dataset here"}
          </p>
          {!isUploading && (
            <p className="mt-1 text-xs text-muted-foreground">
              or{" "}
              <span className="text-primary underline underline-offset-2 cursor-pointer">
                browse files
              </span>
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileText className="h-3.5 w-3.5" aria-hidden="true" />
          <span>CSV, XLSX · up to {MAX_SIZE_MB} MB</span>
        </div>
      </div>

      {validationError && (
        <div
          role="alert"
          className="mt-3 flex items-start gap-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" aria-hidden="true" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
}
