"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, PlusCircle, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useWebSocket } from "@/hooks/use-websocket";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const { user: currentUser, logout } = useAuth();
  const { status: wsStatus } = useWebSocket();

  const isOperator = currentUser?.role === "OPERATOR";
  const requestsLabel = isOperator ? "My Requests" : "All Requests";

  const navLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/requests", label: requestsLabel },
  ];

  const wsBadgeConfig = {
    connected: {
      color: "text-emerald-500 animate-pulse",
      text: "Live Sync",
      title: "Real-time WebSocket stream active",
    },
    reconnecting: {
      color: "text-amber-500 animate-pulse",
      text: "Reconnecting...",
      title: "Reconnecting to real-time stream",
    },
    connecting: {
      color: "text-blue-500 animate-pulse",
      text: "Connecting...",
      title: "Establishing real-time connection",
    },
    disconnected: {
      color: "text-slate-400",
      text: "Standby",
      title: "WebSocket disconnected (REST polling disabled)",
    },
  }[wsStatus] || {
    color: "text-slate-400",
    text: "Standby",
    title: "WebSocket disconnected",
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-card/90 backdrop-blur-md">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-sm group-hover:scale-105 transition-transform">
              S
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight">ServiceFlow</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400">
                Operations
              </span>
            </div>
          </Link>

          {/* Role-Aware Navigation Links */}
          {currentUser && (
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const isActive = pathname.startsWith(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-slate-200/60 dark:bg-slate-800 text-foreground font-semibold"
                        : "text-muted-foreground opacity-75 hover:opacity-100 hover:bg-slate-100 dark:hover:bg-slate-800/50"
                    )}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          )}
        </div>

        {/* Action Controls & Session Profile */}
        <div className="flex items-center gap-3">
          {/* Real-time WebSocket connection beacon */}
          <div
            className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border border-border"
            title={wsBadgeConfig.title}
          >
            <Radio className={cn("h-3.5 w-3.5", wsBadgeConfig.color)} />
            <span className="hidden sm:inline text-xs opacity-75">
              {wsBadgeConfig.text}
            </span>
          </div>

          {currentUser ? (
            <>
              {/* New Request CTA */}
              <Link href="/requests/new">
                <Button size="sm" className="gap-1.5">
                  <PlusCircle className="h-4 w-4" />
                  <span className="hidden sm:inline">New Request</span>
                </Button>
              </Link>

              {/* User Identity Chip */}
              <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-border">
                <div className="flex flex-col text-right">
                  <span className="text-xs font-semibold leading-tight">{currentUser.username}</span>
                  <span className="text-[10px] text-muted-foreground opacity-70 leading-tight">
                    {currentUser.role}
                  </span>
                </div>
                <Badge variant="secondary" className="text-[10px] uppercase font-bold tracking-wider">
                  {currentUser.role}
                </Badge>
              </div>

              {/* Logout Button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => logout()}
                title="Sign out of ServiceFlow"
                className="text-muted-foreground hover:text-rose-600"
              >
                <LogOut className="h-4 w-4" />
                <span className="sr-only">Sign out</span>
              </Button>
            </>
          ) : (
            <Link href="/login">
              <Button size="sm" variant="outline">
                Sign in
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
