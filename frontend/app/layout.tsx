import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";
import CursorGlow from "@/components/CursorGlow";
import FloatingChat from "@/components/FloatingChat";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CarDealsAI - Find Real Car Lease Deals in LA",
  description: "AI-powered search for Toyota, Honda, and Tesla lease and finance offers in Los Angeles. Every deal links to its source.",
  keywords: ["Toyota", "Honda", "Tesla", "lease", "car deals", "Los Angeles", "AI", "finance"],
  openGraph: {
    title: "CarDealsAI - Find Real Car Lease Deals",
    description: "Search current Toyota, Honda, and Tesla offers in LA. Every deal links to its source.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <CursorGlow />
          <Header />
          <main className="min-h-screen pt-16">
            {children}
          </main>
          <FloatingChat />
        </AuthProvider>
      </body>
    </html>
  );
}
