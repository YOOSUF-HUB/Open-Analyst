import { useEffect, useState } from "react";
import { BarChart3, Database } from "lucide-react";
import { ConnectionStatusIndicator } from "@/components/ConnectionStatus";
import { DataExplorer } from "@/pages/DataExplorer";
import { type ConnectionStatus, fetchHealth } from "@/services/api";

type NavItem = "explorer";

export function App() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("loading");
  const [apiVersion, setApiVersion] = useState<string | undefined>();
  const [_activeNav] = useState<NavItem>("explorer");

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((h) => {
        if (!cancelled) {
          setConnectionStatus("connected");
          setApiVersion(h.version);
        }
      })
      .catch(() => {
        if (!cancelled) setConnectionStatus("disconnected");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Top navigation bar */}
      <header className="border-b">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" aria-hidden="true" />
              <span className="font-semibold tracking-tight">Open Analyst</span>
            </div>

            <nav className="hidden sm:flex items-center gap-1" aria-label="Main navigation">
              <a
                href="#"
                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium bg-muted text-foreground"
                aria-current="page"
              >
                <Database className="h-4 w-4" aria-hidden="true" />
                Data Explorer
              </a>
            </nav>
          </div>

          <ConnectionStatusIndicator status={connectionStatus} apiVersion={apiVersion} />
        </div>
      </header>

      {/* Main content */}
      <main className="flex flex-1 flex-col">
        <DataExplorer />
      </main>
    </div>
  );
}
