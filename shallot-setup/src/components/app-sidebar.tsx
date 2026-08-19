"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";
import {
  ShieldCheck,
  LayoutDashboard,
  Cpu,
  Server,
  Shield,
  Brain,
  Settings,
  LogOut,
} from "lucide-react";

export type Page =
  | "overview"
  | "hardware"
  | "infrastructure"
  | "security"
  | "models"
  | "settings";

const NAV_ITEMS: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "hardware", label: "Hardware", icon: Cpu },
  { id: "infrastructure", label: "Infrastructure", icon: Server },
  { id: "security", label: "Security", icon: Shield },
  { id: "models", label: "Models", icon: Brain },
];

interface AppSidebarProps {
  active: Page;
  onNavigate: (page: Page) => void;
}

export function AppSidebar({ active, onNavigate }: AppSidebarProps) {
  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2.5 px-2 py-1.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10">
            <ShieldCheck className="size-4.5 text-primary" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-foreground">
              SHALLOT
            </span>
            <span className="text-[10px] text-muted-foreground">
              OT Access Control
            </span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs text-muted-foreground/60">
            Management
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
                <SidebarMenuItem key={id}>
                  <SidebarMenuButton
                    isActive={active === id}
                    onClick={() => onNavigate(id)}
                    className="cursor-pointer"
                  >
                    <Icon className="size-4" />
                    <span>{label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={() => onNavigate("settings")}
              isActive={active === "settings"}
              className="cursor-pointer"
            >
              <Settings className="size-4" />
              <span>Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
