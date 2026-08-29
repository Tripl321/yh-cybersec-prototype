"use client";

import { useState } from "react";
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar, type Page } from "@/components/app-sidebar";
import { OverviewPage } from "@/components/dashboard/overview";
import { HardwarePage } from "@/components/dashboard/hardware";
import { InfrastructurePage } from "@/components/dashboard/infrastructure";
import { SecurityPage } from "@/components/dashboard/security";
import { ModelsPage } from "@/components/dashboard/models";
import { SettingsPage } from "@/components/dashboard/settings";
import { VisionDashboard } from "@/components/dashboard/vision";
import { ChatDashboard } from "@/components/dashboard/chat";

const TITLES: Record<Page, string> = {
  overview: "Overview",
  chat: "Chat",
  vision: "Vision",
  hardware: "Hardware",
  infrastructure: "Infrastructure",
  security: "Security",
  models: "Models",
  settings: "Settings",
};

export default function DashboardPage() {
  const [page, setPage] = useState<Page>("vision");

  return (
    <SidebarProvider>
      <AppSidebar active={page} onNavigate={setPage} />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex-1">
            <h1 className="text-sm font-semibold tracking-tight">{TITLES[page]}</h1>
          </div>
        </header>
        <main className="flex-1 overflow-auto">
          {page === "overview" && <OverviewPage />}
          {page === "chat" && <ChatDashboard />}
          {page === "vision" && <VisionDashboard />}
          {page === "hardware" && <HardwarePage />}
          {page === "infrastructure" && <InfrastructurePage />}
          {page === "security" && <SecurityPage />}
          {page === "models" && <ModelsPage />}
          {page === "settings" && <SettingsPage />}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
