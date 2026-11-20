import type { Metadata } from "next";
import { Navbar } from "@/components/layout/navbar";
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
            <Navbar />

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
