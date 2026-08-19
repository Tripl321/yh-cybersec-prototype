"use client";

import { Badge } from "@/components/ui/badge";
import {
  Usb,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Cpu,
  Radio,
  MonitorSmartphone,
} from "lucide-react";

export interface HardwareDevice {
  id: string;
  name: string;
  type: "esp32" | "pico" | "arduino" | "unknown";
  port: string;
  flashable: boolean;
}

interface HardwareStepProps {
  devices: HardwareDevice[];
  onScan: () => void;
  scanning: boolean;
  selected: string | null;
  onSelect: (id: string) => void;
}

const ICONS: Record<string, typeof Cpu> = {
  esp32: Cpu,
  pico: MonitorSmartphone,
  arduino: Radio,
  unknown: Usb,
};

const LABELS: Record<string, string> = {
  esp32: "ESP32-S3 (PicoFIDO)",
  pico: "RP2350 (Field Node)",
  arduino: "Arduino UNO Q (Gateway)",
  unknown: "Unknown Device",
};

export function HardwareStep({
  devices,
  onScan,
  scanning,
  selected,
  onSelect,
}: HardwareStepProps) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Connect hardware via USB and scan for devices.
        </p>
        <button
          onClick={onScan}
          disabled={scanning}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-[0_1px_2px_oklch(0_0_0/0.1),0_2px_8px_oklch(0.205_0.042_265/0.15)] transition-all duration-150 hover:shadow-[0_1px_3px_oklch(0_0_0/0.12),0_4px_12px_oklch(0.205_0.042_265/0.2)] hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:hover:scale-100"
        >
          {scanning ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          {scanning ? "Scanning..." : "Scan USB"}
        </button>
      </div>

      {devices.length === 0 && !scanning && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/60 bg-muted/10 py-16 text-center">
          <Usb className="mb-3 size-10 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground/70">
            No devices found. Connect one and scan.
          </p>
        </div>
      )}

      <div className="flex flex-col gap-2">
        {devices.map((device) => {
          const Icon = ICONS[device.type] || Usb;
          const isSelected = selected === device.id;
          return (
            <button
              key={device.id}
              type="button"
              onClick={() => onSelect(device.id)}
              className={`flex w-full items-center gap-4 rounded-2xl border px-4 py-3.5 text-left transition-all duration-200 ${
                isSelected
                  ? "border-primary/30 bg-primary/5 shadow-[0_2px_12px_oklch(0.205_0.042_265/0.08)]"
                  : "border-border/50 bg-background/30 hover:border-border hover:bg-muted/20 hover:shadow-[0_1px_4px_oklch(0_0_0/0.04)]"
              }`}
            >
              <div
                className={`flex size-11 items-center justify-center rounded-xl transition-colors duration-200 ${
                  isSelected ? "bg-primary/10" : "bg-muted/60"
                }`}
              >
                <Icon
                  className={`size-5 ${
                    isSelected
                      ? "text-primary"
                      : "text-muted-foreground/60"
                  }`}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground truncate">
                    {LABELS[device.type] || device.name}
                  </span>
                  {device.flashable && (
                    <Badge
                      variant="secondary"
                      className="text-[10px] px-1.5 py-0 h-5 rounded-md"
                    >
                      Ready
                    </Badge>
                  )}
                </div>
                <span className="text-xs text-muted-foreground/70 font-mono">
                  {device.port}
                </span>
              </div>
              {isSelected && (
                <CheckCircle2 className="size-4.5 text-primary shrink-0" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
