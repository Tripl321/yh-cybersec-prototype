"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export interface Step {
  id: string;
  title: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (index: number) => void;
}

export function Stepper({ steps, currentStep, onStepClick }: StepperProps) {
  return (
    <nav aria-label="Setup progress" className="w-full">
      <ol className="flex items-center gap-1">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isClickable = index <= currentStep;

          return (
            <li
              key={step.id}
              className={cn(
                "flex flex-1 items-center gap-1.5",
                index < steps.length - 1 && "after:h-px after:flex-1 after:bg-border/60"
              )}
            >
              <button
                type="button"
                onClick={() => isClickable && onStepClick?.(index)}
                disabled={!isClickable}
                className={cn(
                  "flex items-center gap-2 rounded-full py-1.5 pl-1.5 pr-3 text-sm font-medium transition-colors duration-200",
                  isClickable
                    ? "cursor-pointer hover:bg-muted/50"
                    : "cursor-not-allowed opacity-30",
                  isCurrent && "bg-primary/5 text-primary",
                  isCompleted && "text-primary/60"
                )}
              >
                <div
                  className={cn(
                    "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-all duration-200",
                    isCompleted &&
                      "bg-primary text-primary-foreground shadow-[0_1px_2px_oklch(0_0_0/0.15)]",
                    isCurrent &&
                      "bg-primary text-primary-foreground shadow-[0_2px_8px_oklch(0.205_0.042_265/0.25)]",
                    !isCompleted &&
                      !isCurrent &&
                      "bg-muted text-muted-foreground"
                  )}
                >
                  {isCompleted ? <Check className="size-3.5" strokeWidth={2.5} /> : index + 1}
                </div>
                <span className="hidden sm:inline">{step.title}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
