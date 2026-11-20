import { Metadata } from "next";
import { LoginForm } from "@/features/auth/login-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "Sign in | ServiceFlow",
  description: "Sign in to ServiceFlow real-time operations console",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-[calc(100vh-12rem)] items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="mx-auto h-12 w-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white font-bold text-2xl shadow-md">
            S
          </div>
          <h2 className="text-2xl font-bold tracking-tight">ServiceFlow Console</h2>
          <p className="text-xs text-muted-foreground opacity-75">
            Real-Time Asynchronous Service Request Management
          </p>
        </div>

        <Card className="shadow-lg border-border">
          <CardHeader className="space-y-1">
            <CardTitle className="text-lg font-semibold">Sign in</CardTitle>
            <CardDescription>
              Enter your credentials to access the operational dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LoginForm />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
