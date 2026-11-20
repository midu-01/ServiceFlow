import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "ServiceFlow | Real-Time Service Management",
  description: "Concurrent service request processing with live operational visibility",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>
          <div className="min-h-screen flex flex-col">
            <header className="border-b border-border bg-card/80 backdrop-blur px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg">
                  S
                </div>
                <div>
                  <h1 className="font-semibold text-lg leading-tight">ServiceFlow</h1>
                  <p className="text-xs text-muted-foreground opacity-70">
                    Real-Time Service Management
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-emerald-500"></span>
                  System Active
                </span>
              </div>
            </header>

            <main className="flex-1 container mx-auto px-6 py-8">
              {children}
            </main>

            <footer className="border-t border-border px-6 py-4 text-center text-xs opacity-60">
              ServiceFlow &copy; 2026. Enterprise Asynchronous Operations Platform.
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
