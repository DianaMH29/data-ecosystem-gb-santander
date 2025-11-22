import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  LayoutDashboard,
  Map,
  Clock,
  Users,
  CloudRain,
  MessageCircle,
  Brain,
  Menu,
  X,
  Shield,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Geografía",
    href: "/geografia",
    icon: Map,
  },
  {
    name: "Temporal",
    href: "/temporal",
    icon: Clock,
  },
  {
    name: "Víctimas",
    href: "/victimas",
    icon: Users,
  },
  {
    name: "Clima",
    href: "/clima",
    icon: CloudRain,
  },
  {
    name: "Predicciones",
    href: "/predicciones",
    icon: Brain,
  },
  {
    name: "Chatbot",
    href: "/chatbot",
    icon: MessageCircle,
  },
];

function NavItem({ item, onClick }) {
  const location = useLocation();
  const isActive = location.pathname === item.href;

  return (
    <NavLink
      to={item.href}
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all hover:bg-accent",
        isActive
          ? "bg-accent text-accent-foreground font-medium"
          : "text-muted-foreground"
      )}
    >
      <item.icon className="h-4 w-4" />
      {item.name}
    </NavLink>
  );
}

export function Sidebar({ className }) {
  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Logo */}
      <div className="flex h-16 items-center px-4 border-b">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg leading-none">Atlas del Crimen</span>
            <span className="text-xs text-muted-foreground">Santander</span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-4">
        <nav className="grid gap-1 px-2">
          {navigation.map((item) => (
            <NavItem key={item.href} item={item} />
          ))}
        </nav>
      </ScrollArea>

      {/* Footer */}
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground text-center">
          Datos de Seguridad
          <br />
          Departamento de Santander
        </p>
      </div>
    </div>
  );
}

export function MobileSidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={() => setOpen(true)}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />

          {/* Sidebar */}
          <div className="fixed inset-y-0 left-0 w-72 bg-background border-r shadow-lg">
            <div className="flex h-16 items-center justify-between px-4 border-b">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                  <Shield className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="font-bold">Atlas del Crimen</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <ScrollArea className="h-[calc(100vh-4rem)]">
              <nav className="grid gap-1 p-4">
                {navigation.map((item) => (
                  <NavItem
                    key={item.href}
                    item={item}
                    onClick={() => setOpen(false)}
                  />
                ))}
              </nav>
            </ScrollArea>
          </div>
        </div>
      )}
    </>
  );
}
