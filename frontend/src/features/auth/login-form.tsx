"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, Lock, LogIn, User, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useAuth } from "@/hooks/use-auth";
import { ApiClientError } from "@/lib/api/client";

const loginSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsSubmitting(true);
    setServerError(null);

    try {
      await login(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setServerError(err.message);
      } else {
        setServerError("Failed to sign in. Please verify your network connection.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoCredentials = (role: "operator" | "supervisor" | "admin") => {
    const creds = {
      operator: { username: "operator", password: "OperatorSecret123!" },
      supervisor: { username: "supervisor", password: "SupervisorSecret123!" },
      admin: { username: "admin", password: "AdminSecret123!" },
    };
    setValue("username", creds[role].username, { shouldValidate: true });
    setValue("password", creds[role].password, { shouldValidate: true });
    setServerError(null);
  };

  return (
    <div className="w-full space-y-6">
      {serverError && (
        <Alert variant="destructive">
          <AlertTitle>Authentication Failed</AlertTitle>
          <AlertDescription>{serverError}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Username
          </label>
          <div className="relative">
            <Input
              type="text"
              placeholder="e.g. operator"
              autoComplete="username"
              error={errors.username?.message}
              {...register("username")}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
            Password
          </label>
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              autoComplete="current-password"
              error={errors.password?.message}
              className="pr-10"
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3 top-2.5 text-muted-foreground opacity-60 hover:opacity-100 transition-opacity focus:outline-none"
              title={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <Button type="submit" className="w-full gap-2 mt-2" isLoading={isSubmitting}>
          <LogIn className="h-4 w-4" />
          Sign in to ServiceFlow
        </Button>
      </form>

      {/* Quick Demo Credentials Assistant */}
      <div className="pt-4 border-t border-border space-y-2.5">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
          <Sparkles className="h-3.5 w-3.5 text-amber-500" />
          <span>Quick Demo Profiles:</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fillDemoCredentials("operator")}
            className="text-xs"
          >
            Operator
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fillDemoCredentials("supervisor")}
            className="text-xs"
          >
            Supervisor
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fillDemoCredentials("admin")}
            className="text-xs"
          >
            Admin
          </Button>
        </div>
      </div>
    </div>
  );
}
