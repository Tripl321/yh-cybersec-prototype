"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Stepper, type Step } from "@/components/setup/stepper";
import { ProfileStep, type Profile } from "@/components/setup/profile-step";
import { HardwareStep, type HardwareDevice } from "@/components/setup/hardware-step";
import { FirmwareStep, type FirmwareTarget } from "@/components/setup/firmware-step";
import { ConfigStep, type GRCControl } from "@/components/setup/config-step";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldCheck,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";

const STEPS: Step[] = [
  { id: "profile", title: "Profile" },
  { id: "hardware", title: "Hardware" },
  { id: "firmware", title: "Flash" },
  { id: "config", title: "Config" },
];

const INITIAL_PROFILE: Profile = {
  name: "",
  role: "operator",
  organization: "",
};

const MOCK_DEVICES: HardwareDevice[] = [
  {
    id: "esp32-1",
    name: "ESP32-S3",
    type: "esp32",
    port: "/dev/ttyUSB0",
    flashable: true,
  },
  {
    id: "pico-1",
    name: "RP2350",
    type: "pico",
    port: "/dev/ttyACM0",
    flashable: true,
  },
];

const MOCK_TARGETS: FirmwareTarget[] = [
  {
    device: "ESP32-S3",
    port: "/dev/ttyUSB0",
    firmware: "pico-fido2",
    version: "v2.1.0",
    progress: 0,
    status: "queued",
  },
  {
    device: "RP2350",
    port: "/dev/ttyACM0",
    firmware: "field-node",
    version: "v1.4.2",
    progress: 0,
    status: "queued",
  },
];

const MOCK_CONTROLS: GRCControl[] = [
  {
    id: "AC-2",
    framework: "NIST",
    control: "AC-2 Account Management",
    description: "Operator identity via WebAuthn/FIDO2",
    status: "implemented",
    component: "web-authn",
  },
  {
    id: "AC-6",
    framework: "NIST",
    control: "AC-6 Least Privilege",
    description: "Role-based tool allowlist in cub-agent",
    status: "implemented",
    component: "cub-agent-llm",
  },
  {
    id: "AU-2",
    framework: "NIST",
    control: "AU-2 Audit Events",
    description: "Provenance log + Wazuh SIEM integration",
    status: "implemented",
    component: "siem-integration",
  },
  {
    id: "SC-28",
    framework: "NIST",
    control: "SC-28 Protection of Data at Rest",
    description: "AES-SIV scrubber for PII/credentials",
    status: "implemented",
    component: "scrubber-aes-siv",
  },
  {
    id: "IA-2",
    framework: "NIST",
    control: "IA-2 Identification and Authentication",
    description: "FIDO2 CTAP2 hardware authentication",
    status: "implemented",
    component: "fido2-hardware",
  },
  {
    id: "IR-4",
    framework: "NIST",
    control: "IR-4 Incident Handling",
    description: "Presence heartbeat + auto-lock on absence",
    status: "partial",
    component: "locha-heartbeat",
  },
  {
    id: "ART-6",
    framework: "EU-AI",
    control: "ART-6 Risk Management",
    description: "LLM guardrails + content filtering in cub-agent",
    status: "implemented",
    component: "cub-agent-llm",
  },
  {
    id: "NIS2-A",
    framework: "NIS2",
    control: "Incident Reporting",
    description: "Automated SIEM alert pipeline",
    status: "implemented",
    component: "siem-integration",
  },
];

const SPRING_STEP = { type: "spring" as const, stiffness: 300, damping: 30, mass: 0.8 };

const STEP_VARIANTS = {
  enter: (direction: number) => ({
    transform: `translateX(${direction > 0 ? 40 : -40}px)`,
    opacity: 0,
  }),
  center: {
    transform: "translateX(0)",
    opacity: 1,
  },
  exit: (direction: number) => ({
    transform: `translateX(${direction > 0 ? -40 : 40}px)`,
    opacity: 0,
  }),
};

export default function SetupWizard() {
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [profile, setProfile] = useState<Profile>(INITIAL_PROFILE);
  const [devices, setDevices] = useState<HardwareDevice[]>([]);
  const [scanning, setScanning] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [targets, setTargets] = useState<FirmwareTarget[]>([]);
  const [deployStarted, setDeployStarted] = useState(false);

  const canNext = (() => {
    switch (step) {
      case 0:
        return profile.name.trim().length > 0;
      case 1:
        return selectedDevice !== null;
      case 2:
        return targets.some((t) => t.status === "done");
      default:
        return false;
    }
  })();

  const goNext = () => {
    if (step === 1 && selectedDevice) {
      setTargets(MOCK_TARGETS);
    }
    if (step === 2) {
      setDeployStarted(true);
    }
    setDirection(1);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const goPrev = () => {
    setDirection(-1);
    setStep((s) => Math.max(s - 1, 0));
  };

  const goStep = (i: number) => {
    setDirection(i > step ? 1 : -1);
    setStep(i);
  };

  const handleScan = () => {
    setScanning(true);
    setTimeout(() => {
      setDevices(MOCK_DEVICES);
      setScanning(false);
      toast.success(`Found ${MOCK_DEVICES.length} device(s)`);
    }, 1800);
  };

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-gradient-to-br from-background via-background to-primary/[0.03] px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={SPRING_STEP}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="flex flex-col items-center gap-3 mb-8">
          <div className="flex size-14 items-center justify-center rounded-2xl bg-primary/10 shadow-[0_2px_12px_oklch(0.205_0.042_265/0.08)]">
            <ShieldCheck className="size-7 text-primary" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              SHALLOT Setup
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Presence-based OT access control deployment
            </p>
          </div>
        </div>

        {/* Stepper */}
        <div className="mb-8">
          <Stepper steps={STEPS} currentStep={step} onStepClick={goStep} />
        </div>

        {/* Card */}
        <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80 backdrop-blur-sm overflow-hidden">
          <CardHeader className="pb-4">
            <CardTitle className="text-base font-semibold text-foreground">
              {STEPS[step].title}
            </CardTitle>
          </CardHeader>
          <CardContent className="relative overflow-hidden min-h-[320px]">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={step}
                custom={direction}
                variants={STEP_VARIANTS}
                initial="enter"
                animate="center"
                exit="exit"
                transition={SPRING_STEP}
              >
                {step === 0 && (
                  <ProfileStep profile={profile} onChange={setProfile} />
                )}
                {step === 1 && (
                  <HardwareStep
                    devices={devices}
                    onScan={handleScan}
                    scanning={scanning}
                    selected={selectedDevice}
                    onSelect={setSelectedDevice}
                  />
                )}
                {step === 2 && (
                  <FirmwareStep
                    targets={targets}
                    onNext={goNext}
                    canNext={canNext}
                  />
                )}
                {step === 3 && (
                  <ConfigStep
                    controls={MOCK_CONTROLS}
                    onStart={() =>
                      toast.success("Deployment started", {
                        description: "Services are coming online...",
                      })
                    }
                    onStartDisabled={!deployStarted}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </CardContent>
        </Card>

        {/* Navigation */}
        {step !== 2 && (
          <div className="flex justify-between mt-6">
            <button
              onClick={goPrev}
              disabled={step === 0}
              className="inline-flex items-center gap-2 rounded-xl border border-border/60 bg-background/50 px-4 py-2.5 text-sm font-medium text-foreground/80 backdrop-blur-sm transition-all duration-150 hover:bg-muted/40 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-0 disabled:pointer-events-none"
            >
              <ArrowLeft className="size-4" />
              Back
            </button>
            {step < STEPS.length - 1 && (
              <button
                onClick={goNext}
                disabled={!canNext}
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-[0_1px_2px_oklch(0_0_0/0.1),0_2px_8px_oklch(0.205_0.042_265/0.15)] transition-all duration-150 hover:shadow-[0_1px_3px_oklch(0_0_0/0.12),0_4px_12px_oklch(0.205_0.042_265/0.2)] hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:hover:scale-100"
              >
                Next
                <ArrowRight className="size-4" />
              </button>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}
