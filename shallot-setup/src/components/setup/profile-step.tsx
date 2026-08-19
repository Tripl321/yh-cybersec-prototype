"use client";

import { User, Shield, Building2 } from "lucide-react";

export interface Profile {
  name: string;
  role: "admin" | "operator" | "technician";
  organization: string;
}

interface ProfileStepProps {
  profile: Profile;
  onChange: (profile: Profile) => void;
}

const ROLES = [
  { value: "admin" as const, label: "Admin", icon: Shield, desc: "Full access" },
  { value: "operator" as const, label: "Operator", icon: User, desc: "Standard ops" },
  { value: "technician" as const, label: "Technician", icon: Building2, desc: "Maintenance" },
] as const;

export function ProfileStep({ profile, onChange }: ProfileStepProps) {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted-foreground leading-relaxed">
        Set up your operator identity for access control and audit logging.
      </p>

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="name" className="text-sm font-medium text-foreground">
            Name
          </label>
          <input
            id="name"
            value={profile.name}
            onChange={(e) => onChange({ ...profile, name: e.target.value })}
            placeholder="Your name"
            className="rounded-xl border border-input/60 bg-background/50 px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 backdrop-blur-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary/40"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="org" className="text-sm font-medium text-foreground">
            Organization
          </label>
          <input
            id="org"
            value={profile.organization}
            onChange={(e) =>
              onChange({ ...profile, organization: e.target.value })
            }
            placeholder="e.g. YH Campus Norrköping"
            className="rounded-xl border border-input/60 bg-background/50 px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 backdrop-blur-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:border-primary/40"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium text-foreground">Role</label>
          <div className="grid grid-cols-3 gap-2.5">
            {ROLES.map(({ value, label, icon: Icon, desc }) => {
              const active = profile.role === value;
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => onChange({ ...profile, role: value })}
                  className={`group flex flex-col items-center gap-1.5 rounded-2xl border px-4 py-4 text-center transition-all duration-200 ${
                    active
                      ? "border-primary/30 bg-primary/5 shadow-[0_2px_12px_oklch(0.205_0.042_265/0.08)]"
                      : "border-border/50 bg-background/30 hover:border-border hover:bg-muted/30 hover:shadow-[0_1px_4px_oklch(0_0_0/0.04)]"
                  }`}
                >
                  <Icon
                    className={`size-5 transition-colors duration-200 ${
                      active
                        ? "text-primary"
                        : "text-muted-foreground/60 group-hover:text-muted-foreground"
                    }`}
                  />
                  <span
                    className={`text-sm font-medium transition-colors duration-200 ${
                      active ? "text-foreground" : "text-foreground/80"
                    }`}
                  >
                    {label}
                  </span>
                  <span className="text-xs text-muted-foreground/70">
                    {desc}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
