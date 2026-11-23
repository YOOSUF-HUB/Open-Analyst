import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import { ConnectionStatusIndicator } from "@/components/ConnectionStatus";
import { type ConnectionStatus, fetchHealth } from "@/services/api";

export function Home() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("loading");
  const [apiVersion, setApiVersion] = useState<string | undefined>();

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const health = await fetchHealth();
        if (!cancelled) {
          setConnectionStatus("connected");
          setApiVersion(health.version);
        }
      } catch {
        if (!cancelled) {
          setConnectionStatus("disconnected");
        }
      }
    }

    void checkHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <span className="font-semibold tracking-tight">Open Analyst</span>
          </div>
          <ConnectionStatusIndicator status={connectionStatus} apiVersion={apiVersion} />
        </div>
      </header>

      <main className="container flex flex-1 flex-col items-center justify-center gap-6 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">Open Analyst</h1>
          <p className="mt-3 text-lg text-muted-foreground">
            Open-source AI Data Analyst — turn raw data into meaningful insights.
          </p>
        </div>

        <div className="mt-4 rounded-lg border bg-card p-6 text-card-foreground shadow-sm w-full max-w-sm">
          <h2 className="mb-4 font-semibold text-sm uppercase tracking-wider text-muted-foreground">
            System Status
          </h2>
          <div className="flex items-center justify-between">
            <span className="text-sm">Backend API</span>
            <ConnectionStatusIndicator status={connectionStatus} apiVersion={apiVersion} />
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Phase 0 — Project Foundation
        </p>
      </main>
    </div>
  );
}
