"use client";

import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/use-auth";
import { requestKeys } from "@/lib/api/query-keys";
import { ApiResponse, PaginatedResponse, ServiceRequest, WebSocketEventEnvelope } from "@/types";

export type WebSocketStatus = "connecting" | "connected" | "reconnecting" | "disconnected";

interface WebSocketContextType {
  status: WebSocketStatus;
  lastEvent: WebSocketEventEnvelope | null;
  recentEvents: WebSocketEventEnvelope[];
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [lastEvent, setLastEvent] = useState<WebSocketEventEnvelope | null>(null);
  const [recentEvents, setRecentEvents] = useState<WebSocketEventEnvelope[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const isExplicitCloseRef = useRef<boolean>(false);

  useEffect(() => {
    // Only connect when user is authenticated
    if (!isAuthenticated || !user) {
      if (wsRef.current) {
        isExplicitCloseRef.current = true;
        wsRef.current.close();
        wsRef.current = null;
      }
      setStatus("disconnected");
      return;
    }

    isExplicitCloseRef.current = false;

    const connectWebSocket = () => {
      if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
        return;
      }

      const token = typeof window !== "undefined" ? localStorage.getItem("serviceflow_token") : null;
      if (!token) {
        setStatus("disconnected");
        return;
      }

      const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
      const wsUrl = `${wsBase}/api/v1/ws/service-requests?token=${encodeURIComponent(token)}`;

      setStatus(reconnectAttemptsRef.current === 0 ? "connecting" : "reconnecting");

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        const hadPriorDisconnection = reconnectAttemptsRef.current > 0;
        reconnectAttemptsRef.current = 0;

        // Auto-reconnection state re-hydration: reload current data from PostgreSQL
        if (hadPriorDisconnection) {
          queryClient.invalidateQueries({ queryKey: requestKeys.all });
        }

        // Start 30s keepalive ping heartbeat
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          // Ignore keepalive pong frames
          if (event.data === '{"type":"pong"}' || event.data === "pong") {
            return;
          }

          const envelope: WebSocketEventEnvelope = JSON.parse(event.data);
          setLastEvent(envelope);
          setRecentEvents((prev) => [envelope, ...prev.slice(0, 19)]); // Keep last 20 events

          // Surgical TanStack Query cache synchronization
          const requestId = envelope.request_id;
          const patchData = envelope.data as Partial<ServiceRequest>;

          if (requestId && patchData) {
            // 1. Surgical update on Detail cache
            queryClient.setQueryData<ApiResponse<ServiceRequest>>(
              requestKeys.detail(requestId),
              (old) => {
                if (!old) return old;
                return {
                  data: {
                    ...old.data,
                    ...patchData,
                  },
                };
              }
            );

            // 2. Surgical update on List query caches
            queryClient.setQueriesData<PaginatedResponse<ServiceRequest>>(
              { queryKey: requestKeys.lists() },
              (old) => {
                if (!old) return old;
                return {
                  ...old,
                  data: old.data.map((item) =>
                    item.id === requestId ? { ...item, ...patchData } : item
                  ),
                };
              }
            );

            // If terminal state or new creation, invalidate queries to synchronize counts
            if (
              envelope.event_type === "service_request.created" ||
              envelope.event_type === "service_request.completed" ||
              envelope.event_type === "service_request.failed" ||
              envelope.event_type === "service_request.cancelled"
            ) {
              queryClient.invalidateQueries({ queryKey: requestKeys.all });
            }
          }
        } catch {
          // Discard unparseable text
        }
      };

      ws.onclose = () => {
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);

        if (!isExplicitCloseRef.current && isAuthenticated) {
          setStatus("reconnecting");
          // Exponential backoff: 1s, 2s, 4s, 8s, up to 30s
          const attempts = reconnectAttemptsRef.current;
          const delay = Math.min(1000 * Math.pow(2, attempts), 30000);
          reconnectAttemptsRef.current += 1;

          if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, delay);
        } else {
          setStatus("disconnected");
        }
      };

      ws.onerror = () => {
        // ws.onclose handles the reconnection logic
      };
    };

    connectWebSocket();

    return () => {
      isExplicitCloseRef.current = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isAuthenticated, user, queryClient]);

  return (
    <WebSocketContext.Provider value={{ status, lastEvent, recentEvents }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
}
