import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ConnectionStatusIndicator } from "@/components/ConnectionStatus";

describe("ConnectionStatusIndicator", () => {
  it("shows loading state", () => {
    render(<ConnectionStatusIndicator status="loading" />);
    expect(screen.getByText("Connecting")).toBeInTheDocument();
  });

  it("shows connected state", () => {
    render(<ConnectionStatusIndicator status="connected" />);
    expect(screen.getByText(/Connected/)).toBeInTheDocument();
  });

  it("shows connected state with version", () => {
    render(<ConnectionStatusIndicator status="connected" apiVersion="0.1.0" />);
    expect(screen.getByText("Connected · v0.1.0")).toBeInTheDocument();
  });

  it("shows disconnected state", () => {
    render(<ConnectionStatusIndicator status="disconnected" />);
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });
});
