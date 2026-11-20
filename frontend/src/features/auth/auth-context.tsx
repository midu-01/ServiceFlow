"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { authKeys } from "@/lib/api/query-keys";
import { ApiResponse, User } from "@/types";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [tokenExists, setTokenExists] = useState<boolean>(true);

  // Check if token exists in localStorage initially
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("serviceflow_token");
      setTokenExists(!!stored);
    }
  }, []);

  // Fetch current user via REST API
  const { data, isLoading, error } = useQuery({
    queryKey: authKeys.me(),
    queryFn: () => apiClient<ApiResponse<User>>("/api/v1/auth/me"),
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: tokenExists,
  });

  const user = data?.data || null;
  const isAuthenticated = !!user;

  // Clear stale token if /api/v1/auth/me returns an authentication error
  useEffect(() => {
    if (error && typeof window !== "undefined") {
      localStorage.removeItem("serviceflow_token");
      setTokenExists(false);
    }
  }, [error]);

  const login = async (credentials: { username: string; password: string }) => {
    const res = await apiClient<ApiResponse<{ access_token: string; user: User }>>(
      "/api/v1/auth/login",
      {
        method: "POST",
        body: JSON.stringify(credentials),
      }
    );

    if (typeof window !== "undefined") {
      localStorage.setItem("serviceflow_token", res.data.access_token);
      setTokenExists(true);
    }

    // Set user in TanStack Query cache immediately
    queryClient.setQueryData(authKeys.me(), { data: res.data.user });
    router.push("/dashboard");
  };

  const logout = async () => {
    try {
      await apiClient("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors on logout
    }

    if (typeof window !== "undefined") {
      localStorage.removeItem("serviceflow_token");
      setTokenExists(false);
    }

    queryClient.removeQueries({ queryKey: authKeys.all });
    queryClient.clear();
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading: tokenExists && isLoading,
        isAuthenticated,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
