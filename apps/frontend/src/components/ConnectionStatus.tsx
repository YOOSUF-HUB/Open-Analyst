import { Loader2, Wifi, WifiOff } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ConnectionStatus } from "@/services/api";

interface ConnectionStatusProps {
  status: ConnectionStatus;
  apiVersion?: string;
}

export function ConnectionStatusIndicator({ status, apiVersion }: ConnectionStatusProps) {
  if (status === "loading") {
    return (
      <Badge variant="secondary" className="gap-1.5">
        <Loader2 className="h-3 w-3 animate-spin" />
        Connecting
      </Badge>
    );
  }

  if (status === "connected") {
    return (
      <Badge className="gap-1.5 bg-emerald-500 hover:bg-emerald-500">
        <Wifi className="h-3 w-3" />
        Connected{apiVersion ? ` · v${apiVersion}` : ""}
      </Badge>
    );
  }

  return (
    <Badge variant="destructive" className="gap-1.5">
      <WifiOff className="h-3 w-3" />
      Disconnected
    </Badge>
  );
}
