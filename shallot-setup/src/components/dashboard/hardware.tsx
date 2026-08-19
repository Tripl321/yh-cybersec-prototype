"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Usb,
  RefreshCw,
  Loader2,
  CheckCircle2,
  Zap,
  Cpu,
  Radio,
  MonitorSmartphone,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";

interface Device {
  id: string;
  name: string;
  type: "esp32" | "pico" | "arduino" | "unknown";
  port: string;
  status: "connected" | "disconnected";
  firmware?: string;
  version?: string;
  flashable: boolean;
}

const MOCK_DEVICES: Device[] = [
  {
    id: "esp32-1",
    name: "ESP32-S3",
    type: "esp32",
    port: "/dev/ttyUSB0",
    status: "connected",
    firmware: "pico-fido2",
    version: "v2.1.0",
    flashable: true,
  },
  {
    id: "pico-1",
    name: "RP2350",
    type: "pico",
    port: "/dev/ttyACM0",
    status: "connected",
    firmware: "field-node",
    version: "v1.4.2",
    flashable: true,
  },
];

const TYPE_ICON: Record<string, typeof Cpu> = {
  esp32: Cpu,
  pico: MonitorSmartphone,
  arduino: Radio,
  unknown: Usb,
};

const TYPE_LABEL: Record<string, string> = {
  esp32: "ESP32-S3 (PicoFIDO)",
  pico: "RP2350 (Field Node)",
  arduino: "Arduino UNO R4 (Gateway)",
  unknown: "Unknown",
};

export function HardwarePage() {
  const [devices, setDevices] = useState<Device[]>(MOCK_DEVICES);
  const [scanning, setScanning] = useState(false);
  const [flashTarget, setFlashTarget] = useState<Device | null>(null);
  const [flashProgress, setFlashProgress] = useState(0);
  const [flashing, setFlashing] = useState(false);

  const handleScan = () => {
    setScanning(true);
    setTimeout(() => {
      setScanning(false);
      toast.success(`Found ${devices.length} device(s)`);
    }, 1800);
  };

  const handleFlash = (device: Device) => {
    setFlashTarget(device);
    setFlashProgress(0);
    setFlashing(true);
    const interval = setInterval(() => {
      setFlashProgress((p) => {
        if (p >= 100) {
          clearInterval(interval);
          setFlashing(false);
          toast.success(`Firmware flashed to ${device.name}`);
          return 100;
        }
        return p + Math.random() * 15 + 5;
      });
    }, 300);
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Hardware
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Device inventory, scanning, and firmware management
          </p>
        </div>
        <Button
          onClick={handleScan}
          disabled={scanning}
          className="shadow-[0_1px_2px_oklch(0_0_0/0.1),0_2px_8px_oklch(0.205_0.042_265/0.15)]"
        >
          {scanning ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          {scanning ? "Scanning..." : "Scan USB"}
        </Button>
      </div>

      {/* Device cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {devices.map((device) => {
          const Icon = TYPE_ICON[device.type] || Usb;
          return (
            <Card
              key={device.id}
              className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80"
            >
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10">
                    <Icon className="size-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-foreground">
                        {TYPE_LABEL[device.type] || device.name}
                      </h3>
                      <Badge
                        variant={device.status === "connected" ? "secondary" : "outline"}
                        className="text-[10px] px-1.5 py-0 h-5 rounded-md"
                      >
                        {device.status}
                      </Badge>
                    </div>
                    <p className="text-xs font-mono text-muted-foreground/60 mt-0.5">
                      {device.port}
                    </p>
                    {device.firmware && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-muted-foreground">
                          {device.firmware}
                        </span>
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5 rounded-md">
                          {device.version}
                        </Badge>
                      </div>
                    )}
                    <Button
                      size="sm"
                      onClick={() => handleFlash(device)}
                      disabled={flashing}
                      className="mt-3 shadow-[0_1px_2px_oklch(0_0_0/0.1)]"
                    >
                      {flashing && flashTarget?.id === device.id ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : (
                        <Zap className="size-3.5" />
                      )}
                      Flash Firmware
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Device table */}
      <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold">Device Details</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-xs">Device</TableHead>
                <TableHead className="text-xs">Type</TableHead>
                <TableHead className="text-xs">Port</TableHead>
                <TableHead className="text-xs">Firmware</TableHead>
                <TableHead className="text-xs">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {devices.map((d) => {
                const Icon = TYPE_ICON[d.type] || Usb;
                return (
                  <TableRow key={d.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Icon className="size-4 text-muted-foreground/60" />
                        <span className="text-sm font-medium">{d.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {d.type}
                    </TableCell>
                    <TableCell className="text-sm font-mono text-muted-foreground/60">
                      {d.port}
                    </TableCell>
                    <TableCell className="text-sm">
                      {d.firmware}{" "}
                      <span className="text-muted-foreground/60">{d.version}</span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={d.status === "connected" ? "secondary" : "destructive"}
                        className="text-[10px] px-1.5 py-0 h-5 rounded-md"
                      >
                        {d.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Flash dialog */}
      <Dialog open={flashTarget !== null} onOpenChange={(open) => !open && setFlashTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Flash Firmware</DialogTitle>
            <DialogDescription>
              Flashing {flashTarget?.firmware} {flashTarget?.version} to{" "}
              {flashTarget?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3 py-4">
            <Progress value={Math.min(flashProgress, 100)} className="h-2 bg-muted/40" />
            <p className="text-sm text-muted-foreground text-center">
              {flashProgress >= 100
                ? "Flash complete!"
                : `Flashing... ${Math.round(Math.min(flashProgress, 100))}%`}
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setFlashTarget(null)}
              disabled={flashing}
            >
              {flashProgress >= 100 ? "Done" : "Cancel"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
